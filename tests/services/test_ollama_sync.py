from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.app.services.intelligence.ollama_sync import OllamaSyncService


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.execute.return_value = MagicMock()
    db.commit = MagicMock()
    return db


@pytest.mark.asyncio
async def test_sync_marks_downloaded_variant(mock_db):
    """Existing variant with matching ollama_tag gets marked downloaded."""
    mock_variant = MagicMock()
    mock_variant.downloaded = False
    mock_variant.ollama_tag = "llama3.1:8b"

    mock_db.execute.return_value.scalars.return_value.all.return_value = [mock_variant]

    mock_installed = [{"name": "llama3.1:8b", "size": 4700000000}]

    with patch("backend.app.services.intelligence.ollama_sync.settings") as mock_settings:
        mock_settings.OLLAMA_BASE_URL = "http://localhost:11434"
        with patch("backend.app.services.intelligence.ollama_sync.httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = {"models": mock_installed}
            mock_response.raise_for_status = MagicMock()
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(return_value=mock_response)

            service = OllamaSyncService()
            result = await service.sync_installed_models(mock_db)

    assert result.matched == 1
    assert mock_variant.downloaded is True
    assert mock_variant.last_downloaded_at is not None


@pytest.mark.asyncio
async def test_sync_graceful_on_offline(mock_db):
    """Returns empty result when Ollama is offline."""
    import httpx

    with patch("backend.app.services.intelligence.ollama_sync.settings") as mock_settings:
        mock_settings.OLLAMA_BASE_URL = "http://localhost:11434"
        with patch("backend.app.services.intelligence.ollama_sync.httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))

            service = OllamaSyncService()
            result = await service.sync_installed_models(mock_db)

    assert result.matched == 0
    assert result.created == 0
    assert len(result.errors) > 0
