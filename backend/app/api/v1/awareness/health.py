"""System health awareness API — service health monitoring."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.core.db import get_current_user, get_db
from backend.app.models.interaction.user import User
from backend.app.services.awareness.health_monitor import SystemHealthService

router = APIRouter(prefix="/health", tags=["awareness-health"])


@router.get("", response_model=dict[str, Any])
def get_system_health(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get health status of all monitored services."""
    service = SystemHealthService(db)
    records = service.get_all_health()
    overall = service.get_overall_status()
    return {
        "services": [
            {
                "id": h.id,
                "service_name": h.service_name,
                "status": h.status,
                "response_time_ms": h.response_time_ms,
                "error_message": h.error_message,
                "last_check": h.last_check.isoformat() if h.last_check else None,
            }
            for h in records
        ],
        "overall_status": overall["overall_status"],
        "summary": overall,
    }


@router.get("/status", response_model=dict[str, Any])
def get_health_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get overall health status summary."""
    service = SystemHealthService(db)
    return service.get_overall_status()
