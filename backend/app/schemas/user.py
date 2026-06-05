from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserLogin(BaseModel):
    username: str = Field(min_length=1, max_length=128)
    password: str


class UserCreate(BaseModel):
    username: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=8)
    role: str = Field(min_length=1, max_length=32)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    username: str | None = None
    email: str
    full_name: str
    role: str

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse | None = None
