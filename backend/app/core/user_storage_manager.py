from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from backend.app.core.storage_abstraction import UserStorage, get_user_storage, validate_storage_path

logger = logging.getLogger(__name__)


class UserStorageManager:
    """Compatibility wrapper for a registry-backed user storage root."""

    def __init__(self, root: str | Path):
        self.root = validate_storage_path(root)
        self._storage = UserStorage(user_id=-1, root=self.root)
        self._storage.ensure_dirs()

    def _ensure_structure(self):
        try:
            self._storage.ensure_dirs()
        except Exception as e:
            logger.error("Failed to ensure user storage structure for %s: %s", self.root, e)

    def get_user_root(self) -> Path:
        return self.root

    def get_profile_path(self) -> Path:
        return self._storage.profile

    def get_avatar_path(self) -> Path:
        return self.get_profile_path() / "avatar"

    def get_vault_path(self) -> Path:
        return self._storage.vault

    def get_workspace_path(self) -> Path:
        return self._storage.workspace

    def get_exports_path(self) -> Path:
        return self._storage.exports

    def get_memory_snapshots_path(self) -> Path:
        return self._storage.memory_snapshots

    @classmethod
    def from_registry_entry(cls, registry_entry) -> Optional["UserStorageManager"]:
        try:
            return cls(registry_entry.storage_root)
        except Exception:
            return None

    @classmethod
    def for_user(cls, user_id: int) -> UserStorage:
        return get_user_storage(user_id)

