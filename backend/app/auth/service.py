from __future__ import annotations

import logging
from fastapi import HTTPException
from sqlalchemy.orm import Session
from backend.app.services.user_service import create_user, authenticate_user
from backend.app.schemas.user import UserRegisterPayload
from backend.app.models.user import User
from backend.app.core.security import validate_password_strength
from backend.app.core.tokens import create_access_token
from backend.app.auth.tokens import create_refresh_token, verify_refresh_token, rotate_refresh_token, revoke_refresh_token_by_jti
from backend.app.auth.rate_limit import record_login_failure, reset_login_failures, is_blocked
from backend.app.auth.audit import log_event
from backend.app.services.storage_registry import register_user_storage, get_registry_for_user
from backend.app.core.storage_abstraction import validate_storage_path

logger = logging.getLogger(__name__)


async def register_user(db: Session, payload: UserRegisterPayload, ip: str | None = None):
    # Validate passwords
    if payload.password != payload.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    if not validate_password_strength(payload.password):
        raise HTTPException(status_code=400, detail="Account password does not meet strength requirements")
    if not validate_password_strength(payload.vault_password):
        raise HTTPException(status_code=400, detail="Vault password does not meet strength requirements")

    try:
        db_user = create_user(db, payload)
        if not db_user:
            log_event("registration_failed", None, ip, {"reason": "username_taken"})
            raise HTTPException(status_code=400, detail="Username already registered")

        # Resolve canonical storage_root from payload, accepting deprecated aliases.
        storage_root = (
            payload.storage_root
            or payload.data_path
            or payload.personal_storage_path
        )
        if not storage_root:
            raise HTTPException(status_code=400, detail="Storage root is required for registration")

        validated_root = validate_storage_path(storage_root)
        register_user_storage(db, db_user.id, str(validated_root))

        # on success, log and create tokens
        log_event("registration_success", db_user.id, ip, {})

        # create tokens
        access = await create_access_token({"sub": str(db_user.id)})
        refresh = await create_refresh_token(db_user.id)

        return {"access_token": access, "token_type": "bearer", "refresh_token": refresh["token"], "user": db_user}

    except HTTPException:
        raise
    except Exception as e:
        # On any filesystem/storage failure, ensure DB user removed if partially created
        logger.exception("Registration failure: %s", e)
        # try to find and remove user
        try:
            if 'db_user' in locals() and db_user:
                registry = get_registry_for_user(db, db_user.id)
                if registry:
                    db.delete(registry)
                db.delete(db_user)
                db.commit()
        except Exception:
            db.rollback()
        log_event("registration_failed", None, ip, {"error": str(e)})
        raise HTTPException(status_code=500, detail="Registration failed")


async def login_user_service(db: Session, username: str, password: str, ip: str | None = None):
    # brute-force protection
    blocked = await is_blocked(ip or "", username)
    if blocked:
        log_event("login_blocked", None, ip, {"username": username})
        raise HTTPException(status_code=429, detail="Too many login attempts. Try again later.")

    user = authenticate_user(db, username, password)
    if not user:
        # record failure
        await record_login_failure(ip or "", username)
        log_event("login_failure", None, ip, {"username": username})
        raise HTTPException(status_code=401, detail="Invalid username or password")

    # reset failures
    await reset_login_failures(ip or "", username)

    # create tokens
    access = await create_access_token({"sub": str(user.id)})
    refresh = await create_refresh_token(user.id)

    log_event("login_success", user.id, ip, {})

    return {"access_token": access, "token_type": "bearer", "refresh_token": refresh["token"], "user": user}


async def logout_user(db: Session, refresh_token: str | None, ip: str | None = None):
    # validate refresh token and revoke
    if not refresh_token:
        return True
    info = await verify_refresh_token(refresh_token)
    if info:
        await revoke_refresh_token_by_jti(info["jti"])
        log_event("logout", info.get("user_id"), ip, {})
    return True


async def refresh_tokens(db: Session, refresh_token: str, ip: str | None = None):
    info = await verify_refresh_token(refresh_token)
    if not info:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    # rotate
    new = await rotate_refresh_token(info["jti"], info["user_id"])
    access = await create_access_token({"sub": str(info["user_id"]) })
    log_event("refresh", info["user_id"], ip, {})
    return {"access_token": access, "token_type": "bearer", "refresh_token": new["token"]}
