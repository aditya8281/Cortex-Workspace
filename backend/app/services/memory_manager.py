"""Centralized Portable Memory System (Cortex Brain Vault) Manager.

Handles path resolution, safety validation, read/write abstraction,
vault redirection, resets, and zip export/import.

All system memory lives under ``SystemPaths["runtime"] / "memory"``.
User vault data is accessed exclusively through ``get_user_storage()``.
"""

import shutil
import zipfile
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import threading

from backend.app.core.config import settings

logger = logging.getLogger(__name__)


class MemoryManager:
    """Centralized system-level memory manager.

    This manages *system* memory (embeddings metadata, graph, sync state,
    activity logs, cache).  User-facing vault operations go through
    ``vault_manager`` + ``get_user_storage()``.
    """

    CATEGORIES = [
        "embeddings",
        "vector_db",
        "graph",
        "sync_state",
        "activity_logs",
        "cache",
        "user_profiles",
        "repos",
        "temp",
    ]

    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._lock = threading.RLock()
        self._indexing_paused = False
        # NOTE: No filesystem side-effects at construction time.
        # Directories are created lazily on first access.

    # ── Service registration ──────────────────────────────────────────

    def register_service(self, name: str, service: Any):
        with self._lock:
            self._services[name] = service
            logger.info("Registered service %s under MemoryManager", name)

    # ── Path resolution ───────────────────────────────────────────────

    def get_memory_path(self) -> Path:
        """Resolve the system memory root directory.

        A test override attribute ``_test_override_path`` on the singleton
        is honored to allow unit tests to point the manager at a temporary
        directory.
        """
        override = getattr(self, "_test_override_path", None)
        if override:
            return Path(override)

        from backend.app.core.storage_manager import storage_manager
        return storage_manager.get_memory_path()

    def set_memory_path(self, path: str) -> None:
        raise NotImplementedError(
            "Dynamic memory path configuration has been removed "
            "in favor of a fixed system path"
        )

    def validate_memory_path(self, path: Path) -> None:
        from backend.app.core.system_paths import get_blocked_system_paths

        resolved = path.expanduser().resolve()
        resolved_str = str(resolved)
        for sys_path in get_blocked_system_paths():
            if resolved_str.startswith(sys_path) or resolved_str == sys_path:
                raise ValueError(
                    f"Security exception: Cannot configure memory path "
                    f"inside system directory '{sys_path}'"
                )
        try:
            resolved.mkdir(parents=True, exist_ok=True)
            test_file = resolved / ".write_test"
            test_file.write_text("cortex", encoding="utf-8")
            test_file.unlink()
        except Exception as e:
            raise ValueError(
                f"Permission error: Target directory '{path}' is not writeable. "
                f"Details: {e}"
            )

    def ensure_vault_structure(self) -> None:
        """Create the memory root directory and all standard subdirectories."""
        root = self.get_memory_path()
        root.mkdir(parents=True, exist_ok=True)
        for category in self.CATEGORIES:
            (root / category).mkdir(parents=True, exist_ok=True)

    def get_path(self, category: str, filename: Optional[str] = None) -> Path:
        if category not in self.CATEGORIES:
            raise ValueError(f"Invalid memory category: {category}")

        root = self.get_memory_path()
        category_dir = (root / category).resolve()
        target_path = (category_dir / filename).resolve() if filename else category_dir

        try:
            target_path.relative_to(root)
        except ValueError:
            raise PermissionError(
                f"Security Violation: Path traversal detected outside "
                f"memory vault for '{filename}'"
            )

        return target_path

    # ── Read/Write abstraction ────────────────────────────────────────

    def read_text(self, category: str, filename: str, encoding: str = "utf-8") -> str:
        path = self.get_path(category, filename)
        if not path.exists():
            raise FileNotFoundError(
                f"Memory entry '{filename}' not found under category '{category}'"
            )
        return path.read_text(encoding=encoding)

    def write_text(self, category: str, filename: str, text: str, encoding: str = "utf-8") -> None:
        path = self.get_path(category, filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding=encoding)

    def read_bytes(self, category: str, filename: str) -> bytes:
        path = self.get_path(category, filename)
        if not path.exists():
            raise FileNotFoundError(
                f"Memory entry '{filename}' not found under category '{category}'"
            )
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

    # ── System control (pause / resume) ───────────────────────────────

    def is_indexing_paused(self) -> bool:
        return self._indexing_paused

    def pause_indexing(self) -> None:
        with self._lock:
            self._indexing_paused = True
            logger.info("Pausing all background indexing services...")
            for name in ("file_watcher", "observer", "sync_service"):
                svc = self._services.get(name)
                if svc:
                    try:
                        if hasattr(svc, "stop"):
                            svc.stop()
                        elif hasattr(svc, "cancel_sync"):
                            svc.cancel_sync()
                    except Exception as exc:
                        logger.error("Failed to stop %s: %s", name, exc)

    def resume_indexing(self) -> None:
        with self._lock:
            self._indexing_paused = False
            logger.info("Resuming all background indexing services...")
            for name in ("file_watcher", "observer"):
                svc = self._services.get(name)
                if svc:
                    try:
                        svc.start()
                    except Exception as exc:
                        logger.error("Failed to start %s: %s", name, exc)

    # ── Reset ─────────────────────────────────────────────────────────

    def change_memory_vault(self, new_path_str: str) -> None:
        raise NotImplementedError(
            "Memory vault relocation has been removed. "
            "System memory is fixed under cortex_system/memory"
        )

    def reset_vault(self) -> None:
        logger.warning("Performing full Cortex Brain Vault reset!")
        self.pause_indexing()
        try:
            from backend.app.db import session
            session.reset_db_engine()

            try:
                from backend.app.core.redis import redis_cache
                import asyncio
                asyncio.run(redis_cache.clear())
            except Exception as re:
                logger.warning("Failed to clear Redis cache: %s", re)

            path = self.get_memory_path()
            if path.exists():
                shutil.rmtree(path)

            self.ensure_vault_structure()
        finally:
            self.resume_indexing()

    # ── Backup & portability ──────────────────────────────────────────

    def export_memory(self, zip_path_str: str) -> str:
        root_dir = self.get_memory_path()
        zip_path = Path(zip_path_str).resolve()
        zip_path.parent.mkdir(parents=True, exist_ok=True)

        self.pause_indexing()
        try:
            from backend.app.db import session
            session.reset_db_engine()

            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                for file_path in root_dir.rglob("*"):
                    if file_path.is_file():
                        zipf.write(file_path, file_path.relative_to(root_dir))
            logger.info("Successfully exported memory vault to %s", zip_path)
            return str(zip_path)
        finally:
            self.resume_indexing()

    def import_memory(self, zip_path_str: str) -> None:
        zip_path = Path(zip_path_str).resolve()
        if not zip_path.exists():
            raise FileNotFoundError(f"Export zip archive not found at '{zip_path}'")

        self.pause_indexing()
        try:
            from backend.app.db import session
            session.reset_db_engine()

            root_dir = self.get_memory_path()
            if root_dir.exists():
                shutil.rmtree(root_dir)
            root_dir.mkdir(parents=True, exist_ok=True)

            with zipfile.ZipFile(zip_path, "r") as zipf:
                zipf.extractall(root_dir)

            self.ensure_vault_structure()
            logger.info("Successfully imported memory vault from %s", zip_path)
        finally:
            self.resume_indexing()


# Singleton — created lazily; no filesystem side-effects at import time.
memory_manager = MemoryManager()
