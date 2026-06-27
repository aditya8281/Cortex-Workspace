"""Application-layer Fernet encryption with key rotation support."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
from datetime import datetime, timedelta, timezone

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class EncryptionService:
    """Fernet symmetric encryption with key ring support.

    Features:
    - AES-128-CBC via Fernet
    - Key ring: current + previous for seamless rotation
    - User-specific key derivation for per-user isolation
    """

    KEY_ROTATION_DAYS = 90
    PBKDF2_ITERATIONS = 480_000

    def __init__(self, master_key: str | None = None) -> None:
        if master_key is None:
            master_key = os.environ.get("SECRET_KEY", "")
        if not master_key:
            raise ValueError("SECRET_KEY environment variable is required for encryption")

        self._master_key = master_key.encode()
        self._current_key = self._derive_key(self._master_key, b"cortex-current")
        self._previous_key = self._derive_key(self._master_key, b"cortex-previous")
        self._current_fernet = Fernet(self._current_key)
        self._previous_fernet = Fernet(self._previous_key)

    def _derive_key(self, master: bytes, salt: bytes) -> bytes:
        """Derive a Fernet-compatible key from master key and salt."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=self.PBKDF2_ITERATIONS,
        )
        return base64.urlsafe_b64encode(kdf.derive(master))

    def encrypt(self, data: str) -> str:
        """Encrypt a string. Returns base64-encoded ciphertext."""
        if not data:
            return data
        return self._current_fernet.encrypt(data.encode("utf-8")).decode("utf-8")

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt a string. Tries current key first, then previous."""
        if not encrypted_data:
            return encrypted_data
        try:
            return self._current_fernet.decrypt(encrypted_data.encode("utf-8")).decode("utf-8")
        except InvalidToken:
            return self._previous_fernet.decrypt(encrypted_data.encode("utf-8")).decode("utf-8")

    def encrypt_dict(self, data: dict) -> str:
        """Encrypt a dictionary as JSON."""
        return self.encrypt(json.dumps(data, default=str))

    def decrypt_dict(self, encrypted_data: str) -> dict:
        """Decrypt to a dictionary."""
        return json.loads(self.decrypt(encrypted_data))

    def encrypt_for_user(self, data: str, user_id: int) -> str:
        """Encrypt with a user-specific key for per-user isolation."""
        user_key = self._derive_key(self._master_key, f"cortex-user-{user_id}".encode())
        return Fernet(user_key).encrypt(data.encode("utf-8")).decode("utf-8")

    def decrypt_for_user(self, encrypted_data: str, user_id: int) -> str:
        """Decrypt with a user-specific key."""
        user_key = self._derive_key(self._master_key, f"cortex-user-{user_id}".encode())
        return Fernet(user_key).decrypt(encrypted_data.encode("utf-8")).decode("utf-8")

    def needs_re_encryption(self, encrypted_data: str) -> bool:
        """Check if data was encrypted with the previous key (needs rotation)."""
        try:
            self._current_fernet.decrypt(encrypted_data.encode("utf-8"))
            return False
        except InvalidToken:
            try:
                self._previous_fernet.decrypt(encrypted_data.encode("utf-8"))
                return True
            except InvalidToken:
                raise ValueError("Cannot decrypt with either key — data may be corrupted")

    def rotate_keys(self) -> dict:
        """Perform key rotation. Returns rotation metadata for audit logging.

        Shifts current → previous, derives new current from fresh salt.
        Previous key stays valid for KEY_ROTATION_DAYS for re-encryption.
        """
        rotation_time = datetime.now(timezone.utc)
        new_salt = secrets.token_bytes(16)
        # Shift: current becomes previous
        self._previous_key = self._current_key
        self._previous_fernet = self._current_fernet
        # Derive new current key
        self._current_key = self._derive_key(self._master_key, new_salt)
        self._current_fernet = Fernet(self._current_key)
        return {
            "rotated_at": rotation_time.isoformat(),
            "previous_key_valid_until": (rotation_time + timedelta(days=self.KEY_ROTATION_DAYS)).isoformat(),
            "new_salt_hash": hashlib.sha256(new_salt).hexdigest(),
        }
