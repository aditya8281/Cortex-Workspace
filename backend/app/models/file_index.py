"""File tracking model for incremental indexing."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base


class IndexedFile(Base):
    __tablename__ = "indexed_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    repo_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("repo_indexes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    file_path: Mapped[str] = mapped_column(String(2000), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    last_indexed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="indexed")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    repo = relationship("RepoIndex", backref="indexed_files")

    __table_args__ = (
        Index("idx_indexed_files_repo_path", "repo_id", "file_path", unique=True),
    )
