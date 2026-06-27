"""Indexing orchestrator — routes file changes to the correct indexer."""

from __future__ import annotations

import logging
from pathlib import Path

from sqlalchemy.orm import Session

from backend.app.services.awareness.file_watcher import FileChange, FileWatcherV2, get_file_watcher_v2
from backend.app.services.memory.document_indexer import DocumentIndexer

logger = logging.getLogger(__name__)

CODE_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".rs",
    ".go",
    ".java",
    ".c",
    ".cpp",
    ".h",
    ".rb",
    ".php",
    ".swift",
    ".kt",
    ".sql",
    ".sh",
}


class IndexingOrchestrator:
    """Routes file changes to the appropriate indexer."""

    def __init__(
        self,
        db: Session,
        document_indexer: DocumentIndexer | None = None,
        file_watcher: FileWatcherV2 | None = None,
    ):
        self._db = db
        self._doc_indexer = document_indexer or DocumentIndexer(db)
        self._watcher = file_watcher or get_file_watcher_v2()
        self._watcher.set_callback(self._handle_change)

    def start_watching(self, repo_path: str) -> bool:
        return self._watcher.watch(repo_path)

    def stop_watching(self, repo_path: str) -> bool:
        return self._watcher.unwatch(repo_path)

    def start(self) -> None:
        self._watcher.start()

    def stop(self) -> None:
        self._watcher.stop()

    def _handle_change(self, change: FileChange) -> None:
        ext = Path(change.path).suffix.lower()

        if ext in CODE_EXTENSIONS:
            logger.debug("Code change (deferred to existing pipeline): %s", change.path)
            return

        if ext not in {
            ".md",
            ".markdown",
            ".rst",
            ".txt",
            ".log",
            ".ipynb",
            ".json",
            ".yaml",
            ".yml",
            ".toml",
            ".xml",
            ".html",
            ".css",
        }:
            return

        if change.event_type == "deleted":
            self._doc_indexer.remove_file(change.path)
        elif change.event_type in ("created", "modified", "moved"):
            self._doc_indexer.index_file(change.path)


_orchestrator: IndexingOrchestrator | None = None


def get_indexing_orchestrator(db: Session) -> IndexingOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = IndexingOrchestrator(db)
    return _orchestrator
