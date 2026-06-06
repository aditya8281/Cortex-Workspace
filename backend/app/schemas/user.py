from typing import Optional, Any

from pydantic import BaseModel, ConfigDict, Field


class UserLogin(BaseModel):
    username: str = Field(min_length=1, max_length=128)
    password: str


class UserCreate(BaseModel):
    username: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=8)
    role: str = Field(default="user", min_length=1, max_length=32)
    full_name: Optional[str] = None


class UserRegisterPayload(BaseModel):
    username: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=8)
    confirm_password: str = Field(min_length=8)
    full_name: str = Field(min_length=1)
    nickname: str = Field(min_length=1)
    bio: Optional[str] = None
    description: Optional[str] = None
    profile_photo: Optional[str] = None
    handles: Optional[dict[str, Any]] = None
    vault_password: str = Field(min_length=8)
    # New canonical field for user-owned storage root (absolute path)
    # New canonical field for user-owned storage root (absolute path)
    data_path: Optional[str] = None
    # Legacy alias accepted for backward compatibility
    personal_storage_path: Optional[str] = None
    preferences: Optional[dict[str, Any]] = None


class UserResponse(BaseModel):
    id: int
    username: str | None = None
    full_name: str
    role: str
    nickname: str
    bio: Optional[str] = None
    description: Optional[str] = None
    profile_photo: Optional[str] = None
    handles: Optional[dict[str, Any]] = None
    data_path: Optional[str] = None
    personal_storage_path: Optional[str] = None
    preferences: Optional[dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    username: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[str] = None


class MeUpdate(BaseModel):
    username: Optional[str] = None
    full_name: Optional[str] = None
    nickname: Optional[str] = None
    bio: Optional[str] = None
    description: Optional[str] = None
    profile_photo: Optional[str] = None
    handles: Optional[dict[str, Any]] = None
    preferences: Optional[dict[str, Any]] = None
    password: Optional[str] = None
    current_password: Optional[str] = None
    vault_password: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse | None = None
