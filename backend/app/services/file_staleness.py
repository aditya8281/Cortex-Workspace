"""Indexed file staleness check service."""

from __future__ import annotations

import os


def is_indexed_file_stale(repo_path: str, file_path: str) -> bool:
    """Return True if the indexed file no longer exists on disk.

    This is the service-layer replacement for IndexedFile.is_stale(),
    keeping the model clean of filesystem operations.
    """
    full_path = os.path.join(repo_path, file_path)
    try:
        os.stat(full_path)
        return False
    except (OSError, TypeError):
        return True
