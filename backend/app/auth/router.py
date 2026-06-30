from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from backend.app.auth import service as auth_service
from backend.app.core.config import settings
from backend.app.core.db import get_db
from backend.app.core.security import (
    revoke_access_token,
    revoke_refresh_token_by_jti,
    verify_access_token,
    verify_refresh_token,
)
from backend.app.models.interaction.user import User
from backend.app.schemas.interaction.user import (
    MeUpdate,
    TokenResponse,
    UserLogin,
    UserRegisterPayload,
    UserResponse,
)
from backend.app.services.interaction.user import _normalize_username, to_user_response

router = APIRouter()


def _secure_flag() -> bool:
    return settings.ENV not in ("development", "test")


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str | None = None) -> None:
    secure = _secure_flag()
    response.set_cookie(
        key="cortex_access",
        value=access_token,
        httponly=True,
        secure=secure,
        samesite="lax",
        path="/",
        max_age=60 * settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )
    if refresh_token:
        response.set_cookie(
            key="cortex_refresh",
            value=refresh_token,
            httponly=True,
            secure=secure,
            samesite="lax",
            path="/",
            max_age=604800,  # 7 days
        )


def _clear_auth_cookies(response: Response) -> None:
    secure = _secure_flag()
    response.set_cookie(
        key="cortex_access", value="", httponly=True, secure=secure, samesite="lax", path="/", max_age=0
    )
    response.set_cookie(
        key="cortex_refresh", value="", httponly=True, secure=secure, samesite="lax", path="/", max_age=0
    )


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


@router.post("/api/v1/auth/check-username", response_model=UsernameCheckResponse)
def check_username(payload: UsernameCheckRequest, db: Session = Depends(get_db)):
    """Real-time username availability check."""
    import re

    username = _normalize_username(payload.username)
    if len(username) < 3:
        return UsernameCheckResponse(available=False, message="Username must be at least 3 characters")
    if len(username) > 128:
        return UsernameCheckResponse(available=False, message="Username must be 128 characters or fewer")
    if not re.match(r"^[a-zA-Z0-9_-]+$", username):
        return UsernameCheckResponse(
            available=False, message="Username can only contain letters, numbers, hyphens, and underscores"
        )
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        return UsernameCheckResponse(available=False, message="Username is already taken")
    return UsernameCheckResponse(available=True, message="Username is available")


@router.post("/api/v1/auth/register", response_model=TokenResponse)
async def register(payload: UserRegisterPayload, request: Request, response: Response, db: Session = Depends(get_db)):
    ip = request.client.host if request.client else None
    result = await auth_service.register_user(db, payload, ip)
    _set_auth_cookies(response, result["access_token"], result.get("refresh_token"))
    return result


@router.post("/api/v1/auth/login", response_model=TokenResponse)
async def login(payload: UserLogin, request: Request, response: Response, db: Session = Depends(get_db)):
    ip = request.client.host if request.client else None
    result = await auth_service.login_user_service(db, payload.username, payload.password, ip)
    _set_auth_cookies(response, result["access_token"], result.get("refresh_token"))
    return result


class RefreshRequest(BaseModel):
    refresh_token: str | None = None


@router.post("/api/v1/auth/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    ip = request.client.host if request.client else None
    refresh_token = _get_refresh_token(request, body.refresh_token)
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token missing")
    result = await auth_service.refresh_tokens(db, refresh_token, ip)
    _set_auth_cookies(response, result["access_token"], result.get("refresh_token"))
    return result


@router.post("/api/v1/auth/logout", response_model=dict[str, Any])
async def logout(body: RefreshRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    ip = request.client.host if request.client else None
    refresh_token = _get_refresh_token(request, body.refresh_token)
    await auth_service.logout_user(db, refresh_token, ip)

    access_token = _get_token(request)
    if access_token:
        try:
            from jose import jwt

            payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            jti = payload.get("jti")
            if jti:
                await revoke_access_token(jti, expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        except Exception as e:
            logger.warning("Failed to revoke access token during logout: %s", e)

    _clear_auth_cookies(response)
    return {"message": "Logged out"}


@router.get("/api/v1/auth/ws-token")
async def get_ws_token(
    request: Request,
    db: Session = Depends(get_db),
):
    """Return the access token for WebSocket connections.
    Frontend cannot read httpOnly cookies, so this endpoint
    extracts the token and returns it for use in WS query params."""
    token = _get_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        user_id = verify_access_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Check user exists and is not deleted
    user = (
        db.query(User)
        .filter(
            User.id == int(user_id),
            User.deleted_at.is_(None),
        )
        .first()
    )
    if not user:
        raise HTTPException(status_code=401, detail="User not found or account deleted")

    return {"token": token}


@router.get("/api/v1/auth/me", response_model=UserResponse)
async def get_me(request: Request, db: Session = Depends(get_db)):
    token = _get_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Invalid token")
    try:
        user_id = verify_access_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(User).filter(User.id == int(user_id), User.deleted_at.is_(None)).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return to_user_response(db, user)


@router.put("/api/v1/auth/me", response_model=dict[str, Any])
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
    user = db.query(User).filter(User.id == int(user_id), User.deleted_at.is_(None)).first()
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


@router.delete("/api/v1/auth/me", response_model=dict[str, Any])
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

    # Revoke the current access token so stale JWTs stop working
    try:
        from jose import JWTError
        from jose import jwt as jose_jwt

        # Decode and revoke access token
        for key in settings.all_secret_keys:
            try:
                payload = jose_jwt.decode(token, key, algorithms=[settings.ALGORITHM])
                jti = payload.get("jti")
                if jti:
                    await revoke_access_token(jti, expires_in_minutes=30)
                break
            except JWTError:
                continue

        # Also revoke the refresh token from its cookie
        refresh_token = request.cookies.get("cortex_refresh")
        if refresh_token:
            refresh_data = await verify_refresh_token(refresh_token)
            if refresh_data and "jti" in refresh_data:
                await revoke_refresh_token_by_jti(refresh_data["jti"])
    except Exception:
        pass  # Best-effort revocation — soft-delete still blocks future logins

    # Clear vault cache
    try:
        from backend.app.services.memory.vault import _vault_cache_lock, _vault_passwords

        with _vault_cache_lock:
            _vault_passwords.pop(user.id, None)
    except Exception:
        pass

    # Soft delete: set deleted_at, don't remove data
    from backend.app.services.interaction.user import delete_user

    delete_user(db, user.id)

    _clear_auth_cookies(response)
    return {
        "message": "Account scheduled for deletion. You have 7 days to restore it before data is permanently removed."
    }


class RestoreAccountRequest(BaseModel):
    password: str


@router.post("/api/v1/auth/restore", response_model=dict[str, Any])
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

    from backend.app.core.security import verify_password

    if not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid password")

    from backend.app.services.interaction.user import restore_user

    restore_user(db, user.id)
    return {"message": "Account restored successfully"}
