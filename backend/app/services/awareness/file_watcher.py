"""Event-driven file watcher using watchdog for OS-level filesystem events."""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from backend.app.services.intelligence.chunker import SKIP_DIRS

logger = logging.getLogger(__name__)


@dataclass
class FileChange:
    path: str
    event_type: str  # "created", "modified", "deleted", "moved"
    old_path: str | None = None
    timestamp: float = field(default_factory=time.time)


class _ChangeHandler(FileSystemEventHandler):
    def __init__(self, callback: Callable[[FileChange], None], debounce_seconds: float = 2.0):
        self._callback = callback
        self._debounce = debounce_seconds
        self._pending: dict[str, float] = {}

    def _should_ignore(self, path: str) -> bool:
        parts = Path(path).parts
        return any(d in SKIP_DIRS for d in parts)

    def _schedule(self, change: FileChange) -> None:
        if self._should_ignore(change.path):
            return
        now = time.time()
        last = self._pending.get(change.path, 0)
        if now - last >= self._debounce:
            self._pending[change.path] = now
            self._callback(change)

    def on_created(self, event: FileSystemEvent) -> None:
        if not event.is_directory and event.src_path is not None:
            self._schedule(FileChange(path=str(event.src_path), event_type="created"))

    def on_modified(self, event: FileSystemEvent) -> None:
        if not event.is_directory and event.src_path is not None:
            self._schedule(FileChange(path=str(event.src_path), event_type="modified"))

    def on_deleted(self, event: FileSystemEvent) -> None:
        if not event.is_directory and event.src_path is not None:
            self._schedule(FileChange(path=str(event.src_path), event_type="deleted"))

    def on_moved(self, event: FileSystemEvent) -> None:
        if not event.is_directory and event.src_path is not None and event.dest_path is not None:
            self._schedule(
                FileChange(
                    path=str(event.dest_path),
                    event_type="moved",
                    old_path=str(event.src_path),
                )
            )


class FileWatcherV2:
    """Event-driven file watcher using watchdog for OS-level filesystem events."""

    def __init__(self, debounce_seconds: float = 2.0):
        self._observer: Observer | None = None  # type: ignore[valid-type]
        self._watched: dict[str, bool] = {}
        self._debounce = debounce_seconds
        self._on_change: Callable[[FileChange], None] | None = None

    def set_callback(self, callback: Callable[[FileChange], None]) -> None:
        self._on_change = callback

    def watch(self, repo_path: str) -> bool:
        if not self._observer:
            self._observer = Observer()

        if repo_path in self._watched:
            return False

        handler = _ChangeHandler(self._on_change or self._default_handler, self._debounce)
        path = Path(repo_path)
        if not path.exists():
            logger.warning("Path does not exist: %s", repo_path)
            return False

        self._observer.schedule(handler, str(path), recursive=True)  # type: ignore[union-attr]
        self._watched[repo_path] = True
        logger.info("Watching: %s", repo_path)
        return True

    def unwatch(self, repo_path: str) -> bool:
        if repo_path not in self._watched:
            return False

        if self._observer:
            for subscription in self._observer.emitters:  # type: ignore[attr-defined]
                if subscription.path == repo_path:
                    subscription.stop()
                    break

        del self._watched[repo_path]
        logger.info("Stopped watching: %s", repo_path)
        return True

    def start(self) -> None:
        if self._observer and self._observer.is_alive():  # type: ignore[attr-defined]
            return
        self._observer = Observer()
        self._observer.start()  # type: ignore[attr-defined]
        logger.info("File watcher started")

    def stop(self) -> None:
        if self._observer and self._observer.is_alive():  # type: ignore[attr-defined]
            self._observer.stop()  # type: ignore[attr-defined]
            self._observer.join(timeout=5.0)  # type: ignore[attr-defined]
            if self._observer.is_alive():  # type: ignore[attr-defined]
                logger.warning("File watcher did not stop within timeout")
            else:
                logger.info("File watcher stopped")
        self._observer = None
        self._watched.clear()

    @property
    def is_running(self) -> bool:
        return self._observer is not None and self._observer.is_alive()  # type: ignore[valid-type, union-attr]

    @property
    def watched_count(self) -> int:
        return len(self._watched)

    @staticmethod
    def _default_handler(change: FileChange) -> None:
        logger.info("File change: %s %s", change.event_type, change.path)


_file_watcher_v2: FileWatcherV2 | None = None
_file_watcher_v2_lock = threading.Lock()


def get_file_watcher_v2() -> FileWatcherV2:
    global _file_watcher_v2
    if _file_watcher_v2 is None:
        with _file_watcher_v2_lock:
            if _file_watcher_v2 is None:
                _file_watcher_v2 = FileWatcherV2()
    return _file_watcher_v2
