"""Consent record model — granular consent tracking per user per data category."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Index, Integer, String, func
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class ConsentRecord(Base):
    """User consent per data category. Access control checks these before data access."""

    __tablename__ = "consent_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    consent_type: Mapped[str] = mapped_column(String(100), nullable=False)
    granted: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    scope: Mapped[str | None] = mapped_column(String(200), nullable=True)
    context: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    __table_args__ = (
        Index("ix_consent_user_type", "user_id", "consent_type", unique=True),
        Index("ix_consent_active", "user_id", "granted", "expires_at"),
    )
