"""Tests for provider registry."""

from unittest.mock import MagicMock, patch

import pytest

from backend.app.services.providers.huggingface import HuggingFaceProvider
from backend.app.services.providers.ollama import OllamaProvider
from backend.app.services.providers.registry import (
    ADAPTER_CLASS_MAP,
    ProviderRegistry,
    load_providers_from_db,
    provider_registry,
)


@pytest.fixture
def registry():
    return ProviderRegistry()


@pytest.fixture
def ollama_adapter():
    return OllamaProvider(base_url="http://localhost:11434")


@pytest.fixture
def hf_adapter():
    return HuggingFaceProvider(token="test-token")


# --- Registry basics ---


def test_registry_initially_empty(registry):
    assert registry.all() == []


def test_register_and_get(registry, ollama_adapter):
    registry.register(ollama_adapter)
    assert registry.get("ollama") is ollama_adapter


def test_get_returns_none_for_unknown(registry):
    assert registry.get("nonexistent") is None


def test_all_returns_all_providers(registry, ollama_adapter, hf_adapter):
    registry.register(ollama_adapter)
    registry.register(hf_adapter)
    all_providers = registry.all()
    assert len(all_providers) == 2
    names = {p.name for p in all_providers}
    assert names == {"ollama", "huggingface"}


def test_enabled_returns_all(registry, ollama_adapter):
    registry.register(ollama_adapter)
    assert registry.enabled() == registry.all()


def test_unregister_removes_provider(registry, ollama_adapter):
    registry.register(ollama_adapter)
    removed = registry.unregister("ollama")
    assert removed is ollama_adapter
    assert registry.get("ollama") is None


def test_unregister_returns_none_for_unknown(registry):
    assert registry.unregister("nonexistent") is None


def test_register_overwrites_existing(registry, ollama_adapter):
    registry.register(ollama_adapter)
    new_adapter = OllamaProvider(base_url="http://custom:9999")
    registry.register(new_adapter)
    assert registry.get("ollama") is new_adapter


# --- ADAPTER_CLASS_MAP ---


def test_adapter_class_map_has_ollama():
    assert "ollama" in ADAPTER_CLASS_MAP
    assert ADAPTER_CLASS_MAP["ollama"] is OllamaProvider


def test_adapter_class_map_has_huggingface():
    assert "huggingface" in ADAPTER_CLASS_MAP
    assert ADAPTER_CLASS_MAP["huggingface"] is HuggingFaceProvider


# --- Module-level singleton ---


def test_singleton_exists():
    assert isinstance(provider_registry, ProviderRegistry)


def test_singleton_is_shared():
    from backend.app.services.providers.registry import provider_registry as pr1
    from backend.app.services.providers.registry import provider_registry as pr2

    assert pr1 is pr2


# --- load_providers_from_db ---


def _make_db_provider(name, display_name, provider_type, base_url=None, enabled=True):
    prov = MagicMock()
    prov.name = name
    prov.display_name = display_name
    prov.provider_type = provider_type
    prov.base_url = base_url
    prov.enabled = enabled
    return prov


def test_load_providers_from_db_ollama():
    db = MagicMock()
    ollama_prov = _make_db_provider("ollama", "Ollama", "local", base_url="http://localhost:11434")
    db.scalars.return_value.all.return_value = [ollama_prov]

    registry = ProviderRegistry()
    with patch("backend.app.services.providers.registry.provider_registry", registry):
        result = load_providers_from_db(db, registry)

    assert len(result.all()) == 1
    adapter = result.get("ollama")
    assert adapter is not None
    assert isinstance(adapter, OllamaProvider)


def test_load_providers_from_db_huggingface():
    db = MagicMock()
    hf_prov = _make_db_provider("huggingface", "HuggingFace", "registry", base_url="https://huggingface.co")
    db.scalars.return_value.all.return_value = [hf_prov]

    registry = ProviderRegistry()
    with patch("backend.app.services.providers.registry.provider_registry", registry):
        result = load_providers_from_db(db, registry)

    assert len(result.all()) == 1
    adapter = result.get("huggingface")
    assert adapter is not None
    assert isinstance(adapter, HuggingFaceProvider)


def test_load_providers_from_db_skips_unknown():
    db = MagicMock()
    unknown_prov = _make_db_provider("unknown_provider", "Unknown", "api")
    db.scalars.return_value.all.return_value = [unknown_prov]

    registry = ProviderRegistry()
    with patch("backend.app.services.providers.registry.provider_registry", registry):
        result = load_providers_from_db(db, registry)

    assert result.all() == []


def test_load_providers_from_db_multiple():
    db = MagicMock()
    ollama_prov = _make_db_provider("ollama", "Ollama", "local", base_url="http://localhost:11434")
    hf_prov = _make_db_provider("huggingface", "HuggingFace", "registry")
    db.scalars.return_value.all.return_value = [ollama_prov, hf_prov]

    registry = ProviderRegistry()
    with patch("backend.app.services.providers.registry.provider_registry", registry):
        result = load_providers_from_db(db, registry)

    assert len(result.all()) == 2
    assert result.get("ollama") is not None
    assert result.get("huggingface") is not None


def test_load_providers_from_db_empty():
    db = MagicMock()
    db.scalars.return_value.all.return_value = []

    registry = ProviderRegistry()
    with patch("backend.app.services.providers.registry.provider_registry", registry):
        result = load_providers_from_db(db, registry)

    assert result.all() == []


def test_load_providers_from_db_uses_singleton_by_default():
    db = MagicMock()
    db.scalars.return_value.all.return_value = []

    with patch("backend.app.services.providers.registry.provider_registry") as mock_singleton:
        load_providers_from_db(db)
        assert mock_singleton is not None


def test_load_providers_from_db_passes_base_url_to_ollama():
    db = MagicMock()
    ollama_prov = _make_db_provider("ollama", "Ollama", "local", base_url="http://custom:11434")
    db.scalars.return_value.all.return_value = [ollama_prov]

    registry = ProviderRegistry()
    with patch("backend.app.services.providers.registry.provider_registry", registry):
        result = load_providers_from_db(db, registry)

    adapter = result.get("ollama")
    assert adapter._base_url == "http://custom:11434"
