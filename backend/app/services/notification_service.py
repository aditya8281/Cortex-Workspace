"""Notification service — create, list, mark read, delete."""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from backend.app.models.notification import Notification

logger = logging.getLogger(__name__)


def create_notification(
    db: Session,
    user_id: int,
    notification_type: str,
    title: str,
    message: str,
) -> Notification:
    """Create and persist a notification."""
    notif = Notification(
        user_id=user_id,
        type=notification_type,
        title=title,
        message=message,
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)
    logger.info("Notification created for user %d: %s", user_id, title)
    return notif


def get_notifications(
    db: Session,
    user_id: int,
    limit: int = 50,
    offset: int = 0,
    unread_only: bool = False,
) -> tuple[list[Notification], int, int]:
    """Return (notifications, total, unread_count)."""
    query = db.query(Notification).filter(Notification.user_id == user_id)
    if unread_only:
        query = query.filter(Notification.read == False)

    total = db.query(Notification).filter(Notification.user_id == user_id).count()
    unread_count = db.query(Notification).filter(
        Notification.user_id == user_id, Notification.read == False
    ).count()

    notifications = (
        query.order_by(Notification.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return notifications, total, unread_count


def mark_read(db: Session, notification_id: int, user_id: int) -> bool:
    """Mark a single notification as read. Returns True if found."""
    notif = db.query(Notification).filter(
        Notification.id == notification_id, Notification.user_id == user_id
    ).first()
    if not notif:
        return False
    notif.read = True
    db.commit()
    return True


def mark_all_read(db: Session, user_id: int) -> int:
    """Mark all unread notifications as read. Returns count updated."""
    count = (
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.read == False)
        .update({"read": True})
    )
    db.commit()
    return count


def delete_notification(db: Session, notification_id: int, user_id: int) -> bool:
    """Delete a notification. Returns True if found."""
    notif = db.query(Notification).filter(
        Notification.id == notification_id, Notification.user_id == user_id
    ).first()
    if not notif:
        return False
    db.delete(notif)
    db.commit()
    return True
