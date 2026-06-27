from unittest.mock import patch

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


def test_get_my_profile(client, mock_auth_real_user):
    resp = client.get("/api/v1/me/profile")
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "test_user"
    assert data["role"] == "user"


def test_update_profile(client, mock_auth_real_user):
    resp = client.put(
        "/api/v1/me/profile",
        json={"full_name": "Updated Name", "bio": "New bio"},
        headers=HEADERS,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["full_name"] == "Updated Name"


def test_update_profile_empty(client, mock_auth_real_user):
    resp = client.put("/api/v1/me/profile", json={}, headers=HEADERS)
    assert resp.status_code == 400


@patch("backend.app.api.v1.interaction.profile._avatar_path")
def test_get_profile_photo_not_found(mock_avatar, client, mock_auth_real_user):
    from pathlib import Path

    mock_avatar.return_value = Path("/nonexistent/photo.webp")
    resp = client.get("/api/v1/me/profile/photo/99999")
    assert resp.status_code == 404


def test_get_my_profile_photo_not_set(client, mock_auth_real_user):
    resp = client.get("/api/v1/me/profile/photo")
    assert resp.status_code == 404


@patch("backend.app.api.v1.interaction.profile._avatar_path")
@patch("backend.app.api.v1.interaction.profile._thumb_path")
def test_remove_profile_photo(mock_thumb, mock_avatar, client, mock_auth_real_user):
    from pathlib import Path

    mock_avatar.return_value = Path("/nonexistent/avatar.webp")
    mock_thumb.return_value = Path("/nonexistent/thumb.webp")
    resp = client.delete("/api/v1/me/profile/photo", headers=HEADERS)
    assert resp.status_code == 200
    assert resp.json()["profile_photo"] is None
