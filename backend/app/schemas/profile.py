from typing import Optional, Any
from pydantic import BaseModel


class UserProfileSchema(BaseModel):
    full_name: str
    nickname: str
    bio: Optional[str] = None
    description: Optional[str] = None
    profile_photo: Optional[str] = None
    handles: Optional[dict[str, Any]] = None


class UserProfileUpdateSchema(BaseModel):
    full_name: Optional[str] = None
    nickname: Optional[str] = None
    bio: Optional[str] = None
    description: Optional[str] = None
    profile_photo: Optional[str] = None
    handles: Optional[dict[str, Any]] = None
