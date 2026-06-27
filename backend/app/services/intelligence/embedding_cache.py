"""Embedding cache service — lookup, store, and invalidate cached embeddings."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from backend.app.models.intelligence.embedding_cache import EmbeddingCache

logger = logging.getLogger(__name__)

DEFAULT_TTL_SECONDS = 30 * 24 * 3600  # 30 days


class EmbeddingCacheService:
    """Manages embedding cache in PostgreSQL for avoiding redundant computation."""

    def __init__(self, db: Session):
        self._db = db

    def get(self, content_hash: str, model_name: str, model_version: str = "default") -> list[float] | None:
        """Retrieve cached embedding if valid. Returns None on miss or expiry."""
        entry = (
            self._db.query(EmbeddingCache)
            .filter(
                EmbeddingCache.content_hash == content_hash,
                EmbeddingCache.model_name == model_name,
                EmbeddingCache.model_version == model_version,
            )
            .first()
        )

        if entry is None:
            return None

        if self._is_expired(entry):
            logger.debug("Cache expired for hash %s", content_hash[:12])
            self._db.delete(entry)
            self._db.commit()
            return None

        entry.access_count += 1
        entry.last_accessed_at = datetime.now(timezone.utc)
        self._db.commit()

        logger.debug("Cache hit for hash %s (accesses=%d)", content_hash[:12], entry.access_count)
        return json.loads(entry.embedding)

    def put(
        self,
        content_hash: str,
        embedding: list[float],
        model_name: str,
        model_version: str = "default",
        token_count: int = 0,
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
    ) -> None:
        """Store embedding in cache. Upserts on conflict."""
        existing = (
            self._db.query(EmbeddingCache)
            .filter(
                EmbeddingCache.content_hash == content_hash,
                EmbeddingCache.model_name == model_name,
                EmbeddingCache.model_version == model_version,
            )
            .first()
        )

        if existing:
            existing.embedding = json.dumps(embedding)
            existing.token_count = token_count
            existing.ttl_seconds = ttl_seconds
            existing.last_accessed_at = datetime.now(timezone.utc)
            existing.access_count += 1
        else:
            entry = EmbeddingCache(
                content_hash=content_hash,
                model_name=model_name,
                model_version=model_version,
                embedding=json.dumps(embedding),
                token_count=token_count,
                ttl_seconds=ttl_seconds,
            )
            self._db.add(entry)

        self._db.commit()
        logger.debug("Cache stored for hash %s (model=%s)", content_hash[:12], model_name)

    def invalidate(self, content_hash: str) -> int:
        """Remove all cache entries for a content hash. Returns count removed."""
        count = self._db.query(EmbeddingCache).filter(EmbeddingCache.content_hash == content_hash).delete()
        self._db.commit()
        if count > 0:
            logger.info("Invalidated %d cache entries for hash %s", count, content_hash[:12])
        return count

    def invalidate_all(self, model_name: str | None = None) -> int:
        """Remove all cache entries, optionally filtered by model name."""
        query = self._db.query(EmbeddingCache)
        if model_name:
            query = query.filter(EmbeddingCache.model_name == model_name)
        count = query.delete()
        self._db.commit()
        logger.info("Invalidated all cache entries (model=%s, count=%d)", model_name, count)
        return count

    def cleanup_expired(self) -> int:
        """Remove all expired cache entries. Returns count removed."""
        all_entries = self._db.query(EmbeddingCache).all()
        expired = [e for e in all_entries if self._is_expired(e)]
        count = len(expired)
        for entry in expired:
            self._db.delete(entry)
        self._db.commit()
        if count > 0:
            logger.info("Cleaned up %d expired cache entries", count)
        return count

    def stats(self) -> dict:
        """Return cache statistics."""
        from sqlalchemy import func

        total = self._db.query(func.count(EmbeddingCache.content_hash)).scalar() or 0
        avg_access = self._db.query(func.avg(EmbeddingCache.access_count)).scalar() or 0
        return {"total_entries": total, "avg_access_count": round(float(avg_access), 2)}

    @staticmethod
    def _is_expired(entry: EmbeddingCache) -> bool:
        if entry.ttl_seconds <= 0:
            return False
        now = datetime.now(timezone.utc)
        last_accessed = entry.last_accessed_at
        if last_accessed.tzinfo is None:
            last_accessed = last_accessed.replace(tzinfo=timezone.utc)
        expires_at = last_accessed + timedelta(seconds=entry.ttl_seconds)
        return now > expires_at


_embedding_cache: EmbeddingCacheService | None = None


def get_embedding_cache(db: Session) -> EmbeddingCacheService:
    """Get or create the global EmbeddingCacheService singleton."""
    global _embedding_cache
    if _embedding_cache is None:
        _embedding_cache = EmbeddingCacheService(db)
    return _embedding_cache
