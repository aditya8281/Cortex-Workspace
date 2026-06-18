"""Canonical system storage layout — simplified for auth + memory only."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from backend.app.core.system_paths import (
    ensure_system_dirs,
    get_system_path,
    get_system_root,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SystemStorage:
    root: Path
    db_root: Path
    logs_root: Path
    cache_root: Path
    runtime_root: Path

    @property
    def database_path(self) -> Path:
        return (self.db_root / "app.db").resolve()


def get_system_storage() -> SystemStorage:
    ensure_system_dirs()
    return SystemStorage(
        root=get_system_root(),
        db_root=get_system_path("db"),
        logs_root=get_system_path("logs"),
        cache_root=get_system_path("cache"),
        runtime_root=get_system_path("runtime"),
    )


def validate_storage_path(path: str | Path) -> Path:
    resolved = Path(path).expanduser().resolve()
    system_root = get_system_storage().root
    # Reject paths that live inside the Cortex system directory
    try:
        resolved.relative_to(system_root.resolve())
        raise ValueError("Storage roots cannot live inside the Cortex system directory")
    except ValueError as exc:
        if "cannot live inside" in str(exc):
            raise
        # relative_to raised because path is NOT inside system_root — that's fine

    resolved.parent.mkdir(parents=True, exist_ok=True)
    if not resolved.parent.exists():
        raise ValueError("Storage root parent directory could not be created")

    return resolved
