"""Deletion pipeline — soft delete, orphan detection, and cascade cleanup."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_
from sqlalchemy.orm import Session

from backend.app.core.vector_db import VectorDB, get_vector_db
from backend.app.models.memory.document import Document, DocumentChunk
from backend.app.services.intelligence.embedding_cache import EmbeddingCacheService, get_embedding_cache

logger = logging.getLogger(__name__)

HARD_DELETE_AFTER_DAYS = 30
CODE_COLLECTION = "cortex_code"
MEMORY_COLLECTION = "cortex_memory"


class DeletionPipeline:
    """Handles document deletion with soft delete, orphan cleanup, and vector removal."""

    def __init__(
        self,
        db: Session,
        vector_db: VectorDB | None = None,
        embedding_cache: EmbeddingCacheService | None = None,
    ):
        self._db = db
        self._vector_db = vector_db or get_vector_db()
        self._embedding_cache = embedding_cache or get_embedding_cache(db)

    def soft_delete(self, document_id: int) -> bool:
        """Mark a document as deleted without removing data."""
        doc = self._db.query(Document).filter(Document.id == document_id).first()
        if not doc or doc.deleted_at is not None:
            return False

        doc.deleted_at = datetime.now(timezone.utc)
        self._db.commit()
        logger.info("Soft deleted document %d (path=%s)", document_id, doc.path)
        return True

    def restore(self, document_id: int) -> bool:
        """Restore a soft-deleted document."""
        doc = self._db.query(Document).filter(Document.id == document_id).first()
        if not doc or doc.deleted_at is None:
            return False

        doc.deleted_at = None
        self._db.commit()
        logger.info("Restored document %d (path=%s)", document_id, doc.path)
        return True

    def hard_delete(self, document_id: int) -> bool:
        """Permanently delete a document and all associated data."""
        doc = self._db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            return False

        self._remove_vectors(document_id)
        self._invalidate_embeddings(document_id)

        self._db.delete(doc)
        self._db.commit()
        logger.info("Hard deleted document %d (path=%s)", document_id, doc.path)
        return True

    def cleanup_orphans(self) -> dict:
        """Find and remove orphaned data. Returns counts of cleaned items."""
        stats = {"vectors_removed": 0, "embeddings_invalidated": 0, "hard_deleted": 0}

        cutoff = datetime.now(timezone.utc) - timedelta(days=HARD_DELETE_AFTER_DAYS)
        stale_docs = (
            self._db.query(Document)
            .filter(
                and_(
                    Document.deleted_at.isnot(None),
                    Document.deleted_at < cutoff,
                )
            )
            .all()
        )

        for doc in stale_docs:
            self.hard_delete(doc.id)
            stats["hard_deleted"] += 1

        stats["vectors_removed"] = self._remove_orphaned_vectors()
        stats["embeddings_invalidated"] = self._invalidate_orphaned_embeddings()

        logger.info("Orphan cleanup: %s", stats)
        return stats

    def delete_by_path(self, path: str) -> bool:
        """Soft delete a document by its path."""
        doc = self._db.query(Document).filter(Document.path == path).first()
        if not doc:
            return False
        return self.soft_delete(doc.id)

    def _remove_vectors(self, document_id: int) -> int:
        """Remove all vector embeddings for a document's chunks."""
        chunks = self._db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).all()

        embedding_ids = [c.embedding_id for c in chunks if c.embedding_id]
        if not embedding_ids:
            return 0

        for collection in [CODE_COLLECTION, MEMORY_COLLECTION]:
            try:
                self._vector_db.delete(collection, embedding_ids)
            except Exception as e:
                logger.warning("Failed to delete vectors from %s: %s", collection, e)

        return len(embedding_ids)

    def _invalidate_embeddings(self, document_id: int) -> int:
        """Invalidate embedding cache entries for a document's chunks."""
        chunks = self._db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).all()

        count = 0
        for chunk in chunks:
            if chunk.embedding_id:
                self._embedding_cache.invalidate(chunk.embedding_id)
                count += 1
        return count

    def _remove_orphaned_vectors(self) -> int:
        """Find Qdrant points with no corresponding DB chunk.

        Qdrant does not expose a list-all-points API, so orphaned vector
        cleanup is best handled by periodic re-indexing rather than
        point-by-point comparison. Returns 0.
        """
        return 0

    def _invalidate_orphaned_embeddings(self) -> int:
        """Invalidate cache entries with no referencing chunks."""
        from backend.app.models.intelligence.embedding_cache import EmbeddingCache

        cached_hashes = {row[0] for row in self._db.query(EmbeddingCache.content_hash).all()}
        used_ids = {
            row[0]
            for row in self._db.query(DocumentChunk.embedding_id).filter(DocumentChunk.embedding_id.isnot(None)).all()
        }

        count = 0
        orphaned = cached_hashes - used_ids
        for h in orphaned:
            self._embedding_cache.invalidate(h)
            count += 1
        return count
