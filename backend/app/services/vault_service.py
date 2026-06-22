"""Vault Service — Encrypted personal document locker.

The vault is NOT part of Cortex Memory. It never participates in RAG,
embeddings, indexing, or AI processing. It is simply an encrypted
personal document locker for storing and retrieving sensitive files.

Two-password architecture:
  1. Login Password  — account authentication
  2. Vault Password  — private vault access
"""

from __future__ import annotations

import base64
import hashlib
import logging
import os
import shutil
from pathlib import Path
from threading import Lock

from cryptography.fernet import Fernet
from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.app.models.user import User

logger = logging.getLogger(__name__)

# Maximum file size for vault uploads: 50 MB
MAX_VAULT_FILE_SIZE = 50 * 1024 * 1024

# ── In-memory vault key cache ────────────────────────────────────────
# After unlock, the password is cached in memory so upload/download can
# encrypt/decrypt with per-file salt derivation without re-sending the
# password on every request.  The cache is cleared on lock/logout.
_vault_cache_lock = Lock()


class SecurePasswordCache(dict):
    """Dict-like cache that stores passwords as bytearrays and wipes memory on pop.

    Accessors (`get`, `__getitem__`) return `str` for backwards compatibility.
    """

    def __setitem__(self, key, value):
        if isinstance(value, str):
            value = bytearray(value.encode())
        super().__setitem__(key, value)

    def get(self, key, default=None):
        val = super().get(key, None)
        if val is None:
            return default
        if isinstance(val, (bytes, bytearray)):
            try:
                return val.decode()
            except Exception:
                return default
        return val

    def __getitem__(self, key):
        val = super().__getitem__(key)
        if isinstance(val, (bytes, bytearray)):
            return val.decode()
        return val

    def pop(self, key, default=None):
        val = super().pop(key, default)
        if val is default:
            return default
        ret = val
        if isinstance(val, (bytes, bytearray)):
            try:
                ret = val.decode()
            except Exception:
                ret = default
            # wipe underlying bytearray
            try:
                for i in range(len(val)):
                    val[i] = 0
            except Exception:
                pass
        return ret


_vault_passwords: SecurePasswordCache = SecurePasswordCache()

ALLOWED_VAULT_EXTENSIONS = {
    ".txt",
    ".md",
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
    ".csv",
    ".json",
    ".xml",
    ".yaml",
    ".yml",
    ".zip",
    ".tar",
    ".gz",
    ".7z",
    ".rar",
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
    ".svg",
    ".mp3",
    ".mp4",
    ".wav",
    ".avi",
    ".mov",
    ".py",
    ".js",
    ".ts",
    ".jsx",
    ".tsx",
    ".html",
    ".css",
    ".sql",
    ".sh",
    ".bat",
    ".conf",
    ".ini",
    ".toml",
    ".key",
    ".pem",
    ".crt",
    ".env",
}


# ── Encryption helpers ───────────────────────────────────────────────


def _derive_vault_key(vault_password: str, salt: bytes | None = None) -> tuple[Fernet, bytes]:
    """Derive a Fernet key from the vault password using PBKDF2."""
    if salt is None:
        salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac(
        "sha256",
        vault_password.encode(),
        salt,
        iterations=600_000,
    )
    fernet_key = Fernet(base64.urlsafe_b64encode(key[:32]))
    return fernet_key, salt


def encrypt_bytes(data: bytes, vault_password: str) -> bytes:
    """Encrypt data using vault-password-derived Fernet key."""
    fernet, salt = _derive_vault_key(vault_password)
    encrypted = fernet.encrypt(data)
    return salt + encrypted  # Prepend salt so we can decrypt later


def decrypt_bytes(data: bytes, vault_password: str) -> bytes:
    """Decrypt data using vault-password-derived Fernet key."""
    salt = data[:16]
    encrypted = data[16:]
    fernet, _ = _derive_vault_key(vault_password, salt)
    return fernet.decrypt(encrypted)


# ── Path resolution ──────────────────────────────────────────────────


def _get_user_vault_dir(db: Session, user_id: int) -> Path:
    """Resolve the vault directory for a user from the central pointer DB."""
    from backend.app.services.storage_registry import get_registry_for_user

    registry = get_registry_for_user(db, user_id)
    if not registry:
        raise HTTPException(status_code=404, detail="No storage registered for this user")
    vault_dir = Path(registry.storage_root) / "vault"
    vault_dir.mkdir(parents=True, exist_ok=True)
    return vault_dir


# ── Lock / Unlock ────────────────────────────────────────────────────


def verify_vault_password(db: Session, user: User, password: str) -> bool:
    """Verify the vault password against the stored hash."""
    if not user.vault_password_hash:
        return False
    from backend.app.core.security import verify_password

    return verify_password(password, user.vault_password_hash)


def lock_vault(db: Session, user: User) -> None:
    """Lock the vault — clears the cached decryption key."""
    # Do not persist lock state to the DB. Vault lock state is intentionally
    # kept ephemeral in-memory only so it never survives browser refreshes
    # or application restarts.
    try:
        user.vault_locked = True
        db.add(user)
        db.commit()
    except Exception:
        logger.exception("Failed to lock vault for user %d", user.id)
        db.rollback()
    with _vault_cache_lock:
        _vault_passwords.pop(user.id, None)
    logger.info("Vault locked and key cleared for user %d", user.id)


def unlock_vault(db: Session, user: User, vault_password: str) -> bool:
    """Unlock the vault after verifying the vault password.

    On success, caches the password in memory so subsequent upload/download
    operations can encrypt/decrypt with per-file salt derivation without
    re-sending the password.
    """
    if not verify_vault_password(db, user, vault_password):
        return False
    # Keep the transient `vault_locked` flag in the ORM object for in-process
    # callers (tests, immediate API logic) but do not rely on persisting it
    # across requests. We attempt a DB write but it's non-fatal if it fails.
    user.vault_locked = False
    try:
        db.add(user)
        db.commit()
    except Exception:
        db.rollback()
    # Cache the password in-memory for decryption operations. Stored as
    # a bytearray internally; accessors return `str` for compatibility.
    with _vault_cache_lock:
        _vault_passwords[user.id] = vault_password
    logger.info("Vault unlocked for user %d", user.id)
    return True


def _get_cached_password(user_id: int) -> str | None:
    """Return the cached vault password for a user, or None if not cached."""
    with _vault_cache_lock:
        return _vault_passwords.get(user_id)


def is_vault_unlocked(user: User) -> bool:
    """Check if the vault is currently unlocked.

    The vault is considered unlocked only if the in-memory password cache
    contains a password for the user. We avoid persisting unlocked state in
    the database to ensure unlocks do not survive browser refreshes or
    process restarts.
    """
    return _get_cached_password(user.id) is not None


def _require_unlocked(user: User) -> None:
    """Raise if the vault is locked or key not cached."""
    if user.vault_locked:
        raise HTTPException(status_code=403, detail="Vault is locked. Please unlock to access vault files.")
    if _get_cached_password(user.id) is None:
        raise HTTPException(status_code=403, detail="Vault key not available. Please unlock again.")


# ── File Operations ──────────────────────────────────────────────────


def get_vault_metadata(user_id: int, vault_dir: Path) -> dict:
    """Read and decrypt vault metadata if it exists."""
    metadata_file = vault_dir / ".metadata.bin"
    if not metadata_file.exists():
        return {"favorites": [], "tags": {}}
    try:
        password = _get_cached_password(user_id)
        if not password:
            return {"favorites": [], "tags": {}}
        encrypted_bytes = metadata_file.read_bytes()
        decrypted_bytes = decrypt_bytes(encrypted_bytes, password)
        import json

        return json.loads(decrypted_bytes.decode())
    except Exception as e:
        logger.error("Error reading vault metadata for user %d: %s", user_id, e)
        return {"favorites": [], "tags": {}}


def save_vault_metadata(user_id: int, vault_dir: Path, metadata: dict) -> None:
    """Encrypt and save vault metadata."""
    metadata_file = vault_dir / ".metadata.bin"
    try:
        password = _get_cached_password(user_id)
        if not password:
            return
        import json

        data_bytes = json.dumps(metadata).encode()
        encrypted_bytes = encrypt_bytes(data_bytes, password)
        metadata_file.write_bytes(encrypted_bytes)
    except Exception as e:
        logger.error("Error saving vault metadata for user %d: %s", user_id, e)


def update_vault_metadata(
    db: Session, user_id: int, file_path: str, favorite: bool | None = None, tags: list[str] | None = None
) -> dict:
    """Update favorite status or tags for a specific file path."""
    vault_dir = _get_user_vault_dir(db, user_id)
    metadata = get_vault_metadata(user_id, vault_dir)

    favorites = metadata.setdefault("favorites", [])
    tags_map = metadata.setdefault("tags", {})

    clean_path = file_path.strip("/")

    if favorite is not None:
        if favorite:
            if clean_path not in favorites:
                favorites.append(clean_path)
        else:
            if clean_path in favorites:
                favorites.remove(clean_path)

    if tags is not None:
        tags_map[clean_path] = tags

    save_vault_metadata(user_id, vault_dir, metadata)

    return {
        "path": clean_path,
        "favorite": clean_path in favorites,
        "tags": tags_map.get(clean_path, []),
    }


def list_vault_files(db: Session, user_id: int, folder: str = "/", recursive: bool = False) -> list[dict]:
    """List files and folders in the vault. Can recursively find all files."""
    vault_dir = _get_user_vault_dir(db, user_id)
    target = (vault_dir / folder.strip("/")).resolve()
    if not str(target).startswith(str(vault_dir.resolve())):
        from fastapi import HTTPException

        raise HTTPException(status_code=403, detail="Access denied")
    if not target.exists():
        return []

    metadata = get_vault_metadata(user_id, vault_dir)
    favorites = metadata.get("favorites", [])
    tags_map = metadata.get("tags", {})

    entries = []
    iterator = target.rglob("*") if recursive else target.iterdir()

    # Materialize and sort items for consistency
    items_list = sorted(list(iterator))
    for item in items_list:
        if item.name.startswith(".") or ".metadata.bin" in item.name:
            continue
        rel = item.relative_to(vault_dir)
        rel_str = str(rel)
        entries.append(
            {
                "name": item.name,
                "path": rel_str,
                "is_dir": item.is_dir(),
                "size": item.stat().st_size if item.is_file() else 0,
                "modified": item.stat().st_mtime,
                "created": item.stat().st_ctime,
                "favorite": rel_str in favorites,
                "tags": tags_map.get(rel_str, []),
            }
        )
    return entries


def upload_vault_file(db: Session, user_id: int, file_path: str, content: bytes) -> dict:
    """Upload a file to the vault, encrypting with per-file salt derivation."""
    if len(content) > MAX_VAULT_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {MAX_VAULT_FILE_SIZE // (1024 * 1024)} MB",
        )

    ext = Path(file_path).suffix.lower()
    if ext and ext not in ALLOWED_VAULT_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type '{ext}' is not allowed in the vault")

    vault_dir = _get_user_vault_dir(db, user_id)
    target = (vault_dir / file_path.strip("/")).resolve()
    if not str(target).startswith(str(vault_dir.resolve())):
        raise HTTPException(status_code=403, detail="Access denied")
    target.parent.mkdir(parents=True, exist_ok=True)

    password = _get_cached_password(user_id)
    if not password:
        raise HTTPException(
            status_code=403, detail="Vault is locked or key unavailable. Unlock the vault before uploading files."
        )

    # Encrypt and write
    encrypted_content = encrypt_bytes(content, password)
    target.write_bytes(encrypted_content)

    return {
        "name": target.name,
        "path": str(target.relative_to(vault_dir)),
        "size": len(encrypted_content),
    }


def download_vault_file(db: Session, user_id: int, file_path: str) -> bytes:
    """Download and decrypt a vault file using the cached password. Returns raw bytes."""
    vault_dir = _get_user_vault_dir(db, user_id)
    target = (vault_dir / file_path.strip("/")).resolve()
    if not str(target).startswith(str(vault_dir.resolve())):
        raise HTTPException(status_code=403, detail="Access denied")
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    content = target.read_bytes()
    password = _get_cached_password(user_id)
    if password:
        try:
            content = decrypt_bytes(content, password)
        except Exception as e:
            logger.warning("Vault decryption failed for user %d file %s (may be unencrypted): %s", user_id, file_path, e)
    return content


def delete_vault_file(db: Session, user_id: int, file_path: str) -> bool:
    """Delete a file or directory from the vault, and clean up metadata."""
    vault_dir = _get_user_vault_dir(db, user_id)
    target = (vault_dir / file_path.strip("/")).resolve()
    if not str(target).startswith(str(vault_dir.resolve())):
        return False

    deleted = False
    if target.is_file():
        target.unlink()
        deleted = True
    elif target.is_dir():
        shutil.rmtree(target)
        deleted = True

    if deleted:
        # Clean up metadata
        metadata = get_vault_metadata(user_id, vault_dir)
        favorites = metadata.get("favorites", [])
        tags_map = metadata.get("tags", {})

        clean_path = file_path.strip("/")

        new_favorites = [f for f in favorites if f != clean_path and not f.startswith(clean_path + "/")]
        new_tags = {p: t for p, t in tags_map.items() if p != clean_path and not p.startswith(clean_path + "/")}

        metadata["favorites"] = new_favorites
        metadata["tags"] = new_tags
        save_vault_metadata(user_id, vault_dir, metadata)

    return deleted


def rename_vault_item(db: Session, user_id: int, old_path: str, new_name: str) -> dict:
    """Rename a file or folder in the vault, and sync metadata paths."""
    vault_dir = _get_user_vault_dir(db, user_id)
    old = (vault_dir / old_path.strip("/")).resolve()
    if not str(old).startswith(str(vault_dir.resolve())):
        raise HTTPException(status_code=403, detail="Access denied")
    if not old.exists():
        raise HTTPException(status_code=404, detail="Item not found")
    if "/" in new_name or "\\" in new_name or new_name in (".", ".."):
        raise HTTPException(status_code=400, detail="Invalid name: path separators not allowed")
    if not new_name:
        raise HTTPException(status_code=400, detail="Name cannot be empty")
    new = old.parent / new_name
    if not str(new.resolve()).startswith(str(vault_dir.resolve())):
        raise HTTPException(status_code=403, detail="Access denied")
    old.rename(new)

    old_rel = str(old.relative_to(vault_dir))
    new_rel = str(new.relative_to(vault_dir))

    # Update metadata
    metadata = get_vault_metadata(user_id, vault_dir)
    favorites = metadata.get("favorites", [])
    tags_map = metadata.get("tags", {})

    new_favorites = []
    for f in favorites:
        if f == old_rel:
            new_favorites.append(new_rel)
        elif f.startswith(old_rel + "/"):
            new_favorites.append(new_rel + f[len(old_rel) :])
        else:
            new_favorites.append(f)

    new_tags = {}
    for p, t in tags_map.items():
        if p == old_rel:
            new_tags[new_rel] = t
        elif p.startswith(old_rel + "/"):
            new_tags[new_rel + p[len(old_rel) :]] = t
        else:
            new_tags[p] = t

    metadata["favorites"] = new_favorites
    metadata["tags"] = new_tags
    save_vault_metadata(user_id, vault_dir, metadata)

    return {
        "name": new.name,
        "path": new_rel,
    }


def create_vault_folder(db: Session, user_id: int, folder_path: str) -> dict:
    """Create a folder in the vault."""
    vault_dir = _get_user_vault_dir(db, user_id)
    target = (vault_dir / folder_path.strip("/")).resolve()
    if not str(target).startswith(str(vault_dir.resolve())):
        raise HTTPException(status_code=403, detail="Access denied")
    target.mkdir(parents=True, exist_ok=True)
    return {
        "name": target.name,
        "path": str(target.relative_to(vault_dir)),
    }


def search_vault_files(db: Session, user_id: int, query: str) -> list[dict]:
    """Search vault files by name."""
    vault_dir = _get_user_vault_dir(db, user_id)
    metadata = get_vault_metadata(user_id, vault_dir)
    favorites = metadata.get("favorites", [])
    tags_map = metadata.get("tags", {})

    results = []
    query_lower = query.lower()
    for item in vault_dir.rglob("*"):
        if item.name.startswith(".") or ".metadata.bin" in item.name:
            continue
        if query_lower in item.name.lower():
            rel = item.relative_to(vault_dir)
            rel_str = str(rel)
            results.append(
                {
                    "name": item.name,
                    "path": rel_str,
                    "is_dir": item.is_dir(),
                    "size": item.stat().st_size if item.is_file() else 0,
                    "modified": item.stat().st_mtime,
                    "created": item.stat().st_ctime,
                    "favorite": rel_str in favorites,
                    "tags": tags_map.get(rel_str, []),
                }
            )
    return results


def change_vault_password(db: Session, user: User, old_pw: str, new_pw: str) -> bool:
    """Safely rotate the vault password and re-encrypt all files and metadata."""
    if not verify_vault_password(db, user, old_pw):
        return False

    # Check password strength
    from backend.app.core.security import hash_password, validate_password_strength

    if not validate_password_strength(new_pw):
        raise HTTPException(status_code=400, detail="New vault password does not meet strength requirements")

    vault_dir = _get_user_vault_dir(db, user.id)

    # Gather all files in the vault (recursively)
    files_to_rekey = []
    for item in vault_dir.rglob("*"):
        if item.name.startswith(".") or ".metadata.bin" in item.name:
            continue
        if item.is_file():
            files_to_rekey.append(item)

    # Try reading metadata too
    metadata_file = vault_dir / ".metadata.bin"
    has_metadata = metadata_file.exists()

    # Decrypt all files into memory first to ensure no partial updates
    decrypted_files = {}
    for item in files_to_rekey:
        content = item.read_bytes()
        try:
            decrypted = decrypt_bytes(content, old_pw)
            decrypted_files[item] = decrypted
        except Exception as e:
            logger.error("Failed to decrypt vault file during password change: %s", e)
            raise HTTPException(
                status_code=500,
                detail="Failed to re-encrypt vault. Password change aborted to prevent data loss.",
            )

    decrypted_metadata = None
    if has_metadata:
        try:
            metadata_content = metadata_file.read_bytes()
            decrypted_metadata = decrypt_bytes(metadata_content, old_pw)
        except Exception:
            raise HTTPException(status_code=500, detail="Failed to decrypt vault metadata. Password change aborted.")

    # Re-encrypt and write everything with the new password
    for item, decrypted_content in decrypted_files.items():
        encrypted = encrypt_bytes(decrypted_content, new_pw)
        item.write_bytes(encrypted)

    if decrypted_metadata:
        encrypted_metadata = encrypt_bytes(decrypted_metadata, new_pw)
        metadata_file.write_bytes(encrypted_metadata)

    # Update password hash in DB
    user.vault_password_hash = hash_password(new_pw)
    db.add(user)
    db.commit()

    # Update in-memory cache if unlocked
    with _vault_cache_lock:
        if user.id in _vault_passwords:
            _vault_passwords[user.id] = new_pw

    return True


def move_vault_item(db: Session, user_id: int, source_path: str, destination_folder: str) -> dict:
    """Move a file or folder to a new destination folder in the vault."""
    vault_dir = _get_user_vault_dir(db, user_id)
    src = (vault_dir / source_path.strip("/")).resolve()
    if not str(src).startswith(str(vault_dir.resolve())):
        raise HTTPException(status_code=403, detail="Access denied")
    if not src.exists():
        raise HTTPException(status_code=404, detail="Source item not found")

    dest_folder = (vault_dir / destination_folder.strip("/")).resolve()
    if not str(dest_folder).startswith(str(vault_dir.resolve())):
        raise HTTPException(status_code=403, detail="Access denied")
    if not dest_folder.is_dir():
        raise HTTPException(status_code=400, detail="Destination is not a folder")

    # Prevent moving a folder into itself or its descendants
    if src.is_dir() and str(dest_folder).startswith(str(src) + os.sep):
        raise HTTPException(status_code=400, detail="Cannot move a folder into itself")

    dest = dest_folder / src.name
    if dest.exists():
        raise HTTPException(status_code=409, detail="An item with that name already exists in the destination")

    old_rel = str(src.relative_to(vault_dir))
    shutil.move(str(src), str(dest))
    new_rel = str(dest.relative_to(vault_dir))

    # Update metadata paths
    metadata = get_vault_metadata(user_id, vault_dir)
    favorites = metadata.get("favorites", [])
    tags_map = metadata.get("tags", {})

    new_favorites = []
    for f in favorites:
        if f == old_rel:
            new_favorites.append(new_rel)
        elif f.startswith(old_rel + "/"):
            new_favorites.append(new_rel + f[len(old_rel) :])
        else:
            new_favorites.append(f)

    new_tags = {}
    for p, t in tags_map.items():
        if p == old_rel:
            new_tags[new_rel] = t
        elif p.startswith(old_rel + "/"):
            new_tags[new_rel + p[len(old_rel) :]] = t
        else:
            new_tags[p] = t

    metadata["favorites"] = new_favorites
    metadata["tags"] = new_tags
    save_vault_metadata(user_id, vault_dir, metadata)

    return {
        "name": dest.name,
        "path": new_rel,
    }


def export_vault_items(db: Session, user_id: int, paths: list[str], destination_dir: str) -> dict:
    """Export and decrypt vault files/folders recursively to a local system directory."""
    import os
    from pathlib import Path

    dest_path = Path(os.path.expanduser(destination_dir)).resolve()

    home_dir = os.path.expanduser("~")
    if not str(dest_path).startswith(home_dir):
        raise HTTPException(status_code=400, detail="Export destination must be within home directory")

    if not dest_path.exists() or not dest_path.is_dir():
        raise HTTPException(
            status_code=400, detail=f"Destination directory '{destination_dir}' does not exist or is not a directory."
        )

    vault_dir = _get_user_vault_dir(db, user_id)
    password = _get_cached_password(user_id)
    if not password:
        raise HTTPException(status_code=403, detail="Vault is locked. Unlock before exporting.")

    exported_count = 0
    for path_str in paths:
        src = (vault_dir / path_str.strip("/")).resolve()
        if not str(src).startswith(str(vault_dir.resolve())):
            raise HTTPException(status_code=403, detail="Access denied")
        if not src.exists():
            raise HTTPException(status_code=404, detail=f"Item not found: {path_str}")

        if src.is_file():
            content = src.read_bytes()
            try:
                content = decrypt_bytes(content, password)
            except Exception:
                logger.warning("Failed to decrypt vault file during export: %s", path_str, exc_info=True)

            dest_file = dest_path / src.name
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            dest_file.write_bytes(content)
            exported_count += 1
        elif src.is_dir():
            for item in src.rglob("*"):
                if item.name.startswith(".") or ".metadata.bin" in item.name:
                    continue
                if item.is_file():
                    content = item.read_bytes()
                    try:
                        content = decrypt_bytes(content, password)
                    except Exception:
                        logger.warning("Failed to decrypt vault file during export: %s", item, exc_info=True)

                    rel_to_parent = item.relative_to(src.parent)
                    dest_file = dest_path / rel_to_parent
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    dest_file.write_bytes(content)
                    exported_count += 1

    return {"exported": True, "count": exported_count}
