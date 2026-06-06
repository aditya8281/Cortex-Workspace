from __future__ import annotations

from typing import Optional
from sqlalchemy.orm import Session
from backend.app.models.user import User
from backend.app.models.user_profile import UserProfile, UserPreferences
from backend.app.schemas.profile import UserProfileSchema, UserProfileUpdateSchema
from backend.app.services.profile_validator import validate_profile_payload
from backend.app.services.profile_audit import record_profile_audit
from backend.app.core.redis import redis_cache
from backend.app.core import storage
import json
import os


CACHE_PREFIX = "profile:"


def _cache_key(user_id: int) -> str:
    return f"{CACHE_PREFIX}{user_id}"


def to_schema(user: User) -> UserProfileSchema:
    # prefer dedicated profile record, fallback to user fields
    try:
        profile = user.profile
    except Exception:
        profile = None

    if profile:
        prefs = None
        try:
            from backend.app.db.session import SessionLocal
            db = SessionLocal()
            up = db.query(UserPreferences).filter(UserPreferences.user_id == user.id).first()
            if up:
                prefs = up.prefs
            db.close()
        except Exception:
            prefs = None

        return UserProfileSchema(
            full_name=profile.full_name,
            nickname=profile.nickname,
            bio=profile.bio,
            description=profile.description,
            profile_photo=profile.profile_photo,
            handles=profile.handles,
            visibility=profile.visibility,
            preferences=prefs,
        )

    # legacy fallback
    return UserProfileSchema(
        full_name=user.full_name,
        nickname=getattr(user, "nickname", None),
        bio=getattr(user, "bio", None),
        description=getattr(user, "description", None),
        profile_photo=getattr(user, "profile_photo", None),
        handles=getattr(user, "handles", None),
        visibility="public",
        preferences=getattr(user, "preferences", None),
    )


def get_cached_profile(user_id: int) -> Optional[dict]:
    key = _cache_key(user_id)
    # redis_cache is async; call directly if loop available
    import asyncio
    loop = asyncio.get_event_loop()
    try:
        data = loop.run_until_complete(redis_cache.get(key))
        return data
    except Exception:
        return None


def set_cached_profile(user_id: int, data: dict):
    key = _cache_key(user_id)
    import asyncio
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(redis_cache.set(key, data, expire_seconds=300))
    except Exception:
        pass


def invalidate_cached_profile(user_id: int):
    key = _cache_key(user_id)
    import asyncio
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(redis_cache.delete(key))
    except Exception:
        pass


def update_profile(db: Session, user: User, payload: UserProfileUpdateSchema, ip: str | None = None) -> UserProfileSchema:
    # validate
    validate_profile_payload(payload)

    # ensure profile record exists
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    if not profile:
        profile = UserProfile(user_id=user.id, full_name=user.full_name)
        db.add(profile)

    # capture before values
    before = {
        "full_name": profile.full_name,
        "nickname": profile.nickname,
        "bio": profile.bio,
        "description": profile.description,
        "profile_photo": profile.profile_photo,
        "handles": profile.handles,
        "visibility": profile.visibility,
    }

    # apply updates
    if payload.full_name is not None:
        profile.full_name = payload.full_name
    if payload.nickname is not None:
        profile.nickname = payload.nickname
    if payload.bio is not None:
        profile.bio = payload.bio
    if payload.description is not None:
        profile.description = payload.description
    if payload.profile_photo is not None:
        profile.profile_photo = payload.profile_photo
    if payload.handles is not None:
        profile.handles = payload.handles
    if payload.visibility is not None:
        profile.visibility = payload.visibility

    # preferences
    if payload.preferences is not None:
        prefs = db.query(UserPreferences).filter(UserPreferences.user_id == user.id).first()
        if not prefs:
            prefs = UserPreferences(user_id=user.id)
            db.add(prefs)
        prefs.prefs = payload.preferences

    db.commit()
    db.refresh(profile)

    # audit changed fields
    after = {
        "full_name": profile.full_name,
        "nickname": profile.nickname,
        "bio": profile.bio,
        "description": profile.description,
        "profile_photo": profile.profile_photo,
        "handles": profile.handles,
        "visibility": profile.visibility,
    }

    for field, old in before.items():
        new = after.get(field)
        if (old or "") != (new or ""):
            record_profile_audit(db, user.id, field, old, new, ip)

    # mirror profile_photo to legacy user field for backward compatibility
    try:
        user.profile_photo = profile.profile_photo
        db.add(user)
        db.commit()
    except Exception:
        db.rollback()

    # invalidate cache
    invalidate_cached_profile(user.id)

    schema = to_schema(user)
    # cache schema
    try:
        set_cached_profile(user.id, json.loads(schema.model_dump_json()))
    except Exception:
        pass

    return schema

