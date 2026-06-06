from fastapi import APIRouter, Depends, Request, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from fastapi.responses import FileResponse

from backend.app.api.deps import get_current_user, get_db
from backend.app.models.user import User
from backend.app.schemas.profile import UserProfileSchema, UserProfileUpdateSchema
from backend.app.services import profile_service
from backend.app.core import storage
from backend.app.core.security import validate_password_strength
import os
from io import BytesIO
from PIL import Image

router = APIRouter()


@router.get("", response_model=UserProfileSchema)
async def get_my_profile(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # attempt cache first
    cached = profile_service.get_cached_profile(current_user.id)
    if cached:
        return UserProfileSchema.model_validate(cached)
    schema = profile_service.to_schema(current_user)
    try:
        profile_service.set_cached_profile(current_user.id, schema.model_dump())
    except Exception:
        pass
    return schema


@router.put("", response_model=UserProfileSchema)
async def update_my_profile(
    request: Request,
    payload: UserProfileUpdateSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ip = request.client.host if request.client else None
    return profile_service.update_profile(db, current_user, payload, ip)


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
@router.post("/photo")
async def upload_profile_photo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Validate content length (2MB max)
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")
    if len(content) > 2 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large")

    # Validate image type and process
    try:
        img = Image.open(BytesIO(content))
        img_format = img.format.lower()
        if img_format not in {"jpeg", "png", "webp", "jpg"}:
            raise HTTPException(status_code=400, detail="Unsupported image format")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image file")

    # normalize and resize
    profile_dir = storage.get_user_profile_root(current_user.id)
    profile_dir.mkdir(parents=True, exist_ok=True)
    avatar_path = profile_dir / "avatar.webp"
    thumb_path = profile_dir / "avatar_thumb.webp"

    # create profile sized image (256x256) and thumbnail (64x64)
    try:
        img = img.convert("RGBA")
        profile_img = img.copy()
        profile_img.thumbnail((256, 256))
        profile_img.save(avatar_path, format="WEBP")

        thumb = img.copy()
        thumb.thumbnail((64, 64))
        thumb.save(thumb_path, format="WEBP")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process image: {e}")

    # update profile record and mirror to user.profile_photo for compatibility
    try:
        from backend.app.models.user_profile import UserProfile
        profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
        if not profile:
            from backend.app.models.user_profile import UserProfile as UPModel
            profile = UPModel(user_id=current_user.id, full_name=current_user.full_name)
            db.add(profile)
        profile.profile_photo = "avatar.webp"
        db.add(profile)
        current_user.profile_photo = "avatar.webp"
        db.add(current_user)
        db.commit()
        db.refresh(current_user)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to save profile meta: {e}")

    # invalidate cache
    try:
        profile_service.invalidate_cached_profile(current_user.id)
    except Exception:
        pass

    return {"profile_photo": current_user.profile_photo}


@router.delete("/photo")
async def remove_profile_photo(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        profile_dir = storage.get_user_profile_root(current_user.id)
        for p in [profile_dir / "avatar.webp", profile_dir / "avatar_thumb.webp"]:
            try:
                if p.exists():
                    p.unlink()
            except Exception:
                pass
    except Exception:
        pass

    try:
        from backend.app.models.user_profile import UserProfile
        profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
        if profile:
            profile.profile_photo = None
            db.add(profile)
        current_user.profile_photo = None
        db.add(current_user)
        db.commit()
        db.refresh(current_user)
    except Exception:
        db.rollback()

    profile_service.invalidate_cached_profile(current_user.id)
    return {"profile_photo": None}


@router.get("/photo")
@router.get("/photo")
async def get_profile_photo(
    current_user: User = Depends(get_current_user),
):
    # prefer profile avatar path
    try:
        profile_dir = storage.get_user_profile_root(current_user.id)
        path = profile_dir / "avatar.webp"
        if not path.exists():
            # fallback to legacy stored filename
            if not current_user.profile_photo:
                raise HTTPException(status_code=404, detail="No profile photo set")
            path = profile_dir / current_user.profile_photo
    except Exception:
        raise HTTPException(status_code=403, detail="Access denied to profile photo")

    if not path.exists():
        raise HTTPException(status_code=404, detail="Profile photo not found")

    return FileResponse(str(path), media_type="image/webp", filename=path.name)


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
