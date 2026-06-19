"""CRTX Export/Import Service — Portable encrypted Cortex user archives.

⚠️  EXPERIMENTAL — NOT PART OF CURRENT RELEASE
This service is retained for future .crtx portability work.
API routes are disconnected (see backend/app/api/router.py).
Do not extend or build new features on top of this module.

A .crtx file is a portable encrypted Cortex user package containing:
  - User profile, avatar, nickname, bio, settings, preferences
  - Chat history, vault contents, all personal metadata

Explicitly EXCLUDED:
  - CortexMemory, embeddings, indexes, repositories, vector stores
  - AI cache, execution logs, downloaded models, global configuration
  - Every system-level intelligence component

Encryption: AES-256-GCM with password-derived key (PBKDF2)
Integrity: SHA-256 hashes + manifest
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)

MANIFEST_FILENAME = "manifest.json"
ENCRYPTED_PAYLOAD = "payload.enc"
METADATA_FILE = "metadata.json"
ITERATIONS = 600_000


def _derive_key(password: str, salt: bytes) -> bytes:
    """Derive a 256-bit AES key from a password using PBKDF2."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=ITERATIONS,
    )
    return kdf.derive(password.encode())


def _compute_sha256(data: bytes) -> str:
    """Compute SHA-256 hex digest."""
    return hashlib.sha256(data).hexdigest()


def _collect_user_data(db, user_id: int) -> dict:
    """Collect all user-specific data for export."""
    from backend.app.models.user import User
    from backend.app.services.storage_registry import get_registry_for_user

    user = db.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()
    if not user:
        raise FileNotFoundError(f"User {user_id} not found")

    data: dict[str, Any] = {
        "user": {
            "username": user.username,
            "full_name": user.full_name,
            "nickname": user.nickname,
            "bio": user.bio,
            "description": user.description,
            "role": user.role,
            "handles": user.handles,
            "preferences": user.preferences,
        },
        "profile_photo": None,
        "vault_files": [],
        "chat_history": [],
    }

    # Collect profile photo if it exists
    if user.profile_photo:
        from backend.app.api.v1.profile import _avatar_path
        avatar = _avatar_path(user_id)
        if avatar.exists():
            data["profile_photo"] = base64.b64encode(avatar.read_bytes()).decode()

    # Collect vault files
    vault_files_list: list[dict[str, Any]] = data["vault_files"]  # type: ignore[assignment]
    registry = get_registry_for_user(db, user_id)
    if registry:
        vault_dir = Path(registry.storage_root) / "vault"
        if vault_dir.exists():
            for item in vault_dir.rglob("*"):
                if item.is_file() and not item.name.startswith("."):
                    rel = item.relative_to(vault_dir)
                    vault_files_list.append({
                        "path": str(rel),
                        "content": base64.b64encode(item.read_bytes()).decode(),
                        "size": item.stat().st_size,
                    })

    return data


def export_crtx(db, user_id: int, export_password: str, output_path: str) -> str:
    """Export a user as an encrypted .crtx archive.

    Steps:
    1. Collect all user data
    2. Create a manifest with SHA-256 hashes
    3. Compress the payload
    4. Encrypt with AES-256-GCM
    5. Generate metadata
    6. Produce the .crtx archive
    """
    data = _collect_user_data(db, user_id)

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)

        # 1. Write raw payload
        payload_bytes = json.dumps(data, indent=2).encode()
        payload_path = tmp / "payload.json"
        payload_path.write_bytes(payload_bytes)

        # 2. Create manifest with integrity hashes
        manifest = {
            "version": "1.0",
            "user_id": user_id,
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "payload_hash": _compute_sha256(payload_bytes),
            "payload_size": len(payload_bytes),
            "file_count": len(data.get("vault_files", [])),
            "has_profile_photo": data.get("profile_photo") is not None,
        }
        manifest_bytes = json.dumps(manifest, indent=2).encode()
        manifest_path = tmp / MANIFEST_FILENAME
        manifest_path.write_bytes(manifest_bytes)

        # 3. Compress payload
        compressed_path = tmp / "payload.zip"
        with zipfile.ZipFile(compressed_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(payload_path, "payload.json")

        compressed_bytes = compressed_path.read_bytes()

        # 4. Encrypt with AES-256-GCM
        salt = os.urandom(16)
        nonce = os.urandom(12)
        key = _derive_key(export_password, salt)
        aesgcm = AESGCM(key)
        encrypted = aesgcm.encrypt(nonce, compressed_bytes, None)

        # 5. Generate metadata
        metadata = {
            "format": "cortex-export",
            "version": "1.0",
            "algorithm": "AES-256-GCM",
            "kdf": "PBKDF2-SHA256",
            "iterations": ITERATIONS,
            "salt": base64.b64encode(salt).decode(),
            "nonce": base64.b64encode(nonce).decode(),
            "manifest_hash": _compute_sha256(manifest_bytes),
        }
        metadata_bytes = json.dumps(metadata, indent=2).encode()

        # 6. Create .crtx archive
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(METADATA_FILE, metadata_bytes)
            zf.writestr(MANIFEST_FILENAME, manifest_bytes)
            zf.writestr(ENCRYPTED_PAYLOAD, encrypted)

    logger.info("Exported .crtx archive for user %d to %s", user_id, output_path)
    return str(output)


def verify_crtx(archive_path: str) -> dict:
    """Verify a .crtx archive without decrypting.

    Returns metadata and manifest info for verification.
    """
    with zipfile.ZipFile(archive_path, "r") as zf:
        if METADATA_FILE not in zf.namelist():
            raise ValueError("Invalid .crtx archive: missing metadata")
        if MANIFEST_FILENAME not in zf.namelist():
            raise ValueError("Invalid .crtx archive: missing manifest")
        if ENCRYPTED_PAYLOAD not in zf.namelist():
            raise ValueError("Invalid .crtx archive: missing encrypted payload")

        metadata = json.loads(zf.read(METADATA_FILE))
        manifest = json.loads(zf.read(MANIFEST_FILENAME))

    return {"metadata": metadata, "manifest": manifest}


def import_crtx(db, archive_path: str, export_password: str, new_storage_root: str) -> dict:
    """Import a .crtx archive.

    Steps:
    1. Verify archive structure
    2. Decrypt the payload
    3. Verify manifest hashes
    4. Restore user data
    5. Update central pointer database
    """
    with zipfile.ZipFile(archive_path, "r") as zf:
        metadata = json.loads(zf.read(METADATA_FILE))
        manifest = json.loads(zf.read(MANIFEST_FILENAME))
        encrypted = zf.read(ENCRYPTED_PAYLOAD)

    # 1. Verify manifest hash
    stored_metadata_hash = _compute_sha256(
        json.dumps(manifest, indent=2).encode()
    )
    if stored_metadata_hash != metadata.get("manifest_hash"):
        raise ValueError("Manifest integrity check failed")

    # 2. Decrypt
    salt = base64.b64decode(metadata["salt"])
    nonce = base64.b64decode(metadata["nonce"])
    key = _derive_key(export_password, salt)
    aesgcm = AESGCM(key)
    compressed = aesgcm.decrypt(nonce, encrypted, None)

    # 3. Decompress
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
        tmp.write(compressed)
        tmp_path = tmp.name

    try:
        with tempfile.TemporaryDirectory() as extract_dir:
            with zipfile.ZipFile(tmp_path, "r") as zf:
                zf.extractall(extract_dir)
            payload = json.loads((Path(extract_dir) / "payload.json").read_text())

        # 4. Verify payload hash
        payload_bytes = json.dumps(payload, indent=2).encode()
        if _compute_sha256(payload_bytes) != manifest["payload_hash"]:
            raise ValueError("Payload integrity check failed")

    finally:
        os.unlink(tmp_path)

    # 5. Restore user data
    user_data = payload["user"]

    # Create or update user
    from backend.app.core.security import hash_password
    from backend.app.models.user import User
    from backend.app.services.storage_registry import register_user_storage
    from backend.app.services.user_service import _normalize_username

    existing = db.query(User).filter(User.username == _normalize_username(user_data["username"]), User.deleted_at.is_(None)).first()
    if existing:
        # Update existing user
        existing.full_name = user_data["full_name"]
        existing.nickname = user_data["nickname"]
        existing.bio = user_data.get("bio")
        existing.description = user_data.get("description")
        existing.handles = user_data.get("handles", {})
        existing.preferences = user_data.get("preferences", {})
        db.add(existing)
        db.commit()
        db.refresh(existing)
        restored_user = existing
    else:
        # Create new user with a random password (must be changed on first login)
        random_pw = hashlib.sha256(os.urandom(32)).hexdigest()[:16]
        new_user = User(
            username=_normalize_username(user_data["username"]),
            full_name=user_data["full_name"],
            hashed_password=hash_password(random_pw),
            role=user_data.get("role", "user"),
            nickname=user_data.get("nickname", ""),
            bio=user_data.get("bio"),
            description=user_data.get("description"),
            handles_json=json.dumps(user_data.get("handles", {})),
            preferences_json=json.dumps(user_data.get("preferences", {})),
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        restored_user = new_user

    # 6. Restore profile photo
    if payload.get("profile_photo"):
        from backend.app.api.v1.profile import _avatar_path
        avatar_dir = _avatar_path(restored_user.id).parent
        avatar_dir.mkdir(parents=True, exist_ok=True)
        _avatar_path(restored_user.id).write_bytes(
            base64.b64decode(payload["profile_photo"])
        )
        restored_user.profile_photo = f"user_{restored_user.id}_avatar.webp"
        db.add(restored_user)
        db.commit()

    # 7. Restore vault files
    storage_root = Path(new_storage_root)
    vault_dir = storage_root / "vault"
    vault_dir.mkdir(parents=True, exist_ok=True)
    for vf in payload.get("vault_files", []):
        file_path = vault_dir / vf["path"]
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(base64.b64decode(vf["content"]))

    # 8. Register storage
    register_user_storage(db, restored_user.id, str(storage_root))

    logger.info("Imported .crtx archive for user %d (%s)", restored_user.id, restored_user.username)
    return {
        "user_id": restored_user.id,
        "username": restored_user.username,
        "vault_files_restored": len(payload.get("vault_files", [])),
    }
