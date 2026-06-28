"""Project index model — user-scoped project type detection."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class ProjectIndex(Base):
    """Indexed project with type and framework detection."""

    __tablename__ = "project_indices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    project_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    project_name: Mapped[str] = mapped_column(String(255), nullable=False)
    project_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    frameworks: Mapped[str | None] = mapped_column(String(500), nullable=True)
    configuration: Mapped[str | None] = mapped_column(String(500), nullable=True)
    last_scanned: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    has_tests: Mapped[int] = mapped_column(Integer, default=0)
    has_ci: Mapped[int] = mapped_column(Integer, default=0)
    has_docker: Mapped[int] = mapped_column(Integer, default=0)

    __table_args__ = (
        Index("ix_project_user_path", "user_id", "project_path", unique=True),
        Index("ix_project_user_type", "user_id", "project_type"),
    )
