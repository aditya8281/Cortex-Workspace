"""Filesystem indexing service — scans directories and detects changes via content hashing."""

from __future__ import annotations

import hashlib
import mimetypes
import os
from datetime import datetime

from sqlalchemy.orm import Session

from backend.app.models.awareness.file_tracker import FileIndex

# Directories to skip during scanning
SKIP_DIRS: set[str] = {
    ".git",
    "node_modules",
    "__pycache__",
    "venv",
    ".venv",
    ".tox",
    ".mypy_cache",
    ".pytest_cache",
    "dist",
    "build",
    ".next",
    ".nuxt",
    "target",
    ".idea",
    ".vscode",
}

# Max file path length (DB column is VARCHAR(1000))
MAX_PATH_LENGTH = 1000

# Max files per scan
MAX_FILES_PER_SCAN = 100_000

# Chunk size for hashing
_HASH_CHUNK_SIZE = 8192


class FilesystemIndexerService:
    """Scans directories, indexes files with content hashes, and detects changes."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def scan_directory(
        self,
        user_id: int,
        directory: str,
    ) -> tuple[list[FileIndex], dict[str, int]]:
        """Walk *directory* recursively, index every file.

        Returns (indexed_files, stats) where stats counts created / updated /
        unchanged / skipped.
        """
        stats: dict[str, int] = {
            "created": 0,
            "updated": 0,
            "unchanged": 0,
            "skipped": 0,
        }
        indexed_files: list[FileIndex] = []
        file_count = 0

        for root, dirs, filenames in os.walk(directory):
            # Mutate dirs in-place to prune ignored subdirectories
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

            for filename in filenames:
                if file_count >= MAX_FILES_PER_SCAN:
                    break

                filepath = os.path.join(root, filename)
                if len(filepath) > MAX_PATH_LENGTH:
                    stats["skipped"] += 1
                    continue

                result = self._index_file(user_id, filepath)
                if result is None:
                    stats["skipped"] += 1
                    continue

                indexed_files.append(result)
                file_count += 1

                # Classify by comparing with any pre-existing record
                existing = (
                    self.db.query(FileIndex)
                    .filter(
                        FileIndex.user_id == user_id,
                        FileIndex.file_path == filepath,
                    )
                    .first()
                )
                if existing is not None and existing.content_hash == result.content_hash and existing.id != result.id:
                    stats["unchanged"] += 1
                elif existing is not None and existing.id != result.id:
                    stats["updated"] += 1
                else:
                    stats["created"] += 1

        return indexed_files, stats

    def detect_changes(
        self,
        user_id: int,
        directory: str,
    ) -> dict[str, list[FileIndex] | list[str]]:
        """Compare indexed state with current filesystem state.

        Returns dict with keys ``created``, ``modified``, ``deleted``.
        """
        indexed = (
            self.db.query(FileIndex)
            .filter(
                FileIndex.user_id == user_id,
                FileIndex.parent_directory.like(f"{directory}%"),
            )
            .all()
        )
        indexed_map: dict[str, FileIndex] = {f.file_path: f for f in indexed}

        # Current files on disk
        current_paths: set[str] = set()
        for root, dirs, filenames in os.walk(directory):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for filename in filenames:
                fp = os.path.join(root, filename)
                if len(fp) <= MAX_PATH_LENGTH:
                    current_paths.add(fp)

        created: list[FileIndex] = []
        modified: list[FileIndex] = []
        deleted: list[str] = []

        for fp in current_paths:
            if fp not in indexed_map:
                result = self._index_file(user_id, fp)
                if result is not None:
                    created.append(result)
            else:
                indexed_file = indexed_map[fp]
                current_hash = self._compute_hash(fp)
                if current_hash != indexed_file.content_hash:
                    result = self._index_file(user_id, fp)
                    if result is not None:
                        modified.append(result)

        for fp, indexed_file in indexed_map.items():
            if fp not in current_paths:
                deleted.append(fp)
                self.db.delete(indexed_file)

        self.db.commit()

        summary: dict[str, list[FileIndex] | list[str]] = {
            "created": created,
            "modified": modified,
            "deleted": deleted,
        }
        return summary

    def get_directory_summary(
        self,
        user_id: int,
        directory: str,
    ) -> dict[str, object]:
        """Return aggregate statistics for files under *directory*."""
        files = (
            self.db.query(FileIndex)
            .filter(
                FileIndex.user_id == user_id,
                FileIndex.parent_directory.like(f"{directory}%"),
            )
            .all()
        )

        extensions: dict[str, int] = {}
        total_size = 0
        for f in files:
            ext = f.file_extension or "none"
            extensions[ext] = extensions.get(ext, 0) + 1
            total_size += f.file_size or 0

        return {
            "total_files": len(files),
            "total_size_bytes": total_size,
            "extensions": extensions,
            "directory": directory,
        }

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _index_file(self, user_id: int, filepath: str) -> FileIndex | None:
        """Index a single file.  Returns *None* if the file is unreadable."""
        try:
            stat_result = os.stat(filepath)
            content_hash = self._compute_hash(filepath)
            mime_type, _ = mimetypes.guess_type(filepath)

            existing = (
                self.db.query(FileIndex)
                .filter(
                    FileIndex.user_id == user_id,
                    FileIndex.file_path == filepath,
                )
                .first()
            )

            if existing is not None:
                if existing.content_hash == content_hash:
                    return existing  # no change
                # Update in place
                existing.file_size = stat_result.st_size
                existing.last_modified = datetime.fromtimestamp(stat_result.st_mtime)
                existing.content_hash = content_hash
                existing.indexed_at = datetime.now()
                existing.mime_type = mime_type
                self.db.commit()
                return existing

            file_index = FileIndex(
                user_id=user_id,
                file_path=filepath,
                file_name=os.path.basename(filepath),
                file_extension=os.path.splitext(filepath)[1],
                file_size=stat_result.st_size,
                mime_type=mime_type,
                last_modified=datetime.fromtimestamp(stat_result.st_mtime),
                indexed_at=datetime.now(),
                content_hash=content_hash,
                parent_directory=os.path.dirname(filepath),
            )
            self.db.add(file_index)
            self.db.commit()
            return file_index
        except (OSError, PermissionError, ValueError):
            return None

    @staticmethod
    def _compute_hash(filepath: str) -> str:
        """Compute SHA-256 hex digest of *filepath* via chunked reading."""
        hasher = hashlib.sha256()
        try:
            with open(filepath, "rb") as fh:
                for chunk in iter(lambda: fh.read(_HASH_CHUNK_SIZE), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except (OSError, PermissionError):
            return ""
