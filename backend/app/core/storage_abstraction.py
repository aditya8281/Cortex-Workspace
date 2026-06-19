"""Canonical system storage layout.

All system-owned data lives under ``ProjectRoot/CortexMemory/``.
User-specific data is stored in user-chosen locations, never here.
"""

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
    """CortexMemory storage layout.

    All fields point inside ``ProjectRoot/CortexMemory/``:
        root           -> CortexMemory/
        logs_root      -> CortexMemory/logs/
        cache_root     -> CortexMemory/cache/
        runtime_root   -> CortexMemory/runtime/
    """

    root: Path
    logs_root: Path
    cache_root: Path
    runtime_root: Path

    @property
    def memory_root(self) -> Path:
        """Central CortexMemory directory for all AI/system data."""
        return (self.root / "memory").resolve()


def get_system_storage() -> SystemStorage:
    ensure_system_dirs()
    return SystemStorage(
        root=get_system_root(),
        logs_root=get_system_path("logs"),
        cache_root=get_system_path("cache"),
        runtime_root=get_system_path("runtime"),
    )


def validate_storage_path(path: str | Path) -> Path:
    resolved = Path(path).expanduser().resolve()
    system_root = get_system_storage().root

    # Reject paths that live inside the Cortex system directory
    if resolved.is_relative_to(system_root.resolve()):
        raise ValueError("Storage roots cannot live inside the Cortex system directory")

    # Disallow obvious dangerous system locations and root
    forbidden_roots = {
        Path("/etc"),
        Path("/bin"),
        Path("/sbin"),
        Path("/usr"),
        Path("/var"),
        Path("/opt"),
        Path("/root"),
    }
    if resolved == Path("/"):
        raise ValueError(f"Storage root '{resolved}' is not allowed")
    for forb in forbidden_roots:
        if resolved.is_relative_to(forb):
            raise ValueError(f"Storage root '{resolved}' is not allowed")

    # Require user storage be located under the invoking user's home directory
    home = Path.home().resolve()
    if not resolved.is_relative_to(home):
        raise ValueError("Storage root must be located under the user's home directory for safety")

    # Ensure parent exists
    resolved.parent.mkdir(parents=True, exist_ok=True)
    if not resolved.parent.exists():
        raise ValueError("Storage root parent directory could not be created")

    return resolved
