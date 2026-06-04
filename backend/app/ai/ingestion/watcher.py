import os
import time
import logging
import threading
import asyncio
from pathlib import Path
from backend.app.db.session import SessionLocal
from backend.app.models.hierarchical_memory import HierarchicalNode
from backend.app.services.hierarchical_indexing import HierarchicalIndexingService
from backend.app.ai.ingestion.scanner import RepoScanner

logger = logging.getLogger(__name__)


class BackgroundFileWatcher:
    """
    Lightweight background thread that polls workspace directories for filesystem events,
    triggering incremental updates on file additions, changes, and removals.
    """

    def __init__(self, poll_interval_seconds: int = 15):
        self.poll_interval = poll_interval_seconds
        self.indexing_service = HierarchicalIndexingService()
        self.scanner = RepoScanner()
        self._stop_event = threading.Event()
        self._thread = None

    def start(self):
        if self._thread is not None:
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name="CortexFileWatcher", daemon=True)
        self._thread.start()
        logger.info("Cortex background file watcher daemon started")

    def stop(self):
        if self._thread is None:
            return
        self._stop_event.set()
        self._thread.join(timeout=3.0)
        self._thread = None
        logger.info("Cortex background file watcher daemon stopped")

    def _run(self):
        # We need a dedicated event loop for this thread to call async indexing functions
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        while not self._stop_event.is_set():
            try:
                loop.run_until_complete(self._scan_and_update())
            except Exception as e:
                logger.error(f"Error in background file watcher scan iteration: {e}", exc_info=True)
            
            # Sleep in increments to check stop event frequently
            for _ in range(int(self.poll_interval)):
                if self._stop_event.is_set():
                    break
                time.sleep(1)

        loop.close()

    async def _scan_and_update(self):
        db = SessionLocal()
        try:
            # Fetch all registered repositories in hierarchical nodes
            repos = db.query(HierarchicalNode).filter(HierarchicalNode.node_type == "repo").all()
            if not repos:
                return

            for repo in repos:
                repo_path_str = repo.path
                if not Path(repo_path_str).exists():
                    logger.warning(f"Repository directory {repo_path_str} no longer exists, removing from hierarchical memory.")
                    db.delete(repo)
                    db.commit()
                    continue

                # Scan workspace directory using scanner
                current_files = self.scanner.scan(repo_path_str)
                
                # Fetch all files registered under this repo path
                db_files = db.query(HierarchicalNode).filter(
                    HierarchicalNode.node_type == "file"
                ).all()
                db_files = [f for f in db_files if f.path.startswith(repo_path_str)]
                db_files_map = {f.path: f for f in db_files}

                # Detect additions, modifications, and deletions
                current_files_set = set(current_files)
                db_files_set = set(db_files_map.keys())

                added_files = current_files_set - db_files_set
                deleted_files = db_files_set - current_files_set

                # Detect modified files (we check mtime for efficiency before reading/hashing)
                modified_files = []
                for path in current_files_set & db_files_set:
                    node = db_files_map[path]
                    try:
                        mtime = os.path.getmtime(path)
                        # Store mtime in node metadata to save hashing calculations
                        metadata = json.loads(node.metadata_json) if node.metadata_json else {}
                        cached_mtime = metadata.get("last_mtime")
                        if cached_mtime is None or float(mtime) != float(cached_mtime):
                            modified_files.append((path, mtime))
                    except OSError:
                        deleted_files.add(path)

                # 1. Process deleted files
                for path in deleted_files:
                    logger.info(f"Background File Watcher: Detected deleted file {path}")
                    await self.indexing_service.incremental_update(path, repo_path_str, db)

                # 2. Process added files
                for path in added_files:
                    logger.info(f"Background File Watcher: Detected new file {path}")
                    node = await self.indexing_service.incremental_update(path, repo_path_str, db)
                    if node:
                        # Cache mtime to prevent double indexing
                        try:
                            mtime = os.path.getmtime(path)
                            metadata = json.loads(node.metadata_json) if node.metadata_json else {}
                            metadata["last_mtime"] = mtime
                            node.metadata_json = json.dumps(metadata)
                            db.flush()
                        except OSError:
                            pass

                # 3. Process modified files
                for path, mtime in modified_files:
                    logger.info(f"Background File Watcher: Detected modified file {path}")
                    node = await self.indexing_service.incremental_update(path, repo_path_str, db)
                    if node:
                        metadata = json.loads(node.metadata_json) if node.metadata_json else {}
                        metadata["last_mtime"] = mtime
                        node.metadata_json = json.dumps(metadata)
                        db.flush()

                if added_files or deleted_files or modified_files:
                    db.commit()

        except Exception as e:
            logger.error(f"Error scanning files in background watcher: {e}")
        finally:
            db.close()
