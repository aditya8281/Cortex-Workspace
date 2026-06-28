"""Hypothesis model — beliefs with evidence and confidence scoring."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class Hypothesis(Base):
    """Hypothesis with evidence tracking and Bayesian confidence scoring.

    Lifecycle: active -> confirmed | rejected
    """

    __tablename__ = "hypotheses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    hypothesis: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_for: Mapped[list] = mapped_column(JSON, default=list)
    evidence_against: Mapped[list] = mapped_column(JSON, default=list)
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    confidence_history: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False, index=True)
    source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    related_plan_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    related_hypothesis_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_hypothesis_user_status", "user_id", "status"),
        Index("ix_hypothesis_user_confidence", "user_id", "confidence"),
    )
