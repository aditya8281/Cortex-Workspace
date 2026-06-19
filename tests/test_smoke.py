"""Quick smoke test for all endpoints.

Each test is fully self-contained — registers its own user and does not
depend on state from other tests.  This makes them safe to run in any
order and compatible with per-test DB isolation (rollback).
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app


@pytest.fixture(name="client")
def fixture_client():
    with TestClient(app) as c:
        yield c


_USERNAME = f"smoke_{uuid.uuid4().hex[:8]}"
_PASSWORD = "securepass123"


def _register_user(client: TestClient) -> dict:
    """Register a user and return the response JSON."""
    storage = f"~/CortexStorage/smoke_{uuid.uuid4().hex[:6]}"
    r = client.post(
        "/api/auth/register",
        json={
            "username": f"smoke_{uuid.uuid4().hex[:8]}",
            "password": _PASSWORD,
            "confirm_password": _PASSWORD,
            "full_name": "Smoke User",
            "nickname": "su",
            "vault_password": "vaultpass123",
            "personal_storage_path": storage,
        },
    )
    assert r.status_code == 200, f"Register failed: {r.text}"
    return r.json()


# ── Health & readonly endpoints (independent) ────────────────────────


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
    """Memory endpoint requires authentication — verify 401 without token."""
    r = client.get("/api/memory")
    assert r.status_code == 401


# ── Auth flow tests (each self-contained) ───────────────────────────


def test_register_and_me(client):
    """Register a user, then immediately access /me with the returned token."""
    data = _register_user(client)
    token = data["access_token"]

    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["username"] == data["user"]["username"]


def test_login_and_me(client):
    """Register → logout flow: register, login, access /me."""
    uname = f"smoke_login_{uuid.uuid4().hex[:8]}"
    storage = f"~/CortexStorage/smoke_{uuid.uuid4().hex[:6]}"
    client.post(
        "/api/auth/register",
        json={
            "username": uname,
            "password": _PASSWORD,
            "confirm_password": _PASSWORD,
            "full_name": "Login User",
            "nickname": "lu",
            "vault_password": "vaultpass123",
            "personal_storage_path": storage,
        },
    )

    r = client.post("/api/auth/login", json={"username": uname, "password": _PASSWORD})
    assert r.status_code == 200
    token = r.json()["access_token"]

    r2 = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 200
    assert r2.json()["username"] == uname


def test_memory_post(client):
    """Register a user and post a memory entry."""
    data = _register_user(client)
    token = data["access_token"]

    r = client.post(
        "/api/memory",
        json={
            "title": "smoke test",
            "content": "hello from smoke test",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200


def test_profile_get_put(client):
    """Register a user, GET profile, then PUT bio."""
    data = _register_user(client)
    token = data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    r = client.get("/api/v1/me/profile", headers=headers)
    assert r.status_code == 200
    assert r.json()["username"] == data["user"]["username"]

    r2 = client.put("/api/v1/me/profile", json={"bio": "smoke bio"}, headers=headers)
    assert r2.status_code == 200
    assert r2.json()["bio"] == "smoke bio"


def test_auth_refresh(client):
    """Register a fresh user and test the refresh token flow."""
    data = _register_user(client)
    refresh_token = data["refresh_token"]

    r = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_auth_logout(client):
    """Register a fresh user and test the logout flow."""
    data = _register_user(client)
    refresh_token = data["refresh_token"]

    r = client.post("/api/auth/logout", json={"refresh_token": refresh_token})
    assert r.status_code == 200


def test_unauthenticated_access(client):
    """Verify protected endpoints reject unauthenticated requests."""
    assert client.get("/api/auth/me").status_code in (401, 403)
    assert client.get("/api/v1/me/profile").status_code in (401, 403)
    assert client.get("/api/v1/users").status_code in (401, 403)
