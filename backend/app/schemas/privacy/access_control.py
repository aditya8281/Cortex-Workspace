"""Access control schemas for API contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AccessPolicyCreate(BaseModel):
    """Input schema for creating access policies."""

    name: str = Field(..., description="Policy name")
    description: str | None = None
    resource_type: str = Field(..., description="Resource type or *")
    action: str = Field(..., description="Action or *")
    effect: str = Field(..., description="allow or deny")
    conditions: dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(0)


class AccessPolicyResponse(BaseModel):
    """Output schema for access policies."""

    id: int
    name: str
    description: str | None = None
    resource_type: str
    action: str
    effect: str
    conditions: dict[str, Any]
    priority: int
    enabled: int
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class RoleCreate(BaseModel):
    """Input schema for creating roles."""

    name: str = Field(..., description="Role name")
    description: str | None = None


class RoleResponse(BaseModel):
    """Output schema for roles."""

    id: int
    name: str
    description: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PermissionResponse(BaseModel):
    """Output schema for permissions."""

    id: int
    resource_type: str
    action: str
    description: str | None = None

    model_config = {"from_attributes": True}
