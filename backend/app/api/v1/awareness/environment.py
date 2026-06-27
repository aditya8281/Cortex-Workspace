"""Environment awareness API — safe environment variables and system paths."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.app.core.db import get_current_user
from backend.app.models.interaction.user import User
from backend.app.services.awareness.env_scanner import EnvironmentScannerService

router = APIRouter(prefix="/environment", tags=["awareness-environment"])


@router.get("")
def get_environment(
    current_user: User = Depends(get_current_user),
):
    """Get safe (non-secret) environment variables."""
    service = EnvironmentScannerService()
    return service.get_environment(current_user.id)


@router.get("/paths")
def get_system_paths(
    current_user: User = Depends(get_current_user),
):
    """Get important system paths."""
    service = EnvironmentScannerService()
    return service.get_system_paths()
