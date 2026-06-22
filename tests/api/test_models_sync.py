from unittest.mock import AsyncMock, patch, MagicMock

import pytest

HEADERS = {"Authorization": "Bearer fake-token"}


def test_sync_endpoint_returns_result(client, mock_auth):
    """POST /models/installed/sync returns SyncInstalledResponse."""
    mock_result = MagicMock()
    mock_result.matched = 2
    mock_result.created = 1
    mock_result.deleted = 0
    mock_result.errors = []

    with patch("backend.app.services.ollama_sync.OllamaSyncService") as MockService:
        MockService.return_value.sync_installed_models = AsyncMock(return_value=mock_result)
        response = client.post("/api/v1/models/installed/sync", headers=HEADERS)

    assert response.status_code == 200
    data = response.json()
    assert data["matched"] == 2
    assert data["created"] == 1
    assert data["deleted"] == 0
