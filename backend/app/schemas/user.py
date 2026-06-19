from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class UserLogin(BaseModel):
    username: str = Field(min_length=1, max_length=128)
    password: str


class UserCreate(BaseModel):
    username: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=8)
    role: str = Field(default="user", min_length=1, max_length=32)
    full_name: str | None = None


class UserRegisterPayload(BaseModel):
    username: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=8)
    confirm_password: str = Field(min_length=8)
    full_name: str = Field(min_length=1)
    nickname: str = Field(min_length=1)
    bio: str | None = None
    description: str | None = None
    profile_photo: str | None = None
    handles: dict[str, Any] | None = None
    vault_password: str = Field(min_length=8)
    # Canonical field: users must provide exactly one storage root.
    storage_root: str | None = None
    # DEPRECATED aliases kept for backward-compatible API ingestion.
    data_path: str | None = None
    personal_storage_path: str | None = None
    preferences: dict[str, Any] | None = None


class UserResponse(BaseModel):
    id: int
    username: str | None = None
    full_name: str
    role: str
    nickname: str
    bio: str | None = None
    description: str | None = None
    profile_photo: str | None = None
    handles: dict[str, Any] | None = None
    storage_root: str | None = None
    github_username: str | None = None
    data_path: str | None = None
    personal_storage_path: str | None = None
    preferences: dict[str, Any] | None = None
    created_at: str | None = None
    updated_at: str | None = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def _serialize_datetime(cls, v: Any) -> str | None:
        if isinstance(v, datetime):
            return v.isoformat()
        return v


class UserUpdate(BaseModel):
    username: str | None = None
    full_name: str | None = None
    role: str | None = None


class MeUpdate(BaseModel):
    username: str | None = None
    full_name: str | None = None
    nickname: str | None = None
    bio: str | None = None
    description: str | None = None
    profile_photo: str | None = None
    handles: dict[str, Any] | None = None
    preferences: dict[str, Any] | None = None
    password: str | None = None
    current_password: str | None = None
    vault_password: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: str | None = None
    user: UserResponse | None = None
