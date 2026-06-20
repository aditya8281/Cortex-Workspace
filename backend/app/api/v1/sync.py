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

    return {
        "watching": file_watcher.watched_count,
        "pending_changes": file_watcher.pending_count,
        "status": "syncing" if file_watcher.pending_count > 0 else "idle",
    }
