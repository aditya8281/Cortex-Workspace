"""Notification endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, get_db
from backend.app.models.interaction.user import User
from backend.app.schemas.notification import NotificationListResponse, NotificationResponse
from backend.app.schemas.notification_extra import NotificationMarkReadResponse, NotificationOkResponse
from backend.app.services.interaction import notifications as notification_service

router = APIRouter()


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    limit: int = 50,
    offset: int = 0,
    unread_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List notifications for the current user."""
    notifications, total, unread_count = notification_service.get_notifications(
        db, current_user.id, limit, offset, unread_only
    )
    return NotificationListResponse(
        notifications=[NotificationResponse.model_validate(n) for n in notifications],
        total=total,
        unread_count=unread_count,
    )


@router.post("/{notification_id}/read", response_model=NotificationOkResponse)
async def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark a notification as read."""
    found = notification_service.mark_read(db, notification_id, current_user.id)
    if not found:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"ok": True}


@router.post("/read-all", response_model=NotificationMarkReadResponse)
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark all notifications as read."""
    count = notification_service.mark_all_read(db, current_user.id)
    return {"ok": True, "marked_read": count}


@router.delete("/{notification_id}", response_model=NotificationOkResponse)
async def delete_notification_endpoint(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a notification."""
    found = notification_service.delete_notification(db, notification_id, current_user.id)
    if not found:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"ok": True}
