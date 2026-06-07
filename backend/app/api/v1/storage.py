from __future__ import annotations

import os
import shutil

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, get_db
from backend.app.models.user import User
from backend.app.services.storage_registry import get_registry_for_user, register_user_storage
from backend.app.core.storage_abstraction import validate_storage_path

router = APIRouter()


class RegisterPayload(BaseModel):
    storage_root: str


class PathCheckResponse(BaseModel):
    exists: bool
    writable: bool
    free_space_bytes: int
    estimated_setup_bytes: int
    permission_ok: bool
    details: dict | None = None


@router.post("/check", response_model=PathCheckResponse)
def check_storage_path(
    payload: RegisterPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    path = validate_storage_path(payload.storage_root)
    exists = path.exists()
    writable = False
    free_space = 0
    details: dict[str, object] = {}

    try:
        candidate = path if exists else path.parent
        writable = os.access(candidate, os.W_OK)
        du = shutil.disk_usage(candidate)
        free_space = du.free
    except Exception as exc:
        details["error"] = str(exc)

    estimated_setup = 1024 * 1024
    permission_ok = writable and (exists or os.access(path.parent, os.W_OK))

    return PathCheckResponse(
        exists=exists,
        writable=writable,
        free_space_bytes=free_space,
        estimated_setup_bytes=estimated_setup,
        permission_ok=permission_ok,
        details=details or None,
    )


@router.post("")
def register_storage(
    payload: RegisterPayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        entry = register_user_storage(db, current_user.id, payload.storage_root)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return {
        "storage_root": entry.storage_root,
        "profile_path": entry.profile_path,
        "vault_path": entry.vault_path,
        "exports_path": entry.exports_path,
        "workspace_path": entry.workspace_path,
        "memory_snapshots_path": entry.memory_snapshots_path,
    }


@router.get("")
def get_my_storage(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    reg = get_registry_for_user(db, current_user.id)
    if not reg:
        raise HTTPException(status_code=404, detail="No storage registered for user")
    return {
        "storage_root": reg.storage_root,
        "profile_path": reg.profile_path,
        "vault_path": reg.vault_path,
        "exports_path": reg.exports_path,
        "workspace_path": reg.workspace_path,
        "memory_snapshots_path": reg.memory_snapshots_path,
    }

