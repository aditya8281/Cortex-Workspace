"""Persistent knowledge memory — search and store discovered intelligence."""

from __future__ import annotations

from datetime import datetime
from math import sqrt

from sqlalchemy.orm import Session

from backend.app.intelligence.models import KnowledgeEntry


class PersistentMemoryService:
    def __init__(self):
        self._embedder = None

    def _get_embedder(self):
        if self._embedder is None:
            from backend.app.rag.embeddings import EmbeddingModel

            self._embedder = EmbeddingModel()
        return self._embedder

    @staticmethod
    def _cosine_similarity(left, right) -> float:
        if left is None or right is None:
            return 0.0
        numerator = float((left * right).sum())
        left_norm = sqrt(float((left * left).sum()))
        right_norm = sqrt(float((right * right).sum()))
        if left_norm == 0.0 or right_norm == 0.0:
            return 0.0
        return numerator / (left_norm * right_norm)

    def search(self, db: Session, query: str, limit: int = 8, user_id: int | None = None) -> list[dict]:
        words = [w.lower() for w in query.split() if len(w) > 2]
        if not words:
            return []

        q = db.query(KnowledgeEntry)
        if user_id is not None:
            q = q.filter(
                (KnowledgeEntry.user_id == user_id) | (KnowledgeEntry.user_id.is_(None))
            )

        entries = q.order_by(KnowledgeEntry.updated_at.desc()).limit(200).all()
        if not entries:
            return []

        embedder = self._get_embedder()
        query_vector = embedder.encode([query])[0]
        scored: list[tuple[float, KnowledgeEntry]] = []
        haystacks = [f"{entry.title} {entry.content} {entry.category}".lower() for entry in entries]
        entry_vectors = embedder.encode(haystacks)

        for entry, haystack, entry_vector in zip(entries, haystacks, entry_vectors):
            keyword_score = sum(1 for w in words if w in haystack)
            semantic_score = self._cosine_similarity(query_vector, entry_vector)
            recency_boost = 0.0
            if entry.updated_at is not None:
                age_days = max(0.0, (datetime.utcnow() - entry.updated_at).total_seconds() / 86400.0)
                # Slightly prefer newer content while keeping semantic relevance dominant.
                recency_boost = max(0.0, 0.08 - min(age_days, 30.0) * 0.002)
            score = (semantic_score * 0.8) + (min(keyword_score, 3) * 0.12) + recency_boost
            if score > 0:
                scored.append((score, entry))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [
            {
                "id": entry.id,
                "category": entry.category,
                "title": entry.title,
                "content": entry.content[:1200],
                "source_path": entry.source_path,
                "score": round(score, 4),
            }
            for score, entry in scored[:limit]
        ]

    def add_document_memory(
        self,
        db: Session,
        *,
        title: str,
        content: str,
        source_path: str,
        category: str = "document",
        user_id: int | None = None,
    ) -> KnowledgeEntry:
        source_key = f"doc:{source_path}"
        existing = (
            db.query(KnowledgeEntry).filter(KnowledgeEntry.source_key == source_key).first()
        )
        if existing is None:
            existing = KnowledgeEntry(
                category=category,
                title=title,
                content=content,
                source_path=source_path,
                source_key=source_key,
                user_id=user_id,
            )
            db.add(existing)
        else:
            existing.title = title
            existing.content = content
            existing.category = category
            existing.source_path = source_path
            existing.user_id = user_id

        db.flush()
        return existing

    def count_entries(self, db: Session, user_id: int | None = None) -> int:
        q = db.query(KnowledgeEntry)
        if user_id is not None:
            q = q.filter(
                (KnowledgeEntry.user_id == user_id) | (KnowledgeEntry.user_id.is_(None))
            )
        return q.count()
