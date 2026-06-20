from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.app.core.db import get_current_user
from backend.app.models.user import User

router = APIRouter()


@router.get("/sync/status")
async def get_sync_status(
    current_user: User = Depends(get_current_user),
):
    from backend.app.services.file_watcher import file_watcher

    state = file_watcher.sync_state
    return {
        "watching": state["watching"],
        "pending_changes": state["pending"],
        "indexed_files": state["indexed"],
        "errors": state["errors"],
        "status": state["status"],
        "last_sync": state["last_sync"],
    }
