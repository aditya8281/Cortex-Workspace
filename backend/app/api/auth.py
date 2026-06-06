from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from backend.app.api.deps import get_db, get_current_user
from backend.app.schemas.user import (
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
    UserRegisterPayload,
    MeUpdate
)
from backend.app.services.user_service import create_user, login_user, delete_user
from backend.app.models.user import User
from backend.app.core.security import hash_password, verify_password, validate_password_strength
from backend.app.models.user import User
from fastapi import Query

router = APIRouter()


@router.post("/api/auth/register", response_model=TokenResponse)
def register(payload: UserRegisterPayload, db: Session = Depends(get_db)):
    # Validate confirm password matches password
    if payload.password != payload.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    # Validate password strength
    if not validate_password_strength(payload.password):
        raise HTTPException(status_code=400, detail="Account password does not meet strength requirements")

    # Validate vault password strength
    if not validate_password_strength(payload.vault_password):
        raise HTTPException(status_code=400, detail="Vault password does not meet strength requirements")

    db_user = create_user(db, payload)
    if not db_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    token_data = login_user(db, db_user.username, payload.password)
    if not token_data:
        raise HTTPException(status_code=500, detail="Registration succeeded but session creation failed")

    return token_data


@router.post("/api/auth/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    token_data = login_user(db, payload.username, payload.password)
    if not token_data:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return token_data


@router.get("/api/auth/username-available")
def username_available(username: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == username).first()
    return {"available": existing is None}


@router.get("/api/auth/me", response_model=UserResponse)
def get_me(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # On login, attempt to resolve any registered user storage and expose the storage root
    try:
        from backend.app.services.storage_registry import get_registry_for_user
        reg = get_registry_for_user(db, current_user.id)
        if reg:
            # expose canonical data_path and keep legacy field in sync
            current_user.data_path = reg.storage_root
            current_user.personal_storage_path = reg.storage_root
    except Exception:
        pass
    return UserResponse.model_validate(current_user)


@router.put("/api/auth/me", response_model=UserResponse)
def update_me(payload: MeUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Check current password first if client is updating sensitive credentials
    if payload.password is not None or payload.username is not None or payload.vault_password is not None:
        if not payload.current_password:
            raise HTTPException(status_code=400, detail="Current password is required to change credentials")
        if not verify_password(payload.current_password, current_user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid current password")

    if payload.full_name is not None:
        current_user.full_name = payload.full_name

    if payload.nickname is not None:
        current_user.nickname = payload.nickname

    if payload.bio is not None:
        current_user.bio = payload.bio

    if payload.description is not None:
        current_user.description = payload.description

    if payload.profile_photo is not None:
        current_user.profile_photo = payload.profile_photo

    if payload.handles is not None:
        current_user.handles = payload.handles

    if payload.preferences is not None:
        current_user.preferences = payload.preferences

    if payload.username is not None:
        existing_username = db.query(User).filter(User.username == payload.username, User.id != current_user.id).first()
        if existing_username:
            raise HTTPException(status_code=400, detail="Username already registered")
        current_user.username = payload.username

    if payload.password is not None:
        if not validate_password_strength(payload.password):
            raise HTTPException(status_code=400, detail="Password does not meet strength requirements")
        current_user.hashed_password = hash_password(payload.password)

    if payload.vault_password is not None:
        if not validate_password_strength(payload.vault_password):
            raise HTTPException(status_code=400, detail="Vault password does not meet strength requirements")
        current_user.vault_password_hash = hash_password(payload.vault_password)

    db.commit()
    db.refresh(current_user)
    return UserResponse.model_validate(current_user)


class AccountDeletePayload(BaseModel):
    password: str
    confirm: bool = False


@router.delete("/api/auth/me")
def delete_me(
    payload: AccountDeletePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not verify_password(payload.password, current_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid account password")

    if not payload.confirm:
        return {
            "confirm_required": True,
            "message": "Please confirm if you want to permanently delete your account. This action is irreversible.",
            "offers": {
                "export_vault_url": "/api/v1/vault/export",
                "export_crtx_url": "/api/v1/me/export-crtx"
            }
        }

    success = delete_user(db, current_user.id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete user")
    return {"message": "User deleted"}
