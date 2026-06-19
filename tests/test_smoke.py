"""Quick smoke test for all endpoints after the deadlock fix."""
import uuid

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app


@pytest.fixture(name="client", scope="module")
def fixture_client():
    return TestClient(app)


# Module-level state shared across smoke tests (module-scoped client).
_USERNAME = f"smoke_{uuid.uuid4().hex[:8]}"
_PASSWORD = "securepass123"
_TOKEN: str = ""


def test_root(client):
    r = client.get("/")
    assert r.status_code == 200


def test_health_live(client):
    r = client.get("/api/v1/health/live")
    assert r.status_code == 200


def test_health_ready(client):
    r = client.get("/api/v1/health/ready")
    assert r.status_code == 200


def test_health_deep(client):
    r = client.get("/api/v1/health/deep")
    assert r.status_code == 200


def test_memory_get(client):
    r = client.get("/api/memory")
    assert r.status_code == 200


def test_register(client):
    global _TOKEN
    r = client.post("/api/auth/register", json={
        "username": _USERNAME,
        "password": _PASSWORD,
        "confirm_password": _PASSWORD,
        "full_name": "Smoke User",
        "nickname": "su",
        "vault_password": "vaultpass123",
        "personal_storage_path": f"~/CortexStorage/smoke_{uuid.uuid4().hex[:6]}",
    })
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    _TOKEN = data["access_token"]


def test_login(client):
    global _TOKEN
    r = client.post("/api/auth/login", json={
        "username": _USERNAME,
        "password": _PASSWORD,
    })
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    _TOKEN = data["access_token"]


def test_me(client):
    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {_TOKEN}"})
    assert r.status_code == 200
    assert r.json()["username"] == _USERNAME


def test_memory_post(client):
    r = client.post("/api/memory", json={
        "title": "smoke test",
        "content": "hello from smoke test",
    }, headers={"Authorization": f"Bearer {_TOKEN}"})
    assert r.status_code == 200


def test_profile_get(client):
    r = client.get("/api/v1/me/profile", headers={"Authorization": f"Bearer {_TOKEN}"})
    assert r.status_code == 200
    assert r.json()["username"] == _USERNAME


def test_profile_put(client):
    r = client.put("/api/v1/me/profile", json={"bio": "smoke bio"},
                   headers={"Authorization": f"Bearer {_TOKEN}"})
    assert r.status_code == 200
    assert r.json()["bio"] == "smoke bio"


def test_auth_refresh(client):
    """Register a fresh user and test the refresh token flow."""
    username = f"refresh_{uuid.uuid4().hex[:8]}"
    r = client.post("/api/auth/register", json={
        "username": username,
        "password": _PASSWORD,
        "confirm_password": _PASSWORD,
        "full_name": "Refresh User",
        "nickname": "ru",
        "vault_password": "vaultpass123",
        "personal_storage_path": f"~/CortexStorage/refresh_{uuid.uuid4().hex[:6]}",
    })
    assert r.status_code == 200
    refresh_token = r.json()["refresh_token"]

    r2 = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert r2.status_code == 200
    assert "access_token" in r2.json()


def test_auth_logout(client):
    """Register a fresh user and test the logout flow."""
    username = f"logout_{uuid.uuid4().hex[:8]}"
    r = client.post("/api/auth/register", json={
        "username": username,
        "password": _PASSWORD,
        "confirm_password": _PASSWORD,
        "full_name": "Logout User",
        "nickname": "lou",
        "vault_password": "vaultpass123",
        "personal_storage_path": f"~/CortexStorage/logout_{uuid.uuid4().hex[:6]}",
    })
    assert r.status_code == 200
    refresh_token = r.json()["refresh_token"]

    r2 = client.post("/api/auth/logout", json={"refresh_token": refresh_token})
    assert r2.status_code == 200


def test_unauthenticated_access(client):
    """Verify protected endpoints reject unauthenticated requests."""
    assert client.get("/api/auth/me").status_code in (401, 403)
    assert client.get("/api/v1/me/profile").status_code in (401, 403)
    assert client.get("/api/v1/users").status_code in (401, 403)
