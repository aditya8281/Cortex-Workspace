"""Tests for vault API — encrypted file storage operations."""
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from backend.app.api.deps import get_current_user
from backend.app.main import app

HEADERS = {"Authorization": "Bearer fake-token"}


@pytest.fixture()
def mock_unlocked_auth():
    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.username = "test_user"
    mock_user.full_name = "Test User"
    mock_user.role = "user"
    mock_user.nickname = "testnick"
    mock_user.bio = None
    mock_user.description = None
    mock_user.profile_photo = None
    mock_user.handles_json = {}
    mock_user.preferences_json = {}
    mock_user.vault_locked = False
    mock_user.vault_password_hash = "some_hash"
    mock_user.github_username = None
    mock_user.created_at = None
    mock_user.updated_at = None
    mock_user.deleted_at = None

    def _override():
        return mock_user

    app.dependency_overrides[get_current_user] = _override
    yield mock_user
    app.dependency_overrides.pop(get_current_user, None)


@patch("backend.app.services.memory.vault.is_vault_unlocked")
def test_vault_status_locked(mock_is_unlocked, client, mock_auth):
    mock_is_unlocked.return_value = False
    resp = client.get("/api/v1/privacy/vault/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["locked"] is True


@patch("backend.app.api.v1.privacy.vault.vault_service")
def test_vault_unlock(mock_svc, client, mock_auth):
    mock_svc.unlock_vault.return_value = True
    resp = client.post("/api/v1/privacy/vault/unlock", json={"vault_password": "test1234!"}, headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["unlocked"] is True


@patch("backend.app.api.v1.privacy.vault.vault_service")
def test_vault_unlock_invalid(mock_svc, client, mock_auth):
    mock_svc.unlock_vault.return_value = False
    resp = client.post("/api/v1/privacy/vault/unlock", json={"vault_password": "wrong"}, headers=HEADERS)
    assert resp.status_code == 401


@patch("backend.app.api.v1.privacy.vault.vault_service")
def test_vault_lock(mock_svc, client, mock_auth):
    resp = client.post("/api/v1/privacy/vault/lock", headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["locked"] is True
    mock_svc.lock_vault.assert_called_once()


@patch("backend.app.api.v1.privacy.vault.vault_service")
def test_vault_list_files(mock_svc, client, mock_unlocked_auth):
    mock_svc._require_unlocked.return_value = None
    mock_svc.list_vault_files.return_value = [{"name": "doc.txt", "path": "doc.txt", "is_dir": False, "size": 100}]
    resp = client.get("/api/v1/privacy/vault/files")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["name"] == "doc.txt"


@patch("backend.app.api.v1.privacy.vault.vault_service")
def test_vault_list_files_locked(mock_svc, client, mock_auth):
    mock_svc._require_unlocked.side_effect = HTTPException(status_code=403, detail="Vault is locked")
    resp = client.get("/api/v1/privacy/vault/files")
    assert resp.status_code == 403
