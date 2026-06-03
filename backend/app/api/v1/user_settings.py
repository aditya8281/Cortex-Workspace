from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from backend.app.api.deps import get_current_user, get_db
from backend.app.models.user import User
from backend.app.models.user_settings import UserSettings
from backend.app.core.config import settings

import base64
import hashlib
from cryptography.fernet import Fernet

router = APIRouter()


def get_fernet() -> Fernet:
    key_hash = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(key_hash)
    return Fernet(fernet_key)


def encrypt_key(plain_text: str) -> bytes:
    if not plain_text:
        return b""
    f = get_fernet()
    return f.encrypt(plain_text.encode())


def decrypt_key(encrypted_bytes: bytes | None) -> str:
    if not encrypted_bytes or len(encrypted_bytes) == 0:
        return ""
    f = get_fernet()
    try:
        return f.decrypt(encrypted_bytes).decode()
    except Exception:
        return ""


def mask_key(plain_key: str) -> str:
    if not plain_key:
        return ""
    if len(plain_key) <= 8:
        return "****"
    return f"{plain_key[:4]}...{plain_key[-4:]}"


class UserSettingsSchema(BaseModel):
    api_base_url: Optional[str] = None
    api_key_masked: Optional[str] = None


class UserSettingsUpdateSchema(BaseModel):
    api_base_url: Optional[str] = None
    api_key: Optional[str] = None


@router.get("", response_model=UserSettingsSchema)
def get_user_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_settings = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()
    if not user_settings:
        return UserSettingsSchema(api_base_url=None, api_key_masked=None)

    plain_key = decrypt_key(user_settings.api_key_encrypted)
    return UserSettingsSchema(
        api_base_url=user_settings.api_base_url,
        api_key_masked=mask_key(plain_key) if plain_key else None
    )


@router.put("", response_model=UserSettingsSchema)
def update_user_settings(
    payload: UserSettingsUpdateSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_settings = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()
    if not user_settings:
        user_settings = UserSettings(user_id=current_user.id)
        db.add(user_settings)

    if payload.api_base_url is not None:
        user_settings.api_base_url = payload.api_base_url

    if payload.api_key is not None:
        existing_plain = decrypt_key(user_settings.api_key_encrypted)
        existing_masked = mask_key(existing_plain) if existing_plain else ""

        if payload.api_key == "":
            user_settings.api_key_encrypted = None
        elif payload.api_key == existing_masked:
            pass
        else:
            user_settings.api_key_encrypted = encrypt_key(payload.api_key)

    db.commit()
    db.refresh(user_settings)

    plain_key = decrypt_key(user_settings.api_key_encrypted)
    return UserSettingsSchema(
        api_base_url=user_settings.api_base_url,
        api_key_masked=mask_key(plain_key) if plain_key else None
    )
