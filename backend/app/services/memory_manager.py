"""Memory Manager service for knowledge entry CRUD with vector search."""

from __future__ import annotations

import json
import logging

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.core.vector_db import get_vector_db, VectorDB
from backend.app.intelligence.models import KnowledgeEntry
from backend.app.services.embedding_service import get_embedding_service, EmbeddingService

logger = logging.getLogger(__name__)

DEFAULT_COLLECTION = "cortex_memory"


class MemoryManager:
    """Manages knowledge entries with vector search integration."""

    def __init__(
        self,
        db: Session,
        vector_db: VectorDB | None = None,
        embedding_service: EmbeddingService | None = None,
    ):
        self._db = db
        self._vector_db = vector_db or get_vector_db()
        self._embedder = embedding_service or get_embedding_service()

    def create(
        self,
        user_id: int | None,
        title: str,
        content: str,
        category: str = "note",
        source_path: str | None = None,
        tags: list[str] | None = None,
    ) -> KnowledgeEntry:
        """Create a knowledge entry with vector embedding."""
        embedding_id = self._embedder.compute_embedding_id(f"{title}\n{content}")

        entry = KnowledgeEntry(
            user_id=user_id,
            title=title,
            content=content,
            category=category,
            source_path=source_path,
            tags=json.dumps(tags) if tags else None,
            embedding_id=embedding_id,
            vector_collection=DEFAULT_COLLECTION,
        )
        self._db.add(entry)
        self._db.commit()
        self._db.refresh(entry)

        vector = self._embedder.embed_single(content)
        self._vector_db.upsert(
            DEFAULT_COLLECTION,
            [
                {
                    "id": embedding_id,
                    "vector": vector,
                    "payload": {
                        "entry_id": entry.id,
                        "user_id": user_id,
                        "category": category,
                    },
                }
            ],
        )
        logger.info("Created memory entry %d: %s", entry.id, title)
        return entry

    def get(self, entry_id: int) -> KnowledgeEntry | None:
        """Get a knowledge entry by ID."""
        return self._db.query(KnowledgeEntry).filter(KnowledgeEntry.id == entry_id).first()

    def list(
        self,
        user_id: int | None = None,
        category: str | None = None,
        limit: int = 24,
        offset: int = 0,
    ) -> tuple[list[KnowledgeEntry], int, dict[str, int]]:
        """List knowledge entries with pagination and category counts."""
        query = self._db.query(KnowledgeEntry)

        if user_id is not None:
            query = query.filter(
                (KnowledgeEntry.user_id == user_id) | (KnowledgeEntry.user_id.is_(None))
            )

        if category is not None:
            query = query.filter(KnowledgeEntry.category == category)

        total = query.count()
        entries = (
            query.order_by(KnowledgeEntry.updated_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        category_query = self._db.query(KnowledgeEntry)
        if user_id is not None:
            category_query = category_query.filter(
                (KnowledgeEntry.user_id == user_id) | (KnowledgeEntry.user_id.is_(None))
            )
        categories = dict(
            category_query.with_entities(
                KnowledgeEntry.category,
                func.count(KnowledgeEntry.id),
            ).group_by(KnowledgeEntry.category).all()
        )

        return entries, total, categories

    def search(
        self,
        query: str,
        user_id: int | None = None,
        category: str | None = None,
        limit: int = 10,
    ) -> list[dict]:
        """Semantic search over knowledge entries using vector similarity."""
        query_vector = self._embedder.embed_single(query)

        filter_payload = {}
        if user_id is not None:
            filter_payload["user_id"] = user_id
        if category:
            filter_payload["category"] = category

        results = self._vector_db.search(
            DEFAULT_COLLECTION,
            query_vector,
            limit=limit,
            filter_payload=filter_payload if filter_payload else None,
        )

        entry_ids = [int(r["id"]) for r in results]
        entries = (
            self._db.query(KnowledgeEntry)
            .filter(KnowledgeEntry.id.in_(entry_ids))
            .all()
            if entry_ids
            else []
        )
        entry_map = {str(e.id): self._serialize(e) for e in entries}

        return [
            {"score": r["score"], "entry": entry_map.get(r["id"])}
            for r in results
        ]

    def update(
        self,
        entry_id: int,
        title: str | None = None,
        content: str | None = None,
        category: str | None = None,
        tags: list[str] | None = None,
    ) -> KnowledgeEntry | None:
        """Update a knowledge entry and re-embed if content changed."""
        entry = self.get(entry_id)
        if not entry:
            return None

        changed = False
        if title is not None and title != entry.title:
            entry.title = title
            changed = True
        if content is not None and content != entry.content:
            entry.content = content
            changed = True
        if category is not None:
            entry.category = category
            changed = True
        if tags is not None:
            entry.tags = json.dumps(tags)
            changed = True

        if changed:
            if title is not None or content is not None:
                new_text = f"{entry.title}\n{entry.content}"
                new_embedding_id = self._embedder.compute_embedding_id(new_text)
                entry.embedding_id = new_embedding_id
                vector = self._embedder.embed_single(entry.content)
                self._vector_db.upsert(
                    DEFAULT_COLLECTION,
                    [
                        {
                            "id": new_embedding_id,
                            "vector": vector,
                            "payload": {
                                "entry_id": entry.id,
                                "user_id": entry.user_id,
                                "category": entry.category,
                            },
                        }
                    ],
                )
            self._db.commit()
            self._db.refresh(entry)

        logger.info("Updated memory entry %d", entry_id)
        return entry

    def delete(self, entry_id: int) -> bool:
        """Delete a knowledge entry and its vector embedding."""
        entry = self.get(entry_id)
        if not entry:
            return False

        if entry.embedding_id:
            self._vector_db.delete(DEFAULT_COLLECTION, [entry.embedding_id])
        self._db.delete(entry)
        self._db.commit()

        logger.info("Deleted memory entry %d", entry_id)
        return True

    @staticmethod
    def _serialize(entry: KnowledgeEntry) -> dict:
        """Serialize entry for API response."""
        tags = []
        if entry.tags:
            try:
                tags = json.loads(entry.tags)
            except (json.JSONDecodeError, TypeError):
                tags = []

        return {
            "id": entry.id,
            "user_id": entry.user_id,
            "title": entry.title,
            "content": entry.content,
            "category": entry.category,
            "source_path": entry.source_path,
            "tags": tags,
            "embedding_id": entry.embedding_id,
            "created_at": entry.created_at.isoformat() if entry.created_at else None,
            "updated_at": entry.updated_at.isoformat() if entry.updated_at else None,
        }
