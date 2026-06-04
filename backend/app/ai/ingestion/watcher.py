import os
import json
import hashlib
import time
import logging
import threading
import asyncio
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from backend.app.core.runtime import get_runtime

from backend.app.db.session import SessionLocal
from backend.app.models.hierarchical_memory import HierarchicalNode
from backend.app.services.hierarchical_indexing import HierarchicalIndexingService
from backend.app.ai.ingestion.scanner import RepoScanner

logger = logging.getLogger(__name__)


class RepoWatchdogHandler(FileSystemEventHandler):
    """
    Watchdog event handler that translates filesystem events into indexing tasks.
    """

    def __init__(self, watcher: "BackgroundFileWatcher", repo_path_str: str):
        self.watcher = watcher
        self.repo_path_str = repo_path_str

    def on_created(self, event):
        if not event.is_directory:
            self.watcher.queue_event("created", event.src_path, self.repo_path_str)

    def on_modified(self, event):
        if not event.is_directory:
            self.watcher.queue_event("modified", event.src_path, self.repo_path_str)

    def on_deleted(self, event):
        if not event.is_directory:
            self.watcher.queue_event("deleted", event.src_path, self.repo_path_str)

    def on_moved(self, event):
        if not event.is_directory:
            self.watcher.queue_event("deleted", event.src_path, self.repo_path_str)
            self.watcher.queue_event("created", event.dest_path, self.repo_path_str)


class BackgroundFileWatcher:
    """
    Event-driven background service using watchdog.observers.Observer
    to monitor repository directories recursively for changes.
    """

    def __init__(self, poll_interval_seconds: int = 15):
        # poll_interval_seconds is kept for backward compatibility and controls repo-list sync frequency.
        self.poll_interval = poll_interval_seconds
        self.indexing_service = HierarchicalIndexingService()
        self.scanner = RepoScanner()
        self._stop_event = threading.Event()
        self._thread = None
        self.loop = None
        self.observer = None
        self.watches = {}  # repo_path_str -> watch handle

    @staticmethod
    def _content_hash(path: Path) -> str | None:
        try:
            return hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError:
            return None

    def start(self):
        if self._thread is not None:
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name="CortexFileWatcher", daemon=True)
        self._thread.start()
        logger.info("Cortex watchdog file watcher daemon started")

    def stop(self):
        if self._thread is None:
            return
        self._stop_event.set()

        # Stop watchdog observer
        if self.observer:
            try:
                self.observer.stop()
                self.observer.join(timeout=2.0)
            except Exception as e:
                logger.error("Error stopping watchdog observer: %s", e)
            self.observer = None

        # Stop the background event loop
        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)

        self._thread.join(timeout=3.0)
        self._thread = None
        self.watches = {}
        logger.info("Cortex watchdog file watcher daemon stopped")

    def _run(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        # Initialize watchdog observer
        self.observer = Observer()
        self.observer.start()

        # Run the repository sync task on the event loop
        self.loop.create_task(self._sync_watches_loop())

        # Start the loop running forever
        try:
            self.loop.run_forever()
        finally:
            self.loop.close()
            self.loop = None

    async def _sync_watches_loop(self):
        """Periodically queries registered repositories and updates the active watches."""
        while not self._stop_event.is_set():
            try:
                db = SessionLocal()
                try:
                    from backend.app.services.memory_manager import memory_manager
                    if not memory_manager.is_indexing_paused():
                        repos = db.query(HierarchicalNode).filter(HierarchicalNode.node_type == "repo").all()
                        runtime = get_runtime()
                        db_repos = {r.path for r in repos if runtime.file_exists(r.path)}

                        # Add new watches
                        for repo_path in db_repos:
                            if repo_path not in self.watches:
                                try:
                                    handler = RepoWatchdogHandler(self, repo_path)
                                    watch = self.observer.schedule(handler, repo_path, recursive=True)
                                    self.watches[repo_path] = watch
                                    logger.info("Watchdog scheduled watch on %s", repo_path)
                                except Exception as we:
                                    logger.error("Failed to schedule watch on %s: %s", repo_path, we)

                        # Remove stale watches
                        for repo_path in list(self.watches.keys()):
                            if repo_path not in db_repos:
                                try:
                                    self.observer.unschedule(self.watches[repo_path])
                                    del self.watches[repo_path]
                                    logger.info("Watchdog unscheduled watch on %s", repo_path)
                                except Exception as we:
                                    logger.error("Failed to unschedule watch on %s: %s", repo_path, we)
                finally:
                    db.close()
            except Exception as e:
                logger.error("Error in watchdog sync watches loop: %s", e)

            # Sleep poll_interval seconds while checking stop event
            for _ in range(int(self.poll_interval)):
                if self._stop_event.is_set():
                    break
                await asyncio.sleep(1)

    def queue_event(self, event_type: str, file_path_str: str, repo_path_str: str):
        """Enqueue filesystem events to be processed on the background event loop."""
        if self.loop and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(
                self.process_change(event_type, file_path_str, repo_path_str),
                self.loop
            )

    async def process_change(self, event_type: str, file_path_str: str, repo_path_str: str):
        """Incremental update runner checking exclusions and cache status."""
        from backend.app.intelligence.exclusions import default_exclusions
        if default_exclusions.should_exclude(file_path_str):
            return

        db = SessionLocal()
        try:
            from backend.app.services.memory_manager import memory_manager
            if memory_manager.is_indexing_paused():
                return

            path = Path(file_path_str)

            if event_type == "deleted":
                logger.info("Watchdog: Detected deleted file %s", file_path_str)
                await self.indexing_service.incremental_update(file_path_str, repo_path_str, db)
                db.commit()
            elif event_type in ("created", "modified"):
                if not path.exists() or not path.is_file():
                    return

                # Fetch node to check cached properties
                node = db.query(HierarchicalNode).filter(
                    HierarchicalNode.node_type == "file",
                    HierarchicalNode.path == file_path_str
                ).first()

                try:
                    runtime = get_runtime()
                    mtime = runtime.get_file_modification_time(file_path_str)
                except (OSError, ValueError):
                    return

                if node:
                    metadata = json.loads(node.metadata_json) if node.metadata_json else {}
                    cached_mtime = metadata.get("last_mtime")
                    if cached_mtime is not None and float(mtime) == float(cached_mtime):
                        return

                    current_hash = self._content_hash(path)
                    if current_hash is not None and node.hash == current_hash:
                        metadata["last_mtime"] = mtime
                        metadata["last_hash"] = current_hash
                        node.metadata_json = json.dumps(metadata)
                        db.commit()
                        return

                logger.info("Watchdog: Detected %s file %s", event_type, file_path_str)
                node = await self.indexing_service.incremental_update(file_path_str, repo_path_str, db)
                if node:
                    current_hash = node.hash or self._content_hash(path)
                    metadata = json.loads(node.metadata_json) if node.metadata_json else {}
                    metadata["last_mtime"] = mtime
                    if current_hash:
                        metadata["last_hash"] = current_hash
                    node.metadata_json = json.dumps(metadata)
                db.commit()
        except Exception as e:
            logger.error("Error processing watchdog change for %s: %s", file_path_str, e, exc_info=True)
            db.rollback()
        finally:
            db.close()
