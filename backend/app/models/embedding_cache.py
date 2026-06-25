"""Embedding cache model for avoiding redundant embedding computation."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func, select
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class EmbeddingCache(Base):
    __tablename__ = "embedding_cache"

    content_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    model_version: Mapped[str] = mapped_column(String(128), nullable=False, default="default")
    embedding: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_accessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    access_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    ttl_seconds: Mapped[int] = mapped_column(Integer, default=2592000, nullable=False)

    @classmethod
    def clean_expired(cls, session) -> int:
        """Remove cache entries where created_at + ttl_seconds < now().

        Returns the number of deleted rows.

        NOTE: This method provides the cleanup logic but does NOT schedule
        itself.  A background job or cron task should call this periodically,
        e.g.:
            from backend.app.db.bootstrap import get_session_factory
            session = get_session_factory()()
            EmbeddingCache.clean_expired(session)
            session.commit()
        """
        stmt = select(cls).where(func.age(func.now(), cls.created_at) > cls.ttl_seconds)
        expired = session.execute(stmt).scalars().all()
        for entry in expired:
            session.delete(entry)
        return len(expired)
