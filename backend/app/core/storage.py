"""Thin convenience wrappers that delegate to :mod:`storage_abstraction`.

All canonical path resolution lives in ``storage_abstraction`` and
``system_paths``.  This module exists only so that legacy callers that
``from backend.app.core.storage import get_*`` keep working.
"""

from __future__ import annotations

from pathlib import Path

from backend.app.core.storage_abstraction import (
    get_system_storage,
    get_user_storage,
)


# ── System paths ──────────────────────────────────────────────────────

def get_data_root() -> Path:
    """Alias kept for backward compatibility."""
    return get_system_storage().root


def get_system_root() -> Path:
    """Alias kept for backward compatibility."""
    return get_system_storage().root


def get_database_path() -> Path:
    return get_system_storage().database_path


def get_memory_root() -> Path:
    return (get_system_storage().runtime_root / "memory").resolve()


def get_embeddings_root() -> Path:
    return get_system_storage().embeddings_root


def get_indexes_root() -> Path:
    return get_system_storage().indexes_root


def get_vector_db_root() -> Path:
    return get_system_storage().vector_db_root


def get_sync_root() -> Path:
    return (get_system_storage().runtime_root / "sync").resolve()


def get_cache_root() -> Path:
    return get_system_storage().cache_root


def get_rag_root() -> Path:
    return get_system_storage().indexes_root


def get_logs_root() -> Path:
    return get_system_storage().logs_root


def get_runtime_root() -> Path:
    return get_system_storage().runtime_root


# ── User paths ────────────────────────────────────────────────────────

def get_user_storage_root(user_id: int | str) -> Path:
    return get_user_storage(int(user_id)).root


def get_user_profile_root(user_id: int | str) -> Path:
    return get_user_storage(int(user_id)).profile


def get_user_vault_root(user_id: int | str) -> Path:
    return get_user_storage(int(user_id)).vault


def get_user_workspace_root(user_id: int | str) -> Path:
    return get_user_storage(int(user_id)).workspace


def get_user_exports_root(user_id: int | str) -> Path:
    return get_user_storage(int(user_id)).exports


def get_user_memory_snapshots_root(user_id: int | str) -> Path:
    return get_user_storage(int(user_id)).memory_snapshots
