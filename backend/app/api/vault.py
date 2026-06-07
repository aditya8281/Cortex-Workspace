from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.app.api.deps import get_current_user, get_current_user_optional
from backend.app.models.user import User
from backend.app.core.security import verify_password
from backend.app.core.storage_abstraction import get_user_storage

router = APIRouter()


class VaultUnlockPayload(BaseModel):
    password: str = Field(min_length=1, max_length=256)


def _dir_stats(path: Path) -> dict[str, int]:
    if not path.exists():
        return {"file_count": 0, "size_bytes": 0}
    file_count = 0
    size_bytes = 0
    for entry in path.rglob("*"):
        if entry.is_file():
            file_count += 1
            size_bytes += entry.stat().st_size
    return {"file_count": file_count, "size_bytes": size_bytes}


def _vault_payload(user: User | None, locked: bool) -> dict[str, object]:
    if user is None:
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "locked": True,
            "encrypted": True,
            "unlocked_by": None,
            "active_path": None,
            "is_paused": False,
            "total_size_bytes": 0,
            "categories": {},
            "vault_hint": "Vault is user-scoped and requires authentication.",
        }

    storage = get_user_storage(user.id)
    categories: dict[str, dict[str, int]] = {}
    total_size_bytes = 0
    for category in ["documents", "images", "certificates", "notes", "others", "metadata", "temp"]:
        stats = _dir_stats(storage.vault / category)
        categories[category] = stats
        total_size_bytes += stats["size_bytes"]

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "locked": locked,
        "encrypted": True,
        "unlocked_by": user.username if not locked else None,
        "active_path": str(storage.vault),
        "is_paused": False,
        "total_size_bytes": total_size_bytes,
        "categories": categories,
        "vault_hint": "Vault remains locked until password verification completes.",
    }


@router.get("/api/vault")
def read_vault(current_user: User | None = Depends(get_current_user_optional)):
    return _vault_payload(current_user, locked=True)


@router.post("/api/vault")
def unlock_vault(payload: VaultUnlockPayload, current_user: User = Depends(get_current_user)):
    if not current_user.vault_password_hash:
        raise HTTPException(status_code=400, detail="Vault password not set up")
    if not verify_password(payload.password, current_user.vault_password_hash):
        raise HTTPException(status_code=401, detail="Invalid vault password")

    return _vault_payload(current_user, locked=False)

