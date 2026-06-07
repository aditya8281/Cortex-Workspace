from __future__ import annotations

import base64
import logging
import os
import shutil
import threading
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from argon2.low_level import Type, hash_secret_raw
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from backend.app.core.storage_abstraction import get_user_storage, validate_storage_path

logger = logging.getLogger(__name__)


class VaultManager:
    """Per-user encrypted vault manager."""

    CATEGORIES = ["documents", "images", "certificates", "notes", "others", "metadata", "temp"]

    def __init__(self):
        self._lock = threading.RLock()

    def get_vault_path(self, user_id: int) -> Path:
        return get_user_storage(user_id).vault

    def validate_vault_path(self, path: Path) -> None:
        validate_storage_path(path)

    def ensure_vault_structure(self, user_id: int) -> None:
        root = self.get_vault_path(user_id)
        root.mkdir(parents=True, exist_ok=True)
        for category in self.CATEGORIES:
            (root / category).mkdir(parents=True, exist_ok=True)

    def get_path(self, user_id: int, category: str, filename: Optional[str] = None) -> Path:
        if category not in self.CATEGORIES:
            raise ValueError(f"Invalid vault category: {category}")

        root = self.get_vault_path(user_id)
        category_dir = (root / category).resolve()
        target_path = (category_dir / filename).resolve() if filename else category_dir
        try:
            target_path.relative_to(root)
        except ValueError as exc:
            raise PermissionError("Path traversal detected outside user vault") from exc
        return target_path

    def _derive_key(self, password: str, salt: bytes) -> bytes:
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

    def write_encrypted_file(self, user_id: int, category: str, filename: str, data: bytes, password: str) -> None:
        path = self.get_path(user_id, category, filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(self.encrypt_bytes(data, password))

    def read_encrypted_file(self, user_id: int, category: str, filename: str, password: str) -> bytes:
        path = self.get_path(user_id, category, filename)
        if not path.exists():
            raise FileNotFoundError(f"Vault file '{filename}' not found under category '{category}'")
        return self.decrypt_bytes(path.read_bytes(), password)

    def delete_file(self, user_id: int, category: str, filename: str) -> None:
        path = self.get_path(user_id, category, filename)
        if path.exists() and path.is_file():
            path.unlink()

    def exists(self, user_id: int, category: str, filename: Optional[str] = None) -> bool:
        try:
            return self.get_path(user_id, category, filename).exists()
        except Exception:
            return False

    def list_files(self, user_id: int, category: str) -> List[str]:
        dir_path = self.get_path(user_id, category)
        if not dir_path.exists():
            return []
        return [f.name for f in dir_path.iterdir() if f.is_file()]

    def export_vault(self, user_id: int, zip_path_str: str) -> str:
        root_dir = self.get_vault_path(user_id)
        zip_path = Path(zip_path_str).resolve()
        zip_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file_path in root_dir.rglob("*"):
                if file_path.is_file():
                    zipf.write(file_path, file_path.relative_to(root_dir))
        return str(zip_path)

    def import_vault(self, user_id: int, zip_path_str: str) -> None:
        zip_path = Path(zip_path_str).resolve()
        if not zip_path.exists():
            raise FileNotFoundError(f"Import zip not found at {zip_path}")
        root_dir = self.get_vault_path(user_id)
        if root_dir.exists():
            shutil.rmtree(root_dir)
        root_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path, "r") as zipf:
            zipf.extractall(root_dir)


vault_manager = VaultManager()

