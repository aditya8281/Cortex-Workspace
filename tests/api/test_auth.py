# Tests for auth flows.  Uses the session-scoped ``client`` fixture
# provided by conftest.py which gives each test session a clean in-memory DB.

import shutil
import tempfile
from pathlib import Path


def _make_test_storage(prefix: str = "cortex_test_") -> Path:
    """Create a temporary storage directory under the user's home directory."""
    storage = Path.home() / f"{prefix}{tempfile.mktemp().split('/')[-1]}"
    storage.mkdir(parents=True, exist_ok=True)
    return storage


def test_create_user(client):
    storage = _make_test_storage("cortex_at_")
    try:
        # Pre-populate a dummy first user so that the created user gets "user" role
        dummy_payload = {
            "username": "dummyadmin",
            "full_name": "Dummy Admin",
            "nickname": "dummy",
            "password": "SecurePass123!",
            "confirm_password": "SecurePass123!",
            "vault_password": "VaultPass123!",
            "personal_storage_path": str(storage),
        }
        client.post("/api/v1/auth/register", json=dummy_payload)

        storage2 = _make_test_storage("cortex_at_")
        payload = {
            "username": "testuser",
            "full_name": "Test User",
            "nickname": "tester",
            "password": "SecurePass123!",
            "confirm_password": "SecurePass123!",
            "vault_password": "VaultPass123!",
            "personal_storage_path": str(storage2),
        }
        response = client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["username"] == "testuser"
        assert data["user"]["full_name"] == "Test User"
        assert data["user"]["role"] == "user"
    finally:
        shutil.rmtree(storage, ignore_errors=True)
        shutil.rmtree(storage2, ignore_errors=True)


def test_create_duplicate_user(client):
    storage = _make_test_storage("cortex_dup_")
    try:
        payload = {
            "username": "duplicateuser",
            "full_name": "Test User 1",
            "nickname": "dupuser",
            "password": "Password123!",
            "confirm_password": "Password123!",
            "vault_password": "VaultPass123!",
            "personal_storage_path": str(storage),
        }
        # First creation
        response = client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 200

        # Second creation (should fail cleanly with 400 instead of crashing with 500)
        response = client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 400
        assert response.json()["detail"] == "Username already registered"
    finally:
        shutil.rmtree(storage, ignore_errors=True)


def test_login_and_me(client):
    storage = _make_test_storage("cortex_me_")
    try:
        # 1. Register a user
        register_payload = {
            "username": "meuser",
            "full_name": "Me User",
            "nickname": "me",
            "password": "MyPass123!",
            "confirm_password": "MyPass123!",
            "vault_password": "VaultPass123!",
            "personal_storage_path": str(storage),
        }
        reg_response = client.post("/api/v1/auth/register", json=register_payload)
        assert reg_response.status_code == 200

        # 2. Login
        login_payload = {"username": "meuser", "password": "MyPass123!"}
        response = client.post("/api/v1/auth/login", json=login_payload)
        assert response.status_code == 200
        token_data = response.json()
        assert "access_token" in token_data
        assert token_data["token_type"] == "bearer"

        # 3. Access protected profile /me with valid token
        headers = {"Authorization": f"Bearer {token_data['access_token']}"}
        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 200
        profile_data = response.json()
        assert profile_data["username"] == "meuser"
        assert profile_data["full_name"] == "Me User"

        # 4. Access protected profile /me with invalid token
        bad_headers = {"Authorization": "Bearer badtoken"}
        response = client.get("/api/v1/auth/me", headers=bad_headers)
        assert response.status_code == 401
    finally:
        shutil.rmtree(storage, ignore_errors=True)


def test_vault_password_update(client):
    storage = _make_test_storage("cortex_vp_")
    try:
        # Register a user
        register_payload = {
            "username": "vaultuser",
            "full_name": "Vault User",
            "nickname": "vault",
            "password": "MyPass123!",
            "confirm_password": "MyPass123!",
            "vault_password": "VaultPass123!",
            "personal_storage_path": str(storage),
        }
        reg_response = client.post("/api/v1/auth/register", json=register_payload)
        assert reg_response.status_code == 200

        # Login
        login_payload = {"username": "vaultuser", "password": "MyPass123!"}
        login_resp = client.post("/api/v1/auth/login", json=login_payload)
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Update vault password with correct current_password
        r = client.put(
            "/api/v1/auth/me",
            json={"vault_password": "newVaultPass123", "current_password": "MyPass123!"},
            headers=headers,
        )
        assert r.status_code == 200

        # Update vault password without current_password should fail
        r = client.put("/api/v1/auth/me", json={"vault_password": "oops"}, headers=headers)
        assert r.status_code == 400
    finally:
        shutil.rmtree(storage, ignore_errors=True)


def test_delete_user_soft_delete(client):
    from datetime import datetime

    from backend.app.api.deps import get_db
    from backend.app.main import app
    from backend.app.models.interaction.user import User
    from backend.app.models.memory.storage_registry import StorageRegistry

    storage = _make_test_storage("cortex_sd_")
    try:
        register_payload = {
            "username": "softdeluser",
            "full_name": "Soft Delete User",
            "nickname": "softdel",
            "password": "MyPass123!",
            "confirm_password": "MyPass123!",
            "vault_password": "VaultPass123!",
            "personal_storage_path": str(storage),
        }
        reg_resp = client.post("/api/v1/auth/register", json=register_payload)
        assert reg_resp.status_code == 200
        user_data = reg_resp.json()["user"]
        user_id = user_data["id"]

        resolved_path = storage.resolve()
        assert resolved_path.exists()
        assert (resolved_path / "vault").exists()

        # Login to get token
        login_payload = {"username": "softdeluser", "password": "MyPass123!"}
        login_resp = client.post("/api/v1/auth/login", json=login_payload)
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Check that registry entry is in database
        db_func = app.dependency_overrides[get_db]
        db = next(db_func())
        try:
            reg = db.query(StorageRegistry).filter(StorageRegistry.user_id == user_id).first()
            assert reg is not None
            assert reg.storage_root == str(resolved_path)
        finally:
            db.close()

        # Soft delete user
        del_resp = client.request("DELETE", "/api/v1/auth/me", json={"password": "MyPass123!"}, headers=headers)
        assert del_resp.status_code == 200

        # Verify storage directory is PRESERVED during grace period
        assert resolved_path.exists()
        assert (resolved_path / "vault").exists()

        # Verify registry entry is PRESERVED
        db = next(db_func())
        try:
            reg = db.query(StorageRegistry).filter(StorageRegistry.user_id == user_id).first()
            assert reg is not None

            # Verify user has deleted_at set
            user = db.query(User).filter(User.id == user_id).first()
            assert user is not None
            assert user.deleted_at is not None
            assert isinstance(user.deleted_at, datetime)
        finally:
            db.close()

        # Verify restore works
        restore_resp = client.post("/api/v1/auth/restore", json={"password": "MyPass123!"}, headers=headers)
        assert restore_resp.status_code == 200

        db = next(db_func())
        try:
            user = db.query(User).filter(User.id == user_id).first()
            assert user is not None
            assert user.deleted_at is None
        finally:
            db.close()
    finally:
        shutil.rmtree(storage, ignore_errors=True)
