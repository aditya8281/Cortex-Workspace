"""Pre-computed path index for fast directory browsing.

Inspired by sist2's path_parent function for hierarchical file navigation.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class PathIndex(Base):
    __tablename__ = "path_index"

    path: Mapped[str] = mapped_column(String(2000), primary_key=True)
    parent_path: Mapped[str] = mapped_column(String(2000), nullable=False, index=True)
    basename: Mapped[str] = mapped_column(String(256), nullable=False)
    depth: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    is_dir: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    file_count: Mapped[int] = mapped_column(Integer, default=0)
    total_size: Mapped[int] = mapped_column(BigInteger, default=0)
    last_modified: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    repo_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("repo_indexes.id", ondelete="CASCADE"), nullable=False, index=True
    )

    __table_args__ = (
        Index("idx_path_index_repo_parent", "repo_id", "parent_path"),
        Index("idx_path_index_repo_depth", "repo_id", "depth"),
    )
