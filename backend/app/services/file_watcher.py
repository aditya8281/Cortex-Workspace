from __future__ import annotations

import asyncio
import logging
import os
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


class SyncJob:
    def __init__(self, job_id: str, repo_path: str, job_type: str, status: str = "pending"):
        self.job_id = job_id
        self.repo_path = repo_path
        self.job_type = job_type
        self.status = status
        self.progress: int = 0
        self.total: int | None = None
        self.result: dict[str, Any] | None = None
        self.error: str | None = None
        self.created_at: datetime = datetime.now(timezone.utc)
        self.updated_at: datetime = datetime.now(timezone.utc)

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "repo_path": self.repo_path,
            "job_type": self.job_type,
            "status": self.status,
            "progress": self.progress,
            "total": self.total,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


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
        self._jobs: dict[str, SyncJob] = {}  # job_id -> SyncJob
        self._initial_scans: dict[str, str] = {}  # repo_path -> job_id for initial scans

    def watch(self, repo_path: str, repo_id: int, embedding_model: str | None = None) -> None:
        """Start watching a directory. Takes initial mtime snapshot."""
        from backend.app.core.config import settings

        self._watched[repo_path] = {
            "repo_id": repo_id,
            "embedding_model": embedding_model or settings.EMBEDDING_MODEL_NAME,
            "sync_enabled": True,
        }
        self._snapshots[repo_path] = self._take_snapshot(repo_path)
        self._sync_state["watching"] = len(self._watched)
        self._sync_state["status"] = "watching"
        logger.info(
            "Watching %s for changes (repo %d, embedding: %s)",
            repo_path,
            repo_id,
            self._watched[repo_path]["embedding_model"],
        )

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

            job_id = None
            try:
                # Create a trackable job for this re-index
                job_id = f"reindex-{uuid.uuid4().hex[:12]}"
                job = SyncJob(
                    job_id=job_id,
                    repo_path=repo_path,
                    job_type="index",
                    status="running",
                )
                job.total = len(files)
                job.progress = 0
                self.add_job(job)

                from backend.app.tasks.worker import enqueue_task

                await enqueue_task("index_repo_task", config["repo_id"])

                # Mark job as completed
                self.update_job_status(
                    job_id,
                    status="completed",
                    progress=len(files),
                    total=len(files),
                    result={"files_indexed": len(files)},
                )
                self._sync_state["indexed"] += len(files)
                self._sync_state["last_sync"] = datetime.now(timezone.utc).isoformat()
            except Exception as e:
                logger.error("Failed to trigger re-index for %s: %s", repo_path, e)
                self._sync_state["errors"] += 1
                if job_id is not None:
                    self.update_job_status(job_id, status="failed", error=str(e))

        self._sync_state["status"] = "watching" if self._watched else "idle"
        self._sync_state["indexed"] = 0
        self._sync_state["errors"] = 0
        self._sync_state["last_reset"] = datetime.now(timezone.utc).isoformat()

    @property
    def watched_count(self) -> int:
        return len(self._watched)

    @property
    def pending_count(self) -> int:
        return sum(len(v) for v in self._pending_changes.values())

    @property
    def sync_state(self) -> dict:
        watched_info = []
        for path, config in self._watched.items():
            initial_job = self.get_initial_scan_job(path)
            watched_info.append(
                {
                    "path": path,
                    "repo_id": config.get("repo_id"),
                    "embedding_model": config.get("embedding_model"),
                    "sync_enabled": config.get("sync_enabled", True),
                    "initial_scan_job_id": initial_job.job_id if initial_job else None,
                    "initial_scan_status": initial_job.status if initial_job else None,
                }
            )
        return {
            **dict(self._sync_state),
            "watched_paths": watched_info,
        }

    @property
    def watched(self) -> dict[str, dict]:
        return dict(self._watched)

    def add_job(self, job: SyncJob) -> None:
        self._jobs[job.job_id] = job
        if job.job_type == "scan" and job.repo_path:
            self._initial_scans[job.repo_path] = job.job_id

    def get_job(self, job_id: str) -> SyncJob | None:
        return self._jobs.get(job_id)

    def get_all_jobs(self) -> list[SyncJob]:
        return list(self._jobs.values())

    def get_initial_scan_job(self, repo_path: str) -> SyncJob | None:
        job_id = self._initial_scans.get(repo_path)
        if job_id:
            return self._jobs.get(job_id)
        return None

    def update_job_status(
        self,
        job_id: str,
        status: str,
        progress: int = 0,
        total: int | None = None,
        result: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        job = self._jobs.get(job_id)
        if job:
            job.status = status
            job.progress = progress
            if total is not None:
                job.total = total
            if result is not None:
                job.result = result
            if error is not None:
                job.error = error
            job.updated_at = datetime.now(timezone.utc)


# Singleton
file_watcher = FileWatcher()
