from unittest.mock import patch

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


@patch("backend.app.api.v1.sync.get_file_watcher_v2")
def test_sync_status(mock_get_watcher, client, mock_auth):
    mock_watcher = mock_get_watcher.return_value
    mock_watcher.watched_count = 2
    mock_watcher.is_running = True
    resp = client.get("/api/v1/sync/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["watching"] == 2
    assert data["status"] == "watching"


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
