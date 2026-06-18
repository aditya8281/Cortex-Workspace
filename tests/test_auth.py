# Tests for auth flows.  Uses the session-scoped ``client`` fixture
# provided by conftest.py which gives each test session a clean in-memory DB.


def test_create_user(client):
    # Pre-populate a dummy first user so that the created user gets "user" role
    dummy_payload = {
        "username": "dummyadmin",
        "full_name": "Dummy Admin",
        "nickname": "dummy",
        "password": "securepassword123",
        "confirm_password": "securepassword123",
        "vault_password": "vaultpassword123",
        "personal_storage_path": "~/CortexVaultTest"
    }
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


def test_vault_password_update(client):
    # Register a user
    register_payload = {
        "username": "vaultuser",
        "full_name": "Vault User",
        "nickname": "vault",
        "password": "mypassword123",
        "confirm_password": "mypassword123",
        "vault_password": "vaultpassword123",
        "personal_storage_path": "~/CortexVaultTest5"
    }
    reg_response = client.post("/api/auth/register", json=register_payload)
    assert reg_response.status_code == 200

    # Login
    login_payload = {"username": "vaultuser", "password": "mypassword123"}
    login_resp = client.post("/api/auth/login", json=login_payload)
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Update vault password with correct current_password
    r = client.put("/api/auth/me", json={"vault_password": "newVaultPass123", "current_password": "mypassword123"}, headers=headers)
    assert r.status_code == 200

    # Update vault password without current_password should fail
    r = client.put("/api/auth/me", json={"vault_password": "oops"}, headers=headers)
    assert r.status_code == 400
