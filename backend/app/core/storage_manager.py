"""Thin compatibility wrapper around the canonical system storage layout.

All path resolution is delegated to :mod:`storage_abstraction`.  This
module exists only so that legacy callers that
``from backend.app.core.storage_manager import storage_manager`` keep
working.

NOTE: ``storage_manager`` is instantiated lazily on first attribute
access to avoid filesystem side-effects at import time.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.app.core.storage_abstraction import SystemStorage


class StorageManager:
    """Lazy compatibility wrapper around the canonical system storage layout."""

    def __init__(self) -> None:
        # Defer to storage_abstraction at construction time, not import time.
        from backend.app.core.storage_abstraction import get_system_storage
        self._storage: SystemStorage = get_system_storage()

    def get_cortex_root(self) -> Path:
        return self._storage.root

    def get_database_path(self) -> Path:
        return self._storage.database_path

    def get_memory_path(self) -> Path:
        return (self._storage.runtime_root / "memory").resolve()

    def get_logs_path(self) -> Path:
        return self._storage.logs_root

    def get_config_path(self) -> Path:
        return (self._storage.runtime_root / "config").resolve()

    def get_model_registry_path(self) -> Path:
        return (self._storage.runtime_root / "model_registry").resolve()

    def get_sync_path(self) -> Path:
        return (self._storage.runtime_root / "sync").resolve()

    def get_cache_path(self) -> Path:
        return self._storage.cache_root


def _get_storage_manager() -> StorageManager:
    """Lazy accessor — the singleton is created on first use."""
    if not hasattr(_get_storage_manager, "_instance"):
        _get_storage_manager._instance = StorageManager()  # type: ignore[attr-defined]
    return _get_storage_manager._instance


class _StorageManagerProxy:
    """Module-level proxy that defers construction until first attribute access."""

    def __getattr__(self, name: str):
        return getattr(_get_storage_manager(), name)


storage_manager = _StorageManagerProxy()
