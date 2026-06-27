"""Provider registry — manages active provider adapters.

Provides a singleton registry for storing, retrieving, and loading provider
adapters backed by the database Provider table.
"""

from __future__ import annotations

import structlog
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.model_catalog import Provider
from backend.app.services.intelligence.providers.base import ProviderAdapter
from backend.app.services.intelligence.providers.huggingface import HuggingFaceProvider
from backend.app.services.intelligence.providers.ollama import OllamaProvider

logger = structlog.get_logger()

ADAPTER_CLASS_MAP: dict[str, type[ProviderAdapter]] = {
    "ollama": OllamaProvider,
    "huggingface": HuggingFaceProvider,
}


class ProviderRegistry:
    """Registry that stores and manages active provider adapters."""

    def __init__(self) -> None:
        self._providers: dict[str, ProviderAdapter] = {}

    def register(self, adapter: ProviderAdapter) -> None:
        """Register a provider adapter by its name."""
        self._providers[adapter.name] = adapter

    def get(self, name: str) -> ProviderAdapter | None:
        """Retrieve a registered provider adapter by name."""
        return self._providers.get(name)

    def all(self) -> list[ProviderAdapter]:
        """Return all registered provider adapters."""
        return list(self._providers.values())

    def enabled(self) -> list[ProviderAdapter]:
        """Return all registered provider adapters (all are considered enabled)."""
        return self.all()

    def unregister(self, name: str) -> ProviderAdapter | None:
        """Remove and return a provider adapter by name."""
        return self._providers.pop(name, None)


def load_providers_from_db(db: Session, registry: ProviderRegistry | None = None) -> ProviderRegistry:
    """Read enabled providers from the database and instantiate adapters.

    Args:
        db: SQLAlchemy session.
        registry: Optional existing registry to populate. Uses the module-level
            singleton if not provided.

    Returns:
        The populated registry.
    """
    if registry is None:
        registry = provider_registry

    stmt = select(Provider).where(Provider.enabled.is_(True))
    db_providers = db.scalars(stmt).all()

    for prov in db_providers:
        adapter_cls = ADAPTER_CLASS_MAP.get(prov.name)
        if adapter_cls is None:
            logger.warning("no_adapter_for_provider", provider_name=prov.name, provider_type=prov.provider_type)
            continue

        kwargs: dict = {}
        if prov.base_url and prov.name in ("ollama", "huggingface"):
            kwargs["base_url"] = prov.base_url

        try:
            adapter = adapter_cls(**kwargs)
            registry.register(adapter)
            logger.debug("provider_loaded", provider_name=prov.name)
        except Exception as e:
            logger.error("provider_load_failed", provider_name=prov.name, error=str(e))

    return registry


provider_registry = ProviderRegistry()
