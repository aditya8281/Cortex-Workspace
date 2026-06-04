import os
import shutil
import zipfile
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import threading

from backend.app.core.paths import PROJECT_ROOT

logger = logging.getLogger(__name__)


class MemoryManager:
    """
    Centralized Portable Memory System (Cortex Brain Vault) Manager.
    Handles path resolution, safety validation, read/write abstraction,
    vault redirection, resets, and zip export/import.
    """

    CATEGORIES = [
        "embeddings",
        "vector_db",
        "metadata_db",
        "graph",
        "sync_state",
        "activity_logs",
        "cache",
        "user_profiles",
        "repos",
        "temp"
    ]

    SYSTEM_PATHS = [
        "/sys", "/etc", "/dev", "/proc", "/boot", "/root", "/usr", "/var", "/lib",
        "/bin", "/sbin", "C:\\Windows", "C:\\System32", "C:\\Program Files", "C:\\Program Files (x86)"
    ]

    def __init__(self):
        self._config_file = PROJECT_ROOT / ".cortex_memory_path"
        self._services: Dict[str, Any] = {}
        self._lock = threading.RLock()
        self._indexing_paused = False
        
        # Initialize default memory path on disk
        self.ensure_vault_structure()

    def register_service(self, name: str, service: Any):
        """Register background services (e.g. file_watcher, observer) for pause/resume."""
        with self._lock:
            self._services[name] = service
            logger.info("Registered service %s under MemoryManager", name)

    def get_memory_path(self) -> Path:
        """Get the current memory root path."""
        # 1. Environment variable override
        env_path = os.environ.get("CORTEX_MEMORY_PATH")
        if env_path:
            return Path(env_path).resolve()

        # 2. Config file override
        if self._config_file.exists():
            try:
                path_str = self._config_file.read_text(encoding="utf-8").strip()
                if path_str:
                    return Path(path_str).resolve()
            except Exception as e:
                logger.warning("Failed to read memory configuration file: %s", e)

        # 3. Default path (~/cortex_memory/)
        return Path("~/cortex_memory").expanduser().resolve()

    def set_memory_path(self, path: str) -> None:
        """Persist the configured memory root path."""
        target_path = Path(path).resolve()
        self.validate_memory_path(target_path)
        self._config_file.write_text(str(target_path), encoding="utf-8")
        logger.info("Configured memory vault path set to %s", target_path)

    def validate_memory_path(self, path: Path) -> None:
        """Validate if a directory is safe to use as the memory vault."""
        resolved = path.resolve()
        
        # 1. Block system level directories
        resolved_str = str(resolved)
        for sys_path in self.SYSTEM_PATHS:
            if resolved_str.startswith(sys_path) or resolved_str == sys_path:
                raise ValueError(f"Security exception: Cannot configure memory path inside system directory '{sys_path}'")

        # 2. Test write permissions
        try:
            resolved.mkdir(parents=True, exist_ok=True)
            test_file = resolved / ".write_test"
            test_file.write_text("cortex", encoding="utf-8")
            test_file.unlink()
        except Exception as e:
            raise ValueError(f"Permission error: Target directory '{path}' is not writeable. Details: {e}")

    def ensure_vault_structure(self) -> None:
        """Creates the memory root directory and all standard vault subdirectories."""
        root = self.get_memory_path()
        root.mkdir(parents=True, exist_ok=True)
        for category in self.CATEGORIES:
            (root / category).mkdir(parents=True, exist_ok=True)

    def get_path(self, category: str, filename: Optional[str] = None) -> Path:
        """
        Resolves a path inside the memory vault for a specific category.
        Ensures the path does not escape the memory vault (prevents traversal).
        """
        if category not in self.CATEGORIES:
            raise ValueError(f"Invalid memory category: {category}")

        root = self.get_memory_path()
        category_dir = (root / category).resolve()

        if filename:
            target_path = (category_dir / filename).resolve()
        else:
            target_path = category_dir

        # Safety constraint: enforce memory root subfolder containment
        try:
            target_path.relative_to(root)
        except ValueError:
            raise PermissionError(f"Security Violation: Path traversal detected outside memory vault for '{filename}'")

        # Double check system paths
        target_str = str(target_path)
        for sys_path in self.SYSTEM_PATHS:
            if target_str.startswith(sys_path) or target_str == sys_path:
                raise PermissionError(f"Security Violation: Access block to system directory '{sys_path}'")

        return target_path

    # ==========================================
    # Read/Write Abstraction Layer
    # ==========================================

    def read_text(self, category: str, filename: str, encoding: str = "utf-8") -> str:
        path = self.get_path(category, filename)
        if not path.exists():
            raise FileNotFoundError(f"Memory entry '{filename}' not found under category '{category}'")
        return path.read_text(encoding=encoding)

    def write_text(self, category: str, filename: str, text: str, encoding: str = "utf-8") -> None:
        path = self.get_path(category, filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding=encoding)

    def read_bytes(self, category: str, filename: str) -> bytes:
        path = self.get_path(category, filename)
        if not path.exists():
            raise FileNotFoundError(f"Memory entry '{filename}' not found under category '{category}'")
        return path.read_bytes()

    def write_bytes(self, category: str, filename: str, data: bytes) -> None:
        path = self.get_path(category, filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def delete_file(self, category: str, filename: str) -> None:
        path = self.get_path(category, filename)
        if path.exists() and path.is_file():
            path.unlink()

    def exists(self, category: str, filename: Optional[str] = None) -> bool:
        try:
            return self.get_path(category, filename).exists()
        except Exception:
            return False

    def list_files(self, category: str) -> List[str]:
        dir_path = self.get_path(category)
        if not dir_path.exists():
            return []
        return [f.name for f in dir_path.iterdir() if f.is_file()]

    # ==========================================
    # System Control (Pause / Resume)
    # ==========================================

    def is_indexing_paused(self) -> bool:
        return self._indexing_paused

    def pause_indexing(self) -> None:
        """Pause all background watchers, observers, and sync activities."""
        with self._lock:
            self._indexing_paused = True
            logger.info("Pausing all background indexing services...")
            
            # 1. Stop observers and watchers
            watcher = self._services.get("file_watcher")
            if watcher:
                try:
                    watcher.stop()
                except Exception as e:
                    logger.error("Failed to stop file_watcher: %s", e)
            
            observer = self._services.get("observer")
            if observer:
                try:
                    observer.stop()
                except Exception as e:
                    logger.error("Failed to stop observer: %s", e)

            # 2. Cancel/Pause any active SyncService
            sync_service = self._services.get("sync_service")
            if sync_service:
                try:
                    sync_service.cancel_sync()
                except Exception as e:
                    logger.error("Failed to cancel active sync: %s", e)

    def resume_indexing(self) -> None:
        """Resume background watchers and observers."""
        with self._lock:
            self._indexing_paused = False
            logger.info("Resuming all background indexing services...")
            
            # Start/Restart file watcher
            watcher = self._services.get("file_watcher")
            if watcher:
                try:
                    watcher.start()
                except Exception as e:
                    logger.error("Failed to start file_watcher: %s", e)

            # Start/Restart observer
            observer = self._services.get("observer")
            if observer:
                try:
                    # Some observer implementations need event loop references
                    # but they'll start using their internal settings
                    observer.start()
                except Exception as e:
                    logger.error("Failed to start observer: %s", e)

    # ==========================================
    # Redirection & Reset Engine
    # ==========================================

    def change_memory_vault(self, new_path_str: str) -> None:
        """
        Dynamically moves the memory vault to a new directory.
        Keeps existing data and rebinds connections with no data loss.
        """
        old_path = self.get_memory_path()
        new_path = Path(new_path_str).resolve()
        
        if old_path == new_path:
            return

        self.validate_memory_path(new_path)
        logger.info("Starting memory vault migration from %s to %s", old_path, new_path)

        # 1. Pause indexing and write processes
        self.pause_indexing()

        try:
            # 2. Close active database connections
            from backend.app.db import session
            session.reset_db_engine()

            # Close active state store connections
            from backend.app.state.manager import StateManager
            # We can re-bind the engine later when it gets called.

            # 3. Safely copy existing vault contents to the new directory (migration)
            new_path.mkdir(parents=True, exist_ok=True)
            for category in self.CATEGORIES:
                old_category_dir = old_path / category
                new_category_dir = new_path / category
                if old_category_dir.exists():
                    shutil.copytree(old_category_dir, new_category_dir, dirs_exist_ok=True)

            # 4. Rebuild path registry (persist new path in settings)
            self.set_memory_path(str(new_path))
            self.ensure_vault_structure()

            # 5. Run migrations at the new path to verify / update schema
            db_path = str(self.get_path("metadata_db", "app.db"))
            session.run_migrations(db_path)

        except Exception as e:
            logger.exception("Error during memory vault migration: %s", e)
            # Revert config file to old path in case of failure
            self.set_memory_path(str(old_path))
            raise e
        finally:
            # 6. Resume system
            self.resume_indexing()

    def reset_vault(self) -> None:
        """
        Performs a full memory reset (One-Folder Reset).
        Deletes all local indexes, caches, and database entries,
        then reconstructs an empty, initialized vault structure.
        """
        logger.warning("Performing full Cortex Brain Vault reset!")
        
        # 1. Pause background processes
        self.pause_indexing()

        try:
            # 2. Close database pools
            from backend.app.db import session
            session.reset_db_engine()

            # 3. Clear Redis in-memory caches
            try:
                from backend.app.core.redis import redis_cache
                import asyncio
                # We run redis clear synchronously in the background thread
                asyncio.run(redis_cache.clear())
            except Exception as re:
                logger.warning("Failed to clear Redis cache: %s", re)

            # 4. Delete the memory root folder completely
            path = self.get_memory_path()
            if path.exists():
                shutil.rmtree(path)

            # 5. Recreate folder structure
            self.ensure_vault_structure()

            # 6. Initialize database schema with migrations
            db_path = str(self.get_path("metadata_db", "app.db"))
            session.run_migrations(db_path)

        finally:
            # 7. Resume background processes
            self.resume_indexing()

    # ==========================================
    # Backup & Portability
    # ==========================================

    def export_memory(self, zip_path_str: str) -> str:
        """Export the entire memory root directory as a zip archive."""
        root_dir = self.get_memory_path()
        zip_path = Path(zip_path_str).resolve()
        zip_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Pause background writes during backup
        self.pause_indexing()
        
        try:
            # Close active connections during compression to prevent locked file errors
            from backend.app.db import session
            session.reset_db_engine()

            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in root_dir.rglob('*'):
                    if file_path.is_file():
                        # Write relative path inside the zip file
                        zipf.write(file_path, file_path.relative_to(root_dir))
            logger.info("Successfully exported memory vault to %s", zip_path)
            return str(zip_path)
        finally:
            self.resume_indexing()

    def import_memory(self, zip_path_str: str) -> None:
        """Import/Restore a memory root directory from a zip archive."""
        zip_path = Path(zip_path_str).resolve()
        if not zip_path.exists():
            raise FileNotFoundError(f"Export zip archive not found at '{zip_path}'")

        # 1. Stop processes
        self.pause_indexing()

        try:
            # 2. Close active databases
            from backend.app.db import session
            session.reset_db_engine()

            # 3. Wipe current memory vault
            root_dir = self.get_memory_path()
            if root_dir.exists():
                shutil.rmtree(root_dir)
            root_dir.mkdir(parents=True, exist_ok=True)

            # 4. Extract zip archive
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                zipf.extractall(root_dir)
            
            # 5. Initialize/Verify directory layout
            self.ensure_vault_structure()

            # 6. Re-run migrations programmatically
            db_path = str(self.get_path("metadata_db", "app.db"))
            session.run_migrations(db_path)
            
            logger.info("Successfully imported memory vault from %s", zip_path)
        finally:
            self.resume_indexing()


# Global Singleton Instance
memory_manager = MemoryManager()
