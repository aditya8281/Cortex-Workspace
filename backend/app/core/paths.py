"""Storage path resolver for web and Tauri modes."""

from __future__ import annotations

import os
from pathlib import Path

# Project root — the directory containing alembic.ini and backend/
PROJECT_ROOT = Path(__file__).resolve().parents[3]


class StorageResolver:
    """Resolves storage paths for web and Tauri modes."""

    def __init__(self, mode: str = "web"):
        self._mode = mode

    def resolve(self) -> Path:
        if self._mode == "tauri":
            return Path(os.environ.get("CORTEX_DATA_DIR", "./CortexMemory"))
        return Path("./CortexMemory").resolve()

    @property
    def models_dir(self) -> Path:
        return self.resolve() / "models"

    @property
    def qdrant_dir(self) -> Path:
        return self.resolve() / "qdrant"

    @property
    def profile_dir(self) -> Path:
        return self.resolve() / "profile"


_storage_resolvers: dict[str, StorageResolver] = {}


def get_storage_resolver(mode: str = "web") -> StorageResolver:
    """Get or create a StorageResolver per mode."""
    if mode not in _storage_resolvers:
        _storage_resolvers[mode] = StorageResolver(mode)
    return _storage_resolvers[mode]
