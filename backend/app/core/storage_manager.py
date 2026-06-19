"""Thin compatibility wrapper around the canonical CortexMemory storage layout."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.app.core.storage_abstraction import SystemStorage


class StorageManager:
    """Lazy compatibility wrapper around the canonical CortexMemory storage layout."""

    def __init__(self) -> None:
        from backend.app.core.storage_abstraction import get_system_storage

        self._storage: SystemStorage = get_system_storage()

    def get_cortex_root(self) -> Path:
        return self._storage.root

    def get_memory_path(self) -> Path:
        """Central CortexMemory directory for all AI/system data."""
        return self._storage.memory_root

    def get_logs_path(self) -> Path:
        return self._storage.logs_root

    def get_config_path(self) -> Path:
        return (self._storage.runtime_root / "config").resolve()

    def get_cache_path(self) -> Path:
        return self._storage.cache_root


_instance: StorageManager | None = None


def _get_storage_manager() -> StorageManager:
    global _instance
    if _instance is None:
        _instance = StorageManager()
    return _instance


class _StorageManagerProxy:
    """Module-level proxy that defers construction until first attribute access."""

    def __getattr__(self, name: str):
        return getattr(_get_storage_manager(), name)


storage_manager = _StorageManagerProxy()
