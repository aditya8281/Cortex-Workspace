from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from backend.app.api.deps import get_db, get_current_user
from backend.app.schemas.user import TokenResponse, UserCreate, UserLogin, UserResponse
from backend.app.services.user_service import create_user, login_user, delete_user
from backend.app.models.user import User
from backend.app.core.security import hash_password, validate_password_strength

router = APIRouter()


@router.post("/api/auth/register", response_model=TokenResponse)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    # ensure role cannot be set by client; service determines first user admin
    payload.role = "user"
    # validate password strength
    if not validate_password_strength(payload.password):
        raise HTTPException(status_code=400, detail="Password does not meet strength requirements")

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


class MeUpdate(BaseModel):
    username: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None


@router.get("/api/auth/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)


@router.put("/api/auth/me", response_model=UserResponse)
def update_me(payload: MeUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if payload.full_name is not None:
        current_user.full_name = payload.full_name

    if payload.username is not None:
        existing_username = db.query(User).filter(User.username == payload.username, User.id != current_user.id).first()
        if existing_username:
            raise HTTPException(status_code=400, detail="Username already registered")
        current_user.username = payload.username

    if payload.password is not None:
        if not validate_password_strength(payload.password):
            raise HTTPException(status_code=400, detail="Password does not meet strength requirements")
        current_user.hashed_password = hash_password(payload.password)

    db.commit()
    db.refresh(current_user)
    return UserResponse.model_validate(current_user)


@router.delete("/api/auth/me")
def delete_me(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    success = delete_user(db, current_user.id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete user")
    return {"message": "User deleted"}
