"""Audit log model — immutable append-only trail for all significant actions."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Index, Integer, String, Text, func
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class AuditLog(Base):
    """Immutable audit trail. Never UPDATE or DELETE in application code."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    session_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    success: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    __table_args__ = (
        Index("ix_audit_user_timestamp", "user_id", "timestamp"),
        Index("ix_audit_resource_timestamp", "resource_type", "resource_id", "timestamp"),
        Index("ix_audit_action_timestamp", "action", "timestamp"),
    )
