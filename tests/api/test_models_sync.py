"""Tests for models sync — catalog synchronization with Ollama."""
from unittest.mock import AsyncMock, MagicMock, patch

HEADERS = {"Authorization": "Bearer fake-token"}


def test_sync_endpoint_returns_result(client, mock_auth):
    """POST /models/installed/sync returns SyncInstalledResponse."""
    mock_result = MagicMock()
    mock_result.matched = 2
    mock_result.created = 1
    mock_result.deleted = 0
    mock_result.errors = []

    with patch("backend.app.services.intelligence.ollama_sync.OllamaSyncService") as MockService:
        MockService.return_value.sync_installed_models = AsyncMock(return_value=mock_result)
        # Patch the core.db.get_db used directly inside the endpoint (not via Depends)
        with patch("backend.app.core.db.get_db") as mock_core_get_db:
            mock_db_session = MagicMock()
            mock_core_get_db.return_value = iter([mock_db_session])
            response = client.post("/api/v1/models/installed/sync", headers=HEADERS)

    assert response.status_code == 200
    data = response.json()
    assert data["matched"] == 2
    assert data["created"] == 1
    assert data["deleted"] == 0
