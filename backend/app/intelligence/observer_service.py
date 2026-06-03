"""Background filesystem observer for incremental intelligence updates."""

from __future__ import annotations

import asyncio
import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path

from backend.app.core.logging import get_logger
from backend.app.core.paths import PROJECT_ROOT
from backend.app.db.session import SessionLocal
from backend.app.intelligence.discovery import FilesystemDiscovery
from backend.app.intelligence.exclusions import default_exclusions
from backend.app.intelligence.models import CortexAutomationSettings
from backend.app.intelligence.sync_service import SyncService

logger = get_logger(__name__)

OBSERVER_STATE_FILE = PROJECT_ROOT / ".cortex" / "observer_snapshot.json"


class BackgroundObserverService:
    """
    Polls discovered roots for mtime changes and triggers incremental sync.
    Uses lightweight polling to avoid heavy OS-wide watchers.
    """

    def __init__(self, poll_interval_seconds: int = 90):
        self.poll_interval = poll_interval_seconds
        self.discovery = FilesystemDiscovery()
        self.sync_service = SyncService()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._loop: asyncio.AbstractEventLoop | None = None

    def start(self, loop: asyncio.AbstractEventLoop | None = None) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._loop = loop
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, name="cortex-observer", daemon=True)
        self._thread.start()
        logger.info("Background observer started (interval=%ss)", self.poll_interval)

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Background observer stopped")

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                if not self._observer_enabled():
                    self._stop_event.wait(self.poll_interval)
                    continue
                changes = self._detect_changes()
                if changes:
                    self._apply_incremental(changes)
            except Exception as exc:
                logger.warning("Observer cycle failed: %s", exc)
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
        for path in removed[:50]:
            changed_paths.append(path)

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

    def _load_snapshot(self) -> dict:
        if not OBSERVER_STATE_FILE.exists():
            return {"files": {}}
        try:
            return json.loads(OBSERVER_STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {"files": {}}

    def _save_snapshot(self, data: dict) -> None:
        OBSERVER_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        OBSERVER_STATE_FILE.write_text(json.dumps(data), encoding="utf-8")
