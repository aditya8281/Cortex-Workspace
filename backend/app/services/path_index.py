"""Pre-computed path indexes for fast directory browsing.

Inspired by sist2's path_parent function. Provides O(1) directory listings
by pre-computing the path hierarchy at index time.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import and_
from sqlalchemy.orm import Session

from backend.app.models.path_index import PathIndex

logger = logging.getLogger(__name__)


class PathIndexer:
    """Builds and queries a pre-computed directory tree for fast browsing."""

    def __init__(self, db: Session):
        self.db = db

    def build_index(self, repo_id: int, root_path: str | Path) -> int:
        """Walk the directory tree and create PathIndex entries.

        Returns the total number of paths created/updated.
        """
        root = Path(root_path)
        if not root.is_dir():
            raise ValueError(f"Path is not a directory: {root_path}")

        count = 0
        for dirpath, dirnames, filenames in os.walk(root):
            rel_dir = os.path.relpath(dirpath, root)
            if rel_dir == ".":
                rel_dir = ""

            # Ensure parent directory entry exists
            if rel_dir:
                parent = os.path.dirname(rel_dir)
                self._upsert_entry(
                    repo_id=repo_id,
                    rel_path=rel_dir,
                    parent_path=parent,
                    is_dir=True,
                    file_count=0,
                    total_size=0,
                )
                count += 1

            # Process files in this directory
            dir_file_count = 0
            dir_total_size = 0
            dir_last_modified = 0.0

            for filename in filenames:
                file_full = os.path.join(dirpath, filename)
                rel_file = os.path.relpath(file_full, root)
                try:
                    st = os.stat(file_full)
                except OSError:
                    continue

                parent_dir = rel_dir
                self._upsert_entry(
                    repo_id=repo_id,
                    rel_path=rel_file,
                    parent_path=parent_dir,
                    is_dir=False,
                    file_count=0,
                    total_size=st.st_size,
                    last_modified=st.st_mtime,
                )
                count += 1

                dir_file_count += 1
                dir_total_size += st.st_size
                dir_last_modified = max(dir_last_modified, st.st_mtime)

            # Update directory entry with aggregated stats
            if rel_dir:
                self._update_dir_stats(repo_id, rel_dir, dir_file_count, dir_total_size, dir_last_modified)

            # Handle subdirectories: count files recursively
            for sub in dirnames:
                sub_rel = os.path.join(rel_dir, sub) if rel_dir else sub
                sub_stats = self._compute_dir_stats(repo_id, root, sub_rel)
                self._upsert_entry(
                    repo_id=repo_id,
                    rel_path=sub_rel,
                    parent_path=rel_dir,
                    is_dir=True,
                    file_count=sub_stats["file_count"],
                    total_size=sub_stats["total_size"],
                    last_modified=sub_stats["last_modified"],
                )
                count += 1

        self.db.commit()
        logger.info("Built path index for repo %d: %d entries", repo_id, count)
        return count

    def get_directory_listing(self, repo_id: int, path: str, offset: int = 0, limit: int = 100) -> list[PathIndex]:
        """List directory contents with stats."""
        return (
            self.db.query(PathIndex)
            .filter(
                and_(
                    PathIndex.repo_id == repo_id,
                    PathIndex.parent_path == path,
                )
            )
            .order_by(PathIndex.is_dir.desc(), PathIndex.basename)
            .offset(offset)
            .limit(limit)
            .all()
        )

    def get_path_info(self, repo_id: int, path: str) -> PathIndex | None:
        """Get info for a single path."""
        return (
            self.db.query(PathIndex)
            .filter(
                and_(
                    PathIndex.repo_id == repo_id,
                    PathIndex.path == path,
                )
            )
            .first()
        )

    def update_path(
        self,
        repo_id: int,
        path: str,
        *,
        is_dir: bool = False,
        file_count: int = 0,
        total_size: int = 0,
        last_modified: float | None = None,
    ) -> PathIndex:
        """Update a single path entry."""
        parent_path = os.path.dirname(path)
        basename = os.path.basename(path)
        depth = path.count(os.sep) if path else 0

        entry = self.get_path_info(repo_id, path)
        if entry:
            entry.file_count = file_count
            entry.total_size = total_size
            if last_modified is not None:
                entry.last_modified = datetime.fromtimestamp(last_modified, tz=timezone.utc)
        else:
            entry = PathIndex(
                path=path,
                parent_path=parent_path,
                basename=basename,
                depth=depth,
                is_dir=is_dir,
                file_count=file_count,
                total_size=total_size,
                last_modified=datetime.fromtimestamp(last_modified, tz=timezone.utc) if last_modified else None,
                repo_id=repo_id,
            )
            self.db.add(entry)

        self.db.flush()
        return entry

    def remove_path(self, repo_id: int, path: str) -> int:
        """Remove a path entry and all its children. Returns count removed."""
        like_pattern = f"{path}/%" if path else "%"
        entries = (
            self.db.query(PathIndex)
            .filter(
                and_(
                    PathIndex.repo_id == repo_id,
                    (PathIndex.path == path) | (PathIndex.path.like(like_pattern)),
                )
            )
            .all()
        )
        count = len(entries)
        for entry in entries:
            self.db.delete(entry)
        self.db.flush()
        logger.info("Removed %d path entries under %s", count, path)
        return count

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _upsert_entry(
        self,
        *,
        repo_id: int,
        rel_path: str,
        parent_path: str,
        is_dir: bool,
        file_count: int,
        total_size: int,
        last_modified: float | None = None,
    ) -> PathIndex:
        """Insert or update a PathIndex entry."""
        basename = os.path.basename(rel_path)
        depth = rel_path.count(os.sep) if rel_path else 0

        entry = self.get_path_info(repo_id, rel_path)
        if entry:
            entry.basename = basename
            entry.depth = depth
            entry.parent_path = parent_path
            entry.is_dir = is_dir
            entry.file_count = file_count
            entry.total_size = total_size
            if last_modified is not None:
                entry.last_modified = datetime.fromtimestamp(last_modified, tz=timezone.utc)
        else:
            entry = PathIndex(
                path=rel_path,
                parent_path=parent_path,
                basename=basename,
                depth=depth,
                is_dir=is_dir,
                file_count=file_count,
                total_size=total_size,
                last_modified=datetime.fromtimestamp(last_modified, tz=timezone.utc) if last_modified else None,
                repo_id=repo_id,
            )
            self.db.add(entry)
            self.db.flush()

        return entry

    def _update_dir_stats(
        self,
        repo_id: int,
        dir_path: str,
        file_count: int,
        total_size: int,
        last_modified: float,
    ) -> None:
        """Update aggregated stats on a directory entry."""
        entry = self.get_path_info(repo_id, dir_path)
        if entry:
            entry.file_count = file_count
            entry.total_size = total_size
            if last_modified > 0:
                entry.last_modified = datetime.fromtimestamp(last_modified, tz=timezone.utc)
            self.db.flush()

    def _compute_dir_stats(self, repo_id: int, root: Path, rel_dir: str) -> dict:
        """Recursively compute file_count, total_size, last_modified for a directory."""
        full = root / rel_dir
        file_count = 0
        total_size = 0
        last_modified = 0.0

        for dirpath, _, filenames in os.walk(full):
            for fn in filenames:
                fp = os.path.join(dirpath, fn)
                try:
                    st = os.stat(fp)
                    file_count += 1
                    total_size += st.st_size
                    last_modified = max(last_modified, st.st_mtime)
                except OSError:
                    continue

        return {"file_count": file_count, "total_size": total_size, "last_modified": last_modified}
