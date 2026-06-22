"""File tracking model for incremental indexing."""

from __future__ import annotations

import os
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, Index, Integer, String, func
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
    file_size: Mapped[int] = mapped_column(BigInteger, default=0)
    mtime: Mapped[float] = mapped_column(Float, default=0.0)
    last_indexed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="indexed")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    repo = relationship("RepoIndex", back_populates="indexed_files")

    __table_args__ = (Index("idx_indexed_files_repo_path", "repo_id", "file_path", unique=True),)

    def is_stale(self) -> bool:
        """Return True if the file no longer exists on disk."""

        repo = self.repo
        if repo is None:
            return True
        full_path = os.path.join(repo.repo_path, self.file_path)
        try:
            os.stat(full_path)
            return False
        except (OSError, TypeError):
            return True
