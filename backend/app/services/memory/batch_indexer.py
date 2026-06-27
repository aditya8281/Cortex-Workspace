"""Batch indexing service for efficient bulk document insertion.

Inspired by sist2's batch bulk indexing pattern (70 docs per bulk call).
Collects documents in a buffer and flushes them in batches.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

DEFAULT_BATCH_SIZE = 50
FLUSH_INTERVAL_SECONDS = 5.0


@dataclass
class BatchItem:
    """A single item to be indexed."""

    content: str
    file_path: str
    metadata: dict[str, Any] = field(default_factory=dict)
    collection: str = "cortex_code"  # or "cortex_memory"


class BatchIndexer:
    """Accumulates documents and indexes them in batches for efficiency."""

    def __init__(
        self,
        db: Session,
        batch_size: int = DEFAULT_BATCH_SIZE,
        flush_interval: float = FLUSH_INTERVAL_SECONDS,
    ):
        self._db = db
        self._batch_size = batch_size
        self._flush_interval = flush_interval
        self._buffer: list[BatchItem] = []
        self._last_flush = time.time()
        self._total_indexed = 0
        self._total_errors = 0

    def add(self, item: BatchItem) -> None:
        """Add an item to the batch buffer. Auto-flushes when full."""
        self._buffer.append(item)
        if len(self._buffer) >= self._batch_size:
            self.flush()

    def add_many(self, items: list[BatchItem]) -> None:
        """Add multiple items to the buffer."""
        for item in items:
            self.add(item)

    def flush(self) -> int:
        """Flush the current buffer to the database and vector store.

        Returns:
            Number of items successfully indexed.
        """
        if not self._buffer:
            return 0

        items = self._buffer[:]
        self._buffer.clear()
        self._last_flush = time.time()

        indexed = 0
        errors = 0

        try:
            # Batch insert to PostgreSQL
            from backend.app.models.repo_index import CodeChunk

            for item in items:
                try:
                    chunk = CodeChunk(
                        content=item.content,
                        file_path=item.file_path,
                        repo_id=item.metadata.get("repo_id"),
                        language=item.metadata.get("language"),
                        chunk_type=item.metadata.get("chunk_type"),
                        line_start=item.metadata.get("line_start"),
                        line_end=item.metadata.get("line_end"),
                        symbol_name=item.metadata.get("symbol_name"),
                    )
                    self._db.add(chunk)
                    indexed += 1
                except Exception as e:
                    logger.warning("Failed to add item to DB batch: %s", e)
                    errors += 1

            self._db.commit()

            # Batch upsert to Qdrant
            from backend.app.core.vector_db import get_vector_db
            from backend.app.services.embedding_service import get_embedding_service

            vector_db = get_vector_db()
            embedder = get_embedding_service()

            # Batch embed
            contents = [item.content for item in items[:indexed]]
            if contents:
                vectors = embedder.embed_batch(contents)

                # Batch upsert to Qdrant
                points = []
                for _i, (item, vector) in enumerate(zip(items[:indexed], vectors, strict=False)):
                    if vector is not None:
                        points.append(
                            {
                                "id": hash(f"{item.file_path}:{item.metadata.get('line_start', 0)}") % (2**63),
                                "vector": vector,
                                "payload": {
                                    "content": item.content[:1000],
                                    "file_path": item.file_path,
                                    **item.metadata,
                                },
                            }
                        )

                if points:
                    collection = items[0].collection if items else "cortex_code"
                    vector_db.upsert_batch(collection, points)  # type: ignore[attr-defined]

        except Exception as e:
            logger.error("Batch flush failed: %s", e)
            self._db.rollback()
            errors += indexed
            indexed = 0

        self._total_indexed += indexed
        self._total_errors += errors

        if indexed > 0:
            logger.info("Batch indexed %d items (%d errors)", indexed, errors)

        return indexed

    def maybe_flush(self) -> int:
        """Flush if buffer is non-empty and enough time has passed."""
        if not self._buffer:
            return 0
        if time.time() - self._last_flush >= self._flush_interval:
            return self.flush()
        return 0

    @property
    def stats(self) -> dict:
        return {
            "buffer_size": len(self._buffer),
            "total_indexed": self._total_indexed,
            "total_errors": self._total_errors,
            "last_flush": self._last_flush,
        }


# Module-level singleton
_batch_indexer: BatchIndexer | None = None


def get_batch_indexer(db: Session) -> BatchIndexer:
    global _batch_indexer
    if _batch_indexer is None:
        _batch_indexer = BatchIndexer(db)
    return _batch_indexer
