from pathlib import Path
import os
from backend.app.core.paths import PROJECT_ROOT
from backend.app.core.config import settings


def get_data_root() -> Path:
    """
    Returns the top-level Cortex data root. Priority:
    - If env var or settings.MEMORY_PATH points to an explicit CortexData root, use it.
    - Otherwise default to PROJECT_ROOT / "CortexData".
    """
    env = settings.MEMORY_PATH or os.environ.get("CORTEX_MEMORY_PATH")
    if env:
        p = Path(env).expanduser().resolve()
        # If user pointed at a subfolder (like .cortex_memory), normalize to parent CortexData
        return p
    return (PROJECT_ROOT / "CortexData").resolve()


def get_system_root() -> Path:
    root = get_data_root() / "system"
    root.mkdir(parents=True, exist_ok=True)
    return root


def get_database_path() -> Path:
    db_dir = get_system_root() / "database"
    db_dir.mkdir(parents=True, exist_ok=True)
    return (db_dir / "app.db").resolve()


def get_memory_root() -> Path:
    root = get_system_root() / "memory"
    root.mkdir(parents=True, exist_ok=True)
    return root


def get_embeddings_root() -> Path:
    root = get_system_root() / "embeddings"
    root.mkdir(parents=True, exist_ok=True)
    return root


def get_indexes_root() -> Path:
    root = get_system_root() / "indexes"
    root.mkdir(parents=True, exist_ok=True)
    return root


def get_vector_db_root() -> Path:
    root = get_system_root() / "vector_db"
    root.mkdir(parents=True, exist_ok=True)
    return root


def get_sync_root() -> Path:
    root = get_system_root() / "sync"
    root.mkdir(parents=True, exist_ok=True)
    return root


def get_cache_root() -> Path:
    root = get_system_root() / "cache"
    root.mkdir(parents=True, exist_ok=True)
    return root


def get_rag_root() -> Path:
    root = get_system_root() / "rag"
    root.mkdir(parents=True, exist_ok=True)
    return root


def get_users_root() -> Path:
    root = get_data_root() / "users"
    root.mkdir(parents=True, exist_ok=True)
    return root


def get_user_profile_root(user_id: int | str) -> Path:
    user_dir = get_users_root() / f"user_{user_id}" / "profile"
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir


def get_user_vault_root(user_id: int | str) -> Path:
    # Per new architecture, user vaults are under users/<id>/vault
    user_dir = get_users_root() / f"user_{user_id}" / "vault"
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir
