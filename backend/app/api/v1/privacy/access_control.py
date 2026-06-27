"""Privacy Access Control API — RBAC, ABAC, and consent-gated endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, get_db
from backend.app.models.interaction.user import User
from backend.app.schemas.privacy.access_control import (
    PermissionResponse,
    RoleCreate,
    RoleResponse,
)
from backend.app.services.privacy.access_control import AccessControlService

router = APIRouter()


# ── RBAC Endpoints ─────────────────────────────────────────────────────


@router.get("/check", response_model=dict)
def check_access(
    resource_type: str = Query(..., description="Resource type to check"),
    action: str = Query(..., description="Action to check"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Check if current user has access to a resource/action via RBAC + ABAC."""
    service = AccessControlService(db)
    allowed = service.check_access(current_user.id, resource_type, action)
    return {
        "allowed": allowed,
        "resource_type": resource_type,
        "action": action,
        "user_id": current_user.id,
    }


@router.get("/roles", response_model=list[RoleResponse])
def get_my_roles(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get roles assigned to the current user."""
    service = AccessControlService(db)
    return service.get_user_roles(current_user.id)


@router.get("/permissions", response_model=list[PermissionResponse])
def get_my_permissions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get aggregated permissions for the current user from all assigned roles."""
    service = AccessControlService(db)
    return service.get_user_permissions(current_user.id)


# ── Admin Role Management ──────────────────────────────────────────────


@router.post("/roles/assign")
def assign_role(
    body: RoleCreate,
    target_user_id: int = Query(..., description="User ID to assign role to"),
    current_user: User = Depends(get_current_user),  # noqa: ARG001
    db: Session = Depends(get_db),
):
    """Assign a role to a user (admin operation)."""
    service = AccessControlService(db)
    try:
        service.assign_role(target_user_id, body.name)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"user_id": target_user_id, "role": body.name, "assigned": True}


@router.post("/roles/remove")
def remove_role(
    role_name: str = Query(..., description="Role name to remove"),
    target_user_id: int = Query(..., description="User ID to remove role from"),
    current_user: User = Depends(get_current_user),  # noqa: ARG001
    db: Session = Depends(get_db),
):
    """Remove a role from a user (admin operation)."""
    service = AccessControlService(db)
    service.remove_role(target_user_id, role_name)
    return {"user_id": target_user_id, "role": role_name, "removed": True}
