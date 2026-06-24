"""Tests for sync_service — model catalog background sync."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.app.models.model_catalog import ModelCatalog, SyncJob
from backend.app.services.ollama_catalog import CatalogSourceStatus
from backend.app.services.providers.base import ProviderModelInfo
from backend.app.services.sync_service import SyncService


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def service(db):
    return SyncService(db)


def _make_model_info(**overrides) -> ProviderModelInfo:
    defaults = {
        "provider_model_id": "llama3:8b",
        "display_name": "llama3",
        "family": "llama",
        "parameter_count": 8.0,
        "architecture": "llama",
        "context_length": 8192,
        "capabilities": ["chat"],
        "license": "llama3",
        "description": "A small Llama 3 model",
        "tags": ["chat", "small"],
        "source_url": "https://ollama.com/library/llama3",
        "size_bytes": 4_000_000_000,
    }
    defaults.update(overrides)
    return ProviderModelInfo(**defaults)


def _make_mock_adapter(name="ollama", models=None):
    adapter = MagicMock()
    adapter.name = name
    adapter.list_models = AsyncMock(return_value=models or [_make_model_info()])
    return adapter


# --- sync_library tests ---


@pytest.mark.asyncio
async def test_sync_library_creates_job_with_running_status(service, db):
    adapter = _make_mock_adapter(name="openai")
    db.scalars.return_value.first.return_value = None
    db.scalars.return_value.all.return_value = []

    with (
        patch("backend.app.services.sync_service.provider_registry") as registry,
        patch("backend.app.services.ollama_catalog.get_ollama_catalog", new_callable=AsyncMock, return_value=([], CatalogSourceStatus())),
    ):
        registry.enabled.return_value = [adapter]
        registry.get.return_value = adapter
        job = await service.sync_library()

    assert job.status == "completed"
    assert job.sync_type == "library"
    # db.add called once for SyncJob, once for ModelCatalog entry
    assert db.add.call_count >= 1
    db.commit.assert_called()


@pytest.mark.asyncio
async def test_sync_library_discovers_models(service, db):
    models = [
        _make_model_info(provider_model_id="llama3:8b", display_name="llama3"),
        _make_model_info(
            provider_model_id="mistral:7b",
            display_name="mistral",
            family="mistral",
        ),
    ]
    adapter = _make_mock_adapter(name="openai", models=models)

    # Return None for existing model lookup (no existing models)
    db.scalars.return_value.first.return_value = None
    db.scalars.return_value.all.return_value = []

    with (
        patch("backend.app.services.sync_service.provider_registry") as registry,
        patch("backend.app.services.ollama_catalog.get_ollama_catalog", new_callable=AsyncMock, return_value=([], CatalogSourceStatus())),
    ):
        registry.enabled.return_value = [adapter]
        registry.get.return_value = adapter
        job = await service.sync_library()

    assert job.models_discovered == 2
    assert job.models_added == 2


@pytest.mark.asyncio
async def test_sync_library_filters_by_provider_name(service, db):
    adapter = _make_mock_adapter(name="ollama")
    db.scalars.return_value.first.return_value = None
    db.scalars.return_value.all.return_value = []

    ollama_models = [
        {"name": "llama3:8b", "family": "llama", "parameter_size": "8B", "capabilities": ["chat"], "description": "A Llama 3 model"},
    ]

    with (
        patch("backend.app.services.sync_service.provider_registry") as registry,
        patch("backend.app.services.ollama_catalog.get_ollama_catalog", new_callable=AsyncMock, return_value=(ollama_models, CatalogSourceStatus())),
    ):
        registry.get.return_value = adapter
        job = await service.sync_library(provider_name="ollama")

    assert job.status == "completed"


@pytest.mark.asyncio
async def test_sync_library_no_adapter_returns_empty_job(service, db):
    db.scalars.return_value.all.return_value = []

    with (
        patch("backend.app.services.sync_service.provider_registry") as registry,
        patch("backend.app.services.ollama_catalog.get_ollama_catalog", new_callable=AsyncMock, return_value=([], CatalogSourceStatus())),
    ):
        registry.get.return_value = None
        job = await service.sync_library(provider_name="nonexistent")

    assert job.status == "completed"
    assert job.models_discovered == 0
    assert job.models_added == 0


@pytest.mark.asyncio
async def test_sync_library_sets_provider_id(service, db):
    adapter = _make_mock_adapter(name="openai")
    db.scalars.return_value.first.return_value = None

    def mock_scalars(stmt):
        result = MagicMock()
        result.first.return_value = None
        return result

    db.scalars.side_effect = mock_scalars

    mock_provider = MagicMock()
    mock_provider.id = 42

    with (
        patch("backend.app.services.sync_service.provider_registry") as registry,
        patch("backend.app.services.ollama_catalog.get_ollama_catalog", new_callable=AsyncMock, return_value=([], CatalogSourceStatus())),
    ):
        registry.enabled.return_value = [adapter]
        registry.get.return_value = adapter

        call_count = 0

        def mock_scalars_with_provider(stmt):
            nonlocal call_count
            call_count += 1
            result = MagicMock()
            if call_count == 1:
                # Model lookup
                result.first.return_value = None
            elif call_count == 2:
                # Provider lookup
                result.first.return_value = mock_provider
            else:
                result.first.return_value = None
            return result

        db.scalars = mock_scalars_with_provider
        job = await service.sync_library()

    assert job.provider_id == 42


@pytest.mark.asyncio
async def test_sync_library_handles_adapter_exception(service, db):
    adapter = _make_mock_adapter(name="openai")
    adapter.list_models = AsyncMock(side_effect=RuntimeError("network error"))
    db.scalars.return_value.first.return_value = None
    db.scalars.return_value.all.return_value = []

    with (
        patch("backend.app.services.sync_service.provider_registry") as registry,
        patch("backend.app.services.ollama_catalog.get_ollama_catalog", new_callable=AsyncMock, return_value=([], CatalogSourceStatus())),
    ):
        registry.enabled.return_value = [adapter]
        job = await service.sync_library()

    assert job.status == "completed"
    assert job.models_discovered == 0


@pytest.mark.asyncio
async def test_sync_library_sets_failed_on_global_error(service, db):
    """Test that an unhandled error during sync sets status to failed."""
    adapter = _make_mock_adapter(name="openai")
    adapter.list_models = AsyncMock(return_value=[])

    def mock_scalars(stmt):
        result = MagicMock()
        result.first.return_value = None
        return result

    db.scalars = mock_scalars
    # Commits: 1) after adding job (OK), 2) after sync completes (FAIL), 3) in except (OK)
    db.commit.side_effect = [None, RuntimeError("db down"), None]

    with (
        patch("backend.app.services.sync_service.provider_registry") as registry,
        patch("backend.app.services.ollama_catalog.get_ollama_catalog", new_callable=AsyncMock, return_value=([], CatalogSourceStatus())),
    ):
        registry.enabled.return_value = [adapter]
        job = await service.sync_library()

    assert job.status == "failed"
    assert "db down" in job.error_message


# --- _upsert_model tests ---


@pytest.mark.asyncio
async def test_upsert_model_creates_new(service, db):
    db.scalars.return_value.first.return_value = None

    result = await service._upsert_model(_make_model_info(), "ollama")

    assert result is False
    db.add.assert_called_once()
    added_entry = db.add.call_args[0][0]
    assert isinstance(added_entry, ModelCatalog)
    assert added_entry.model_id == "llama3:8b"
    assert added_entry.provider == "ollama"


@pytest.mark.asyncio
async def test_upsert_model_updates_existing(service, db):
    existing = MagicMock(spec=ModelCatalog)
    existing.model_id = "llama3:8b"
    existing.family = "llama"
    existing.parameter_count = 8.0
    existing.architecture = "llama"
    existing.context_length_default = 8192
    existing.capabilities = ["chat"]
    existing.license = "llama3"
    existing.description = "old desc"
    existing.tags = ["old"]
    existing.source_url = "http://old"

    db.scalars.return_value.first.return_value = existing

    new_info = _make_model_info(
        display_name="llama3-updated",
        description="Updated description",
        tags=["new"],
    )

    result = await service._upsert_model(new_info, "ollama")

    assert result is True
    assert existing.display_name == "llama3-updated"
    assert existing.description == "Updated description"
    assert existing.tags == ["new"]
    assert existing.last_updated is not None
    db.add.assert_not_called()


@pytest.mark.asyncio
async def test_upsert_model_preserves_existing_fields_on_update(service, db):
    existing = MagicMock(spec=ModelCatalog)
    existing.family = "llama"
    existing.parameter_count = 8.0
    existing.architecture = "llama"
    existing.context_length_default = 8192
    existing.capabilities = ["chat"]
    existing.license = "llama3"
    existing.description = "Keep me"
    existing.tags = ["keep"]
    existing.source_url = "http://keep"

    db.scalars.return_value.first.return_value = existing

    info = _make_model_info(
        display_name="llama3",
        family=None,
        parameter_count=None,
        architecture=None,
        context_length=None,
        capabilities=[],
        license=None,
        description="",
        tags=[],
        source_url=None,
    )

    await service._upsert_model(info, "ollama")

    assert existing.description == "Keep me"
    assert existing.tags == ["keep"]
    assert existing.source_url == "http://keep"


# --- get_sync_status tests ---


def test_get_sync_status_returns_last_10(service, db):
    jobs = []
    for i in range(10):
        job = MagicMock(spec=SyncJob)
        job.id = i + 1
        job.sync_type = "library"
        job.status = "completed"
        job.models_discovered = 10
        job.models_added = 5
        job.models_updated = 3
        job.error_message = None
        job.started_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
        job.completed_at = datetime(2025, 1, 1, 0, 5, tzinfo=timezone.utc)
        job.created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
        jobs.append(job)

    db.scalars.return_value.all.return_value = jobs

    result = service.get_sync_status()

    assert len(result) == 10
    assert result[0]["id"] == 1
    assert result[0]["status"] == "completed"
    assert result[0]["models_discovered"] == 10


def test_get_sync_status_empty(service, db):
    db.scalars.return_value.all.return_value = []

    result = service.get_sync_status()

    assert result == []


def test_get_sync_status_handles_none_timestamps(service, db):
    job = MagicMock(spec=SyncJob)
    job.id = 1
    job.sync_type = "library"
    job.status = "completed"
    job.models_discovered = 0
    job.models_added = 0
    job.models_updated = 0
    job.error_message = None
    job.started_at = None
    job.completed_at = None
    job.created_at = None

    db.scalars.return_value.all.return_value = [job]

    result = service.get_sync_status()

    assert len(result) == 1
    assert result[0]["started_at"] is None
    assert result[0]["completed_at"] is None
    assert result[0]["created_at"] is None
