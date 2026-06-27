"""HTTP client mocks for external API testing."""

from unittest.mock import AsyncMock, MagicMock


def create_mock_http_response(status_code: int = 200, json_data: dict | None = None) -> MagicMock:
    """Create a mock HTTP response."""
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = json_data or {}
    response.raise_for_status.return_value = None
    response.text = str(json_data or {})
    return response


def create_mock_http_client() -> AsyncMock:
    """Create a mocked HTTP client (httpx-style)."""
    client = AsyncMock()
    client.get = AsyncMock(return_value=create_mock_http_response())
    client.post = AsyncMock(return_value=create_mock_http_response(201))
    client.put = AsyncMock(return_value=create_mock_http_response())
    client.delete = AsyncMock(return_value=create_mock_http_response(204))
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)
    return client
