from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, get_db
from backend.app.models.user import User
from backend.app.schemas.profile import UserProfileSchema, UserProfileUpdateSchema
from backend.app.services.profile_service import to_schema, update_profile

router = APIRouter()


@router.get("", response_model=UserProfileSchema)
def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return to_schema(current_user)


@router.put("", response_model=UserProfileSchema)
def update_my_profile(
    payload: UserProfileUpdateSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return update_profile(db, current_user, payload)


# --- Preferences endpoints -------------------------------------------------
from pydantic import BaseModel
from typing import Optional


class PreferencesSchema(BaseModel):
    interaction_style: Optional[str] = None
    response_style: Optional[str] = None


@router.put("/preferences")
def update_preferences(
    payload: PreferencesSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    prefs = current_user.preferences or {}
    if payload.interaction_style is not None:
        prefs["interaction_style"] = payload.interaction_style
    if payload.response_style is not None:
        prefs["response_style"] = payload.response_style

    current_user.preferences = prefs
    db.commit()
    db.refresh(current_user)
    # Keep backward-compatible preferences response while also returning full profile
    return {"preferences": current_user.preferences, "profile": to_schema(current_user)}


# --- Profile photo upload / remove ---------------------------------------
from fastapi import UploadFile, File, HTTPException
from backend.app.core import storage
import os
from fastapi.responses import FileResponse


@router.post("/photo")
async def upload_profile_photo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Basic validation
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")

    # store under users/<id>/profile with a deterministic user-prefixed filename
    import time
    ext = os.path.splitext(file.filename)[1] or ".bin"
    filename = f"user_{current_user.id}_{int(time.time())}{ext}"
    try:
        profile_dir = storage.get_user_profile_root(current_user.id)
        target = profile_dir / filename
        target.write_bytes(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save profile photo: {e}")

    # Save a relative path reference in the user model (filename only)
    current_user.profile_photo = str(filename)
    db.commit()
    db.refresh(current_user)
    return {"profile_photo": current_user.profile_photo}


@router.delete("/photo")
def remove_profile_photo(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user.profile_photo:
        raise HTTPException(status_code=404, detail="No profile photo set")

    try:
        profile_dir = storage.get_user_profile_root(current_user.id)
        target = profile_dir / current_user.profile_photo
        if target.exists():
            target.unlink()
    except Exception:
        pass

    current_user.profile_photo = None
    db.commit()
    db.refresh(current_user)
    return {"profile_photo": None}


@router.get("/photo")
def get_profile_photo(
    current_user: User = Depends(get_current_user),
):
    if not current_user.profile_photo:
        raise HTTPException(status_code=404, detail="No profile photo set")

    try:
        profile_dir = storage.get_user_profile_root(current_user.id)
        path = profile_dir / current_user.profile_photo
    except Exception:
        raise HTTPException(status_code=403, detail="Access denied to profile photo")

    if not path.exists():
        raise HTTPException(status_code=404, detail="Profile photo not found")

    return FileResponse(str(path), media_type="image/*", filename=current_user.profile_photo)


# --- Password management endpoints ---------------------------------------
from pydantic import BaseModel, Field
from backend.app.core.security import verify_password, hash_password


class PasswordChangePayload(BaseModel):
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=8)
    confirm_password: str = Field(min_length=8)


@router.post("/change-password")
def change_account_password(
    payload: PasswordChangePayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.new_password != payload.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid current password")

    current_user.hashed_password = hash_password(payload.new_password)
    db.commit()
    return {"message": "Password updated"}


class VaultPasswordChangePayload(BaseModel):
    account_password: str = Field(min_length=1)
    new_vault_password: str = Field(min_length=8)
    confirm_vault_password: str = Field(min_length=8)


@router.post("/change-vault-password")
def change_vault_password(
    payload: VaultPasswordChangePayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.new_vault_password != payload.confirm_vault_password:
        raise HTTPException(status_code=400, detail="Vault passwords do not match")
    # verify account password before allowing vault password change
    if not verify_password(payload.account_password, current_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid account password")

    current_user.vault_password_hash = hash_password(payload.new_vault_password)
    db.commit()
    return {"message": "Vault password updated"}
