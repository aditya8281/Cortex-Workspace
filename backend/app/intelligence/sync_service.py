"""Full and incremental environment sync for Cortex."""

from __future__ import annotations

import json
import os
import time
import math
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Dict, Optional

from sqlalchemy.orm import Session

from backend.app.ai.ingestion.scanner import RepoScanner
from backend.app.core.paths import PROJECT_ROOT
from backend.app.core.config import settings
from backend.app.intelligence.discovery import FilesystemDiscovery
from backend.app.intelligence.memory_service import PersistentMemoryService
from backend.app.intelligence.models import SyncRun
from backend.app.intelligence.proactive_service import ProactiveService
from backend.app.intelligence.repository_intelligence import RepositoryIntelligenceService
from backend.app.services.hierarchical_indexing import HierarchicalIndexingService
from backend.app.models.hierarchical_memory import HierarchicalNode
import numpy as np

logger = logging.getLogger(__name__)

def get_state_file():
    from backend.app.services.memory_manager import memory_manager
    return memory_manager.get_path("sync_state", "filesystem_index_state.json")


class SyncProgressState:
    def __init__(self):
        self.status = "idle"  # idle, syncing, paused, completed, failed
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
        self.pause_event.set()  # Set means running, Cleared means paused
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
            # Block until set() is called on pause_event
            self.pause_event.wait()
            # Resumed
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
        self.indexing_service = HierarchicalIndexingService()
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
        self.progress_state.pause_event.set()  # wake up if paused
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
            
            # Live tracking progress fields
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
        embedding_model: str | None = None,
        vector_db: str | None = None,
        code_parsing: str | None = None,
        force: bool = False,
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
            self.progress_state.reset()
            
            # Force Resync: purge local FAISS store, SQLite hierarchical nodes, and state cache files
            if force:
                logger.info("Memory Sync Engine: force resync requested. Purging database & indices...")
                db.query(HierarchicalNode).delete()
                db.commit()
                self.indexing_service.vector_store.indices["chunk"].reset()
                self.indexing_service.vector_store.indices["file"].reset()
                self.indexing_service.vector_store.indices["folder"].reset()
                self.indexing_service.vector_store.indices["repo"].reset()
                self.indexing_service.vector_store.save()
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
            
            # Full BFS discovery scanning based on user scope includes/excludes config
            current_files_list = self.scanner.scan()
            self.progress_state.total_files = len(current_files_list)
            self.progress_state.update_metrics()

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
            run.progress_message = "Updating memory layers..."
            db.commit()

            from backend.app.intelligence.scope_config import SyncScopeConfig
            config = SyncScopeConfig()
            
            # 1. Process deleted files
            for path in removed:
                if self.progress_state.check_paused_or_cancelled():
                    break
                self.progress_state.current_path = f"Removing {Path(path).name}"
                try:
                    repo_path = self._resolve_repo_path(path, config.include_folders, settings.WORKSPACE_ROOT)
                    await self.indexing_service.incremental_update(path, repo_path, db)
                except Exception as e:
                    self.progress_state.errors += 1
                    self.progress_state.error_logs.append(f"Failed to remove {Path(path).name}: {str(e)}")
                    self.progress_state.error_logs = self.progress_state.error_logs[-20:]
                
                self.progress_state.indexed += 1
                self.progress_state.update_metrics()

            # 2. Process added and modified files (Concurrency and Throttled indexing)
            batch_size = 5
            consecutive_files = added + modified
            for i in range(0, len(consecutive_files), batch_size):
                if self.progress_state.check_paused_or_cancelled():
                    break

                batch = consecutive_files[i:i + batch_size]
                for path in batch:
                    if self.progress_state.check_paused_or_cancelled():
                        break

                    self.progress_state.current_path = path
                    try:
                        repo_path = self._resolve_repo_path(path, config.include_folders, settings.WORKSPACE_ROOT)
                        # Index file, extract, chunk, and embed to FAISS + SQLite
                        await self.indexing_service.index_file(path, repo_path, db)
                    except Exception as e:
                        self.progress_state.errors += 1
                        self.progress_state.error_logs.append(f"Failed to index {Path(path).name}: {str(e)}")
                        self.progress_state.error_logs = self.progress_state.error_logs[-20:]
                    
                    self.progress_state.indexed += 1
                    self.progress_state.update_metrics()

                # IO throttling delay
                time.sleep(0.02)
                db.commit()

            # Check for cancellation before folder/repo summarization
            if self.progress_state.cancel_event.is_set():
                run.status = "failed"
                run.progress_message = "Sync cancelled"
                db.commit()
                return run

            # 3. Bubble up folder summaries and repository summaries bottom-up
            run.progress_message = "Summarizing folder structures..."
            db.commit()
            
            roots = [Path(p).resolve() for p in config.include_folders]
            workspace = Path(settings.WORKSPACE_ROOT).resolve()
            if workspace not in roots and workspace.exists():
                roots.append(workspace)

            for root in roots:
                root_str = str(root)
                folders = db.query(HierarchicalNode).filter(
                    HierarchicalNode.node_type == "folder"
                ).all()
                folders = [f for f in folders if f.path.startswith(root_str)]
                folders.sort(key=lambda x: len(Path(x.path).parts), reverse=True)
                
                for fold in folders:
                    if self.progress_state.check_paused_or_cancelled():
                        break
                    try:
                        await self.indexing_service.index_folder(fold.path, root_str, db)
                    except Exception as e:
                        logger.warning(f"Failed to index folder summary for {fold.path}: {e}")

            # 4. Generate repository level profiles
            run.progress_message = "Analyzing repositories..."
            db.commit()
            
            memory_updates = 0
            for root in roots:
                if self.progress_state.check_paused_or_cancelled():
                    break
                repo_path_str = str(root)
                try:
                    repo_node = db.query(HierarchicalNode).filter(
                        HierarchicalNode.path == repo_path_str,
                        HierarchicalNode.node_type == "repo"
                    ).first()
                    if not repo_node:
                        repo_node = HierarchicalNode(
                            node_type="repo",
                            path=repo_path_str,
                            content=f"Workspace repository named {root.name}",
                            metadata_json="{}"
                        )
                        db.add(repo_node)
                        db.flush()

                    child_folders = db.query(HierarchicalNode).filter(
                        HierarchicalNode.parent_id == repo_node.id,
                        HierarchicalNode.node_type == "folder"
                    ).all()
                    folder_summaries = "\n".join(f"- {Path(f.path).name}: {f.content}" for f in child_folders) if child_folders else "None."

                    prompt = (
                        f"Provide a brief summary of the contents and purpose of the workspace directory '{root.name}':\n"
                        f"{folder_summaries}"
                    )
                    try:
                        summary = await self.indexing_service.router.generate(prompt=prompt)
                        metadata = {"short_description": summary.strip()}
                    except Exception:
                        metadata = {"short_description": f"Workspace directory named {root.name}"}

                    repo_node.content = metadata["short_description"]
                    repo_node.metadata_json = json.dumps(metadata)
                    db.flush()

                    embedder = self.indexing_service._get_embedder()
                    vec = embedder.encode([repo_node.content])[0]
                    self.indexing_service.vector_store.remove_vectors("repo", np.array([repo_node.id]))
                    self.indexing_service.vector_store.add_vectors("repo", np.array([vec]), np.array([repo_node.id]))
                    self.indexing_service.vector_store.save()
                    memory_updates += 1
                except Exception as e:
                    logger.warning(f"Failed to generate repository profile for include {repo_path_str}: {e}")

            # 5. Proactive notifications & evaluations
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
                repo_count=len(roots),
                pdf_total=pdf_count,
            )

            run.memory_updates = memory_updates + self.memory.count_entries(db, user_id)
            self._save_filesystem_state(current_files, len(roots), run.memory_updates)

            self.progress_state.status = "completed"
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
        embedding_model: str | None = None,
        vector_db: str | None = None,
        code_parsing: str | None = None,
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

        from backend.app.intelligence.scope_config import SyncScopeConfig
        config = SyncScopeConfig()

        self.progress_state.reset()
        removed_count = 0
        indexed_count = 0
        changed_file_paths: list[str] = []
        deleted_paths: list[str] = []

        for path in unique_changes:
            if self.progress_state.check_paused_or_cancelled():
                break

            path_obj = Path(path)
            if not path_obj.exists():
                deleted_paths.append(path)
                self.progress_state.current_path = f"Removing {path_obj.name}"
                try:
                    repo_path = self._resolve_repo_path(path, config.include_folders, settings.WORKSPACE_ROOT)
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        loop.run_until_complete(self.indexing_service.incremental_update(path, repo_path, db))
                    finally:
                        loop.close()
                    tracked.pop(path, None)
                    removed_count += 1
                except Exception as e:
                    self.progress_state.errors += 1
                    self.progress_state.error_logs.append(f"Failed to remove {path_obj.name}: {str(e)}")
                    self.progress_state.error_logs = self.progress_state.error_logs[-20:]
                finally:
                    self.progress_state.indexed += 1
                    self.progress_state.update_metrics()
                continue

            changed_file_paths.append(path)

        files = self.scanner.scan_incremental(changed_file_paths)
        self.progress_state.total_files = len(deleted_paths) + len(files)
        self.progress_state.update_metrics()
        for path in files:
            if self.progress_state.check_paused_or_cancelled():
                break

            self.progress_state.current_path = path
            try:
                repo_path = self._resolve_repo_path(path, config.include_folders, settings.WORKSPACE_ROOT)
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(self.indexing_service.incremental_update(path, repo_path, db))
                finally:
                    loop.close()
                try:
                    tracked[path] = os.path.getmtime(path)
                except OSError:
                    tracked.pop(path, None)
                indexed_count += 1
            except Exception as e:
                self.progress_state.errors += 1
                self.progress_state.error_logs.append(f"Failed incremental index for {Path(path).name}: {str(e)}")
                self.progress_state.error_logs = self.progress_state.error_logs[-20:]
            finally:
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

    def _resolve_repo_path(self, file_path: str, include_folders: List[str], workspace_root: str) -> str:
        path = Path(file_path).resolve()
        for root in sorted(include_folders, key=len, reverse=True):
            root_path = Path(root).resolve()
            try:
                path.relative_to(root_path)
                return str(root_path)
            except ValueError:
                continue
        return workspace_root

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
