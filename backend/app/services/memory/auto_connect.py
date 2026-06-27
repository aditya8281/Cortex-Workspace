"""Auto-connection service — finds related memories and creates graph edges."""

from __future__ import annotations

import re

from sqlalchemy.orm import Session

from backend.app.models.memory.episodic import EpisodicMemory
from backend.app.models.memory.memory_graph import MemoryEdge
from backend.app.models.memory.semantic import SemanticMemory
from backend.app.services.memory.memory_graph_service import MemoryGraphService

# Common stop words to exclude from keyword extraction
STOP_WORDS: set[str] = {
    "the",
    "a",
    "an",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "have",
    "has",
    "had",
    "do",
    "does",
    "did",
    "will",
    "would",
    "could",
    "should",
    "may",
    "might",
    "shall",
    "can",
    "need",
    "dare",
    "ought",
    "used",
    "to",
    "of",
    "in",
    "for",
    "on",
    "with",
    "at",
    "by",
    "from",
    "as",
    "into",
    "through",
    "during",
    "before",
    "after",
    "above",
    "below",
    "between",
    "out",
    "off",
    "over",
    "under",
    "again",
    "further",
    "then",
    "once",
    "here",
    "there",
    "when",
    "where",
    "why",
    "how",
    "all",
    "both",
    "each",
    "few",
    "more",
    "most",
    "other",
    "some",
    "such",
    "no",
    "nor",
    "not",
    "only",
    "own",
    "same",
    "so",
    "than",
    "too",
    "very",
    "just",
    "because",
    "but",
    "and",
    "or",
    "if",
    "while",
    "about",
    "it",
    "its",
    "this",
    "that",
    "these",
    "those",
    "i",
    "me",
    "my",
    "we",
    "our",
    "you",
    "your",
    "he",
    "him",
    "his",
    "she",
    "her",
    "they",
    "them",
    "their",
}

# Minimum keyword length
MIN_KEYWORD_LENGTH = 3


class AutoConnectionService:
    """Automatically creates connections between related memories.

    Uses keyword-based matching in v1.03. Will be enhanced with
    embedding similarity in v1.07.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.graph = MemoryGraphService(db)

    def _extract_keywords(self, content: str) -> set[str]:
        """Extract meaningful keywords from content."""
        words = re.findall(r"[a-z0-9]+", content.lower())
        return {w for w in words if len(w) >= MIN_KEYWORD_LENGTH and w not in STOP_WORDS}

    def connect_related(
        self,
        user_id: int,
        memory_type: str,
        memory_id: int,
        content: str,
        max_connections: int = 5,
    ) -> list[MemoryEdge]:
        """Find and connect related memories via keyword overlap."""
        # Get or create the node for this memory
        source_node = self.graph.add_node(
            user_id=user_id,
            memory_type=memory_type,
            memory_id=memory_id,
            label=content[:100],
        )

        # Extract keywords
        keywords = self._extract_keywords(content)
        if not keywords:
            return []

        # Search for related memories (excluding this one)
        related_memories: list[tuple[str, int, int, str]] = []

        # Search episodic memories
        episodic_query = self.db.query(EpisodicMemory).filter(EpisodicMemory.user_id == user_id)
        if memory_type == "episodic":
            episodic_query = episodic_query.filter(EpisodicMemory.id != memory_id)
        episodic = episodic_query.all()

        for mem in episodic:
            mem_keywords = self._extract_keywords(mem.content)
            overlap = keywords & mem_keywords
            if overlap:
                related_memories.append(("episodic", mem.id, len(overlap), mem.content))

        # Search semantic memories
        semantic_query = self.db.query(SemanticMemory).filter(SemanticMemory.user_id == user_id)
        if memory_type == "semantic":
            semantic_query = semantic_query.filter(SemanticMemory.id != memory_id)
        semantic = semantic_query.all()

        for mem in semantic:
            mem_keywords = self._extract_keywords(mem.content)
            overlap = keywords & mem_keywords
            if overlap:
                related_memories.append(("semantic", mem.id, len(overlap), mem.content))

        # Sort by keyword overlap (most related first)
        related_memories.sort(key=lambda x: x[2], reverse=True)
        related_memories = related_memories[:max_connections]

        # Create edges
        created_edges: list[MemoryEdge] = []
        for mem_type, mem_id, overlap_count, mem_content in related_memories:
            target_node = self.graph.add_node(
                user_id=user_id,
                memory_type=mem_type,
                memory_id=mem_id,
                label=mem_content[:100],
            )

            weight = min(1.0, overlap_count / max(len(keywords), 1))

            edge = self.graph.add_edge(
                source_id=source_node.id,
                target_id=target_node.id,
                edge_type="related_to",
                weight=weight,
                bidirectional=True,
            )
            created_edges.append(edge)

        return created_edges
