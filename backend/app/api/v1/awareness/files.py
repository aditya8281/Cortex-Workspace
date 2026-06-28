"""Filesystem awareness API — scan directories, detect changes, get summaries."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.core.db import get_current_user, get_db
from backend.app.models.interaction.user import User
from backend.app.services.awareness.file_indexer import FilesystemIndexerService

router = APIRouter(prefix="/files", tags=["awareness-files"])


@router.post("/scan", response_model=dict[str, Any])
def scan_directory(
    directory: str = Query(..., min_length=1, max_length=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Scan a directory and index all files."""
    service = FilesystemIndexerService(db)
    files, stats = service.scan_directory(current_user.id, directory)
    return {
        "files_indexed": len(files),
        "stats": stats,
        "directory": directory,
    }


@router.get("/changes", response_model=dict[str, Any])
def detect_changes(
    directory: str = Query(..., min_length=1, max_length=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Detect file changes since last scan."""
    service = FilesystemIndexerService(db)
    changes = service.detect_changes(current_user.id, directory)
    return {
        "created": len(changes["created"]),
        "modified": len(changes["modified"]),
        "deleted": len(changes["deleted"]),
    }


@router.get("/summary", response_model=dict[str, Any])
def get_directory_summary(
    directory: str = Query(..., min_length=1, max_length=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a summary of files in a directory."""
    service = FilesystemIndexerService(db)
    return service.get_directory_summary(current_user.id, directory)
