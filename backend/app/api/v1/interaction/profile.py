"""Profile endpoint — view, update profile, and manage profile photo."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, get_db
from backend.app.core.db import get_current_user_optional
from backend.app.db.session import SessionLocal
from backend.app.models.interaction.user import User
from backend.app.models.memory.storage_registry import StorageRegistry
from backend.app.schemas.user import UserResponse
from backend.app.services.interaction.user import to_user_response

router = APIRouter()


# ── Helpers ──────────────────────────────────────────────────────────


def _photo_dir(user_id: int) -> Path:
    """Return (and lazily create) the directory for a user's profile photos."""
    # Try to resolve the user's registered storage root. If found, store
    # profile photos under `<storage_root>/profile/`. Otherwise fall back to
    # the system CortexMemory `photos/{user_id}` directory for backward
    # compatibility. For privacy reasons we now require a registered
    # `StorageRegistry` entry and will refuse to operate without it.
    try:
        db = SessionLocal()
        reg = db.query(StorageRegistry).filter(StorageRegistry.user_id == user_id).first()
    except Exception:
        reg = None
    finally:
        try:
            db.close()
        except Exception:
            pass

    if reg and reg.storage_root:
        d = Path(reg.storage_root).expanduser().resolve() / "profile"
        d.mkdir(parents=True, exist_ok=True)
        return d

    # Do not write profile photos into system-level CortexMemory; require
    # the user to register a storage root instead.
    from fastapi import HTTPException

    raise HTTPException(
        status_code=400,
        detail="No user storage registered. Please configure your storage root before uploading a profile photo.",
    )


def _avatar_path(user_id: int) -> Path:
    return _photo_dir(user_id) / f"user_{user_id}_avatar.webp"


def _thumb_path(user_id: int) -> Path:
    return _photo_dir(user_id) / "avatar_thumb.webp"


def _save_avatar(user_id: int, raw_bytes: bytes) -> str:
    """Process *raw_bytes* into a 256×256 WebP avatar + 64×64 thumbnail.

    Returns the filename stored in ``user.profile_photo``.
    """
    from PIL import Image

    img = Image.open(BytesIO(raw_bytes)).convert("RGBA")

    fname = f"user_{user_id}_avatar.webp"

    # Full-size avatar (256×256)
    avatar = img.copy()
    avatar.thumbnail((256, 256))
    avatar.save(_avatar_path(user_id), format="WEBP")

    # Thumbnail (64×64)
    thumb = img.copy()
    thumb.thumbnail((64, 64))
    thumb.save(_thumb_path(user_id), format="WEBP")

    return fname


# ── Schemas ──────────────────────────────────────────────────────────


class ProfileUpdate(BaseModel):
    full_name: str | None = None
    nickname: str | None = None
    bio: str | None = None
    description: str | None = None
    programming_languages: list[str] | None = None
    frameworks: list[str] | None = None
    current_projects: list[dict] | None = None
    contribution_style: str | None = None
    social_links: dict[str, Any] | None = None
    preferences: dict[str, Any] | None = None


# ── Profile CRUD ─────────────────────────────────────────────────────


@router.get("", response_model=UserResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the current user's profile."""
    return to_user_response(db, current_user)


@router.put("", response_model=UserResponse)
async def update_my_profile(
    body: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update the current user's profile fields."""
    update_data = body.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No valid fields provided")

    for key, value in update_data.items():
        setattr(current_user, key, value)

    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return to_user_response(db, current_user)


# ── Profile Photo ────────────────────────────────────────────────────


@router.post("/photo", response_model=dict)
async def upload_profile_photo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload and process a profile photo (JPEG, PNG, or WebP, max 2 MB)."""
    # Read in chunks to enforce size limit before loading entire file into memory
    MAX_PHOTO = 2 * 1024 * 1024  # 2 MB
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await file.read(64 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > MAX_PHOTO:
            raise HTTPException(status_code=413, detail="File too large (max 2 MB)")
        chunks.append(chunk)
    content = b"".join(chunks)
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")

    # Validate image type — check content_type header first, then PIL
    content_type = (file.content_type or "").lower()
    allowed_mimes = {"image/jpeg", "image/png", "image/webp", "image/jpg"}

    # If content_type says image/*, trust it for the allowed set
    if content_type and content_type not in allowed_mimes:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported image type: {content_type}. Use JPEG, PNG, or WebP.",
        )

    # Validate with PIL (auto-detect format from bytes)
    try:
        from PIL import Image

        img = Image.open(BytesIO(content))
        fmt = (img.format or "").lower()
        if fmt not in {"jpeg", "jpg", "png", "webp"}:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported image format: {fmt}. Use JPEG, PNG, or WebP.",
            )
    except HTTPException:
        raise
    except Exception:
        # If content_type was valid but PIL failed, give a clearer message
        if content_type in allowed_mimes:
            raise HTTPException(
                status_code=400,
                detail=f"File could not be read as an image. The content type was {content_type}, but the file may be corrupted or invalid.",
            )
        raise HTTPException(
            status_code=400,
            detail="Could not read image. Please upload a valid JPEG, PNG, or WebP file.",
        )

    fname = _save_avatar(current_user.id, content)

    current_user.profile_photo = fname
    db.add(current_user)
    db.commit()
    db.refresh(current_user)

    return {"profile_photo": current_user.profile_photo}


@router.get("/photo/{user_id}")
async def get_profile_photo(
    user_id: int,
    current_user: User | None = Depends(get_current_user_optional),
):
    """Serve a user's profile photo (optional auth — logged-in users see own photos, anonymous get 404)."""
    # Only serve own photos to authenticated users; anonymous users get 404
    if current_user and current_user.id != user_id:
        raise HTTPException(status_code=404, detail="Photo not found")

    avatar = _avatar_path(user_id)
    if not avatar.exists():
        raise HTTPException(status_code=404, detail="Profile photo not found")

    return FileResponse(str(avatar), media_type="image/webp", filename=avatar.name)


@router.get("/photo")
async def get_my_profile_photo(
    current_user: User = Depends(get_current_user),
):
    """Serve the current user's own profile photo (auth required)."""
    if not current_user.profile_photo:
        raise HTTPException(status_code=404, detail="No profile photo set")

    path = _avatar_path(current_user.id)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Profile photo not found")

    return FileResponse(str(path), media_type="image/webp", filename=path.name)


@router.delete("/photo", response_model=dict)
async def remove_profile_photo(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove the current user's profile photo."""
    for p in (_avatar_path(current_user.id), _thumb_path(current_user.id)):
        try:
            if p.exists():
                p.unlink()
        except Exception:
            pass

    current_user.profile_photo = None
    db.add(current_user)
    db.commit()
    db.refresh(current_user)

    return {"profile_photo": None}
