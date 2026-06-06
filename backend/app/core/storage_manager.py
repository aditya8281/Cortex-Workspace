from pathlib import Path
import logging
from backend.app.core.paths import PROJECT_ROOT

logger = logging.getLogger(__name__)


class StorageManager:
    """Single source of truth for Cortex storage layout.

    Creates and validates the canonical Cortex storage root under the project.
    """

    def __init__(self, root_name: str = "CortexMemory"):
        self.root = (PROJECT_ROOT / root_name).resolve()
        self._ensure_structure()

    def _ensure_structure(self) -> None:
        """Create canonical subdirectories if they do not exist."""
        try:
            dirs = [
                self.root,
                self.get_database_path().parent,
                self.get_memory_path(),
                self.get_embeddings_path(),
                self.get_indexes_path(),
                self.get_logs_path(),
                self.get_config_path(),
                self.get_model_registry_path(),
                self.get_sync_path(),
                self.get_cache_path(),
            ]
            for d in dirs:
                Path(d).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error("Failed to ensure storage structure: %s", e)

    def get_cortex_root(self) -> Path:
        return self.root

    def get_database_path(self) -> Path:
        return (self.root / "database" / "app.db").resolve()

    def get_memory_path(self) -> Path:
        return (self.root / "memory").resolve()

    def get_embeddings_path(self) -> Path:
        return (self.root / "embeddings").resolve()

    def get_indexes_path(self) -> Path:
        return (self.root / "indexes").resolve()

    def get_logs_path(self) -> Path:
        return (self.root / "logs").resolve()

    def get_config_path(self) -> Path:
        return (self.root / "config").resolve()

    def get_model_registry_path(self) -> Path:
        return (self.root / "model_registry").resolve()

    def get_sync_path(self) -> Path:
        return (self.root / "sync").resolve()

    def get_cache_path(self) -> Path:
        return (self.root / "cache").resolve()


# Module-level singleton
storage_manager = StorageManager()
