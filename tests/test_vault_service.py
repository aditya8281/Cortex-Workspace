"""Comprehensive tests for the vault service.

Covers:
  - Vault lock/unlock lifecycle with real DB users
  - File operations: upload, download, delete, rename, list, search, create folder
  - Path traversal protection
  - File size limits
  - File type validation
  - Require-unlocked guard
"""

import os
import tempfile
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.api.deps import get_db
from backend.app.core.security import hash_password
from backend.app.db.base import Base
from backend.app.main import app
from backend.app.models.auth_event import AuthEvent  # noqa: F401
from backend.app.models.storage_registry import StorageRegistry  # noqa: F401
from backend.app.models.user import User  # noqa: F401
from backend.app.services.memory import vault as vault_service
from backend.app.services.memory.storage_registry import register_user_storage
from backend.app.services.memory.vault import (
    _vault_cache_lock,
    _vault_passwords,
)

# ── Fixtures ─────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def _vault_db():
    """Create an isolated file-backed DB for vault tests."""
    db_fd, db_path = tempfile.mkstemp(suffix=".vault_test.db")
    os.close(db_fd)
    db_url = f"sqlite:///{db_path}"
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    yield Session, db_path
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    os.unlink(db_path)


@pytest.fixture(scope="module")
def _vault_client(_vault_db):
    """TestClient that uses the vault test DB."""
    TestSession, _ = _vault_db

    def _override():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="module")
def _vault_user(_vault_db):
    """Create a test user with a registered storage root and return (db_session, user, storage_root)."""
    TestSession, _ = _vault_db
    db = TestSession()
    # Create temp dir under the user's home so validate_storage_path() accepts it
    home_vault_tmp = Path.home() / ".vault_test_tmp"
    home_vault_tmp.mkdir(exist_ok=True)
    storage_root = tempfile.mkdtemp(prefix="vault_test_", dir=str(home_vault_tmp))
    vault_pw = "TestVaultPass123"

    user = User(
        username=f"vaulttest_{uuid.uuid4().hex[:8]}",
        full_name="Vault Test User",
        hashed_password=hash_password("LoginPass123"),
        role="user",
        nickname="vt",
        vault_password_hash=hash_password(vault_pw),
        vault_locked=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    register_user_storage(db, user.id, storage_root)

    yield db, user, storage_root, vault_pw

    # Cleanup
    import shutil

    db.close()
    if os.path.exists(storage_root):
        shutil.rmtree(storage_root, ignore_errors=True)


# ── Lock / Unlock lifecycle ──────────────────────────────────────────


def test_unlock_caches_password(_vault_user):
    """After unlock, the vault password must be cached in memory."""
    db, user, _, vault_pw = _vault_user
    result = vault_service.unlock_vault(db, user, vault_pw)
    assert result is True
    assert user.vault_locked is False
    assert _vault_passwords.get(user.id) == vault_pw


def test_unlock_wrong_password_fails(_vault_user):
    """Unlock with wrong password must return False and keep vault locked."""
    db, user, _, _ = _vault_user
    # Ensure vault is locked before testing
    vault_service.lock_vault(db, user)
    result = vault_service.unlock_vault(db, user, "WrongPassword999")
    assert result is False
    assert user.vault_locked is True


def test_lock_clears_cached_password(_vault_user):
    """After lock, the cached password must be removed."""
    db, user, _, vault_pw = _vault_user
    # Unlock first
    vault_service.unlock_vault(db, user, vault_pw)
    assert _vault_passwords.get(user.id) is not None

    vault_service.lock_vault(db, user)
    assert user.vault_locked is True
    assert _vault_passwords.get(user.id) is None


def test_is_vault_unlocked(_vault_user):
    """is_vault_unlocked reflects the vault_locked field."""
    db, user, _, vault_pw = _vault_user
    user.vault_locked = True
    db.commit()
    assert vault_service.is_vault_unlocked(user) is False

    vault_service.unlock_vault(db, user, vault_pw)
    assert vault_service.is_vault_unlocked(user) is True

    # Re-lock for subsequent tests
    vault_service.lock_vault(db, user)


def test_require_unlocked_raises_when_locked(_vault_user):
    """_require_unlocked must raise HTTPException when vault is locked."""
    db, user, _, _ = _vault_user
    user.vault_locked = True
    db.commit()
    with pytest.raises(Exception) as exc_info:
        vault_service._require_unlocked(user)
    assert exc_info.value.status_code == 403


def test_require_unlocked_raises_when_key_missing(_vault_user):
    """_require_unlocked must raise when vault is unlocked but key not cached."""
    db, user, _, _ = _vault_user
    user.vault_locked = False
    db.commit()
    # Ensure no cached password
    with _vault_cache_lock:
        _vault_passwords.pop(user.id, None)
    with pytest.raises(Exception) as exc_info:
        vault_service._require_unlocked(user)
    assert exc_info.value.status_code == 403

    # Restore locked state
    user.vault_locked = True
    db.commit()


def test_verify_vault_password(_vault_user):
    """verify_vault_password returns True for correct password, False for wrong."""
    db, user, _, vault_pw = _vault_user
    assert vault_service.verify_vault_password(db, user, vault_pw) is True
    assert vault_service.verify_vault_password(db, user, "wrong") is False


def test_verify_vault_password_no_hash(_vault_user):
    """verify_vault_password returns False when no vault_password_hash is set."""
    db, user, _, _ = _vault_user
    original_hash = user.vault_password_hash
    user.vault_password_hash = None
    db.commit()
    assert vault_service.verify_vault_password(db, user, "anything") is False
    # Restore
    user.vault_password_hash = original_hash
    db.commit()


# ── File Operations ──────────────────────────────────────────────────


def test_upload_and_download_file(_vault_user):
    """Upload a file, then download and verify the content."""
    db, user, _, vault_pw = _vault_user
    vault_service.unlock_vault(db, user, vault_pw)

    content = b"Hello, vault world!"
    result = vault_service.upload_vault_file(db, user.id, "test.txt", content)
    assert result["name"] == "test.txt"
    assert result["path"] == "test.txt"

    downloaded = vault_service.download_vault_file(db, user.id, "test.txt")
    assert downloaded == content

    vault_service.lock_vault(db, user)


def test_upload_encrypts_file_on_disk(_vault_user):
    """Uploaded file on disk must be encrypted (different from plaintext)."""
    db, user, _, vault_pw = _vault_user
    vault_service.unlock_vault(db, user, vault_pw)

    content = b"plaintext secret data"
    vault_service.upload_vault_file(db, user.id, "secret.txt", content)

    # Read raw bytes from disk
    from backend.app.services.memory.storage_registry import get_registry_for_user

    registry = get_registry_for_user(db, user.id)
    raw = (Path(registry.storage_root) / "vault" / "secret.txt").read_bytes()
    assert raw != content  # Must be encrypted

    # Cleanup
    vault_service.delete_vault_file(db, user.id, "secret.txt")
    vault_service.lock_vault(db, user)


def test_upload_too_large_rejected(_vault_user):
    """Files exceeding MAX_VAULT_FILE_SIZE must be rejected."""
    db, user, _, vault_pw = _vault_user
    vault_service.unlock_vault(db, user, vault_pw)

    huge_content = b"x" * (50 * 1024 * 1024 + 1)
    with pytest.raises(Exception) as exc_info:
        vault_service.upload_vault_file(db, user.id, "huge.bin", huge_content)
    assert exc_info.value.status_code == 400

    vault_service.lock_vault(db, user)


def test_upload_disallowed_extension(_vault_user):
    """Files with disallowed extensions must be rejected."""
    db, user, _, vault_pw = _vault_user
    vault_service.unlock_vault(db, user, vault_pw)

    with pytest.raises(Exception) as exc_info:
        vault_service.upload_vault_file(db, user.id, "malware.exe", b"bad")
    assert exc_info.value.status_code == 400

    vault_service.lock_vault(db, user)


def test_list_vault_files(_vault_user):
    """list_vault_files returns correct entries."""
    db, user, _, vault_pw = _vault_user
    vault_service.unlock_vault(db, user, vault_pw)

    vault_service.upload_vault_file(db, user.id, "doc1.txt", b"doc1")
    vault_service.upload_vault_file(db, user.id, "doc2.md", b"doc2")
    vault_service.create_vault_folder(db, user.id, "subfolder")

    files = vault_service.list_vault_files(db, user.id, "/")
    names = {f["name"] for f in files}
    assert "doc1.txt" in names
    assert "doc2.md" in names
    assert "subfolder" in names

    # List subfolder
    sub_files = vault_service.list_vault_files(db, user.id, "subfolder")
    assert sub_files == []

    # Cleanup
    vault_service.delete_vault_file(db, user.id, "doc1.txt")
    vault_service.delete_vault_file(db, user.id, "doc2.md")
    vault_service.delete_vault_file(db, user.id, "subfolder")
    vault_service.lock_vault(db, user)


def test_delete_vault_file(_vault_user):
    """delete_vault_file removes the file and returns True."""
    db, user, _, vault_pw = _vault_user
    vault_service.unlock_vault(db, user, vault_pw)

    vault_service.upload_vault_file(db, user.id, "to_delete.txt", b"bye")
    assert vault_service.delete_vault_file(db, user.id, "to_delete.txt") is True
    assert vault_service.delete_vault_file(db, user.id, "to_delete.txt") is False

    vault_service.lock_vault(db, user)


def test_delete_vault_folder(_vault_user):
    """delete_vault_file removes directories recursively."""
    db, user, _, vault_pw = _vault_user
    vault_service.unlock_vault(db, user, vault_pw)

    vault_service.create_vault_folder(db, user.id, "deleteme")
    vault_service.upload_vault_file(db, user.id, "deleteme/child.txt", b"child")
    assert vault_service.delete_vault_file(db, user.id, "deleteme") is True

    vault_service.lock_vault(db, user)


def test_rename_vault_item(_vault_user):
    """rename_vault_item renames a file correctly."""
    db, user, _, vault_pw = _vault_user
    vault_service.unlock_vault(db, user, vault_pw)

    vault_service.upload_vault_file(db, user.id, "old_name.txt", b"data")
    result = vault_service.rename_vault_item(db, user.id, "old_name.txt", "new_name.txt")
    assert result["name"] == "new_name.txt"

    # Old name should not exist
    downloaded = vault_service.download_vault_file(db, user.id, "new_name.txt")
    assert downloaded == b"data"

    vault_service.delete_vault_file(db, user.id, "new_name.txt")
    vault_service.lock_vault(db, user)


def test_rename_nonexistent_raises(_vault_user):
    """Renaming a nonexistent item must raise 404."""
    db, user, _, vault_pw = _vault_user
    vault_service.unlock_vault(db, user, vault_pw)

    with pytest.raises(Exception) as exc_info:
        vault_service.rename_vault_item(db, user.id, "nope.txt", "new.txt")
    assert exc_info.value.status_code == 404

    vault_service.lock_vault(db, user)


def test_create_vault_folder(_vault_user):
    """create_vault_folder creates the directory."""
    db, user, _, vault_pw = _vault_user
    vault_service.unlock_vault(db, user, vault_pw)

    result = vault_service.create_vault_folder(db, user.id, "new_folder")
    assert result["name"] == "new_folder"

    vault_service.delete_vault_file(db, user.id, "new_folder")
    vault_service.lock_vault(db, user)


def test_search_vault_files(_vault_user):
    """search_vault_files finds files by name substring."""
    db, user, _, vault_pw = _vault_user
    vault_service.unlock_vault(db, user, vault_pw)

    vault_service.upload_vault_file(db, user.id, "report_2024.pdf", b"r1")
    vault_service.upload_vault_file(db, user.id, "report_2025.pdf", b"r2")
    vault_service.upload_vault_file(db, user.id, "notes.txt", b"n1")

    results = vault_service.search_vault_files(db, user.id, "report")
    names = {r["name"] for r in results}
    assert "report_2024.pdf" in names
    assert "report_2025.pdf" in names
    assert "notes.txt" not in names

    # Cleanup
    vault_service.delete_vault_file(db, user.id, "report_2024.pdf")
    vault_service.delete_vault_file(db, user.id, "report_2025.pdf")
    vault_service.delete_vault_file(db, user.id, "notes.txt")
    vault_service.lock_vault(db, user)


# ── Path traversal protection ────────────────────────────────────────


def test_path_traversal_blocked_in_download(_vault_user):
    """Downloads with ../ in path must be blocked."""
    db, user, _, vault_pw = _vault_user
    vault_service.unlock_vault(db, user, vault_pw)

    with pytest.raises(Exception) as exc_info:
        vault_service.download_vault_file(db, user.id, "../../etc/passwd")
    assert exc_info.value.status_code in (403, 404)

    vault_service.lock_vault(db, user)


def test_path_traversal_blocked_in_delete(_vault_user):
    """Deletes with ../ in path must be blocked."""
    db, user, _, vault_pw = _vault_user
    vault_service.unlock_vault(db, user, vault_pw)

    result = vault_service.delete_vault_file(db, user.id, "../../something")
    assert result is False

    vault_service.lock_vault(db, user)


def test_path_traversal_blocked_in_rename(_vault_user):
    """Renames with ../ in path must be blocked."""
    db, user, _, vault_pw = _vault_user
    vault_service.unlock_vault(db, user, vault_pw)

    with pytest.raises(Exception) as exc_info:
        vault_service.rename_vault_item(db, user.id, "../../etc/hosts", "evil.txt")
    assert exc_info.value.status_code == 403

    vault_service.lock_vault(db, user)


def test_path_traversal_blocked_in_create_folder(_vault_user):
    """Folder creation with ../ in path must be blocked."""
    db, user, _, vault_pw = _vault_user
    vault_service.unlock_vault(db, user, vault_pw)

    with pytest.raises(Exception) as exc_info:
        vault_service.create_vault_folder(db, user.id, "../../evil_folder")
    assert exc_info.value.status_code == 403

    vault_service.lock_vault(db, user)


# ── Edge cases ───────────────────────────────────────────────────────


def test_upload_empty_file(_vault_user):
    """Uploading an empty file should work (size reflects encrypted output)."""
    db, user, _, vault_pw = _vault_user
    vault_service.unlock_vault(db, user, vault_pw)

    result = vault_service.upload_vault_file(db, user.id, "empty.txt", b"")
    assert result["size"] == 0

    downloaded = vault_service.download_vault_file(db, user.id, "empty.txt")
    assert downloaded == b""

    vault_service.delete_vault_file(db, user.id, "empty.txt")
    vault_service.lock_vault(db, user)


def test_upload_nested_path(_vault_user):
    """Uploading to a nested path should create parent directories."""
    db, user, _, vault_pw = _vault_user
    vault_service.unlock_vault(db, user, vault_pw)

    result = vault_service.upload_vault_file(db, user.id, "a/b/c/deep.txt", b"deep")
    assert result["path"] == "a/b/c/deep.txt"

    downloaded = vault_service.download_vault_file(db, user.id, "a/b/c/deep.txt")
    assert downloaded == b"deep"

    # Cleanup
    vault_service.delete_vault_file(db, user.id, "a")
    vault_service.lock_vault(db, user)


def test_download_nonexistent_file(_vault_user):
    """Downloading a nonexistent file must raise 404."""
    db, user, _, vault_pw = _vault_user
    vault_service.unlock_vault(db, user, vault_pw)

    with pytest.raises(Exception) as exc_info:
        vault_service.download_vault_file(db, user.id, "nope.txt")
    assert exc_info.value.status_code == 404

    vault_service.lock_vault(db, user)


# Path is imported at the top of the file.
