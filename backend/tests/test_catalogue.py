"""Tests for catalogue manager."""

from unittest.mock import patch

from backend.app.services.catalogue import CatalogueManager
from backend.app.services.ollama_catalog import CatalogSourceStatus

MOCK_CATALOG = [
    {
        "name": "llama3.1:8b",
        "family": "llama",
        "parameter_size": "8B",
        "capabilities": ["chat", "code"],
        "source": "registry",
        "size": 4700000000,
        "quantization": "Q4_K_M",
    },
    {
        "name": "qwen2.5:7b",
        "family": "qwen",
        "parameter_size": "7B",
        "capabilities": ["chat"],
        "source": "registry",
        "size": 4400000000,
        "quantization": "Q4_K_M",
    },
]


@patch(
    "backend.app.services.ollama_catalog.get_ollama_catalog_sync",
    return_value=(MOCK_CATALOG, CatalogSourceStatus()),
)
def test_ingest_from_catalog(mock_sync, _db_session):
    cm = CatalogueManager(_db_session)
    count = cm.ingest_from_catalog()
    assert count == 2  # Two new base models


@patch(
    "backend.app.services.ollama_catalog.get_ollama_catalog_sync",
    return_value=(MOCK_CATALOG, CatalogSourceStatus()),
)
def test_ingest_is_idempotent(mock_sync, _db_session):
    cm = CatalogueManager(_db_session)
    cm.ingest_from_catalog()
    count2 = cm.ingest_from_catalog()
    assert count2 == 0  # Should not add duplicates


@patch(
    "backend.app.services.ollama_catalog.get_ollama_catalog_sync",
    return_value=(MOCK_CATALOG, CatalogSourceStatus()),
)
def test_get_all_catalogue(mock_sync, _db_session):
    cm = CatalogueManager(_db_session)
    cm.ingest_from_catalog()
    models = cm.get_all_catalogue()
    assert len(models) == 2


def test_seed_curated_models_backward_compat(_db_session):
    """seed_curated_models() still works as a wrapper."""
    with patch(
        "backend.app.services.ollama_catalog.get_ollama_catalog_sync",
        return_value=(MOCK_CATALOG, CatalogSourceStatus()),
    ):
        cm = CatalogueManager(_db_session)
        count = cm.seed_curated_models()
        assert count == 2
