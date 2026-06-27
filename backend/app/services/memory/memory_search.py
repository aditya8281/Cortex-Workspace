"""Memory search service — cross-type retrieval with multi-signal scoring."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import desc
from sqlalchemy.orm import Session

from backend.app.models.memory.episodic import EpisodicMemory
from backend.app.models.memory.memory_graph import MemoryEdge, MemoryNode
from backend.app.models.memory.semantic import SemanticMemory
from backend.app.models.memory.working import WorkingMemory
from backend.app.services.memory.temporal import TemporalScoring

# Scoring weights
WEIGHT_TEXT_RELEVANCE = 0.30
WEIGHT_RECENCY = 0.25
WEIGHT_IMPORTANCE = 0.20
WEIGHT_ACCESS_FREQUENCY = 0.15
WEIGHT_GRAPH_CENTRALITY = 0.10


class MemorySearchService:
    """Cross-type memory search with multi-signal scoring."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.temporal = TemporalScoring()

    def search(
        self,
        user_id: int,
        query: str,
        memory_type: str | None = None,
        limit: int = 10,
        min_score: float = 0.0,
    ) -> list[dict]:
        """Search across all memory types with multi-signal scoring."""
        results: list[dict] = []
        query_terms = query.lower().split()

        # Search episodic memories
        if memory_type is None or memory_type == "episodic":
            episodic = (
                self.db.query(EpisodicMemory)
                .filter(
                    EpisodicMemory.user_id == user_id,
                    EpisodicMemory.content.ilike(f"%{query}%"),
                )
                .all()
            )

            for mem in episodic:
                score = self._compute_score(
                    user_id=user_id,
                    content=mem.content,
                    importance=mem.importance,
                    confidence=mem.confidence,
                    access_count=mem.access_count,
                    created_at=mem.created_at,
                    last_accessed=mem.last_accessed,
                    memory_id=mem.id,
                    memory_type="episodic",
                    query_terms=query_terms,
                )
                if score >= min_score:
                    results.append(
                        {
                            "type": "episodic",
                            "id": mem.id,
                            "content": mem.content,
                            "importance": mem.importance,
                            "confidence": mem.confidence,
                            "emotion": mem.emotion,
                            "created_at": mem.created_at.isoformat(),
                            "score": score,
                        }
                    )

        # Search semantic memories
        if memory_type is None or memory_type == "semantic":
            semantic = (
                self.db.query(SemanticMemory)
                .filter(
                    SemanticMemory.user_id == user_id,
                    SemanticMemory.content.ilike(f"%{query}%"),
                )
                .all()
            )

            for mem in semantic:
                score = self._compute_score(
                    user_id=user_id,
                    content=mem.content,
                    importance=mem.confidence,
                    confidence=mem.confidence,
                    access_count=mem.access_count,
                    created_at=mem.created_at,
                    last_accessed=mem.last_accessed,
                    memory_id=mem.id,
                    memory_type="semantic",
                    query_terms=query_terms,
                )
                if score >= min_score:
                    results.append(
                        {
                            "type": "semantic",
                            "id": mem.id,
                            "content": mem.content,
                            "category": mem.category,
                            "confidence": mem.confidence,
                            "source": mem.source,
                            "created_at": mem.created_at.isoformat(),
                            "score": score,
                        }
                    )

        # Search working memory
        if memory_type is None or memory_type == "working":
            working = (
                self.db.query(WorkingMemory)
                .filter(
                    WorkingMemory.user_id == user_id,
                    WorkingMemory.content.ilike(f"%{query}%"),
                    WorkingMemory.expires_at > datetime.utcnow(),
                )
                .all()
            )

            for mem in working:
                score = self._compute_score(
                    user_id=user_id,
                    content=mem.content,
                    importance=0.5,
                    confidence=1.0,
                    access_count=0,
                    created_at=mem.created_at,
                    last_accessed=None,
                    memory_id=mem.id,
                    memory_type="working",
                    query_terms=query_terms,
                )
                score *= 1.2  # Working memory boost

                if score >= min_score:
                    results.append(
                        {
                            "type": "working",
                            "id": mem.id,
                            "content": mem.content,
                            "slot": mem.slot,
                            "priority": mem.priority,
                            "created_at": mem.created_at.isoformat(),
                            "score": min(1.0, score),
                        }
                    )

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]

    def _compute_score(
        self,
        user_id: int,
        content: str,
        importance: float,
        confidence: float,
        access_count: int,
        created_at: datetime,
        last_accessed: datetime | None,
        memory_id: int,
        memory_type: str,
        query_terms: list[str],
    ) -> float:
        """Compute composite relevance score."""
        content_lower = content.lower()
        text_relevance = sum(
            1 for term in query_terms if term in content_lower
        ) / max(len(query_terms), 1)

        recency = self.temporal.recency_score(created_at, last_accessed)
        importance_weight = self.temporal.importance_weight(importance, confidence)
        access_weight = self.temporal.access_frequency_weight(access_count)
        graph_centrality = self._get_graph_centrality(
            user_id, memory_type, memory_id
        )

        score = (
            WEIGHT_TEXT_RELEVANCE * text_relevance
            + WEIGHT_RECENCY * recency
            + WEIGHT_IMPORTANCE * importance_weight
            + WEIGHT_ACCESS_FREQUENCY * access_weight
            + WEIGHT_GRAPH_CENTRALITY * graph_centrality
        )

        return min(1.0, max(0.0, score))

    def _get_graph_centrality(
        self, user_id: int, memory_type: str, memory_id: int
    ) -> float:
        """Get graph centrality score (0.0-1.0) for a memory."""
        node = (
            self.db.query(MemoryNode)
            .filter(
                MemoryNode.user_id == user_id,
                MemoryNode.memory_type == memory_type,
                MemoryNode.memory_id == memory_id,
            )
            .first()
        )

        if not node:
            return 0.0

        edge_count = (
            self.db.query(MemoryEdge)
            .filter(
                (MemoryEdge.source_id == node.id)
                | (MemoryEdge.target_id == node.id)
            )
            .count()
        )

        return min(1.0, edge_count / 10.0)

    def search_by_importance(
        self, user_id: int, min_importance: float = 0.5, limit: int = 10
    ) -> list[dict]:
        """Search by importance threshold across episodic memories."""
        memories = (
            self.db.query(EpisodicMemory)
            .filter(
                EpisodicMemory.user_id == user_id,
                EpisodicMemory.importance >= min_importance,
            )
            .order_by(desc(EpisodicMemory.importance))
            .limit(limit)
            .all()
        )

        return [
            {
                "type": "episodic",
                "id": m.id,
                "content": m.content,
                "importance": m.importance,
                "confidence": m.confidence,
                "created_at": m.created_at.isoformat(),
            }
            for m in memories
        ]

    def search_by_recency(
        self, user_id: int, limit: int = 10
    ) -> list[dict]:
        """Search by most recent across episodic and semantic."""
        episodic = (
            self.db.query(EpisodicMemory)
            .filter(EpisodicMemory.user_id == user_id)
            .order_by(desc(EpisodicMemory.created_at))
            .limit(limit)
            .all()
        )

        semantic = (
            self.db.query(SemanticMemory)
            .filter(SemanticMemory.user_id == user_id)
            .order_by(desc(SemanticMemory.created_at))
            .limit(limit)
            .all()
        )

        results: list[dict] = []
        for m in episodic:
            results.append(
                {
                    "type": "episodic",
                    "id": m.id,
                    "content": m.content,
                    "created_at": m.created_at.isoformat(),
                }
            )
        for m in semantic:
            results.append(
                {
                    "type": "semantic",
                    "id": m.id,
                    "content": m.content,
                    "created_at": m.created_at.isoformat(),
                }
            )

        results.sort(key=lambda x: x["created_at"], reverse=True)
        return results[:limit]

    def get_related_memories(
        self, user_id: int, memory_type: str, memory_id: int, limit: int = 5
    ) -> list[dict]:
        """Get memories related via graph connections."""
        node = (
            self.db.query(MemoryNode)
            .filter(
                MemoryNode.user_id == user_id,
                MemoryNode.memory_type == memory_type,
                MemoryNode.memory_id == memory_id,
            )
            .first()
        )

        if not node:
            return []

        edges = (
            self.db.query(MemoryEdge)
            .filter(
                (MemoryEdge.source_id == node.id)
                | (MemoryEdge.target_id == node.id)
            )
            .order_by(desc(MemoryEdge.weight))
            .limit(limit)
            .all()
        )

        results: list[dict] = []
        for edge in edges:
            connected_id = (
                edge.target_id if edge.source_id == node.id else edge.source_id
            )
            connected_node = (
                self.db.query(MemoryNode)
                .filter(MemoryNode.id == connected_id)
                .first()
            )

            if connected_node:
                results.append(
                    {
                        "memory_type": connected_node.memory_type,
                        "memory_id": connected_node.memory_id,
                        "label": connected_node.label,
                        "edge_weight": edge.weight,
                        "edge_type": edge.edge_type,
                    }
                )

        return results
