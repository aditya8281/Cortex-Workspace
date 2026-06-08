"""Full and incremental environment sync for Cortex.

Tracks filesystem changes and maintains a local state file.
No RAG/embedding/vector-store dependency.
"""

from __future__ import annotations

import json
import os
import time
import math
import logging
import threading

from backend.app.core.runtime import get_runtime
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List

from sqlalchemy.orm import Session

from backend.app.intelligence.scanner import RepoScanner
from backend.app.core.config import settings
from backend.app.intelligence.discovery import FilesystemDiscovery
from backend.app.intelligence.memory_service import PersistentMemoryService
from backend.app.intelligence.models import SyncRun
from backend.app.intelligence.proactive_service import ProactiveService
from backend.app.intelligence.repository_intelligence import RepositoryIntelligenceService

logger = logging.getLogger(__name__)

def get_state_file():
    from backend.app.core import storage
    return storage.get_sync_root() / "filesystem_index_state.json"


class SyncProgressState:
    def __init__(self):
        self.status = "idle"
        self.current_path = ""
        self.total_files = 0
        self.indexed = 0
        self.pending = 0
        self.errors = 0
        self.progress_percent = 0.0
        self.speed_files_per_sec = 0.0
        self.estimated_time_remaining = 0.0
        self.started_at = None
        self.paused_at = None
        self.pause_event = threading.Event()
        self.pause_event.set()
        self.cancel_event = threading.Event()
        self.error_logs: List[str] = []

    def reset(self):
        self.status = "syncing"
        self.current_path = ""
        self.total_files = 0
        self.indexed = 0
        self.pending = 0
        self.errors = 0
        self.progress_percent = 0.0
        self.speed_files_per_sec = 0.0
        self.estimated_time_remaining = 0.0
        self.started_at = time.time()
        self.paused_at = None
        self.pause_event.set()
        self.cancel_event.clear()
        self.error_logs = []

    def check_paused_or_cancelled(self) -> bool:
        if self.cancel_event.is_set():
            return True
        if not self.pause_event.is_set():
            self.status = "paused"
            self.paused_at = time.time()
            self.pause_event.wait()
            self.status = "syncing"
            if self.paused_at and self.started_at:
                self.started_at += (time.time() - self.paused_at)
                self.paused_at = None
        return self.cancel_event.is_set()

    def update_metrics(self):
        if self.total_files > 0:
            self.progress_percent = round((self.indexed / self.total_files) * 100, 1)
        self.pending = max(0, self.total_files - self.indexed)

        elapsed = time.time() - (self.started_at or time.time())
        if elapsed > 0.5:
            self.speed_files_per_sec = round(self.indexed / elapsed, 1)
            if self.speed_files_per_sec > 0:
                self.estimated_time_remaining = math.ceil(self.pending / self.speed_files_per_sec)
            else:
                self.estimated_time_remaining = 0


class SyncService:
    _lock = threading.Lock()
    _active_run_id: int | None = None

    def __init__(self):
        self.scanner = RepoScanner()
        self.discovery = FilesystemDiscovery()
        self.repo_intel = RepositoryIntelligenceService()
        self.memory = PersistentMemoryService()
        self.proactive = ProactiveService()
        self.progress_state = SyncProgressState()

    def pause_sync(self):
        self.progress_state.pause_event.clear()
        self.progress_state.status = "paused"
        logger.info("Memory Sync Engine: sync paused by user request.")

    def resume_sync(self):
        self.progress_state.pause_event.set()
        self.progress_state.status = "syncing"
        logger.info("Memory Sync Engine: sync resumed by user request.")

    def cancel_sync(self):
        self.progress_state.cancel_event.set()
        self.progress_state.pause_event.set()
        self.progress_state.status = "idle"
        logger.info("Memory Sync Engine: sync cancelled/stopped by user request.")

    def get_status(self, db: Session) -> dict[str, Any]:
        latest = db.query(SyncRun).order_by(SyncRun.started_at.desc()).first()
        state = self._load_filesystem_state()

        return {
            "last_sync_time": latest.completed_at.isoformat() if latest and latest.completed_at else None,
            "last_sync_status": latest.status if latest else None,
            "files_indexed": self.progress_state.indexed if self.progress_state.status in ["syncing", "paused"] else (latest.files_indexed if latest else state.get("file_count", 0)),
            "repositories_indexed": latest.repositories_indexed if latest else state.get("repo_count", 0),
            "memory_updates": latest.memory_updates if latest else state.get("memory_count", 0),
            "active_sync_id": self._active_run_id,
            "active_sync_status": self.progress_state.status if self.progress_state.status != "idle" else (latest.status if latest and latest.status == "running" else None),
            "progress_message": self.progress_state.current_path or (latest.progress_message if latest and latest.status == "running" else None),
            "discovery_roots": [str(p) for p in self.discovery.discover_roots()[:20]],
            "tracked_files": state.get("file_count", 0),
            "sync_status": self.progress_state.status,
            "current_path": self.progress_state.current_path,
            "total_files": self.progress_state.total_files,
            "indexed": self.progress_state.indexed,
            "pending": self.progress_state.pending,
            "errors": self.progress_state.errors,
            "progress_percent": self.progress_state.progress_percent,
            "speed_files_per_sec": self.progress_state.speed_files_per_sec,
            "estimated_time_remaining": self.progress_state.estimated_time_remaining,
            "error_logs": self.progress_state.error_logs
        }

    async def run_full_sync(
        self,
        db: Session,
        *,
        user_id: int | None = None,
        run_id: int | None = None,
        force: bool = False,
    ) -> SyncRun:
        with self._lock:
            if run_id is not None:
                run = db.get(SyncRun, run_id)
                if run is None:
                    run = SyncRun(user_id=user_id, status="running", progress_message="Discovering environment...")
                    db.add(run)
                    db.commit()
                    db.refresh(run)
            elif self._active_run_id is not None:
                running = db.get(SyncRun, self._active_run_id)
                if running and running.status == "running":
                    return running
                run = SyncRun(user_id=user_id, status="running", progress_message="Discovering environment...")
                db.add(run)
                db.commit()
                db.refresh(run)
            else:
                running = (
                    db.query(SyncRun)
                    .filter(SyncRun.status == "running")
                    .order_by(SyncRun.started_at.desc())
                    .first()
                )
                if running:
                    self._active_run_id = running.id
                    return running
                run = SyncRun(user_id=user_id, status="running", progress_message="Discovering environment...")
                db.add(run)
                db.commit()
                db.refresh(run)
            self._active_run_id = run.id

        try:
            self.progress_state.reset()

            if force:
                logger.info("Memory Sync Engine: force resync requested. Purging state cache...")
                state_path = get_state_file()
                if state_path.exists():
                    try:
                        os.remove(state_path)
                    except Exception:
                        pass

            previous_state = self._load_filesystem_state()
            previous_files: dict[str, float] = previous_state.get("files", {})

            run.progress_message = "Scanning filesystem..."
            db.commit()

            current_files_list = self.scanner.scan()
            self.progress_state.total_files = len(current_files_list)
            self.progress_state.update_metrics()

            current_files = {}
            runtime = get_runtime()
            for path in current_files_list:
                try:
                    current_files[path] = runtime.get_file_modification_time(path)
                except (OSError, ValueError):
                    continue

            added = [p for p in current_files if p not in previous_files]
            modified = [
                p for p in current_files if p in previous_files and previous_files[p] != current_files[p]
            ]
            removed = [p for p in previous_files if p not in current_files]

            run.files_added = len(added)
            run.files_modified = len(modified)
            run.files_removed = len(removed)
            run.files_indexed = len(current_files)
            run.progress_message = "Updating memory layers..."
            db.commit()

            # Track file discovery progress (no vector indexing)
            for i, path in enumerate(added + modified + removed):
                if self.progress_state.check_paused_or_cancelled():
                    break
                self.progress_state.current_path = path
                self.progress_state.indexed += 1
                self.progress_state.update_metrics()

            if self.progress_state.cancel_event.is_set():
                run.status = "failed"
                run.progress_message = "Sync cancelled"
                db.commit()
                return run

            # Proactive notifications & evaluations
            pdf_count = sum(1 for p in current_files if p.lower().endswith(".pdf"))
            new_pdf_count = sum(1 for p in added if p.lower().endswith(".pdf"))

            def _repo_root_for(path_str: str) -> Path | None:
                path = Path(path_str).resolve()
                for parent in [path] + list(path.parents):
                    if (parent / ".git").is_dir():
                        return parent
                return None

            new_repo_roots = {
                str(root)
                for root in (_repo_root_for(p) for p in added)
                if root is not None
            }
            self.proactive.evaluate_after_sync(
                db,
                user_id=user_id,
                new_repos=len(new_repo_roots),
                new_pdfs=new_pdf_count,
                modified_project_files=len(modified),
                repo_count=0,
                pdf_total=pdf_count,
            )

            memory_count = self.memory.count_entries(db, user_id)
            self._save_filesystem_state(current_files, 0, memory_count)

            self.progress_state.status = "completed"
            run.status = "completed"
            run.completed_at = datetime.now(timezone.utc).replace(tzinfo=None)
            run.progress_message = "Sync complete"
            run.result_summary = (
                f"Tracked {run.files_indexed} files. "
                f"Added {run.files_added}, modified {run.files_modified}, removed {run.files_removed}."
            )
            db.commit()
            db.refresh(run)
            return run
        except Exception as exc:
            self.progress_state.status = "failed"
            run.status = "failed"
            run.completed_at = datetime.now(timezone.utc).replace(tzinfo=None)
            run.progress_message = "Sync failed"
            run.result_summary = str(exc)
            db.commit()
            db.refresh(run)
            return run
        finally:
            with self._lock:
                if self._active_run_id == run.id:
                    self._active_run_id = None

    def run_incremental_sync(
        self,
        db: Session,
        changed_paths: list[str],
        *,
        user_id: int | None = None,
    ) -> dict[str, Any]:
        state = self._load_filesystem_state()
        tracked: dict[str, float] = state.get("files", {})
        unique_changes: list[str] = []
        seen_changes: set[str] = set()
        for raw_path in changed_paths:
            resolved = str(Path(raw_path).resolve())
            if resolved not in seen_changes:
                seen_changes.add(resolved)
                unique_changes.append(resolved)

        if not unique_changes:
            return {"updated_files": 0, "removed_files": 0, "message": "No indexable changes"}

        self.progress_state.reset()
        removed_count = 0
        indexed_count = 0

        for path in unique_changes:
            if self.progress_state.check_paused_or_cancelled():
                break

            path_obj = Path(path)
            if not path_obj.exists():
                self.progress_state.current_path = f"Removing {path_obj.name}"
                tracked.pop(path, None)
                removed_count += 1
            else:
                try:
                    runtime = get_runtime()
                    tracked[path] = runtime.get_file_modification_time(path)
                except (OSError, ValueError):
                    tracked.pop(path, None)
                indexed_count += 1

            self.progress_state.indexed += 1
            self.progress_state.update_metrics()

        memory_count = self.memory.count_entries(db, user_id)
        self._save_filesystem_state(tracked, state.get("repo_count", 0), memory_count)
        self.progress_state.status = "completed" if not self.progress_state.cancel_event.is_set() else "idle"
        self.progress_state.current_path = "Incremental sync complete"
        self.progress_state.update_metrics()
        db.commit()
        return {
            "updated_files": indexed_count,
            "removed_files": removed_count,
            "tracked_files": len(tracked),
            "message": "Incremental sync complete" if not self.progress_state.cancel_event.is_set() else "Incremental sync cancelled",
        }

    def _load_filesystem_state(self) -> dict[str, Any]:
        state_path = get_state_file()
        if not state_path.exists():
            return {"files": {}, "file_count": 0, "repo_count": 0, "memory_count": 0}
        try:
            return json.loads(state_path.read_text(encoding="utf-8"))
        except Exception:
            return {"files": {}, "file_count": 0, "repo_count": 0, "memory_count": 0}

    def _save_filesystem_state(
        self, files: dict[str, float], repo_count: int, memory_count: int
    ) -> None:
        state_path = get_state_file()
        state_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "files": files,
            "file_count": len(files),
            "repo_count": repo_count,
            "memory_count": memory_count,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        state_path.write_text(json.dumps(payload), encoding="utf-8")
