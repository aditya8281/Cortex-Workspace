"""Full and incremental environment sync for Cortex."""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from backend.app.ai.ingestion.scanner import RepoScanner
from backend.app.core.paths import PROJECT_ROOT
from backend.app.intelligence.discovery import FilesystemDiscovery
from backend.app.intelligence.memory_service import PersistentMemoryService
from backend.app.intelligence.models import SyncRun
from backend.app.intelligence.proactive_service import ProactiveService
from backend.app.intelligence.repository_intelligence import RepositoryIntelligenceService
from backend.app.rag.index_manager import IndexManager

STATE_FILE = PROJECT_ROOT / ".cortex" / "filesystem_index_state.json"


class SyncService:
    _lock = threading.Lock()
    _active_run_id: int | None = None

    def __init__(self):
        self.scanner = RepoScanner()
        self.discovery = FilesystemDiscovery()
        self.repo_intel = RepositoryIntelligenceService()
        self.memory = PersistentMemoryService()
        self.proactive = ProactiveService()

    def get_status(self, db: Session) -> dict[str, Any]:
        latest = db.query(SyncRun).order_by(SyncRun.started_at.desc()).first()
        state = self._load_filesystem_state()
        return {
            "last_sync_time": latest.completed_at.isoformat() if latest and latest.completed_at else None,
            "last_sync_status": latest.status if latest else None,
            "files_indexed": latest.files_indexed if latest else state.get("file_count", 0),
            "repositories_indexed": latest.repositories_indexed if latest else state.get("repo_count", 0),
            "memory_updates": latest.memory_updates if latest else state.get("memory_count", 0),
            "active_sync_id": self._active_run_id,
            "active_sync_status": latest.status if latest and latest.status == "running" else None,
            "progress_message": latest.progress_message if latest and latest.status == "running" else None,
            "discovery_roots": [str(p) for p in self.discovery.discover_roots()[:20]],
            "tracked_files": state.get("file_count", 0),
        }

    def run_full_sync(
        self,
        db: Session,
        *,
        user_id: int | None = None,
        run_id: int | None = None,
        embedding_model: str | None = None,
        vector_db: str | None = None,
        code_parsing: str | None = None,
    ) -> SyncRun:
        with self._lock:
            if run_id is not None:
                run = db.get(SyncRun, run_id)
                if run is None:
                    run = SyncRun(
                        user_id=user_id,
                        status="running",
                        progress_message="Discovering environment...",
                    )
                    db.add(run)
                    db.commit()
                    db.refresh(run)
            elif self._active_run_id is not None:
                running = db.get(SyncRun, self._active_run_id)
                if running and running.status == "running":
                    return running
                run = SyncRun(
                    user_id=user_id,
                    status="running",
                    progress_message="Discovering environment...",
                )
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
                run = SyncRun(
                    user_id=user_id,
                    status="running",
                    progress_message="Discovering environment...",
                )
                db.add(run)
                db.commit()
                db.refresh(run)
            self._active_run_id = run.id

        try:
            previous_state = self._load_filesystem_state()
            previous_files: dict[str, float] = previous_state.get("files", {})

            run.progress_message = "Scanning filesystem..."
            db.commit()
            current_files_list = self.scanner.scan()
            current_files = {}
            for path in current_files_list:
                try:
                    current_files[path] = os.path.getmtime(path)
                except OSError:
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
            run.progress_message = "Updating embeddings..."
            db.commit()

            manager = IndexManager(
                repo_path=str(PROJECT_ROOT),
                embedding_model=embedding_model,
                vector_db=vector_db,
                code_parsing=code_parsing,
            )
            manager.get_store()

            run.progress_message = "Analyzing repositories..."
            db.commit()
            repos = self.discovery.find_git_repositories()
            run.repositories_indexed = len(repos)
            memory_updates = 0

            for repo_path in repos:
                profile = self.repo_intel.analyze(repo_path)
                self.repo_intel.upsert_profile(db, profile, user_id=user_id)
                self.repo_intel.store_searchable_memory(db, profile, user_id=user_id)
                memory_updates += 1

            pdf_count = sum(1 for p in current_files if p.lower().endswith(".pdf"))
            new_pdf_count = sum(1 for p in added if p.lower().endswith(".pdf"))

            self.proactive.evaluate_after_sync(
                db,
                user_id=user_id,
                new_repos=len([p for p in added if (Path(p) / ".git").exists()]),
                new_pdfs=new_pdf_count,
                modified_project_files=len(modified),
                repo_count=len(repos),
                pdf_total=pdf_count,
            )

            run.memory_updates = memory_updates + self.memory.count_entries(db, user_id)
            self._save_filesystem_state(current_files, len(repos), run.memory_updates)

            run.status = "completed"
            run.completed_at = datetime.now(timezone.utc).replace(tzinfo=None)
            run.progress_message = "Sync complete"
            run.result_summary = (
                f"Indexed {run.files_indexed} files across {run.repositories_indexed} repositories. "
                f"Added {run.files_added}, modified {run.files_modified}, removed {run.files_removed}. "
                f"Memory entries updated: {memory_updates}."
            )
            db.commit()
            db.refresh(run)
            return run
        except Exception as exc:
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
        embedding_model: str | None = None,
        vector_db: str | None = None,
        code_parsing: str | None = None,
    ) -> dict[str, Any]:
        files = self.scanner.scan_incremental(changed_paths)
        if not files:
            return {"updated_files": 0, "message": "No indexable changes"}

        state = self._load_filesystem_state()
        tracked: dict[str, float] = state.get("files", {})
        for path in files:
            try:
                tracked[path] = os.path.getmtime(path)
            except OSError:
                pass

        manager = IndexManager(
            repo_path=str(PROJECT_ROOT),
            embedding_model=embedding_model,
            vector_db=vector_db,
            code_parsing=code_parsing,
        )
        manager.get_store()

        repo_updates = 0
        for path in changed_paths:
            p = Path(path).resolve()
            if (p / ".git").exists() or (p.parent / ".git").exists():
                repo_root = p if (p / ".git").exists() else self._find_repo_root(p)
                if repo_root:
                    profile = self.repo_intel.analyze(repo_root)
                    self.repo_intel.upsert_profile(db, profile, user_id=user_id)
                    self.repo_intel.store_searchable_memory(db, profile, user_id=user_id)
                    repo_updates += 1

        self._save_filesystem_state(tracked, state.get("repo_count", 0), state.get("memory_count", 0))
        db.commit()
        return {"updated_files": len(files), "repository_updates": repo_updates}

    def _find_repo_root(self, path: Path) -> Path | None:
        current = path if path.is_dir() else path.parent
        for _ in range(12):
            if (current / ".git").exists():
                return current
            if current.parent == current:
                break
            current = current.parent
        return None

    def _load_filesystem_state(self) -> dict[str, Any]:
        if not STATE_FILE.exists():
            return {"files": {}, "file_count": 0, "repo_count": 0, "memory_count": 0}
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {"files": {}, "file_count": 0, "repo_count": 0, "memory_count": 0}

    def _save_filesystem_state(
        self, files: dict[str, float], repo_count: int, memory_count: int
    ) -> None:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "files": files,
            "file_count": len(files),
            "repo_count": repo_count,
            "memory_count": memory_count,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        STATE_FILE.write_text(json.dumps(payload), encoding="utf-8")
