from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, get_db
from backend.app.models.user import User
from backend.app.services.storage_registry import register_user_storage, get_registry_for_user
import os
import shutil
from pydantic import BaseModel

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
def check_storage_path(payload: RegisterPayload, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    path = os.path.expanduser(payload.storage_root)
    exists = os.path.exists(path)
    writable = False
    free_space = 0
    details = {}
    try:
        if exists:
            writable = os.access(path, os.W_OK)
            du = shutil.disk_usage(path)
            free_space = du.free
            details["fstype"] = shutil.disk_usage(path)
        else:
            # for non-existent path, check parent
            parent = os.path.dirname(path) or "."
            writable = os.access(parent, os.W_OK)
            du = shutil.disk_usage(parent)
            free_space = du.free
    except Exception as e:
        details["error"] = str(e)

    # simple estimate: small skeleton ~16KB but allow 1MB buffer
    estimated_setup = 1024 * 1024

    # permission_ok: exists and writable or creatable by user
    permission_ok = writable and (exists or os.access(os.path.dirname(path) or ".", os.W_OK))

    return PathCheckResponse(
        exists=exists,
        writable=writable,
        free_space_bytes=free_space,
        estimated_setup_bytes=estimated_setup,
        permission_ok=permission_ok,
        details=details
    )

router = APIRouter()


class RegisterPayload(BaseModel):
    storage_root: str


@router.post("")
def register_storage(payload: RegisterPayload, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        entry = register_user_storage(db, current_user.id, payload.storage_root)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    # store pointer on user for convenience
    try:
        # store canonical pointer and keep legacy pointer in sync
        current_user.data_path = entry.storage_root
        current_user.personal_storage_path = entry.storage_root
        db.commit()
        db.refresh(current_user)
    except Exception:
        pass
    return {
        "storage_root": entry.storage_root,
        "profile_path": entry.profile_path,
        "vault_path": entry.vault_path,
        "exports_path": entry.exports_path,
        "activity_path": entry.activity_path,
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
        "activity_path": reg.activity_path,
    }
