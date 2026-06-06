import os
import shutil
import zipfile
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import threading
import base64

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from argon2.low_level import hash_secret_raw, Type

from backend.app.core.paths import PROJECT_ROOT
from backend.app.core.config import settings
from backend.app.core.system_paths import (
    LINUX_BLOCKED_SYSTEM_PATHS,
    MACOS_BLOCKED_SYSTEM_PATHS,
    WINDOWS_BLOCKED_SYSTEM_PATHS,
)

logger = logging.getLogger(__name__)


class VaultManager:
    """
    User Vault Manager: private, encrypted, password-gated storage.
    Stores encrypted files under a separate VAULT_PATH from shared memory.
    """

    CATEGORIES = [
        "documents",
        "images",
        "certificates",
        "notes",
        "others",
        "metadata",
        "temp",
    ]

    @staticmethod
    def get_blocked_system_paths() -> set:
        import platform
        system = platform.system()
        if system == "Linux":
            return LINUX_BLOCKED_SYSTEM_PATHS
        elif system == "Darwin":
            return MACOS_BLOCKED_SYSTEM_PATHS
        elif system == "Windows":
            return WINDOWS_BLOCKED_SYSTEM_PATHS
        else:
            return LINUX_BLOCKED_SYSTEM_PATHS

    def __init__(self):
        self._lock = threading.RLock()
        # Initialize default vault path
        self.ensure_vault_structure()

    def get_vault_path(self) -> Path:
        env_path = (
            settings.VAULT_PATH
            or os.environ.get("CORTEX_VAULT_PATH")
        )
        if env_path:
            return Path(env_path).expanduser().resolve()
        # default project-local path
        return (PROJECT_ROOT / ".cortex_vault").resolve()

    def validate_vault_path(self, path: Path) -> None:
        resolved = path.expanduser().resolve()
        resolved_str = str(resolved)
        for sys_path in self.get_blocked_system_paths():
            if resolved_str.startswith(sys_path) or resolved_str == sys_path:
                raise ValueError(f"Security exception: Cannot configure vault path inside system directory '{sys_path}'")

        try:
            resolved.mkdir(parents=True, exist_ok=True)
            test_file = resolved / ".write_test"
            test_file.write_text("vault", encoding="utf-8")
            test_file.unlink()
        except Exception as e:
            raise ValueError(f"Permission error: Target directory '{path}' is not writeable. Details: {e}")

    def ensure_vault_structure(self) -> None:
        root = self.get_vault_path()
        root.mkdir(parents=True, exist_ok=True)
        for category in self.CATEGORIES:
            (root / category).mkdir(parents=True, exist_ok=True)

    def get_path(self, category: str, filename: Optional[str] = None) -> Path:
        if category not in self.CATEGORIES:
            raise ValueError(f"Invalid vault category: {category}")

        root = self.get_vault_path()
        category_dir = (root / category).resolve()
        if filename:
            target_path = (category_dir / filename).resolve()
        else:
            target_path = category_dir

        try:
            target_path.relative_to(root)
        except ValueError:
            raise PermissionError(f"Path traversal detected outside vault for '{filename}'")

        target_str = str(target_path)
        for sys_path in self.get_blocked_system_paths():
            if target_str.startswith(sys_path) or target_str == sys_path:
                raise PermissionError(f"Access block to system directory '{sys_path}'")

        return target_path

    # =============== Encryption helpers ===============
    def _derive_key(self, password: str, salt: bytes) -> bytes:
        # Argon2id raw output 32 bytes for AES-256 key
        return hash_secret_raw(
            password.encode("utf-8"),
            salt,
            time_cost=3,
            memory_cost=65536,
            parallelism=1,
            hash_len=32,
            type=Type.ID,
        )

    def encrypt_bytes(self, plaintext: bytes, password: str) -> bytes:
        # File format: salt(16) || nonce(12) || ciphertext
        salt = os.urandom(16)
        key = self._derive_key(password, salt)
        aesgcm = AESGCM(key)
        nonce = os.urandom(12)
        ct = aesgcm.encrypt(nonce, plaintext, None)
        return salt + nonce + ct

    def decrypt_bytes(self, blob: bytes, password: str) -> bytes:
        if len(blob) < 28:
            raise ValueError("Invalid encrypted blob")
        salt = blob[:16]
        nonce = blob[16:28]
        ct = blob[28:]
        key = self._derive_key(password, salt)
        aesgcm = AESGCM(key)
        return aesgcm.decrypt(nonce, ct, None)

    # =============== File operations ===============
    def write_encrypted_file(self, category: str, filename: str, data: bytes, password: str) -> None:
        path = self.get_path(category, filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        enc = self.encrypt_bytes(data, password)
        with open(path, "wb") as f:
            f.write(enc)

    def read_encrypted_file(self, category: str, filename: str, password: str) -> bytes:
        path = self.get_path(category, filename)
        if not path.exists():
            raise FileNotFoundError(f"Vault file '{filename}' not found under category '{category}'")
        blob = path.read_bytes()
        return self.decrypt_bytes(blob, password)

    def delete_file(self, category: str, filename: str) -> None:
        path = self.get_path(category, filename)
        if path.exists() and path.is_file():
            path.unlink()

    def exists(self, category: str, filename: Optional[str] = None) -> bool:
        try:
            return self.get_path(category, filename).exists()
        except Exception:
            return False

    def list_files(self, category: str) -> List[str]:
        dir_path = self.get_path(category)
        if not dir_path.exists():
            return []
        return [f.name for f in dir_path.iterdir() if f.is_file()]

    def export_vault(self, zip_path_str: str) -> str:
        root_dir = self.get_vault_path()
        zip_path = Path(zip_path_str).resolve()
        zip_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in root_dir.rglob('*'):
                if file_path.is_file():
                    zipf.write(file_path, file_path.relative_to(root_dir))
        return str(zip_path)

    def import_vault(self, zip_path_str: str) -> None:
        zip_path = Path(zip_path_str).resolve()
        if not zip_path.exists():
            raise FileNotFoundError(f"Import zip not found at {zip_path}")
        root_dir = self.get_vault_path()
        if root_dir.exists():
            shutil.rmtree(root_dir)
        root_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            zipf.extractall(root_dir)


# Global singleton
vault_manager = VaultManager()
