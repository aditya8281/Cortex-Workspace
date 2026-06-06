from pathlib import Path
from backend.app.core.storage_manager import storage_manager


def get_data_root() -> Path:
    """Return the Cortex storage root managed by StorageManager."""
    return storage_manager.get_cortex_root()


def get_system_root() -> Path:
    # The system root is the Cortex storage root itself
    root = get_data_root()
    root.mkdir(parents=True, exist_ok=True)
    return root


def get_database_path() -> Path:
    return storage_manager.get_database_path()


def get_memory_root() -> Path:
    return storage_manager.get_memory_path()


def get_embeddings_root() -> Path:
    return storage_manager.get_embeddings_path()


def get_indexes_root() -> Path:
    return storage_manager.get_indexes_path()


def get_vector_db_root() -> Path:
    # vector_db is implemented under indexes for the canonical layout
    return storage_manager.get_indexes_path()


def get_sync_root() -> Path:
    return storage_manager.get_sync_path()


def get_cache_root() -> Path:
    return storage_manager.get_cache_path()


def get_rag_root() -> Path:
    # RAG artifacts belong to system memory/indexes; map to indexes root
    return storage_manager.get_indexes_path()


def get_users_root() -> Path:
    # Legacy fallback: keep a system-managed users area within cortex_system for environments
    # without a registered personal_storage_path. New deployments SHOULD rely on per-user
    # storage roots registered in the storage registry.
    root = get_data_root() / "users"
    root.mkdir(parents=True, exist_ok=True)
    return root


def get_user_profile_root(user_id: int | str) -> Path:
    # Try registry first to allow user-provided storage roots
    try:
        # lazy import to avoid circular deps at module import time
        from backend.app.db.session import SessionLocal
        from backend.app.services.storage_registry import get_registry_for_user
        db = SessionLocal()
        reg = get_registry_for_user(db, int(user_id)) if db else None
        if reg and reg.profile_path:
            p = Path(reg.profile_path).expanduser().resolve()
            p.mkdir(parents=True, exist_ok=True)
            return p
    except Exception:
        pass

    user_dir = get_users_root() / f"user_{user_id}" / "profile"
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir


def get_user_vault_root(user_id: int | str) -> Path:
    # Prefer registry mapping for user vault location; vaults are user-private
    try:
        from backend.app.db.session import SessionLocal
        from backend.app.services.storage_registry import get_registry_for_user
        db = SessionLocal()
        reg = get_registry_for_user(db, int(user_id)) if db else None
        if reg and reg.vault_path:
            p = Path(reg.vault_path).expanduser().resolve()
            p.mkdir(parents=True, exist_ok=True)
            return p
    except Exception:
        pass

    user_dir = get_users_root() / f"user_{user_id}" / "vault"
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir
