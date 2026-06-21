from unittest.mock import patch

import pytest

HEADERS = {"Authorization": "Bearer fake-token"}


def test_sync_defaults(client, mock_auth):
    resp = client.get("/api/v1/sync/defaults")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data["default_paths"], list)
    assert isinstance(data["exclude_dirs"], list)
    assert isinstance(data["embedding_models"], list)
    assert len(data["embedding_models"]) > 0
    assert data["embedding_models"][0]["value"] == "nomic-embed-text"


@patch("backend.app.api.v1.sync.file_watcher")
def test_sync_status(mock_watcher, client, mock_auth):
    mock_watcher.sync_state = {
        "watching": 2,
        "pending": 5,
        "indexed": 100,
        "errors": 1,
        "status": "running",
        "last_sync": "2025-01-01T00:00:00",
        "watched_paths": [],
    }
    resp = client.get("/api/v1/sync/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["watching"] == 2
    assert data["pending_changes"] == 5
    assert data["indexed_files"] == 100
    assert data["errors"] == 1
    assert data["status"] == "running"


def test_sync_validate_path(client, mock_auth):
    resp = client.post("/api/v1/sync/validate-path", json={"path": "/nonexistent/path"}, headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["path"] == "/nonexistent/path"
    assert "resolved_path" in data
    assert isinstance(data["exists"], bool)


def test_sync_validate_path_exists(client, mock_auth):
    resp = client.post("/api/v1/sync/validate-path", json={"path": "/tmp"}, headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["exists"] is True
