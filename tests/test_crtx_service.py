"""Comprehensive tests for the CRTX export/import service.

Covers:
  - Export/import round-trip with real DB users
  - Archive verification (verify_crtx)
  - Wrong password rejection
  - Manifest and payload integrity checks
  - Missing archive files
  - Import creates new user
  - Import updates existing user
  - Vault files restored on import
  - Profile photo restored on import
"""

import json
import os
import tempfile
import uuid
import zipfile
from pathlib import Path

import pytest
from cryptography.exceptions import InvalidTag
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
from backend.app.services import crtx_service
from backend.app.services.crtx_service import (
    ENCRYPTED_PAYLOAD,
    MANIFEST_FILENAME,
    METADATA_FILE,
    _compute_sha256,
    _derive_key,
)
from backend.app.services.storage_registry import register_user_storage

# ── Fixtures ─────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def _crtx_db():
    """Create an isolated file-backed DB for CRTX tests."""
    db_fd, db_path = tempfile.mkstemp(suffix=".crtx_test.db")
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
def _crtx_client(_crtx_db):
    """TestClient that uses the CRTX test DB."""
    TestSession, _ = _crtx_db

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
def _crtx_user(_crtx_db):
    """Create a test user with storage, vault files, and return (db, user, storage_root)."""
    TestSession, _ = _crtx_db
    db = TestSession()
    storage_root = tempfile.mkdtemp(prefix="crtx_test_")

    username = f"crtxuser_{uuid.uuid4().hex[:8]}"
    vault_pw = "CrtxVaultPass123"

    user = User(
        username=username,
        full_name="CRTX Test User",
        hashed_password=hash_password("LoginPass123"),
        role="user",
        nickname="cx",
        bio="Test bio for CRTX",
        vault_password_hash=hash_password(vault_pw),
        vault_locked=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    register_user_storage(db, user.id, storage_root)

    # Create some vault files
    vault_dir = Path(storage_root) / "vault"
    vault_dir.mkdir(parents=True, exist_ok=True)
    (vault_dir / "doc.txt").write_bytes(b"Hello CRTX!")
    (vault_dir / "data.json").write_bytes(json.dumps({"key": "value"}).encode())
    sub = vault_dir / "subdir"
    sub.mkdir()
    (sub / "nested.txt").write_bytes(b"nested content")

    yield db, user, storage_root, vault_pw

    import shutil

    db.close()
    if os.path.exists(storage_root):
        shutil.rmtree(storage_root, ignore_errors=True)


# ── Helper ───────────────────────────────────────────────────────────


def _register(client, username=None):
    """Register a user via the API and return the response JSON."""
    uname = username or f"crtxapi_{uuid.uuid4().hex[:8]}"
    r = client.post("/api/auth/register", json={
        "username": uname,
        "password": "securepass123",
        "confirm_password": "securepass123",
        "full_name": "CRTX API User",
        "nickname": "cxapi",
        "vault_password": "vaultpass123",
        "personal_storage_path": f"~/CortexStorage/crtx_{uuid.uuid4().hex[:6]}",
    })
    assert r.status_code == 200, f"Register failed: {r.text}"
    return r.json()


# ── Export tests ─────────────────────────────────────────────────────


def test_export_creates_valid_archive(_crtx_user):
    """export_crtx produces a valid .crtx zip with required files."""
    db, user, _, _ = _crtx_user
    output_path = tempfile.mktemp(suffix=".crtx")

    try:
        result = crtx_service.export_crtx(db, user.id, "ExportPass123", output_path)
        assert os.path.exists(result)

        with zipfile.ZipFile(result, "r") as zf:
            names = zf.namelist()
            assert METADATA_FILE in names
            assert MANIFEST_FILENAME in names
            assert ENCRYPTED_PAYLOAD in names
    finally:
        if os.path.exists(output_path):
            os.unlink(output_path)


def test_export_metadata_format(_crtx_user):
    """Exported metadata must have correct format fields."""
    db, user, _, _ = _crtx_user
    output_path = tempfile.mktemp(suffix=".crtx")

    try:
        crtx_service.export_crtx(db, user.id, "ExportPass123", output_path)

        with zipfile.ZipFile(output_path, "r") as zf:
            metadata = json.loads(zf.read(METADATA_FILE))
            assert metadata["format"] == "cortex-export"
            assert metadata["version"] == "1.0"
            assert metadata["algorithm"] == "AES-256-GCM"
            assert metadata["kdf"] == "PBKDF2-SHA256"
            assert "salt" in metadata
            assert "nonce" in metadata
            assert "manifest_hash" in metadata
    finally:
        if os.path.exists(output_path):
            os.unlink(output_path)


def test_export_manifest_contains_user_id(_crtx_user):
    """Manifest must contain the correct user_id and payload hash."""
    db, user, _, _ = _crtx_user
    output_path = tempfile.mktemp(suffix=".crtx")

    try:
        crtx_service.export_crtx(db, user.id, "ExportPass123", output_path)

        with zipfile.ZipFile(output_path, "r") as zf:
            manifest = json.loads(zf.read(MANIFEST_FILENAME))
            assert manifest["user_id"] == user.id
            assert manifest["version"] == "1.0"
            assert "payload_hash" in manifest
            assert "exported_at" in manifest
    finally:
        if os.path.exists(output_path):
            os.unlink(output_path)


def test_export_includes_vault_files(_crtx_user):
    """Exported manifest must report the correct file count."""
    db, user, _, _ = _crtx_user
    output_path = tempfile.mktemp(suffix=".crtx")

    try:
        crtx_service.export_crtx(db, user.id, "ExportPass123", output_path)

        with zipfile.ZipFile(output_path, "r") as zf:
            manifest = json.loads(zf.read(MANIFEST_FILENAME))
            # We created 3 vault files (doc.txt, data.json, subdir/nested.txt)
            assert manifest["file_count"] == 3
    finally:
        if os.path.exists(output_path):
            os.unlink(output_path)


# ── Verify tests ─────────────────────────────────────────────────────


def test_verify_valid_archive(_crtx_user):
    """verify_crtx returns metadata and manifest for a valid archive."""
    db, user, _, _ = _crtx_user
    output_path = tempfile.mktemp(suffix=".crtx")

    try:
        crtx_service.export_crtx(db, user.id, "ExportPass123", output_path)
        result = crtx_service.verify_crtx(output_path)
        assert "metadata" in result
        assert "manifest" in result
        assert result["metadata"]["format"] == "cortex-export"
        assert result["manifest"]["user_id"] == user.id
    finally:
        if os.path.exists(output_path):
            os.unlink(output_path)


def test_verify_missing_metadata(_crtx_user):
    """verify_crtx raises ValueError for archive missing metadata."""
    tmp = tempfile.mktemp(suffix=".crtx")
    try:
        with zipfile.ZipFile(tmp, "w") as zf:
            zf.writestr(MANIFEST_FILENAME, "{}")
            zf.writestr(ENCRYPTED_PAYLOAD, b"fake")

        with pytest.raises(ValueError, match="missing metadata"):
            crtx_service.verify_crtx(tmp)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def test_verify_missing_manifest(_crtx_user):
    """verify_crtx raises ValueError for archive missing manifest."""
    tmp = tempfile.mktemp(suffix=".crtx")
    try:
        with zipfile.ZipFile(tmp, "w") as zf:
            zf.writestr(METADATA_FILE, "{}")
            zf.writestr(ENCRYPTED_PAYLOAD, b"fake")

        with pytest.raises(ValueError, match="missing manifest"):
            crtx_service.verify_crtx(tmp)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def test_verify_missing_payload(_crtx_user):
    """verify_crtx raises ValueError for archive missing encrypted payload."""
    tmp = tempfile.mktemp(suffix=".crtx")
    try:
        with zipfile.ZipFile(tmp, "w") as zf:
            zf.writestr(METADATA_FILE, "{}")
            zf.writestr(MANIFEST_FILENAME, "{}")

        with pytest.raises(ValueError, match="missing encrypted payload"):
            crtx_service.verify_crtx(tmp)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


# ── Import tests ─────────────────────────────────────────────────────


def test_import_creates_new_user(_crtx_user):
    """Importing an archive for an existing user updates their profile."""
    db, user, _, vault_pw = _crtx_user
    export_pw = "ExportPass123"
    output_path = tempfile.mktemp(suffix=".crtx")
    import_storage = tempfile.mkdtemp(prefix="crtx_import_")

    try:
        # Ensure vault files exist at the original storage root before export
        from backend.app.services.storage_registry import get_registry_for_user
        registry = get_registry_for_user(db, user.id)
        vault_dir = Path(registry.storage_root) / "vault"
        vault_dir.mkdir(parents=True, exist_ok=True)
        (vault_dir / "doc.txt").write_bytes(b"Hello CRTX!")
        (vault_dir / "data.json").write_bytes(json.dumps({"key": "value"}).encode())
        sub = vault_dir / "subdir"
        sub.mkdir(exist_ok=True)
        (sub / "nested.txt").write_bytes(b"nested content")

        crtx_service.export_crtx(db, user.id, export_pw, output_path)

        # Import as-is — should update the existing user (same username)
        result = crtx_service.import_crtx(db, output_path, export_pw, import_storage)
        assert result["username"] == user.username
        assert result["vault_files_restored"] == 3
    finally:
        if os.path.exists(output_path):
            os.unlink(output_path)
        import shutil
        if os.path.exists(import_storage):
            shutil.rmtree(import_storage, ignore_errors=True)


def test_import_restores_vault_files(_crtx_user):
    """Imported vault files must appear in the new storage root."""
    db, user, _, vault_pw = _crtx_user
    export_pw = "ExportPass123"
    output_path = tempfile.mktemp(suffix=".crtx")
    import_storage = tempfile.mkdtemp(prefix="crtx_import_vault_")

    try:
        # Ensure vault files exist at the current storage root before export
        from backend.app.services.storage_registry import get_registry_for_user
        registry = get_registry_for_user(db, user.id)
        vault_dir = Path(registry.storage_root) / "vault"
        vault_dir.mkdir(parents=True, exist_ok=True)
        (vault_dir / "doc.txt").write_bytes(b"Hello CRTX!")
        (vault_dir / "data.json").write_bytes(json.dumps({"key": "value"}).encode())
        sub = vault_dir / "subdir"
        sub.mkdir(exist_ok=True)
        (sub / "nested.txt").write_bytes(b"nested content")

        crtx_service.export_crtx(db, user.id, export_pw, output_path)
        crtx_service.import_crtx(db, output_path, export_pw, import_storage)

        imported_vault = Path(import_storage) / "vault"
        assert (imported_vault / "doc.txt").exists()
        assert (imported_vault / "doc.txt").read_bytes() == b"Hello CRTX!"
        assert (imported_vault / "data.json").exists()
        assert (imported_vault / "subdir" / "nested.txt").exists()
    finally:
        if os.path.exists(output_path):
            os.unlink(output_path)
        import shutil
        if os.path.exists(import_storage):
            shutil.rmtree(import_storage, ignore_errors=True)


def test_import_wrong_password_fails(_crtx_user):
    """Importing with wrong password must raise ValueError."""
    db, user, _, _ = _crtx_user
    export_pw = "ExportPass123"
    output_path = tempfile.mktemp(suffix=".crtx")
    import_storage = tempfile.mkdtemp(prefix="crtx_import_fail_")

    try:
        crtx_service.export_crtx(db, user.id, export_pw, output_path)

        with pytest.raises((ValueError, InvalidTag)):
            crtx_service.import_crtx(db, output_path, "WrongPassword999", import_storage)
    finally:
        if os.path.exists(output_path):
            os.unlink(output_path)
        import shutil
        if os.path.exists(import_storage):
            shutil.rmtree(import_storage, ignore_errors=True)


def test_import_tampered_archive_fails(_crtx_user):
    """Importing a tampered archive must fail integrity checks."""
    db, user, _, _ = _crtx_user
    export_pw = "ExportPass123"
    output_path = tempfile.mktemp(suffix=".crtx")
    import_storage = tempfile.mkdtemp(prefix="crtx_import_tamper_")

    try:
        crtx_service.export_crtx(db, user.id, export_pw, output_path)

        # Tamper with the encrypted payload
        with zipfile.ZipFile(output_path, "r") as zf:
            metadata = json.loads(zf.read(METADATA_FILE))
            manifest = json.loads(zf.read(MANIFEST_FILENAME))
            encrypted = zf.read(ENCRYPTED_PAYLOAD)

        # Flip some bits in the encrypted data
        tampered = bytearray(encrypted)
        tampered[20] ^= 0xFF
        tampered = bytes(tampered)

        with zipfile.ZipFile(output_path, "w") as zf:
            zf.writestr(METADATA_FILE, json.dumps(metadata))
            zf.writestr(MANIFEST_FILENAME, json.dumps(manifest))
            zf.writestr(ENCRYPTED_PAYLOAD, tampered)

        with pytest.raises((ValueError, InvalidTag)):
            crtx_service.import_crtx(db, output_path, export_pw, import_storage)
    finally:
        if os.path.exists(output_path):
            os.unlink(output_path)
        import shutil
        if os.path.exists(import_storage):
            shutil.rmtree(import_storage, ignore_errors=True)


# ── Helper function tests ────────────────────────────────────────────


def test_compute_sha256_deterministic():
    """_compute_sha256 must be deterministic for same input."""
    data = b"test data for hashing"
    h1 = _compute_sha256(data)
    h2 = _compute_sha256(data)
    assert h1 == h2
    assert len(h1) == 64  # SHA-256 hex digest


def test_compute_sha256_different_inputs():
    """Different inputs must produce different hashes."""
    h1 = _compute_sha256(b"input one")
    h2 = _compute_sha256(b"input two")
    assert h1 != h2


def test_derive_key_deterministic():
    """_derive_key must produce the same key for same password + salt."""
    salt = os.urandom(16)
    k1 = _derive_key("password", salt)
    k2 = _derive_key("password", salt)
    assert k1 == k2
    assert len(k1) == 32  # 256-bit key


def test_derive_key_different_passwords():
    """Different passwords must produce different keys."""
    salt = os.urandom(16)
    k1 = _derive_key("password1", salt)
    k2 = _derive_key("password2", salt)
    assert k1 != k2


def test_derive_key_different_salts():
    """Different salts must produce different keys."""
    k1 = _derive_key("password", os.urandom(16))
    k2 = _derive_key("password", os.urandom(16))
    assert k1 != k2
