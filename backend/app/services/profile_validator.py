from __future__ import annotations

import re
from backend.app.schemas.profile import UserProfileUpdateSchema
from fastapi import HTTPException

# validation rules
NICKNAME_MAX = 64
BIO_MAX = 1024
HANDLE_RE = re.compile(r"^[a-zA-Z0-9_.-]{1,32}$")


def sanitize_text(val: str) -> str:
    # basic sanitize: trim and remove control chars
    if val is None:
        return val
    s = ''.join(ch for ch in val if ord(ch) >= 32)
    return s.strip()


def validate_handle_format(handles: dict) -> dict:
    clean = {}
    for k, v in (handles or {}).items():
        if not isinstance(k, str) or not isinstance(v, str):
            raise HTTPException(status_code=400, detail="Invalid handle format")
        if not HANDLE_RE.match(v):
            raise HTTPException(status_code=400, detail=f"Invalid handle value for {k}")
        clean[k] = v
    return clean


def validate_profile_payload(payload: UserProfileUpdateSchema):
    if payload.nickname is not None:
        nick = sanitize_text(payload.nickname)
        if len(nick) == 0 or len(nick) > NICKNAME_MAX:
            raise HTTPException(status_code=400, detail="Invalid nickname length")
        payload.nickname = nick

    if payload.bio is not None:
        bio = sanitize_text(payload.bio)
        if len(bio) > BIO_MAX:
            raise HTTPException(status_code=400, detail="Bio too long")
        payload.bio = bio

    if payload.full_name is not None:
        payload.full_name = sanitize_text(payload.full_name)

    if payload.description is not None:
        payload.description = sanitize_text(payload.description)

    if payload.handles is not None:
        payload.handles = validate_handle_format(payload.handles)

    if payload.visibility is not None:
        if payload.visibility not in {"public", "private", "system_only"}:
            raise HTTPException(status_code=400, detail="Invalid visibility value")

    return True
