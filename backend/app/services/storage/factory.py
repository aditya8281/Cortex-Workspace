"""Workspace factory — resolves user_id to UserWorkspace.

Single entry point for all user data access. The central brain
(Postgres) holds auth + pointers. UserWorkspace holds the actual data.

Usage:
    ws = get_user_workspace(user_id, db)
    ws.conversations.append_message(conv_id, "user", "hello")
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from backend.app.services.storage.user_workspace import UserWorkspace

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Default base when no registry entry exists
_DEFAULT_BASE = Path.home() / "CortexStorage"


def get_user_workspace(user_id: int, db: Session | None = None) -> UserWorkspace:
    """Get or create a UserWorkspace for the given user.

    Resolution order:
    1. StorageRegistry table (user chose a custom path at signup)
    2. Default: ~/CortexStorage/{username}/
    3. Fallback: ~/CortexStorage/user_{user_id}/
    """
    storage_root = _resolve_storage_root(user_id, db)
    ws = UserWorkspace(storage_root)
    ws.ensure_dirs()
    return ws


def _resolve_storage_root(user_id: int, db: Session | None = None) -> str:
    """Find the storage root for a user. DB first, then filesystem default."""
    if db is not None:
        try:
            from backend.app.models.memory.storage_registry import StorageRegistry

            registry = db.query(StorageRegistry).filter(StorageRegistry.user_id == user_id).first()
            if registry and registry.storage_root:
                root = Path(registry.storage_root)
                root.mkdir(parents=True, exist_ok=True)
                return str(root)
        except Exception as exc:
            logger.debug("StorageRegistry lookup failed for user %d: %s", user_id, exc)

    # Try to find username from DB
    username = _get_username(user_id, db)
    if username:
        path = _DEFAULT_BASE / username
        path.mkdir(parents=True, exist_ok=True)
        return str(path)

    # Fallback
    path = _DEFAULT_BASE / f"user_{user_id}"
    path.mkdir(parents=True, exist_ok=True)
    return str(path)


def _get_username(user_id: int, db: Session | None = None) -> str | None:
    """Get username from DB for path construction."""
    if db is None:
        return None
    try:
        from backend.app.models.auth.user import User

        user = db.query(User).filter(User.id == user_id).first()
        return user.username if user else None
    except Exception:
        return None


def ensure_user_workspace(user_id: int, db: Session | None = None) -> UserWorkspace:
    """Ensure workspace exists and return it. Same as get_user_workspace.

    Named differently for clarity at call sites that are creating
    vs just reading.
    """
    return get_user_workspace(user_id, db)
