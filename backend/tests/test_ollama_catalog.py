"""Tests for the unified Ollama catalog service."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from backend.app.services.intelligence.ollama_catalog import (
    OllamaCatalogService,
    get_catalog_service,
    get_ollama_catalog,
    get_ollama_catalog_sync,
)

# ── Fixtures ─────────────────────────────────────────────────────


@pytest.fixture
def service(tmp_path: Path) -> OllamaCatalogService:
    """Create a catalog service with a temp cache dir."""
    import backend.app.services.intelligence.ollama_catalog as mod

    svc = OllamaCatalogService()
    # Override cache path to use tmp
    mod.CACHE_DIR = tmp_path
    mod.CACHE_FILE = tmp_path / "ollama_catalog.json"
    mod.FALLBACK_FILE = tmp_path / "ollama_catalog_fallback.json"
    return svc


@pytest.fixture
def sample_api_response() -> dict:
    """Sample /api/tags response."""
    return {
        "models": [
            {
                "name": "llama3.1:8b",
                "size": 4_700_000_000_000,
                "digest": "abc123",
                "modified_at": "2024-01-01T00:00:00Z",
                "details": {
                    "family": "llama",
                    "parameter_size": "8B",
                    "quantization_level": "Q4_K_M",
                },
            },
            {
                "name": "qwen2.5:7b",
                "size": 4_500_000_000_000,
                "digest": "def456",
                "modified_at": "2024-01-01T00:00:00Z",
                "details": {
                    "family": "qwen",
                    "parameter_size": "7B",
                    "quantization_level": "Q4_K_M",
                },
            },
        ]
    }


@pytest.fixture
def sample_show_response() -> dict:
    """Sample /api/show response."""
    return {
        "capabilities": ["completion", "tools"],
        "template": "{{ .System }}\n{{ .Prompt }}\n{{ .Tools }}",
        "parameters": "temperature 0.7",
        "license": "Apache 2.0",
        "details": {
            "family": "llama",
            "parameter_size": "8B",
            "quantization_level": "Q4_K_M",
        },
        "model_info": {
            "general.architecture": "llama",
            "general.parameter_count": 8000000000,
        },
    }


@pytest.fixture
def sample_manifest() -> dict:
    """Sample OCI manifest."""
    return {
        "schemaVersion": 2,
        "mediaType": "application/vnd.oci.image.manifest.v1+json",
        "config": {"digest": "sha256:config123", "size": 100},
        "layers": [
            {
                "mediaType": "application/vnd.ollama.image.model",
                "digest": "sha256:model123",
                "size": 4_700_000_000_000,
            },
            {
                "mediaType": "application/vnd.ollama.image.template",
                "digest": "sha256:template123",
                "size": 200,
            },
            {
                "mediaType": "application/vnd.ollama.image.params",
                "digest": "sha256:params123",
                "size": 50,
            },
        ],
    }


# ── Initialization tests ─────────────────────────────────────────


class TestServiceInit:
    def test_service_initializes(self) -> None:
        svc = OllamaCatalogService()
        assert svc is not None
        assert svc._client is None

    def test_singleton(self) -> None:
        svc1 = get_catalog_service()
        svc2 = get_catalog_service()
        assert svc1 is svc2


# ── Cache tests ──────────────────────────────────────────────────


class TestCache:
    def test_load_cache_empty(self, service: OllamaCatalogService) -> None:
        assert service._load_cache() is None

    def test_save_and_load_cache(self, service: OllamaCatalogService) -> None:
        models = [{"name": "llama3.1:8b", "source": "registry"}]
        service._save_cache(models)
        cache = service._load_cache()
        assert cache is not None
        assert cache["models"] == models
        assert "fetched_at" in cache

    def test_cache_validity(self, service: OllamaCatalogService) -> None:
        # No cache
        assert not service._is_cache_valid({})

        # Valid cache
        cache = {"fetched_at": datetime.now(timezone.utc).isoformat(), "models": []}
        assert service._is_cache_valid(cache)

        # Expired cache
        old = {"fetched_at": (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat(), "models": []}
        assert not service._is_cache_valid(old)

    def test_load_cache_corrupt_file(self, service: OllamaCatalogService) -> None:
        from backend.app.services.intelligence.ollama_catalog import CACHE_FILE

        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text("not json")
        assert service._load_cache() is None


# ── Capability detection tests ───────────────────────────────────


class TestCapabilityDetection:
    def test_tools_capability(self) -> None:
        template = "{{ .System }}\n{{ .Prompt }}\n{{ .Tools }}"
        caps = OllamaCatalogService._detect_capabilities(template)
        assert "tools" in caps

    def test_vision_capability(self) -> None:
        template = "{{ .Images }}\n{{ .System }}"
        caps = OllamaCatalogService._detect_capabilities(template)
        assert "vision" in caps

    def test_thinking_capability(self) -> None:
        template = "<think>\n{{ .Content }}"
        caps = OllamaCatalogService._detect_capabilities(template)
        assert "thinking" in caps

    def test_no_capabilities(self) -> None:
        caps = OllamaCatalogService._detect_capabilities("")
        assert caps == []

    def test_multiple_capabilities(self) -> None:
        template = "{{ .Tools }} {{ .Images }} <think>"
        caps = OllamaCatalogService._detect_capabilities(template)
        assert "tools" in caps
        assert "vision" in caps
        assert "thinking" in caps


# ── API entry building tests ─────────────────────────────────────


class TestBuildApiEntry:
    def test_basic_entry(self, sample_api_response: dict) -> None:
        tag_info = sample_api_response["models"][0]
        entry = OllamaCatalogService._build_api_entry(tag_info, None, "local")
        assert entry["name"] == "llama3.1:8b"
        assert entry["source"] == "local"
        assert entry["family"] == "llama"
        assert entry["parameter_size"] == "8B"
        assert entry["quantization"] == "Q4_K_M"

    def test_entry_with_show(self, sample_api_response: dict, sample_show_response: dict) -> None:
        tag_info = sample_api_response["models"][0]
        entry = OllamaCatalogService._build_api_entry(tag_info, sample_show_response, "cloud")
        assert entry["source"] == "cloud"
        assert "tools" in entry["capabilities"]
        assert entry["license"] == "Apache 2.0"

    def test_entry_defaults(self) -> None:
        tag_info = {"name": "test:latest", "size": 1000}
        entry = OllamaCatalogService._build_api_entry(tag_info, None, "registry")
        assert entry["name"] == "test:latest"
        assert entry["capabilities"] == []


# ── API source probing tests ─────────────────────────────────────


class TestApiProbing:
    @pytest.mark.asyncio
    async def test_probe_api_source(self, service: OllamaCatalogService, sample_api_response: dict) -> None:
        from unittest.mock import MagicMock

        mock_resp = MagicMock()
        mock_resp.json.return_value = sample_api_response
        mock_resp.raise_for_status = MagicMock()

        mock_show_resp = MagicMock()
        mock_show_resp.json.return_value = {"capabilities": ["completion"]}
        mock_show_resp.raise_for_status = MagicMock()

        client = AsyncMock()
        client.get = AsyncMock(return_value=mock_resp)
        client.post = AsyncMock(return_value=mock_show_resp)
        client.is_closed = False
        service._client = client

        with patch.object(service, "get_client", new_callable=AsyncMock, return_value=client):
            results = await service._probe_api_source("http://localhost:11434", {})

        assert len(results) == 2
        assert results[0]["name"] == "llama3.1:8b"
        assert results[1]["name"] == "qwen2.5:7b"


# ── Cache integration tests ──────────────────────────────────────


class TestCacheIntegration:
    @pytest.mark.asyncio
    async def test_fetch_catalog_returns_cached(self, service: OllamaCatalogService) -> None:
        cached = [{"name": "llama3.1:8b", "source": "cached"}]
        service._save_cache(cached)

        result, status = await service.fetch_catalog(force_refresh=False)
        assert result == cached
        assert not status.from_fallback

    @pytest.mark.asyncio
    async def test_fetch_catalog_force_refresh(self, service: OllamaCatalogService) -> None:
        cached = [{"name": "stale", "source": "cached"}]
        service._save_cache(cached)

        with (
            patch.object(service, "fetch_cloud_models", return_value=[]),
            patch.object(service, "fetch_local_models", return_value=[]),
            patch.object(service, "fetch_registry_models", return_value=[]),
        ):
            result, status = await service.fetch_catalog(force_refresh=True)

        assert result == []
        assert not status.from_fallback


# ── Deduplication tests ──────────────────────────────────────────


class TestDeduplication:
    @pytest.mark.asyncio
    async def test_cloud_takes_priority(self, service: OllamaCatalogService) -> None:
        cloud = [{"name": "llama3.1:8b", "source": "cloud", "capabilities": ["tools"]}]
        registry = [{"name": "llama3.1:8b", "source": "registry", "capabilities": []}]

        with (
            patch.object(service, "fetch_cloud_models", return_value=cloud),
            patch.object(service, "fetch_local_models", return_value=[]),
            patch.object(service, "fetch_registry_models", return_value=registry),
        ):
            result, _status = await service.fetch_catalog(force_refresh=True)

        assert len(result) == 1
        assert result[0]["source"] == "cloud"


# ── Sync wrapper tests ───────────────────────────────────────────


class TestSyncWrapper:
    def test_fetch_catalog_sync(self, service: OllamaCatalogService) -> None:
        cached = [{"name": "test:latest", "source": "cache"}]
        service._save_cache(cached)

        result = service.fetch_catalog_sync(force_refresh=False)
        assert isinstance(result, tuple)
        models, status = result
        assert models == cached
        assert not status.from_fallback


# ── Module-level function tests ──────────────────────────────────


class TestModuleFunctions:
    def test_get_ollama_catalog_sync(self) -> None:
        result = get_ollama_catalog_sync(force_refresh=False)
        assert isinstance(result, tuple)
        models, status = result
        assert isinstance(models, list)

    @pytest.mark.asyncio
    async def test_get_ollama_catalog(self) -> None:
        result = await get_ollama_catalog(force_refresh=False)
        assert isinstance(result, tuple)
        models, status = result
        assert isinstance(models, list)
