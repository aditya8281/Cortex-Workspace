import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.main import app
from backend.app.db.base import Base
from backend.app.models.user import User  # noqa: F401
from backend.app.api.deps import get_db


@pytest.fixture(name="db_session", scope="function")
def fixture_db_session(tmp_path):
    # Each test gets its own isolated database file via pytest tmp_path
    db_file = tmp_path / "test.db"
    db_url = f"sqlite:///{db_file}"

    test_engine = create_engine(db_url, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)
        test_engine.dispose()


@pytest.fixture(name="client", scope="function")
def fixture_client(tmp_path):
    # Each test client gets its own completely isolated database
    db_file = tmp_path / "client_test.db"
    db_url = f"sqlite:///{db_file}"

    test_engine = create_engine(db_url, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()


def test_create_user(client):
    # Pre-populate a dummy first user so that the created user gets "admin" role
    dummy_payload = {
        "username": "dummyadmin",
        "full_name": "Dummy Admin",
        "nickname": "dummy",
        "password": "securepassword123",
        "confirm_password": "securepassword123",
        "vault_password": "vaultpassword123",
        "personal_storage_path": "~/CortexVaultTest"
    }
    # first registration becomes admin
    client.post("/api/auth/register", json=dummy_payload)

    payload = {
        "username": "testuser",
        "full_name": "Test User",
        "nickname": "tester",
        "password": "securepassword123",
        "confirm_password": "securepassword123",
        "vault_password": "vaultpassword123",
        "personal_storage_path": "~/CortexVaultTest2"
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["username"] == "testuser"
    assert data["user"]["full_name"] == "Test User"
    assert data["user"]["role"] == "user"


def test_create_duplicate_user(client):
    payload = {
        "username": "duplicateuser",
        "full_name": "Test User 1",
        "nickname": "dupuser",
        "password": "password123",
        "confirm_password": "password123",
        "vault_password": "vaultpassword123",
        "personal_storage_path": "~/CortexVaultTest3"
    }
    # First creation
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 200

    # Second creation (should fail cleanly with 400 instead of crashing with 500)
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "Username already registered"


def test_login_and_me(client):
    # 1. Register a user
    register_payload = {
        "username": "meuser",
        "full_name": "Me User",
        "nickname": "me",
        "password": "mypassword123",
        "confirm_password": "mypassword123",
        "vault_password": "vaultpassword123",
        "personal_storage_path": "~/CortexVaultTest4"
    }
    reg_response = client.post("/api/auth/register", json=register_payload)
    assert reg_response.status_code == 200

    # 2. Login
    login_payload = {
        "username": "meuser",
        "password": "mypassword123"
    }
    response = client.post("/api/auth/login", json=login_payload)
    assert response.status_code == 200
    token_data = response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"

    # 3. Access protected profile /me with valid token
    headers = {"Authorization": f"Bearer {token_data['access_token']}"}
    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == 200
    profile_data = response.json()
    assert profile_data["username"] == "meuser"
    assert profile_data["full_name"] == "Me User"

    # 4. Access protected profile /me with invalid token
    bad_headers = {"Authorization": "Bearer badtoken"}
    response = client.get("/api/auth/me", headers=bad_headers)
    assert response.status_code == 401


def test_profile_preferences_photo_and_password_flows(client):
    # Setup admin + user
    dummy_payload = {
        "username": "dummyadmin2",
        "full_name": "Dummy Admin",
        "nickname": "dummy",
        "password": "securepassword123",
        "confirm_password": "securepassword123",
        "vault_password": "vaultpassword123",
        "personal_storage_path": "~/CortexVaultTest"
    }
    client.post("/api/auth/register", json=dummy_payload)

    payload = {
        "username": "profileuser",
        "full_name": "Profile User",
        "nickname": "prof",
        "password": "initialPass123",
        "confirm_password": "initialPass123",
        "vault_password": "vaultPass123",
        "personal_storage_path": "~/CortexVaultTestP"
    }
    reg_response = client.post("/api/auth/register", json=payload)
    assert reg_response.status_code == 200

    # login
    login_payload = {"username": "profileuser", "password": "initialPass123"}
    login_resp = client.post("/api/auth/login", json=login_payload)
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # update preferences
    pref_payload = {"interaction_style": "casual", "response_style": "concise"}
    r = client.put("/api/v1/me/profile/preferences", json=pref_payload, headers=headers)
    assert r.status_code == 200
    assert r.json()["preferences"]["interaction_style"] == "casual"

    # upload profile photo
    files = {"file": ("avatar.png", b"PNGDATA", "image/png")}
    r = client.post("/api/v1/me/profile/photo", files=files, headers=headers)
    assert r.status_code == 200
    photo_name = r.json().get("profile_photo")
    assert photo_name and photo_name.startswith("user_")

    # ensure profile shows photo
    r = client.get("/api/v1/me/profile", headers=headers)
    assert r.status_code == 200
    assert r.json().get("profile_photo") == photo_name

    # remove photo
    r = client.delete("/api/v1/me/profile/photo", headers=headers)
    assert r.status_code == 200
    assert r.json().get("profile_photo") is None

    # change account password
    pwd_payload = {"current_password": "initialPass123", "new_password": "NewPass1234", "confirm_password": "NewPass1234"}
    r = client.post("/api/v1/me/profile/change-password", json=pwd_payload, headers=headers)
    assert r.status_code == 200

    # login with new password
    r = client.post("/api/auth/login", json={"username": "profileuser", "password": "NewPass1234"})
    assert r.status_code == 200

    new_token = r.json()["access_token"]
    new_headers = {"Authorization": f"Bearer {new_token}"}

    # change vault password (requires account password)
    vault_payload = {"account_password": "NewPass1234", "new_vault_password": "NewVault1234", "confirm_vault_password": "NewVault1234"}
    r = client.post("/api/v1/me/profile/change-vault-password", json=vault_payload, headers=new_headers)
    assert r.status_code == 200

    # verify that updating /api/auth/me with vault_password without current_password fails
    r = client.put("/api/auth/me", json={"vault_password": "oops"}, headers=new_headers)
    assert r.status_code == 400
