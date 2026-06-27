from unittest.mock import MagicMock, patch

HEADERS = {"Authorization": "Bearer fake-token"}


def test_get_indexing_config(client, mock_auth):
    resp = client.get("/api/v1/indexing/config")
    assert resp.status_code == 200
    data = resp.json()
    assert data["config"] is None
    assert data["defaults"] is True


def test_save_indexing_config(client, mock_auth):
    payload = {
        "name": "default",
        "include_paths": ["/src"],
        "exclude_paths": ["/node_modules"],
        "include_patterns": ["*.py"],
        "exclude_patterns": ["*.log"],
        "max_file_size_bytes": 2_000_000,
        "follow_symlinks": True,
        "sync_enabled": True,
        "sync_interval_seconds": 600,
        "priority": 1,
    }
    resp = client.put("/api/v1/indexing/config", json=payload, headers=HEADERS)
    assert resp.status_code == 200
    assert resp.json()["status"] == "saved"

    resp2 = client.get("/api/v1/indexing/config")
    assert resp2.status_code == 200
    data = resp2.json()
    assert data["config"] is not None
    assert data["config"]["name"] == "default"
    assert data["config"]["include_paths"] == ["/src"]
    assert data["config"]["max_file_size_bytes"] == 2_000_000


@patch("backend.app.api.v1.awareness.indexing.IndexingRules")
def test_indexing_preview(mock_rules_cls, client, mock_auth):
    mock_rules = MagicMock()
    mock_rules.get_stats.return_value = {
        "total_files": 100,
        "will_index": 80,
        "excluded_by_directory": 5,
        "excluded_by_pattern": 10,
        "excluded_by_size": 5,
    }
    mock_rules_cls.return_value = mock_rules

    resp = client.post("/api/v1/indexing/preview?repo_path=/test/repo", headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_files"] == 100
    assert data["will_index"] == 80
