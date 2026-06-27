from __future__ import annotations

import logging
import time

from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.app.auth.audit import log_event
from backend.app.auth.rate_limit import is_blocked, record_login_failure, reset_login_failures
from backend.app.core.security import (
    create_access_token,
    create_refresh_token,
    revoke_refresh_token_by_jti,
    rotate_refresh_token,
    validate_password_strength,
    verify_refresh_token,
)
from backend.app.core.storage_abstraction import validate_storage_path
from backend.app.schemas.user import UserRegisterPayload
from backend.app.services.interaction.user import _normalize_username, authenticate_user, create_user, serialize_user
from backend.app.services.memory.storage_registry import get_registry_for_user, register_user_storage

logger = logging.getLogger(__name__)


# ── Register ───────────────────────────────────────────────────────────


async def register_user(db: Session, payload: UserRegisterPayload, ip: str | None = None):
    t0 = time.monotonic()
    logger.info("[REGISTER] ENTER username=%s ip=%s", payload.username, ip)

    if payload.password != payload.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    if not validate_password_strength(payload.password):
        raise HTTPException(status_code=400, detail="Account password does not meet strength requirements")
    if not validate_password_strength(payload.vault_password):
        raise HTTPException(status_code=400, detail="Vault password does not meet strength requirements")
    logger.debug("[REGISTER] Passwords validated in %.2fs", time.monotonic() - t0)

    # Validate storage path BEFORE creating user to avoid orphaned DB rows
    storage_root = payload.storage_root or payload.data_path or payload.personal_storage_path
    if not storage_root:
        from pathlib import Path

        storage_root = str(Path.home() / "CortexStorage" / (_normalize_username(payload.username) or "user"))
    try:
        validated_root = validate_storage_path(storage_root)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid storage root: {e}")

    try:
        t_db = time.monotonic()
        logger.info("[REGISTER] BEFORE_DB_WRITE")
        db_user = create_user(db, payload)
        logger.info(
            "[REGISTER] AFTER_DB_WRITE user_id=%s elapsed=%.2fs", getattr(db_user, "id", None), time.monotonic() - t_db
        )

        if not db_user:
            log_event("registration_failed", None, ip, {"reason": "username_taken"}, db=db)
            raise HTTPException(status_code=400, detail="Username already registered")

        t_fs = time.monotonic()
        register_user_storage(db, db_user.id, str(validated_root))
        logger.debug("[REGISTER] Storage registered in %.2fs", time.monotonic() - t_fs)

        log_event("registration_success", db_user.id, ip, {}, db=db)

        t_tok = time.monotonic()
        access = create_access_token({"sub": str(db_user.id)})
        refresh = await create_refresh_token(db_user.id)
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
            if "db_user" in locals() and db_user:
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


async def login_user_service(db: Session, username: str, password: str, ip: str | None = None):
    t0 = time.monotonic()
    logger.info("[LOGIN] ENTER username=%s ip=%s", username, ip)

    blocked = await is_blocked(ip or "", username)
    if blocked:
        log_event("login_blocked", None, ip, {"username": username}, db=db)
        logger.warning("[LOGIN] BLOCKED username=%s ip=%s", username, ip)
        raise HTTPException(status_code=429, detail="Too many login attempts. Try again later.")

    t_db = time.monotonic()
    logger.info("[LOGIN] BEFORE_DB_READ")
    user = authenticate_user(db, username, password)
    logger.info("[LOGIN] AFTER_DB_READ elapsed=%.2fs found=%s", time.monotonic() - t_db, user is not None)

    if not user:
        await record_login_failure(ip or "", username)
        log_event("login_failure", None, ip, {"username": username}, db=db)
        logger.warning("[LOGIN] INVALID_CREDENTIALS username=%s", username)
        raise HTTPException(status_code=401, detail="Invalid username or password")

    await reset_login_failures(ip or "", username)

    t_tok = time.monotonic()
    access = create_access_token({"sub": str(user.id)})
    refresh = await create_refresh_token(user.id)
    logger.debug("[LOGIN] Tokens created in %.2fs", time.monotonic() - t_tok)

    log_event("login_success", user.id, ip, {}, db=db)
    try:
        from backend.app.services.memory.vault import _vault_cache_lock, _vault_passwords

        with _vault_cache_lock:
            _vault_passwords.pop(user.id, None)
    except Exception:
        pass
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
    info = await verify_refresh_token(refresh_token)
    if info:
        await revoke_refresh_token_by_jti(info["jti"])
        log_event("logout", info.get("user_id"), ip, {}, db=db)
        # Ensure any cached vault password for this user is cleared on logout
        try:
            from backend.app.services.memory.vault import _vault_cache_lock, _vault_passwords

            user_id_raw = info.get("user_id")
            if user_id_raw is not None:
                with _vault_cache_lock:
                    _vault_passwords.pop(int(user_id_raw), None)
        except Exception:
            pass
    return True


# ── Token refresh ──────────────────────────────────────────────────────


async def refresh_tokens(db: Session, refresh_token: str, ip: str | None = None):
    from backend.app.core.security import create_access_token_async

    info = await verify_refresh_token(refresh_token)
    if not info:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    new = await rotate_refresh_token(info["jti"], info["user_id"])
    if new is None:
        # Token was already revoked — this is a reuse attempt.
        # Revoke ALL tokens for this user as a safety measure.
        log_event("refresh_reuse_detected", info["user_id"], ip, {"jti": info["jti"]}, db=db)
        # Revoke all active refresh tokens for this user
        from backend.app.core.redis import redis_cache

        try:
            await redis_cache.clear_pattern(f"refresh:user:{info['user_id']}:*")
        except Exception:
            logger.warning("Failed to revoke all tokens for user %d on reuse", info["user_id"])
        raise HTTPException(status_code=401, detail="Refresh token already used")
    access = await create_access_token_async({"sub": str(info["user_id"])})
    log_event("refresh", info["user_id"], ip, {}, db=db)
    # NOTE: We intentionally do NOT clear the vault password cache on token
    # refresh.  The vault is a separate authentication boundary — clearing it
    # on every access-token rotation forces users to re-enter their vault
    # password multiple times per session, which is a poor UX.  The cache is
    # cleared on explicit logout and lock instead.
    return {"access_token": access, "token_type": "bearer", "refresh_token": new["token"]}
