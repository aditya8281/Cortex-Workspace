"""Focus session tracking for attention-aware context."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class AttentionTracker(Base):
    __tablename__ = "attention_tracker"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Session info
    session_type: Mapped[str] = mapped_column(String(32), default="general")
    task_description: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # Focus metrics
    focus_score: Mapped[float] = mapped_column(Float, default=0.0)
    distraction_count: Mapped[int] = mapped_column(Integer, default=0)
    switch_count: Mapped[int] = mapped_column(Integer, default=0)
    duration_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    productive_seconds: Mapped[float] = mapped_column(Float, default=0.0)

    # Activity data
    active_apps: Mapped[list] = mapped_column(JSON, default=list)
    context_switches: Mapped[list] = mapped_column(JSON, default=list)

    # Timestamps
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
