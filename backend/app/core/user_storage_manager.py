from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class UserStorageManager:
    """Manage per-user storage tree under a user-selected root.

    Usage:
      mgr = UserStorageManager(Path('/home/user/CortexData'))
      mgr.get_profile_path()
    """

    def __init__(self, root: str | Path):
        self.root = Path(root).expanduser().resolve()
        self._ensure_structure()

    def _ensure_structure(self):
        try:
            for d in [self.root, self.get_profile_path(), self.get_vault_path(), self.get_chat_path(), self.get_workspace_path(), self.get_exports_path()]:
                Path(d).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error("Failed to ensure user storage structure for %s: %s", self.root, e)

    def get_user_root(self) -> Path:
        return self.root

    def get_profile_path(self) -> Path:
        return (self.root / "profile").resolve()

    def get_avatar_path(self) -> Path:
        # avatar directory/file inside profile
        return (self.get_profile_path() / "avatar").resolve()

    def get_vault_path(self) -> Path:
        return (self.root / "vault").resolve()

    def get_chat_path(self) -> Path:
        return (self.root / "chats").resolve()

    def get_workspace_path(self) -> Path:
        return (self.root / "workspace").resolve()

    def get_exports_path(self) -> Path:
        return (self.root / "exports").resolve()

    @classmethod
    def from_registry_entry(cls, registry_entry) -> Optional["UserStorageManager"]:
        try:
            return cls(registry_entry.storage_root)
        except Exception:
            return None
