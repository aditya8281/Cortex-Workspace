from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.auth import service as auth_service
from backend.app.core.config import settings
from backend.app.core.db import get_db
from backend.app.core.security import verify_access_token
from backend.app.models.user import User
from backend.app.schemas.user import (
    MeUpdate,
    TokenResponse,
    UserLogin,
    UserRegisterPayload,
    UserResponse,
)
from backend.app.services.user_service import _normalize_username, to_user_response

router = APIRouter()


def _secure_flag() -> bool:
    return settings.ENV not in ("development", "test")


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str | None = None) -> None:
    secure = _secure_flag()
    response.set_cookie(
        key="cortex_access", value=access_token, httponly=True, secure=secure, samesite="lax", path="/",
        max_age=60 * settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )
    if refresh_token:
        response.set_cookie(
            key="cortex_refresh", value=refresh_token, httponly=True, secure=secure, samesite="lax", path="/",
            max_age=604800,  # 7 days
        )


def _clear_auth_cookies(response: Response) -> None:
    secure = _secure_flag()
    response.set_cookie(key="cortex_access", value="", httponly=True, secure=secure, samesite="lax", path="/", max_age=0)
    response.set_cookie(key="cortex_refresh", value="", httponly=True, secure=secure, samesite="lax", path="/", max_age=0)


def _get_token(request: Request) -> str | None:
    auth = request.headers.get("Authorization")
    if auth and auth.startswith("Bearer "):
        return auth[7:]
    return request.cookies.get("cortex_access")


def _get_refresh_token(request: Request, body_refresh: str | None = None) -> str | None:
    if body_refresh:
        return body_refresh
    return request.cookies.get("cortex_refresh")


class UsernameCheckRequest(BaseModel):
    username: str


class UsernameCheckResponse(BaseModel):
    available: bool
    message: str


@router.post("/api/auth/check-username", response_model=UsernameCheckResponse)
def check_username(payload: UsernameCheckRequest, db: Session = Depends(get_db)):
    """Real-time username availability check."""
    import re
    username = _normalize_username(payload.username)
    if len(username) < 3:
        return UsernameCheckResponse(available=False, message="Username must be at least 3 characters")
    if len(username) > 128:
        return UsernameCheckResponse(available=False, message="Username must be 128 characters or fewer")
    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        return UsernameCheckResponse(available=False, message="Username can only contain letters, numbers, hyphens, and underscores")
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        return UsernameCheckResponse(available=False, message="Username is already taken")
    return UsernameCheckResponse(available=True, message="Username is available")


@router.post("/api/auth/register", response_model=TokenResponse)
async def register(payload: UserRegisterPayload, request: Request, response: Response, db: Session = Depends(get_db)):
    ip = request.client.host if request.client else None
    result = await auth_service.register_user(db, payload, ip)
    _set_auth_cookies(response, result["access_token"], result.get("refresh_token"))
    return result


@router.post("/api/auth/login", response_model=TokenResponse)
async def login(payload: UserLogin, request: Request, response: Response, db: Session = Depends(get_db)):
    ip = request.client.host if request.client else None
    result = await auth_service.login_user_service(db, payload.username, payload.password, ip)
    _set_auth_cookies(response, result["access_token"], result.get("refresh_token"))
    return result


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/api/auth/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    ip = request.client.host if request.client else None
    refresh_token = _get_refresh_token(request, body.refresh_token)
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token missing")
    result = await auth_service.refresh_tokens(db, refresh_token, ip)
    _set_auth_cookies(response, result["access_token"], result.get("refresh_token"))
    return result


@router.post("/api/auth/logout")
async def logout(body: RefreshRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    ip = request.client.host if request.client else None
    refresh_token = _get_refresh_token(request, body.refresh_token)
    await auth_service.logout_user(db, refresh_token, ip)
    _clear_auth_cookies(response)
    return {"message": "Logged out"}


@router.get("/api/auth/me", response_model=UserResponse)
async def get_me(request: Request, db: Session = Depends(get_db)):
    token = _get_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Invalid token")
    try:
        user_id = verify_access_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return to_user_response(db, user)


@router.put("/api/auth/me")
async def update_me(
    body: MeUpdate,
    request: Request,
    db: Session = Depends(get_db),
):
    token = _get_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Invalid token")
    try:
        user_id = verify_access_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    # support vault password update which requires current_password
    if body.vault_password is not None:
        if not body.current_password:
            raise HTTPException(status_code=400, detail="Current password required")
        from backend.app.core.security import hash_password, verify_password
        if not verify_password(body.current_password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid current password")
        user.vault_password_hash = hash_password(body.vault_password)
        db.add(user)
        db.commit()
        db.refresh(user)
        return {"message": "Vault password updated"}

    return {"message": "No changes"}


class DeleteAccountRequest(BaseModel):
    password: str


@router.delete("/api/auth/me")
async def delete_me(
    body: DeleteAccountRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """Soft-delete the current user's account. Requires password confirmation.
    Data is preserved for a 7-day grace period during which the account can be restored."""
    token = _get_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Invalid token")
    try:
        user_id = verify_access_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    if user.deleted_at:
        raise HTTPException(status_code=400, detail="Account already deleted")

    from backend.app.core.security import verify_password
    if not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid password")

    # Clear vault cache
    try:
        from backend.app.services.vault_service import _vault_cache_lock, _vault_passwords
        with _vault_cache_lock:
            _vault_passwords.pop(user.id, None)
    except Exception:
        pass

    # Soft delete: set deleted_at, don't remove data
    from backend.app.services.user_service import delete_user
    delete_user(db, user.id)

    _clear_auth_cookies(response)
    return {"message": "Account scheduled for deletion. You have 7 days to restore it before data is permanently removed."}


class RestoreAccountRequest(BaseModel):
    password: str | None = None


@router.post("/api/auth/restore")
async def restore_account(
    body: RestoreAccountRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """Restore a soft-deleted account within the 7-day grace period."""
    token = _get_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Invalid token")
    try:
        user_id = verify_access_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.deleted_at:
        raise HTTPException(status_code=400, detail="Account is not deleted or does not exist")

    # Check grace period
    from datetime import datetime, timezone
    grace_days = 7
    if user.deleted_at:
        deleted_at = user.deleted_at
        if deleted_at.tzinfo is None:
            deleted_at = deleted_at.replace(tzinfo=timezone.utc)
        elapsed = (datetime.now(timezone.utc) - deleted_at).days
        if elapsed > grace_days:
            raise HTTPException(status_code=400, detail="Grace period has expired. Account cannot be restored.")

    if body.password:
        from backend.app.core.security import verify_password
        if not verify_password(body.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid password")

    from backend.app.services.user_service import restore_user
    restore_user(db, user.id)
    return {"message": "Account restored successfully"}
