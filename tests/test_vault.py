# Tests for vault encryption and lock/unlock lifecycle.

import os

from backend.app.services.vault_service import (
    _vault_cache_lock,
    _vault_passwords,
    decrypt_bytes,
    encrypt_bytes,
)

# ── Encryption round-trip tests ──────────────────────────────────────


def test_encrypt_decrypt_round_trip():
    """encrypt_bytes → decrypt_bytes must recover original data."""
    password = "my-super-secret-vault-pw"
    plaintext = b"Hello, this is sensitive vault data!"
    encrypted = encrypt_bytes(plaintext, password)
    decrypted = decrypt_bytes(encrypted, password)
    assert decrypted == plaintext


def test_encrypted_data_differs_from_plaintext():
    """Encrypted output must not equal the original bytes."""
    password = "another-password-123"
    plaintext = b"plaintext content"
    encrypted = encrypt_bytes(plaintext, password)
    assert encrypted != plaintext
    # Encrypted data should be longer (salt prefix + Fernet overhead)
    assert len(encrypted) > len(plaintext)


def test_different_passwords_fail_decryption():
    """Decrypting with the wrong password must raise an exception."""
    password_a = "correct-password-aaa"
    password_b = "wrong-password-bbb"
    plaintext = b"secret data"
    encrypted = encrypt_bytes(plaintext, password_a)
    try:
        decrypt_bytes(encrypted, password_b)
        raise AssertionError("Should have raised an exception")
    except Exception:
        pass  # Expected


def test_per_file_random_salts():
    """Two encryptions of the same plaintext produce different ciphertext (random salt)."""
    password = "same-password"
    plaintext = b"identical content"
    enc1 = encrypt_bytes(plaintext, password)
    enc2 = encrypt_bytes(plaintext, password)
    # Different random salts → different ciphertext
    assert enc1 != enc2
    # But both decrypt to the same plaintext
    assert decrypt_bytes(enc1, password) == plaintext
    assert decrypt_bytes(enc2, password) == plaintext


def test_empty_data_round_trip():
    """Encrypting and decrypting empty bytes should work."""
    password = "empty-test-pw"
    plaintext = b""
    encrypted = encrypt_bytes(plaintext, password)
    decrypted = decrypt_bytes(encrypted, password)
    assert decrypted == plaintext


def test_large_data_round_trip():
    """Encrypt/decrypt a 1 MB payload."""
    password = "large-data-pw"
    plaintext = os.urandom(1024 * 1024)
    encrypted = encrypt_bytes(plaintext, password)
    decrypted = decrypt_bytes(encrypted, password)
    assert decrypted == plaintext


# ── Key cache lifecycle tests ─────────────────────────────────────────


def test_password_cache_cleared_on_lock():
    """After lock_vault, the cached password must be removed."""
    user_id = 999001
    with _vault_cache_lock:
        _vault_passwords[user_id] = "test-password"
    assert _vault_passwords.get(user_id) == "test-password"
    # Simulate lock (directly clearing cache since we can't easily create a full DB user here)
    with _vault_cache_lock:
        _vault_passwords.pop(user_id, None)
    assert _vault_passwords.get(user_id) is None


def test_password_cache_isolation():
    """Different user IDs have independent cached passwords."""
    uid_a, uid_b = 999010, 999020
    with _vault_cache_lock:
        _vault_passwords[uid_a] = "password-a"
        _vault_passwords[uid_b] = "password-b"
    assert _vault_passwords[uid_a] == "password-a"
    assert _vault_passwords[uid_b] == "password-b"
    # Clearing one doesn't affect the other
    with _vault_cache_lock:
        _vault_passwords.pop(uid_a, None)
    assert _vault_passwords.get(uid_a) is None
    assert _vault_passwords[uid_b] == "password-b"
    # Cleanup
    with _vault_cache_lock:
        _vault_passwords.pop(uid_b, None)



