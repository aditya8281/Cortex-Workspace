from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.app.api.deps import get_current_user, get_current_user_optional
from backend.app.models.user import User
from backend.app.services.memory_manager import memory_manager
from backend.app.core.security import verify_password

router = APIRouter()


class VaultUnlockPayload(BaseModel):
    password: str = Field(min_length=1, max_length=256)


def _get_category_stats() -> dict[str, dict[str, int]]:
    active_path = memory_manager.get_memory_path()
    categories: dict[str, dict[str, int]] = {}

    for category in memory_manager.CATEGORIES:
        category_path = active_path / category
        if category_path.exists():
            file_count = len([entry for entry in category_path.iterdir() if entry.is_file()])
            size_bytes = sum(entry.stat().st_size for entry in category_path.rglob("*") if entry.is_file())
        else:
            file_count = 0
            size_bytes = 0

        categories[category] = {
            "file_count": file_count,
            "size_bytes": size_bytes,
        }

    return categories


def _vault_payload(*, locked: bool, unlocked_by: str | None = None) -> dict[str, object]:
    active_path = memory_manager.get_memory_path()
    categories = _get_category_stats()
    total_size_bytes = sum(item["size_bytes"] for item in categories.values())

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "locked": locked,
        "encrypted": True,
        "unlocked_by": unlocked_by,
        "active_path": str(active_path),
        "is_paused": memory_manager.is_indexing_paused(),
        "total_size_bytes": total_size_bytes,
        "categories": categories,
        "vault_hint": "Vault remains locked until password verification completes.",
    }


@router.get("/api/vault")
def read_vault(current_user: User | None = Depends(get_current_user_optional)):
    return _vault_payload(locked=True, unlocked_by=None if current_user is None else current_user.username)


@router.post("/api/vault")
def unlock_vault(payload: VaultUnlockPayload, current_user: User = Depends(get_current_user)):
    if not verify_password(payload.password, current_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid password")

    return _vault_payload(locked=False, unlocked_by=current_user.username)
