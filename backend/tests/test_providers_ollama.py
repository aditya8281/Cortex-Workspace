"""Tests for Ollama provider adapter."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.app.services.providers.ollama import OllamaProvider


@pytest.fixture
def provider():
    return OllamaProvider(base_url="http://localhost:11434")


def test_provider_name(provider):
    assert provider.name == "ollama"
    assert provider.display_name == "Ollama"


def test_provider_name_custom_url():
    p = OllamaProvider(base_url="http://custom:9999/")
    assert p._base_url == "http://custom:9999"


def _make_response(json_data=None, status_code=200, raise_for_status=None):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json = MagicMock(return_value=json_data)
    if raise_for_status:
        resp.raise_for_status = raise_for_status
    else:
        resp.raise_for_status = MagicMock()
    return resp


@pytest.mark.asyncio
async def test_health_check_success(provider):
    resp = _make_response(status_code=200)
    with patch.object(provider._client, "get", new_callable=AsyncMock, return_value=resp):
        assert await provider.health_check() is True


@pytest.mark.asyncio
async def test_health_check_failure(provider):
    with patch.object(provider._client, "get", side_effect=Exception("Connection refused")):
        assert await provider.health_check() is False


@pytest.mark.asyncio
async def test_list_models_empty(provider):
    resp = _make_response(json_data={"models": []})
    with patch.object(provider._client, "get", new_callable=AsyncMock, return_value=resp):
        models = await provider.list_models()
        assert models == []


@pytest.mark.asyncio
async def test_list_models_with_data(provider):
    resp = _make_response(
        json_data={
            "models": [
                {"name": "llama3.1:8b", "size": 4000000000, "modified_at": "2025-01-01", "digest": "abc123"},
                {"name": "codellama:13b", "size": 8000000000, "modified_at": "2025-02-01", "digest": "def456"},
            ]
        }
    )
    with patch.object(provider._client, "get", new_callable=AsyncMock, return_value=resp):
        models = await provider.list_models()
        assert len(models) == 2
        assert models[0].provider_model_id == "llama3.1:8b"
        assert models[0].display_name == "llama3.1"
        assert models[0].family == "llama3.1"
        assert models[0].size_bytes == 4000000000
        assert "ollama.com" in models[0].source_url
        assert models[1].provider_model_id == "codellama:13b"
        assert models[1].display_name == "codellama"


@pytest.mark.asyncio
async def test_list_models_failure(provider):
    with patch.object(provider._client, "get", side_effect=Exception("timeout")):
        models = await provider.list_models()
        assert models == []


@pytest.mark.asyncio
async def test_list_installed(provider):
    resp = _make_response(json_data={"models": [{"name": "llama3.1:8b", "size": 4000000000}]})
    with patch.object(provider._client, "get", new_callable=AsyncMock, return_value=resp):
        installed = await provider.list_installed()
        assert len(installed) == 1
        assert installed[0].provider_model_id == "llama3.1:8b"


@pytest.mark.asyncio
async def test_get_model_variants_returns_empty(provider):
    variants = await provider.get_model_variants("llama3.1:8b")
    assert variants == []


@pytest.mark.asyncio
async def test_get_model_detail(provider):
    resp = _make_response(
        json_data={
            "details": {
                "family": "llama",
                "architecture": "llama",
                "parameter_size": "8B",
                "context_length": 8192,
                "license": "meta-llama",
                "tags": ["chat", "text-generation"],
            }
        }
    )
    with patch.object(provider._client, "post", new_callable=AsyncMock, return_value=resp):
        detail = await provider.get_model_detail("llama3.1:8b")
        assert detail is not None
        assert detail.provider_model_id == "llama3.1:8b"
        assert detail.display_name == "llama3.1"
        assert detail.family == "llama"
        assert detail.parameter_count == "8B"
        assert detail.context_length == 8192
        assert detail.license == "meta-llama"
        assert "chat" in detail.capabilities


@pytest.mark.asyncio
async def test_get_model_detail_failure(provider):
    with patch.object(provider._client, "post", side_effect=Exception("not found")):
        detail = await provider.get_model_detail("nonexistent")
        assert detail is None


@pytest.mark.asyncio
async def test_download_model_success(provider):
    lines = [
        json.dumps({"status": "pulling manifest"}),
        json.dumps({"status": "downloading", "completed": 500, "total": 1000}),
        json.dumps({"status": "downloading", "completed": 1000, "total": 1000}),
        json.dumps({"status": "success"}),
    ]

    async def mock_aiter_lines():
        for line in lines:
            yield line

    mock_stream = AsyncMock()
    mock_stream.status_code = 200
    mock_stream.__aenter__ = AsyncMock(return_value=mock_stream)
    mock_stream.__aexit__ = AsyncMock(return_value=False)
    mock_stream.aiter_lines = MagicMock(return_value=mock_aiter_lines())

    with patch.object(provider._client, "stream", return_value=mock_stream):
        progress_values = []
        result = await provider.download_model("llama3.1:8b", on_progress=lambda p: progress_values.append(p))
        assert result.success is True
        assert result.model_name == "llama3.1:8b"
        assert len(progress_values) == 2
        assert progress_values[0] == 0.5
        assert progress_values[1] == 1.0


@pytest.mark.asyncio
async def test_download_model_failure(provider):
    with patch.object(provider._client, "stream", side_effect=Exception("network error")):
        result = await provider.download_model("llama3.1:8b")
        assert result.success is False
        assert result.error_message is not None


@pytest.mark.asyncio
async def test_cancel_download_returns_false(provider):
    assert await provider.cancel_download("llama3.1:8b") is False


@pytest.mark.asyncio
async def test_delete_model_success(provider):
    resp = _make_response(status_code=200)
    with patch.object(provider._client, "request", new_callable=AsyncMock, return_value=resp):
        assert await provider.delete_model("llama3.1:8b") is True


@pytest.mark.asyncio
async def test_delete_model_failure(provider):
    with patch.object(provider._client, "request", side_effect=Exception("error")):
        assert await provider.delete_model("llama3.1:8b") is False


def test_infer_capabilities_chat(provider):
    caps = provider._infer_capabilities({"family": "llama"})
    assert "chat" in caps
    assert "vision" not in caps


def test_infer_capabilities_vision(provider):
    caps = provider._infer_capabilities({"family": "llava"})
    assert "vision" in caps


def test_infer_capabilities_code(provider):
    caps = provider._infer_capabilities({"family": "codellama"})
    assert "code" in caps


def test_infer_capabilities_embedding(provider):
    caps = provider._infer_capabilities({"family": "nomic-bert"})
    assert "embedding" in caps
