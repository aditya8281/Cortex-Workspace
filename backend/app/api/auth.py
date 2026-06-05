from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db
from backend.app.schemas.user import TokenResponse, UserCreate, UserLogin
from backend.app.services.user_service import create_user, login_user

router = APIRouter()


@router.post("/api/auth/register", response_model=TokenResponse)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    db_user = create_user(db, payload)
    if not db_user:
        raise HTTPException(status_code=400, detail="Username or email already registered")

    token_data = login_user(db, payload.username, payload.password)
    if not token_data:
        raise HTTPException(status_code=500, detail="Registration succeeded but session creation failed")

    return token_data


@router.post("/api/auth/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    token_data = login_user(db, payload.username, payload.password)
    if not token_data:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return token_data
