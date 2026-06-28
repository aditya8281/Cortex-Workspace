"""Tests for v1.05 P02 encryption service."""

from __future__ import annotations

import pytest
from cryptography.fernet import InvalidToken

from backend.app.services.privacy.encryption import EncryptionService


class TestEncryptionService:
    @pytest.fixture()
    def service(self, monkeypatch: pytest.MonkeyPatch) -> EncryptionService:
        monkeypatch.setenv("SECRET_KEY", "test-secret-key-for-unit-tests-only-32ch")
        return EncryptionService()

    def test_encrypt_decrypt_string(self, service: EncryptionService) -> None:
        original = "sensitive data here"
        encrypted = service.encrypt(original)
        assert encrypted != original
        assert service.decrypt(encrypted) == original

    def test_encrypt_decrypt_empty(self, service: EncryptionService) -> None:
        assert service.encrypt("") == ""
        assert service.decrypt("") == ""

    def test_encrypt_decrypt_dict(self, service: EncryptionService) -> None:
        original = {"key": "value", "nested": {"a": 1}}
        encrypted = service.encrypt_dict(original)
        decrypted = service.decrypt_dict(encrypted)
        assert decrypted == original

    def test_user_specific_encryption(self, service: EncryptionService) -> None:
        data = "user secret"
        enc1 = service.encrypt_for_user(data, user_id=1)
        enc2 = service.encrypt_for_user(data, user_id=2)
        assert enc1 != enc2
        assert service.decrypt_for_user(enc1, 1) == data
        assert service.decrypt_for_user(enc2, 2) == data

    def test_wrong_user_cannot_decrypt(self, service: EncryptionService) -> None:
        data = "user 1 secret"
        encrypted = service.encrypt_for_user(data, user_id=1)
        with pytest.raises(InvalidToken):
            service.decrypt_for_user(encrypted, user_id=2)

    def test_needs_re_encryption_false(self, service: EncryptionService) -> None:
        encrypted = service.encrypt("data")
        assert service.needs_re_encryption(encrypted) is False

    def test_key_rotation_works(self, service: EncryptionService) -> None:
        """After rotation, old data decrypts with previous key, new data with current."""
        data = "rotate me"
        encrypted_before = service.encrypt(data)

        # Rotate keys
        meta = service.rotate_keys()
        assert "rotated_at" in meta
        assert "new_salt_hash" in meta

        # Old data still decrypts (previous key still valid)
        assert service.decrypt(encrypted_before) == data
        assert service.needs_re_encryption(encrypted_before) is True

        # New encryption uses new key
        encrypted_after = service.encrypt(data)
        assert encrypted_after != encrypted_before
        assert service.decrypt(encrypted_after) == data
        assert service.needs_re_encryption(encrypted_after) is False

    def test_missing_secret_key_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("SECRET_KEY", raising=False)
        with pytest.raises(ValueError):
            EncryptionService()
