"""Immutable audit logging service — write-once, queryable."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.privacy.audit_log import AuditLog


class AuditLoggingService:
    """Append-only audit logging.

    Every significant system action flows through this service.
    Records are never updated — only created or retention-deleted.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def log(
        self,
        user_id: int,
        action: str,
        resource_type: str,
        resource_id: int | None = None,
        details: dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        session_id: str | None = None,
        success: bool = True,
        error_message: str | None = None,
        duration_ms: int | None = None,
    ) -> AuditLog:
        """Create an immutable audit log entry."""
        entry = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            timestamp=datetime.now(timezone.utc),
            success=1 if success else 0,
            error_message=error_message,
            duration_ms=duration_ms,
        )
        self.db.add(entry)
        self.db.flush()
        self.db.refresh(entry)
        return entry

    def get_user_logs(
        self,
        user_id: int,
        limit: int = 100,
        offset: int = 0,
        action_filter: str | None = None,
        resource_type_filter: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> list[AuditLog]:
        """Query audit logs for a user with filtering and pagination."""
        stmt = select(AuditLog).where(AuditLog.user_id == user_id)
        if action_filter:
            stmt = stmt.where(AuditLog.action == action_filter)
        if resource_type_filter:
            stmt = stmt.where(AuditLog.resource_type == resource_type_filter)
        if start_time:
            stmt = stmt.where(AuditLog.timestamp >= start_time)
        if end_time:
            stmt = stmt.where(AuditLog.timestamp <= end_time)
        stmt = stmt.order_by(AuditLog.timestamp.desc()).offset(offset).limit(limit)
        return list(self.db.execute(stmt).scalars().all())

    def get_resource_logs(self, resource_type: str, resource_id: int) -> list[AuditLog]:
        """Complete audit history for a specific resource."""
        stmt = (
            select(AuditLog)
            .where(AuditLog.resource_type == resource_type)
            .where(AuditLog.resource_id == resource_id)
            .order_by(AuditLog.timestamp.desc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_action_stats(self, user_id: int, days: int = 30) -> dict[str, Any]:
        """Action statistics for a user over the given period."""
        since = datetime.now(timezone.utc) - timedelta(days=days)
        stmt = select(AuditLog).where(
            AuditLog.user_id == user_id,
            AuditLog.timestamp >= since,
        )
        logs = list(self.db.execute(stmt).scalars().all())

        action_counts: dict[str, int] = {}
        success_count = 0
        for log in logs:
            action_counts[log.action] = action_counts.get(log.action, 0) + 1
            if log.success:
                success_count += 1
        failure_count = len(logs) - success_count
        return {
            "total_actions": len(logs),
            "action_breakdown": action_counts,
            "success_count": success_count,
            "failure_count": failure_count,
            "success_rate": (success_count / len(logs) * 100) if logs else 0,
            "period_days": days,
        }

    def get_recent_activity(self, user_id: int, limit: int = 20) -> list[AuditLog]:
        """Most recent activity for dashboard display."""
        stmt = select(AuditLog).where(AuditLog.user_id == user_id).order_by(AuditLog.timestamp.desc()).limit(limit)
        return list(self.db.execute(stmt).scalars().all())

    def count_user_logs(self, user_id: int) -> int:
        """Count total audit logs for a user."""
        from sqlalchemy import func

        stmt = select(func.count()).where(AuditLog.user_id == user_id)
        return self.db.execute(stmt).scalar_one()

    def delete_old_logs(self, retention_days: int = 90) -> int:
        """Delete audit logs older than retention period.

        The ONLY legitimate deletion path for audit logs.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
        from sqlalchemy import delete

        stmt = delete(AuditLog).where(AuditLog.timestamp < cutoff)
        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount or 0  # type: ignore[attr-defined]
