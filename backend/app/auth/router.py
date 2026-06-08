from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from backend.app.core.db import get_db
from backend.app.core.tokens import verify_access_token
from backend.app.models.user import User
from backend.app.schemas.user import (
    UserRegisterPayload, UserLogin, TokenResponse, UserResponse, MeUpdate,
)
from backend.app.auth import service as auth_service

oauth2_scheme = HTTPBearer()

router = APIRouter()


# ── IMPORTANT ──────────────────────────────────────────────────────
# register, login, and update_me are *sync* ``def`` (not ``async def``).
# FastAPI runs sync endpoints inside its thread-pool so the blocking
# work (argon2 hashing, SQLite writes, filesystem I/O) never touches
# the async event loop.  This is the PRIMARY fix for the hanging issue.
#
# refresh, logout, and get_me are lightweight (JWT decode + Redis) and
# stay ``async def`` — they don't block the event loop.
# ──────────────────────────────────────────────────────────────────


@router.post("/api/auth/register", response_model=TokenResponse)
def register(payload: UserRegisterPayload, request: Request, db: Session = Depends(get_db)):
    ip = request.client.host if request.client else None
    result = auth_service.register_user(db, payload, ip)
    return {
        "access_token": result["access_token"],
        "token_type": "bearer",
        "refresh_token": result.get("refresh_token"),
        "user": result["user"],
    }


@router.post("/api/auth/login", response_model=TokenResponse)
def login(payload: UserLogin, request: Request, db: Session = Depends(get_db)):
    ip = request.client.host if request.client else None
    return auth_service.login_user_service(db, payload.username, payload.password, ip)


@router.post("/api/auth/refresh", response_model=TokenResponse)
async def refresh(request: Request, db: Session = Depends(get_db)):
    body = await request.json()
    refresh_token = body.get("refresh_token")
    ip = request.client.host if request.client else None
    return auth_service.refresh_tokens(db, refresh_token, ip)


@router.post("/api/auth/logout")
async def logout(request: Request, db: Session = Depends(get_db)):
    body = await request.json()
    refresh_token = body.get("refresh_token")
    ip = request.client.host if request.client else None
    auth_service.logout_user(db, refresh_token, ip)
    return {"message": "Logged out"}


@router.get("/api/auth/me", response_model=UserResponse)
async def get_me(token: HTTPAuthorizationCredentials = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        user_id = verify_access_token(token.credentials)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return UserResponse.model_validate(user)


@router.put("/api/auth/me")
def update_me(
    body: MeUpdate,
    token: HTTPAuthorizationCredentials = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    try:
        user_id = verify_access_token(token.credentials)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    # support vault password update which requires current_password
    if body.vault_password is not None:
        if not body.current_password:
            raise HTTPException(status_code=400, detail="Current password required")
        from backend.app.core.security import verify_password, hash_password
        if not verify_password(body.current_password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid current password")
        user.vault_password_hash = hash_password(body.vault_password)
        db.add(user)
        db.commit()
        db.refresh(user)
        return {"message": "Vault password updated"}

    return {"message": "No changes"}
