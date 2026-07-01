"""System snapshot monitoring endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.core.db import get_current_user, get_db
from backend.app.models.interaction.user import User
from backend.app.schemas.awareness.system_snapshot import (
    SystemSnapshotListResponse,
    SystemSnapshotResponse,
)
from backend.app.services.awareness.system_monitor import SystemMonitorService

router = APIRouter(prefix="/system", tags=["awareness-system"])


@router.post("/snapshot", response_model=SystemSnapshotResponse)
def take_snapshot(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Take a new system snapshot for the current user."""
    svc = SystemMonitorService(db)
    snap = svc.take_snapshot(user_id=current_user.id)
    return snap


@router.get("/recent", response_model=SystemSnapshotListResponse)
def get_recent(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get recent system snapshots for the current user."""
    svc = SystemMonitorService(db)
    snaps = svc.get_recent_snapshots(user_id=current_user.id, limit=limit)
    return {"snapshots": snaps, "total": len(snaps)}


@router.get("/anomalies", response_model=dict)
def get_anomalies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Detect anomalies from recent system snapshots."""
    svc = SystemMonitorService(db)
    return {"anomalies": svc.detect_anomalies()}
