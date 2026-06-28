"""Repository index model — user-scoped repo analysis for awareness."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class RepositoryIndex(Base):
    """Indexed repository with structural analysis."""

    __tablename__ = "repository_indices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    repo_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    repo_name: Mapped[str] = mapped_column(String(255), nullable=False)
    languages: Mapped[str | None] = mapped_column(String(500), nullable=True)
    total_files: Mapped[int] = mapped_column(Integer, default=0)
    total_lines: Mapped[int] = mapped_column(Integer, default=0)
    last_indexed: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    framework: Mapped[str | None] = mapped_column(String(100), nullable=True)
    dependencies: Mapped[str | None] = mapped_column(String(500), nullable=True)
    git_branch: Mapped[str | None] = mapped_column(String(200), nullable=True)
    last_commit_hash: Mapped[str | None] = mapped_column(String(40), nullable=True)

    __table_args__ = (
        Index("ix_repo_user_path", "user_id", "repo_path", unique=True),
        Index("ix_repo_user_framework", "user_id", "framework"),
    )
