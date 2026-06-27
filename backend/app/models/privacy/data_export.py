"""Data export model — tracks export requests for GDPR Article 20 compliance."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class DataExport(Base):
    """Data export request tracking — async export with lifecycle management."""

    __tablename__ = "data_exports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    export_type: Mapped[str] = mapped_column(String(50), nullable=False, default="full")
    data_types: Mapped[list | None] = mapped_column(JSON, nullable=True)
    format: Mapped[str] = mapped_column(String(20), nullable=False, default="json")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    file_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    checksum_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
