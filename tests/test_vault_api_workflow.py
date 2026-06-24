"""Tests for vault API endpoints — upload, download, delete, rename, move, search, etc."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from backend.app.api.deps import get_current_user
from backend.app.main import app

HEADERS = {"Authorization": "Bearer fake-token"}


@pytest.fixture()
def unlocked_user():
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


# ── Upload ──────────────────────────────────────────────────────────


@patch("backend.app.api.v1.vault.vault_service")
def test_upload_file(mock_svc, client, unlocked_user):
    mock_svc._require_unlocked.return_value = None
    mock_svc.upload_vault_file.return_value = {
        "path": "test.txt",
        "name": "test.txt",
        "size": 7,
    }
    resp = client.post(
        "/api/v1/me/vault/files/upload",
        files={"file": ("test.txt", b"content", "text/plain")},
        headers=HEADERS,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "test.txt"
    mock_svc.upload_vault_file.assert_called_once()


@patch("backend.app.api.v1.vault.vault_service")
def test_upload_file_locked(mock_svc, client, mock_auth):
    mock_svc._require_unlocked.side_effect = HTTPException(status_code=403, detail="Vault is locked")
    resp = client.post(
        "/api/v1/me/vault/files/upload",
        files={"file": ("test.txt", b"content", "text/plain")},
        headers=HEADERS,
    )
    assert resp.status_code == 403


# ── Download ────────────────────────────────────────────────────────


@patch("backend.app.api.v1.vault.vault_service")
def test_download_file(mock_svc, client, unlocked_user):
    mock_svc._require_unlocked.return_value = None
    mock_svc.download_vault_file.return_value = b"file content"
    resp = client.get("/api/v1/me/vault/files/download/test.txt", headers=HEADERS)
    assert resp.status_code == 200
    assert resp.content == b"file content"
    assert "attachment" in resp.headers.get("content-disposition", "")


@patch("backend.app.api.v1.vault.vault_service")
def test_download_file_not_found(mock_svc, client, unlocked_user):
    mock_svc._require_unlocked.return_value = None
    mock_svc.download_vault_file.side_effect = HTTPException(status_code=404, detail="File not found")
    resp = client.get("/api/v1/me/vault/files/download/missing.txt", headers=HEADERS)
    assert resp.status_code == 404


# ── Delete ──────────────────────────────────────────────────────────


@patch("backend.app.api.v1.vault.vault_service")
def test_delete_file(mock_svc, client, unlocked_user):
    mock_svc._require_unlocked.return_value = None
    mock_svc.delete_vault_file.return_value = True
    resp = client.delete("/api/v1/me/vault/files/test.txt", headers=HEADERS)
    assert resp.status_code == 200
    assert resp.json()["deleted"] is True


@patch("backend.app.api.v1.vault.vault_service")
def test_delete_file_not_found(mock_svc, client, unlocked_user):
    mock_svc._require_unlocked.return_value = None
    mock_svc.delete_vault_file.return_value = False
    resp = client.delete("/api/v1/me/vault/files/missing.txt", headers=HEADERS)
    assert resp.status_code == 404


@patch("backend.app.api.v1.vault.vault_service")
def test_delete_file_locked(mock_svc, client, mock_auth):
    mock_svc._require_unlocked.side_effect = HTTPException(status_code=403, detail="Vault is locked")
    resp = client.delete("/api/v1/me/vault/files/test.txt", headers=HEADERS)
    assert resp.status_code == 403


# ── Rename ──────────────────────────────────────────────────────────


@patch("backend.app.api.v1.vault.vault_service")
def test_rename_file(mock_svc, client, unlocked_user):
    mock_svc._require_unlocked.return_value = None
    mock_svc.rename_vault_item.return_value = {"path": "new.txt", "name": "new.txt"}
    resp = client.put(
        "/api/v1/me/vault/files/old.txt/rename",
        json={"new_name": "new.txt"},
        headers=HEADERS,
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "new.txt"


@patch("backend.app.api.v1.vault.vault_service")
def test_rename_file_locked(mock_svc, client, mock_auth):
    mock_svc._require_unlocked.side_effect = HTTPException(status_code=403, detail="Vault is locked")
    resp = client.put(
        "/api/v1/me/vault/files/old.txt/rename",
        json={"new_name": "new.txt"},
        headers=HEADERS,
    )
    assert resp.status_code == 403


# ── Move ────────────────────────────────────────────────────────────


@patch("backend.app.api.v1.vault.vault_service")
def test_move_file(mock_svc, client, unlocked_user):
    mock_svc._require_unlocked.return_value = None
    mock_svc.move_vault_item.return_value = {"name": "file.txt", "path": "sub/file.txt"}
    resp = client.post(
        "/api/v1/me/vault/files/move",
        json={"source_path": "file.txt", "destination_folder": "sub"},
        headers=HEADERS,
    )
    assert resp.status_code == 200
    assert resp.json()["path"] == "sub/file.txt"


# ── Create Folder ───────────────────────────────────────────────────


@patch("backend.app.api.v1.vault.vault_service")
def test_create_folder(mock_svc, client, unlocked_user):
    mock_svc._require_unlocked.return_value = None
    mock_svc.create_vault_folder.return_value = {"path": "new_folder", "name": "new_folder"}
    resp = client.post(
        "/api/v1/me/vault/folders",
        json={"folder_path": "new_folder"},
        headers=HEADERS,
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "new_folder"


@patch("backend.app.api.v1.vault.vault_service")
def test_create_folder_locked(mock_svc, client, mock_auth):
    mock_svc._require_unlocked.side_effect = HTTPException(status_code=403, detail="Vault is locked")
    resp = client.post(
        "/api/v1/me/vault/folders",
        json={"folder_path": "new_folder"},
        headers=HEADERS,
    )
    assert resp.status_code == 403


# ── Search ──────────────────────────────────────────────────────────


@patch("backend.app.api.v1.vault.vault_service")
def test_search_files(mock_svc, client, unlocked_user):
    mock_svc._require_unlocked.return_value = None
    mock_svc.search_vault_files.return_value = {
        "results": [{"name": "doc.txt", "path": "doc.txt", "is_dir": False, "score": 0.95}]
    }
    resp = client.post(
        "/api/v1/me/vault/search",
        json={"query": "doc"},
        headers=HEADERS,
    )
    assert resp.status_code == 200
    assert len(resp.json()["results"]) == 1


@patch("backend.app.api.v1.vault.vault_service")
def test_search_files_empty(mock_svc, client, unlocked_user):
    mock_svc._require_unlocked.return_value = None
    mock_svc.search_vault_files.return_value = {"results": []}
    resp = client.post(
        "/api/v1/me/vault/search",
        json={"query": "nonexistent"},
        headers=HEADERS,
    )
    assert resp.status_code == 200
    assert resp.json()["results"] == []


# ── Metadata ────────────────────────────────────────────────────────


@patch("backend.app.api.v1.vault.vault_service")
def test_update_metadata(mock_svc, client, unlocked_user):
    mock_svc._require_unlocked.return_value = None
    mock_svc.update_vault_metadata.return_value = {"path": "doc.txt", "favorite": True, "tags": ["important"]}
    resp = client.put(
        "/api/v1/me/vault/files/doc.txt/metadata",
        json={"favorite": True, "tags": ["important"]},
        headers=HEADERS,
    )
    assert resp.status_code == 200
    assert resp.json()["favorite"] is True


# ── Change Password ─────────────────────────────────────────────────


@patch("backend.app.api.v1.vault.vault_service")
def test_change_password(mock_svc, client, unlocked_user):
    mock_svc._require_unlocked.return_value = None
    mock_svc.change_vault_password.return_value = True
    resp = client.post(
        "/api/v1/me/vault/change-password",
        json={"old_password": "old1234!", "new_password": "new1234!"},
        headers=HEADERS,
    )
    assert resp.status_code == 200
    assert "success" in resp.json()["message"].lower()


@patch("backend.app.api.v1.vault.vault_service")
def test_change_password_wrong_old(mock_svc, client, unlocked_user):
    mock_svc._require_unlocked.return_value = None
    mock_svc.change_vault_password.return_value = False
    resp = client.post(
        "/api/v1/me/vault/change-password",
        json={"old_password": "wrong", "new_password": "new1234!"},
        headers=HEADERS,
    )
    assert resp.status_code == 400


# ── Export ──────────────────────────────────────────────────────────


@patch("backend.app.api.v1.vault.vault_service")
def test_export_files(mock_svc, client, unlocked_user):
    mock_svc._require_unlocked.return_value = None
    mock_svc.export_vault_items.return_value = {"exported": True, "count": 3}
    resp = client.post(
        "/api/v1/me/vault/files/export",
        json={"paths": ["doc.txt", "images/"], "destination_dir": "/tmp/export"},
        headers=HEADERS,
    )
    assert resp.status_code == 200
    assert resp.json()["count"] == 3
