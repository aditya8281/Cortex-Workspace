"""Background filesystem observer for incremental intelligence updates."""

from __future__ import annotations

import asyncio
import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path

from backend.app.core.runtime import get_runtime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from backend.app.core.logging import get_logger
from backend.app.db.session import SessionLocal
from backend.app.intelligence.discovery import FilesystemDiscovery
from backend.app.intelligence.exclusions import default_exclusions
from backend.app.intelligence.models import CortexAutomationSettings
from backend.app.intelligence.sync_service import SyncService

logger = get_logger(__name__)


def get_observer_state_file() -> Path:
    from backend.app.services.memory_manager import memory_manager
    return memory_manager.get_path("sync_state", "observer_snapshot.json")


class ObserverWatchdogHandler(FileSystemEventHandler):
    """
    Watchdog event handler that translates filesystem events into observer sync tasks.
    """

    def __init__(self, service: BackgroundObserverService, root_path: str):
        self.service = service
        self.root_path = root_path

    def on_created(self, event):
        if not event.is_directory:
            self.service.queue_event(event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            self.service.queue_event(event.src_path)

    def on_deleted(self, event):
        if not event.is_directory:
            self.service.queue_event(event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            self.service.queue_event(event.src_path)
            self.service.queue_event(event.dest_path)


class BackgroundObserverService:
    """
    Event-driven background service using watchdog.observers.Observer
    to watch discovered root directories for changes.
    """

    def __init__(self, poll_interval_seconds: int = 90):
        # poll_interval_seconds controls sync frequency of discovered roots list.
        self.poll_interval = poll_interval_seconds
        self.discovery = FilesystemDiscovery()
        self.sync_service = SyncService()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self.observer: Observer | None = None
        self.watches: dict[str, any] = {}  # root_path_str -> watch handle

    def start(self, loop: asyncio.AbstractEventLoop | None = None) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._loop = loop or asyncio.get_event_loop()
        self._stop_event.clear()
        
        self.observer = Observer()
        self.observer.start()
        
        self._thread = threading.Thread(target=self._run_loop, name="cortex-observer", daemon=True)
        self._thread.start()
        logger.info("Background observer service started via Watchdog")

    def stop(self) -> None:
        self._stop_event.set()
        
        if self.observer:
            try:
                self.observer.stop()
                self.observer.join(timeout=2.0)
            except Exception as e:
                logger.error("Error stopping observer watchdog: %s", e)
            self.observer = None
            
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None
            
        self.watches = {}
        logger.info("Background observer service stopped")

    def _run_loop(self) -> None:
        # Run one-time offline change detection using the saved snapshot
        try:
            if self._observer_enabled():
                logger.info("Observer: Running initial change detection scan...")
                changes = self._detect_changes()
                if changes:
                    logger.info("Observer: Found %d offline changes, processing...", len(changes))
                    self._apply_incremental(changes)
        except Exception as e:
            logger.warning("Observer: Initial offline change scan failed: %s", e)

        # Now start watchdog loop to capture live events
        while not self._stop_event.is_set():
            try:
                from backend.app.services.memory_manager import memory_manager
                if memory_manager.is_indexing_paused() or not self._observer_enabled():
                    if self.watches:
                        logger.info("Observer: Disabled or paused, unscheduling all watches.")
                        for path, watch in list(self.watches.items()):
                            try:
                                self.observer.unschedule(watch)
                            except Exception:
                                pass
                        self.watches.clear()
                else:
                    roots = self.discovery.discover_roots()[:24]
                    runtime = get_runtime()
                    discovered = {str(Path(r).resolve()) for r in roots if runtime.file_exists(r)}

                    # Add new watches
                    for r_path in discovered:
                        if r_path not in self.watches:
                            try:
                                handler = ObserverWatchdogHandler(self, r_path)
                                watch = self.observer.schedule(handler, r_path, recursive=True)
                                self.watches[r_path] = watch
                                logger.info("Observer watchdog scheduled watch on %s", r_path)
                            except Exception as we:
                                logger.error("Observer watchdog failed to schedule watch on %s: %s", r_path, we)

                    # Remove stale watches
                    for r_path in list(self.watches.keys()):
                        if r_path not in discovered:
                            try:
                                self.observer.unschedule(self.watches[r_path])
                                del self.watches[r_path]
                                logger.info("Observer watchdog unscheduled watch on %s", r_path)
                            except Exception as we:
                                logger.error("Observer watchdog failed to unschedule watch on %s: %s", r_path, we)

            except Exception as exc:
                logger.warning("Observer watchdog loop iteration failed: %s", exc)

            # Wait for poll interval (or check stop event)
            self._stop_event.wait(self.poll_interval)

    def _observer_enabled(self) -> bool:
        db = SessionLocal()
        try:
            settings = (
                db.query(CortexAutomationSettings)
                .filter(CortexAutomationSettings.user_id.is_(None))
                .first()
            )
            if settings is None:
                return True
            return bool(settings.observer_enabled)
        finally:
            db.close()

    def _detect_changes(self) -> list[str]:
        snapshot = self._load_snapshot()
        previous: dict[str, float] = snapshot.get("files", {})
        current: dict[str, float] = {}
        changed_paths: list[str] = []

        for root in self.discovery.discover_roots()[:24]:
            if default_exclusions.should_skip_path(root):
                continue
            for dirpath, dirnames, filenames in os.walk(root):
                parent = Path(dirpath)
                dirnames[:] = [
                    d
                    for d in dirnames
                    if not default_exclusions.should_prune_dir(d, parent)
                ]
                depth = len(parent.relative_to(root).parts) if parent != root else 0
                if depth > 6:
                    dirnames.clear()
                    continue

                for name in filenames:
                    path = parent / name
                    if not default_exclusions.is_indexable_file(path):
                        continue
                    path_str = str(path.resolve())
                    try:
                        mtime = path.stat().st_mtime
                    except OSError:
                        continue
                    current[path_str] = mtime
                    if path_str not in previous or previous[path_str] != mtime:
                        changed_paths.append(path_str)

                if len(changed_paths) > 500:
                    break

        removed = [p for p in previous if p not in current]
        for p in removed[:50]:
            changed_paths.append(p)

        snapshot["files"] = current
        snapshot["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._save_snapshot(snapshot)

        return changed_paths[:200]

    def _apply_incremental(self, changes: list[str]) -> None:
        db = SessionLocal()
        try:
            result = self.sync_service.run_incremental_sync(db, changes)
            logger.info("Incremental observer sync: %s", result)
        finally:
            db.close()

    def queue_event(self, path_str: str):
        """Enqueue live watchdog event to update snapshot and trigger async processing."""
        try:
            path = Path(path_str)
            if path.exists() and path.is_file():
                mtime = path.stat().st_mtime
                snapshot = self._load_snapshot()
                snapshot.setdefault("files", {})[path_str] = mtime
                self._save_snapshot(snapshot)
            elif not path.exists():
                snapshot = self._load_snapshot()
                if path_str in snapshot.get("files", {}):
                    del snapshot["files"][path_str]
                    self._save_snapshot(snapshot)
        except Exception:
            pass

        if self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(
                self.process_change(path_str),
                self._loop
            )

    async def process_change(self, path_str: str):
        """Processes a single file path change by running sync in executor."""
        if not self._observer_enabled():
            return
            
        from backend.app.services.memory_manager import memory_manager
        if memory_manager.is_indexing_paused():
            return

        path = Path(path_str)
        if default_exclusions.should_skip_path(path):
            return

        def run_sync():
            db = SessionLocal()
            try:
                result = self.sync_service.run_incremental_sync(db, [path_str])
                logger.info("Incremental observer sync: %s", result)
            except Exception as e:
                logger.error("Error in incremental observer sync: %s", e)
            finally:
                db.close()

        if self._loop:
            await self._loop.run_in_executor(None, run_sync)

    def _load_snapshot(self) -> dict:
        state_file = get_observer_state_file()
        if not state_file.exists():
            return {"files": {}}
        try:
            return json.loads(state_file.read_text(encoding="utf-8"))
        except Exception:
            return {"files": {}}

    def _save_snapshot(self, data: dict) -> None:
        state_file = get_observer_state_file()
        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_file.write_text(json.dumps(data), encoding="utf-8")
