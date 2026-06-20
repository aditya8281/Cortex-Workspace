from __future__ import annotations

import asyncio
import logging
import os
from collections import defaultdict
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class FileWatcher:
    """Watches directories for changes using polling and triggers re-indexing."""

    def __init__(self, poll_interval: float = 5.0):
        self._watched: dict[str, dict] = {}  # path -> config
        self._pending_changes: dict[str, set[str]] = defaultdict(set)
        self._snapshots: dict[str, dict[str, float]] = {}  # path -> {filepath: mtime}
        self._poll_interval = poll_interval
        self._debounce_task: asyncio.Task | None = None
        self._running = False
        self._sync_state: dict = {
            "status": "idle",
            "watching": 0,
            "pending": 0,
            "indexed": 0,
            "errors": 0,
            "last_sync": None,
        }

    def watch(self, repo_path: str, repo_id: int) -> None:
        """Start watching a directory. Takes initial mtime snapshot."""
        self._watched[repo_path] = {"repo_id": repo_id}
        self._snapshots[repo_path] = self._take_snapshot(repo_path)
        self._sync_state["watching"] = len(self._watched)
        self._sync_state["status"] = "watching"
        logger.info("Watching %s for changes (repo %d)", repo_path, repo_id)

    def unwatch(self, repo_path: str) -> None:
        """Stop watching a directory."""
        self._watched.pop(repo_path, None)
        self._snapshots.pop(repo_path, None)
        self._pending_changes.pop(repo_path, None)
        self._sync_state["watching"] = len(self._watched)
        if not self._watched:
            self._sync_state["status"] = "idle"

    def _take_snapshot(self, repo_path: str) -> dict[str, float]:
        """Build a {filepath: mtime} snapshot, respecting SKIP_DIRS."""
        from backend.app.services.chunker import SKIP_DIRS
        snapshot: dict[str, float] = {}
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for f in files:
                fp = os.path.join(root, f)
                try:
                    snapshot[fp] = os.path.getmtime(fp)
                except OSError:
                    continue
        return snapshot

    async def start(self) -> None:
        """Start the file watcher polling loop."""
        self._running = True
        self._debounce_task = asyncio.create_task(self._poll_loop())
        logger.info("File watcher started (poll interval %.1fs)", self._poll_interval)

    async def stop(self) -> None:
        """Stop the file watcher."""
        self._running = False
        if self._debounce_task:
            self._debounce_task.cancel()
            try:
                await self._debounce_task
            except asyncio.CancelledError:
                pass
        logger.info("File watcher stopped")

    async def _poll_loop(self) -> None:
        """Periodically poll filesystem for changes."""
        while self._running:
            try:
                await asyncio.sleep(self._poll_interval)
                await self._poll_and_record()
                if self._pending_changes:
                    await self._process_changes()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("File watcher poll error: %s", e)
                await asyncio.sleep(self._poll_interval)

    async def _poll_and_record(self) -> None:
        """Compare current mtime against snapshot, record changes."""
        for repo_path in list(self._watched.keys()):
            new_snapshot = self._take_snapshot(repo_path)
            old_snapshot = self._snapshots.get(repo_path, {})

            # Detect modified or created files
            for fp, mtime in new_snapshot.items():
                if fp not in old_snapshot or old_snapshot[fp] != mtime:
                    self._pending_changes[repo_path].add(fp)

            # Detect deleted files
            for fp in old_snapshot:
                if fp not in new_snapshot:
                    self._pending_changes[repo_path].add(fp)

            # Update snapshot
            self._snapshots[repo_path] = new_snapshot

        self._sync_state["pending"] = self.pending_count

    async def _process_changes(self) -> None:
        """Process accumulated file changes by triggering incremental re-index."""
        changes = dict(self._pending_changes)
        self._pending_changes.clear()

        self._sync_state["status"] = "indexing"
        self._sync_state["pending"] = 0

        for repo_path, files in changes.items():
            config = self._watched.get(repo_path)
            if not config:
                continue

            # Check if sync is enabled for this repo
            if not config.get("sync_enabled", True):
                logger.debug("Sync disabled for %s, skipping", repo_path)
                continue

            logger.info("Processing %d file changes in %s", len(files), repo_path)

            try:
                from backend.app.tasks.worker import enqueue_task
                await enqueue_task("index_repo_task", config["repo_id"])
                self._sync_state["indexed"] += len(files)
                self._sync_state["last_sync"] = datetime.now(timezone.utc).isoformat()
            except Exception as e:
                logger.error("Failed to trigger re-index for %s: %s", repo_path, e)
                self._sync_state["errors"] += 1

        self._sync_state["status"] = "watching" if self._watched else "idle"

    @property
    def watched_count(self) -> int:
        return len(self._watched)

    @property
    def pending_count(self) -> int:
        return sum(len(v) for v in self._pending_changes.values())

    @property
    def sync_state(self) -> dict:
        return dict(self._sync_state)


# Singleton
file_watcher = FileWatcher()
