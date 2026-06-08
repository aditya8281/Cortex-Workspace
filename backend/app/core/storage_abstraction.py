from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from backend.app.core.system_paths import (
    SecurityError,
    get_system_root,
    get_system_path,
    get_blocked_system_paths,
    ensure_system_dirs,
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


@dataclass(frozen=True)
class UserStorage:
    user_id: int
    root: Path

    @property
    def profile(self) -> Path:
        return (self.root / "profile").resolve()

    @property
    def vault(self) -> Path:
        return (self.root / "vault").resolve()

    @property
    def workspace(self) -> Path:
        return (self.root / "workspace").resolve()

    @property
    def exports(self) -> Path:
        return (self.root / "exports").resolve()

    @property
    def memory_snapshots(self) -> Path:
        return (self.root / "memory_snapshots").resolve()

    def ensure_dirs(self) -> None:
        for path in [self.root, self.profile, self.vault, self.workspace,
                     self.exports, self.memory_snapshots]:
            path.mkdir(parents=True, exist_ok=True)


# ── Single source of truth for system storage ─────────────────────────


def get_system_storage() -> SystemStorage:
    ensure_system_dirs()
    return SystemStorage(
        root=get_system_root(),
        db_root=get_system_path("db"),
        logs_root=get_system_path("logs"),
        cache_root=get_system_path("cache"),
        runtime_root=get_system_path("runtime"),
    )


# ── Path utilities ────────────────────────────────────────────────────


def _path_is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except Exception:
        return False


def validate_storage_path(path: str | Path) -> Path:
    resolved = Path(path).expanduser().resolve()
    system_root = get_system_storage().root
    if _path_is_relative_to(resolved, system_root):
        raise ValueError("Storage roots cannot live inside the Cortex system directory")

    resolved_str = str(resolved)
    for blocked in get_blocked_system_paths():
        if resolved_str == blocked or resolved_str.startswith(blocked.rstrip("/\\") + "/"):
            raise ValueError(f"Storage root cannot live inside blocked system path: {blocked}")

    resolved.parent.mkdir(parents=True, exist_ok=True)
    if not resolved.parent.exists():
        raise ValueError("Storage root parent directory could not be created")

    return resolved


# ── User storage ──────────────────────────────────────────────────────


def _iter_user_storage_roots():
    from backend.app.db.session import SessionLocal
    from backend.app.models.storage_registry import StorageRegistry

    db = SessionLocal()
    try:
        rows = db.query(StorageRegistry).all()
        for row in rows:
            try:
                yield row.user_id, Path(row.storage_root).expanduser().resolve()
            except Exception:
                continue
    finally:
        db.close()


def get_user_storage(user_id: int) -> UserStorage:
    from backend.app.db.session import SessionLocal
    from backend.app.services.storage_registry import get_registry_for_user

    db = SessionLocal()
    try:
        registry = get_registry_for_user(db, int(user_id))
    finally:
        db.close()

    if registry is None:
        raise LookupError(f"No storage registered for user_id={user_id}")

    root = validate_storage_path(registry.storage_root)
    storage = UserStorage(user_id=int(user_id), root=root)
    storage.ensure_dirs()
    return storage


# ── Isolation guardrails ─────────────────────────────────────────────


def is_system_path(path: str | Path) -> bool:
    """Return True if *path* lives under the system storage root."""
    resolved = Path(path).expanduser().resolve()
    return _path_is_relative_to(resolved, get_system_storage().root)


def is_user_path(path: str | Path) -> bool:
    """Return True if *path* lives under any registered user storage root."""
    resolved = Path(path).expanduser().resolve()
    for _, user_root in _iter_user_storage_roots():
        if _path_is_relative_to(resolved, user_root):
            return True
    return False


def assert_no_cross_write(path: str | Path) -> None:
    """Raise ``SecurityError`` if system code attempts to write into user storage."""
    resolved = Path(path).expanduser().resolve()
    system_root = get_system_storage().root
    if _path_is_relative_to(resolved, system_root):
        return

    for _, user_root in _iter_user_storage_roots():
        if _path_is_relative_to(resolved, user_root):
            raise SecurityError(
                f"System code cannot write into user storage path: {resolved}"
            )


def is_vault_path(path: str | Path) -> bool:
    resolved = Path(path).expanduser().resolve()
    for _, user_root in _iter_user_storage_roots():
        vault_root = (user_root / "vault").resolve()
        if _path_is_relative_to(resolved, vault_root):
            return True
    return False



