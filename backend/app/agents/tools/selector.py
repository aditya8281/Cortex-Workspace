"""RAG-based tool selection — P05 Task 2.

Embeds tool descriptions and ranks tools by similarity to user queries.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field


@dataclass
class ToolSelector:
    """Selects tools via embedding similarity or keyword fallback."""

    embedding_service: object | None = None  # Protocol: embed(str) -> list[float]
    top_k: int = 8
    min_similarity: float = 0.3
    _tool_embeddings: dict[str, list[float]] = field(default_factory=dict)

    async def index_tools(self, tools: list[dict]) -> None:
        """Index tool descriptions for RAG-based selection."""
        if not self.embedding_service:
            return

        for tool in tools:
            fn = tool.get("function", {})
            name = fn.get("name", "")
            desc = fn.get("description", "")
            if not name or not desc:
                continue

            embedding = await self.embedding_service.embed(desc)  # type: ignore[attr-defined]
            self._tool_embeddings[name] = embedding

    async def select_tools(
        self,
        query: str,
        tools: list[dict],
        context: str | None = None,
    ) -> list[dict]:
        """Select the most relevant tools for a query."""
        # If no embeddings or no embedding service, fallback to top_k by order
        if not self._tool_embeddings or not self.embedding_service:
            return tools[: self.top_k]

        # Embed query (+ optional context)
        search_text = query
        if context:
            search_text = f"{context} {query}"

        query_embedding = await self.embedding_service.embed(search_text)  # type: ignore[attr-defined]

        # Score each tool by cosine similarity
        scored: list[tuple[float, dict]] = []
        for tool in tools:
            fn = tool.get("function", {})
            name = fn.get("name", "")
            tool_embedding = self._tool_embeddings.get(name)
            if tool_embedding is None:
                continue

            similarity = self._cosine_similarity(query_embedding, tool_embedding)
            if similarity >= self.min_similarity:
                scored.append((similarity, tool))

        # Sort descending by similarity, take top_k
        scored.sort(key=lambda x: x[0], reverse=True)
        return [tool for _, tool in scored[: self.top_k]]

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        """Compute cosine similarity between two vectors."""
        if len(a) != len(b) or not a:
            return 0.0

        dot = sum(x * y for x, y in zip(a, b, strict=True))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))

        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0

        return dot / (norm_a * norm_b)
