"""Comprehensive tests for the refresh token lifecycle.

Covers:
  - Token creation at register and login
  - Successful rotation (old token invalidated, new token works)
  - Reuse detection (old token rejected after rotation)
  - Revoked token rejection
  - Invalid / missing / expired token handling
  - Logout invalidates refresh token
"""
import uuid

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app


@pytest.fixture(name="client")
def fixture_client():
    return TestClient(app)


def _register(client: TestClient, username: str | None = None) -> dict:
    """Register a user and return the full response JSON."""
    uname = username or f"rt_{uuid.uuid4().hex[:8]}"
    r = client.post("/api/auth/register", json={
        "username": uname,
        "password": "securepass123",
        "confirm_password": "securepass123",
        "full_name": "Refresh Test User",
        "nickname": "rt",
        "vault_password": "vaultpass123",
        "personal_storage_path": f"~/CortexStorage/rt_{uuid.uuid4().hex[:6]}",
    })
    assert r.status_code == 200, f"Register failed: {r.text}"
    return r.json()


# ── Happy path ──────────────────────────────────────────────────────


def test_refresh_returns_new_tokens(client):
    """Register → refresh → should return new access + refresh tokens.

    The refresh token must always differ (new JTI).  The access token
    may match if both are created within the same minute (same exp),
    so we only assert it exists and is a valid bearer string.
    """
    data = _register(client)
    old_refresh = data["refresh_token"]

    r = client.post("/api/auth/refresh", json={"refresh_token": old_refresh})
    assert r.status_code == 200
    body = r.json()
    assert "access_token" in body and len(body["access_token"]) > 20
    assert "refresh_token" in body
    # Refresh token must always differ (new JTI + new exp)
    assert body["refresh_token"] != old_refresh


def test_refreshed_access_token_works(client):
    """Register → refresh → use new access token on /api/auth/me."""
    data = _register(client)
    r = client.post("/api/auth/refresh", json={"refresh_token": data["refresh_token"]})
    new_access = r.json()["access_token"]

    r2 = client.get("/api/auth/me", headers={"Authorization": f"Bearer {new_access}"})
    assert r2.status_code == 200


def test_double_rotation(client):
    """Register → refresh → refresh again → second rotation should work."""
    data = _register(client)
    rt1 = data["refresh_token"]

    r1 = client.post("/api/auth/refresh", json={"refresh_token": rt1})
    assert r1.status_code == 200
    rt2 = r1.json()["refresh_token"]

    r2 = client.post("/api/auth/refresh", json={"refresh_token": rt2})
    assert r2.status_code == 200
    rt3 = r2.json()["refresh_token"]
    assert rt3 != rt2


# ── Revocation / reuse detection ────────────────────────────────────


def test_old_token_rejected_after_rotation(client):
    """Register → refresh (rotates) → try old token again → should 401."""
    data = _register(client)
    old_refresh = data["refresh_token"]

    # First rotation succeeds
    r1 = client.post("/api/auth/refresh", json={"refresh_token": old_refresh})
    assert r1.status_code == 200

    # Reusing the old token should be rejected
    r2 = client.post("/api/auth/refresh", json={"refresh_token": old_refresh})
    assert r2.status_code == 401


def test_concurrent_reuse_detected(client):
    """Simulate two requests with the same token — second should fail.

    Sequence:
      1. Register → get refresh_token
      2. First refresh succeeds (rotates token)
      3. Second refresh with the SAME old token → 401
    """
    data = _register(client)
    rt = data["refresh_token"]

    r1 = client.post("/api/auth/refresh", json={"refresh_token": rt})
    assert r1.status_code == 200

    # Replay attack
    r2 = client.post("/api/auth/refresh", json={"refresh_token": rt})
    assert r2.status_code == 401


# ── Logout invalidates ─────────────────────────────────────────────


def test_refresh_after_logout_fails(client):
    """Register → logout → try to refresh with same token → should 401."""
    data = _register(client)
    rt = data["refresh_token"]

    r = client.post("/api/auth/logout", json={"refresh_token": rt})
    assert r.status_code == 200

    r2 = client.post("/api/auth/refresh", json={"refresh_token": rt})
    assert r2.status_code == 401


# ── Error cases ─────────────────────────────────────────────────────


def test_refresh_with_missing_token(client):
    r = client.post("/api/auth/refresh", json={})
    # Missing refresh_token → Pydantic validation error (422)
    assert r.status_code == 422


def test_refresh_with_invalid_token(client):
    r = client.post("/api/auth/refresh", json={"refresh_token": "not.a.valid.jwt"})
    assert r.status_code == 401


def test_refresh_with_empty_string(client):
    r = client.post("/api/auth/refresh", json={"refresh_token": ""})
    assert r.status_code == 401


def test_refresh_with_garbage_token(client):
    r = client.post("/api/auth/refresh", json={"refresh_token": "garbage123"})
    assert r.status_code == 401


def test_refresh_with_expired_token(client):
    """Construct a JWT with exp in the past and verify it's rejected."""
    from datetime import datetime, timedelta, timezone

    from jose import jwt as jose_jwt

    from backend.app.core.config import settings

    ALGORITHM = settings.ALGORITHM
    SECRET = settings.SECRET_KEY

    payload = {
        "sub": "999",
        "jti": str(uuid.uuid4()),
        "exp": datetime.now(timezone.utc) - timedelta(hours=1),
    }
    expired_token = jose_jwt.encode(payload, SECRET, algorithm=ALGORITHM)
    r = client.post("/api/auth/refresh", json={"refresh_token": expired_token})
    assert r.status_code == 401
