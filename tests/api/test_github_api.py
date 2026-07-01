"""Tests for GitHub API — repository sync and webhook integration."""

import pytest

HEADERS = {"Authorization": "Bearer fake-token"}


def _make_real_user(db_session):
    from backend.app.core.security import hash_password
    from backend.app.models.interaction.user import User

    user = User(
        username="test_user",
        full_name="Test User",
        hashed_password=hash_password("password123"),
        role="user",
        nickname="testnick",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def mock_auth_real_user(db_session):
    from backend.app.api.deps import get_current_user
    from backend.app.main import app

    user = _make_real_user(db_session)

    def _override():
        return user

    app.dependency_overrides[get_current_user] = _override
    yield user
    app.dependency_overrides.pop(get_current_user, None)


def test_get_github_status(client, mock_auth_real_user):
    resp = client.get("/api/v1/me/github")
    assert resp.status_code == 200
    data = resp.json()
    assert data["connected"] is False
    assert data["github_username"] is None


def test_connect_github(client, mock_auth_real_user):
    resp = client.post(
        "/api/v1/me/github",
        json={"username": "test-gh-user", "token": "ghp_fake_token_123"},
        headers=HEADERS,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["connected"] is True
    assert data["github_username"] == "test-gh-user"


def test_connect_github_invalid_username(client, mock_auth_real_user):
    resp = client.post(
        "/api/v1/me/github",
        json={"username": "invalid user!@#", "token": "ghp_fake"},
        headers=HEADERS,
    )
    assert resp.status_code == 400


def test_disconnect_github(client, mock_auth_real_user):
    resp = client.delete("/api/v1/me/github", headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["connected"] is False
    assert data["github_username"] is None
