"""Pre-computed statistics service for indexed documents.

Caches statistics in Redis for fast access with a configurable TTL.
Inspired by sist2's pre-computed statistics approach.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, text
from sqlalchemy.orm import Session

from backend.app.core.redis import redis_cache
from backend.app.models.awareness.repo_index import CodeChunk, RepoIndex
from backend.app.models.memory.document import Document, DocumentChunk

logger = logging.getLogger(__name__)

STATS_TTL_SECONDS = 300  # 5 minutes


class DocumentStatistics:
    """Computes and caches statistics about indexed documents."""

    def _cache_key(self, repo_id: int | None) -> str:
        if repo_id is not None:
            return f"cortex:stats:repo:{repo_id}"
        return "cortex:stats:global"

    async def get_statistics(self, db: Session, repo_id: int | None = None) -> dict:
        """Return cached statistics, falling back to fresh computation."""
        cache_key = self._cache_key(repo_id)

        try:
            cached = await redis_cache.get(cache_key)
            if cached is not None:
                return cached
        except Exception as e:
            logger.debug("Redis read failed for stats: %s", e)

        stats = self._compute_statistics(db, repo_id)

        try:
            await redis_cache.set(cache_key, stats, expire_seconds=STATS_TTL_SECONDS)
        except Exception as e:
            logger.debug("Redis write failed for stats: %s", e)

        return stats

    async def refresh_statistics(self, db: Session, repo_id: int | None = None) -> dict:
        """Force recompute and cache statistics."""
        cache_key = self._cache_key(repo_id)
        stats = self._compute_statistics(db, repo_id)

        try:
            await redis_cache.set(cache_key, stats, expire_seconds=STATS_TTL_SECONDS)
        except Exception as e:
            logger.debug("Redis write failed for stats refresh: %s", e)

        return stats

    def _compute_statistics(self, db: Session, repo_id: int | None = None) -> dict:
        """Compute all statistics from the database."""
        stats: dict = {}

        # --- Document stats ---
        doc_query = db.query(Document)
        if repo_id is not None:
            doc_query = doc_query.join(RepoIndex, Document.path.like(RepoIndex.repo_path + "%")).filter(
                RepoIndex.id == repo_id
            )

        total_documents = doc_query.count()
        stats["total_documents"] = total_documents

        # Documents by type
        type_counts = (
            doc_query.with_entities(Document.doc_type, func.count(Document.id)).group_by(Document.doc_type).all()
        )
        stats["documents_by_type"] = {
            (dt.value if hasattr(dt, "value") else str(dt)): count for dt, count in type_counts
        }

        # --- Document chunk stats ---
        chunk_query = db.query(DocumentChunk)
        if repo_id is not None:
            chunk_query = (
                chunk_query.join(Document, DocumentChunk.document_id == Document.id)
                .join(RepoIndex, Document.path.like(RepoIndex.repo_path + "%"))
                .filter(RepoIndex.id == repo_id)
            )

        total_chunks = chunk_query.count()
        stats["total_document_chunks"] = total_chunks

        avg_chunk_result = chunk_query.with_entities(func.avg(DocumentChunk.token_count)).scalar()
        stats["avg_document_chunk_size"] = round(float(avg_chunk_result or 0), 1)

        # --- Code chunk stats ---
        code_query = db.query(CodeChunk)
        if repo_id is not None:
            code_query = code_query.filter(CodeChunk.repo_id == repo_id)

        total_code_chunks = code_query.count()
        stats["total_code_chunks"] = total_code_chunks

        # --- Documents indexed per day (last 30 days) ---
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        daily_counts = (
            doc_query.filter(Document.last_indexed_at >= thirty_days_ago)
            .with_entities(
                func.date(Document.last_indexed_at).label("day"),
                func.count(Document.id),
            )
            .group_by(text("day"))
            .order_by(text("day DESC"))
            .all()
        )
        stats["documents_indexed_per_day"] = [{"date": str(day), "count": count} for day, count in daily_counts]

        # --- Top languages (from code chunks) ---
        lang_query = db.query(CodeChunk)
        if repo_id is not None:
            lang_query = lang_query.filter(CodeChunk.repo_id == repo_id)

        top_languages = (
            lang_query.filter(CodeChunk.language.isnot(None))
            .with_entities(CodeChunk.language, func.count(CodeChunk.id))
            .group_by(CodeChunk.language)
            .order_by(func.count(CodeChunk.id).desc())
            .limit(10)
            .all()
        )
        stats["top_languages"] = [{"language": lang, "count": count} for lang, count in top_languages]

        # --- Top repositories ---
        top_repos = (
            db.query(
                RepoIndex.id,
                RepoIndex.repo_name,
                func.count(CodeChunk.id).label("chunk_count"),
            )
            .join(CodeChunk, RepoIndex.id == CodeChunk.repo_id)
            .group_by(RepoIndex.id, RepoIndex.repo_name)
            .order_by(text("chunk_count DESC"))
            .limit(10)
            .all()
        )
        stats["top_repositories"] = [
            {"repo_id": rid, "repo_name": name, "chunk_count": count} for rid, name, count in top_repos
        ]

        # --- Total file size ---
        total_size = doc_query.with_entities(func.sum(Document.file_size)).scalar()
        stats["total_file_size_bytes"] = int(total_size or 0)

        stats["computed_at"] = datetime.now(timezone.utc).isoformat()
        stats["repo_id"] = repo_id

        return stats


_document_statistics: DocumentStatistics | None = None


def get_document_statistics() -> DocumentStatistics:
    global _document_statistics
    if _document_statistics is None:
        _document_statistics = DocumentStatistics()
    return _document_statistics
