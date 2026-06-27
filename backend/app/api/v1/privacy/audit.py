"""Privacy Audit Logging API — append-only audit trail endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, get_db
from backend.app.models.interaction.user import User
from backend.app.schemas.privacy.audit import AuditLogResponse
from backend.app.services.privacy.audit import AuditLoggingService

router = APIRouter()


@router.get("/logs", response_model=list[AuditLogResponse])
def get_my_audit_logs(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    action: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get current user's audit logs, ordered by newest first."""
    service = AuditLoggingService(db)
    return service.get_user_logs(current_user.id, limit=limit, offset=offset)


@router.get("/logs/count", response_model=dict)
def get_audit_log_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Count total audit logs for the current user."""
    service = AuditLoggingService(db)
    return {"count": service.count_user_logs(current_user.id)}


@router.get("/activity", response_model=list[dict])
def get_recent_activity(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get recent activity summary for the current user."""
    service = AuditLoggingService(db)
    logs = service.get_recent_activity(current_user.id, limit=limit)
    return [
        {
            "id": log.id,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "timestamp": log.timestamp.isoformat() if log.timestamp else None,
        }
        for log in logs
    ]
