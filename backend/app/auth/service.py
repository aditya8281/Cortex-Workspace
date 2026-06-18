from __future__ import annotations

import logging
import time

from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.app.auth.audit import log_event
from backend.app.auth.rate_limit import (
    is_blocked_sync,
    record_login_failure_sync,
    reset_login_failures_sync,
)
from backend.app.core.security import create_access_token as _create_access_token_sync
from backend.app.core.security import validate_password_strength
from backend.app.core.storage_abstraction import validate_storage_path
from backend.app.schemas.user import UserRegisterPayload
from backend.app.services.storage_registry import get_registry_for_user, register_user_storage
from backend.app.services.user_service import authenticate_user, create_user, serialize_user

logger = logging.getLogger(__name__)


# ── Register ───────────────────────────────────────────────────────────

def register_user(db: Session, payload: UserRegisterPayload, ip: str | None = None):
    """
    Synchronous registration — runs in FastAPI's threadpool so it never
    blocks the event loop.  All I/O (argon2, SQLite writes, filesystem) stays
    inside this thread.
    """
    t0 = time.monotonic()
    logger.info("[REGISTER] ENTER username=%s ip=%s", payload.username, ip)

    # ── password validation ──────────────────────────────────────────
    if payload.password != payload.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    if not validate_password_strength(payload.password):
        raise HTTPException(status_code=400, detail="Account password does not meet strength requirements")
    if not validate_password_strength(payload.vault_password):
        raise HTTPException(status_code=400, detail="Vault password does not meet strength requirements")
    logger.debug("[REGISTER] Passwords validated in %.2fs", time.monotonic() - t0)

    try:
        # ── DB user insert ──────────────────────────────────────────
        t_db = time.monotonic()
        logger.info("[REGISTER] BEFORE_DB_WRITE")
        db_user = create_user(db, payload)
        logger.info("[REGISTER] AFTER_DB_WRITE user_id=%s elapsed=%.2fs", getattr(db_user, 'id', None), time.monotonic() - t_db)

        if not db_user:
            log_event("registration_failed", None, ip, {"reason": "username_taken"}, db=db)
            raise HTTPException(status_code=400, detail="Username already registered")

        # ── storage registration (filesystem I/O) ───────────────────
        t_fs = time.monotonic()
        storage_root = (
            payload.storage_root
            or payload.data_path
            or payload.personal_storage_path
        )
        if not storage_root:
            raise HTTPException(status_code=400, detail="Storage root is required for registration")

        validated_root = validate_storage_path(storage_root)
        register_user_storage(db, db_user.id, str(validated_root))
        logger.debug("[REGISTER] Storage registered in %.2fs", time.monotonic() - t_fs)

        # ── audit (uses request db session) ─────────────────────────
        log_event("registration_success", db_user.id, ip, {}, db=db)

        # ── JWT + refresh token ─────────────────────────────────────
        from backend.app.auth.tokens import create_refresh_token_sync
        t_tok = time.monotonic()
        access = _create_access_token_sync({"sub": str(db_user.id)})
        refresh = create_refresh_token_sync(db_user.id)
        logger.debug("[REGISTER] Tokens created in %.2fs", time.monotonic() - t_tok)

        logger.info("[REGISTER] SUCCESS user_id=%s total=%.2fs", db_user.id, time.monotonic() - t0)
        return {
            "access_token": access,
            "token_type": "bearer",
            "refresh_token": refresh["token"],
            "user": serialize_user(db, db_user),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("[REGISTER] FAILURE %s", e)
        try:
            if 'db_user' in locals() and db_user:
                registry = get_registry_for_user(db, db_user.id)
                if registry:
                    db.delete(registry)
                db.delete(db_user)
                db.commit()
        except Exception:
            db.rollback()
        log_event("registration_failed", None, ip, {"error": str(e)}, db=db)
        raise HTTPException(status_code=500, detail="Registration failed")


# ── Login ──────────────────────────────────────────────────────────────

def login_user_service(db: Session, username: str, password: str, ip: str | None = None):
    """
    Synchronous login — runs in FastAPI's threadpool so it never blocks
    the event loop.  Pure read-only path (fetch user → verify password →
    return token).  No filesystem side-effects.
    """
    t0 = time.monotonic()
    logger.info("[LOGIN] ENTER username=%s ip=%s", username, ip)

    # ── rate-limit check (Redis, fail-open) ──────────────────────────
    blocked = is_blocked_sync(ip or "", username)
    if blocked:
        log_event("login_blocked", None, ip, {"username": username}, db=db)
        logger.warning("[LOGIN] BLOCKED username=%s ip=%s", username, ip)
        raise HTTPException(status_code=429, detail="Too many login attempts. Try again later.")

    # ── DB lookup + password verify ──────────────────────────────────
    t_db = time.monotonic()
    logger.info("[LOGIN] BEFORE_DB_READ")
    user = authenticate_user(db, username, password)
    logger.info("[LOGIN] AFTER_DB_READ elapsed=%.2fs found=%s", time.monotonic() - t_db, user is not None)

    if not user:
        record_login_failure_sync(ip or "", username)
        log_event("login_failure", None, ip, {"username": username}, db=db)
        logger.warning("[LOGIN] INVALID_CREDENTIALS username=%s", username)
        raise HTTPException(status_code=401, detail="Invalid username or password")

    # ── reset rate-limit on success ──────────────────────────────────
    reset_login_failures_sync(ip or "", username)

    # ── tokens ───────────────────────────────────────────────────────
    from backend.app.auth.tokens import create_refresh_token_sync
    t_tok = time.monotonic()
    access = _create_access_token_sync({"sub": str(user.id)})
    refresh = create_refresh_token_sync(user.id)
    logger.debug("[LOGIN] Tokens created in %.2fs", time.monotonic() - t_tok)

    log_event("login_success", user.id, ip, {}, db=db)
    logger.info("[LOGIN] SUCCESS user_id=%s total=%.2fs", user.id, time.monotonic() - t0)

    return {
        "access_token": access,
        "token_type": "bearer",
        "refresh_token": refresh["token"],
        "user": serialize_user(db, user),
    }


# ── Logout ─────────────────────────────────────────────────────────────

async def logout_user(db: Session, refresh_token: str | None, ip: str | None = None):
    if not refresh_token:
        return True
    from backend.app.auth.tokens import revoke_refresh_token_by_jti, verify_refresh_token
    info = await verify_refresh_token(refresh_token)
    if info:
        await revoke_refresh_token_by_jti(info["jti"])
        log_event("logout", info.get("user_id"), ip, {}, db=db)
    return True


# ── Token refresh ──────────────────────────────────────────────────────

async def refresh_tokens(db: Session, refresh_token: str, ip: str | None = None):
    from backend.app.auth.tokens import rotate_refresh_token, verify_refresh_token
    from backend.app.core.tokens import create_access_token_async
    info = await verify_refresh_token(refresh_token)
    if not info:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    new = await rotate_refresh_token(info["jti"], info["user_id"])
    if new is None:
        # Token was already revoked — this is a reuse attempt.
        # Revoke ALL tokens for this user as a safety measure.
        log_event("refresh_reuse_detected", info["user_id"], ip,
                  {"jti": info["jti"]}, db=db)
        raise HTTPException(status_code=401, detail="Refresh token already used")
    access = await create_access_token_async({"sub": str(info["user_id"])})
    log_event("refresh", info["user_id"], ip, {}, db=db)
    return {"access_token": access, "token_type": "bearer", "refresh_token": new["token"]}
