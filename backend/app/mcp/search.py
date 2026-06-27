"""MCP tool search — RAG-based tool selection.

When many MCP servers are connected, injecting all tool schemas into the
LLM prompt becomes infeasible (too many tokens). Instead:
1. Embed all tool descriptions
2. For each user message, find top-K relevant tools
3. Inject only relevant tools into the prompt

This is the same pattern used for document retrieval, applied to tools.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class MCPToolSearch:
    """RAG-based tool selection for MCP tools.

    Design:
    - Tool descriptions embedded into vector store (in-memory or Qdrant)
    - Per user message, retrieve top-K relevant tools
    - K is configurable (default: 10)
    - Fallback to keyword search if embedding unavailable
    """

    def __init__(self, embedding_service=None, top_k: int = 10):
        self.embedding_service = embedding_service
        self.top_k = top_k
        self._tool_index: dict[str, dict] = {}
        self._indexed = False

    async def index_tools(self, tools: list[dict]) -> None:
        """Index all tool schemas for search."""
        for tool in tools:
            func = tool.get("function", {})
            name = func.get("name", "")
            description = func.get("description", "")

            embedding = None
            if self.embedding_service:
                embedding = await self.embedding_service.embed(description)

            self._tool_index[name] = {
                "description": description,
                "embedding": embedding,
                "schema": tool,
            }

        self._indexed = True
        logger.info("Indexed %d tools for search", len(tools))

    async def search(self, query: str, top_k: int | None = None) -> list[dict]:
        """Find top-K relevant tools for a user message.

        Args:
            query: User message text
            top_k: Override default top_k

        Returns:
            List of tool schemas in OpenAI format, ranked by relevance
        """
        k = top_k or self.top_k

        if not self._indexed:
            logger.warning("Tool index not built, returning all tools")
            return list(self._tool_index.values())[:k]

        if self.embedding_service:
            return await self._embedding_search(query, k)

        return self._keyword_search(query, k)

    async def _embedding_search(self, query: str, k: int) -> list[dict]:
        """Vector similarity search."""
        query_embedding = await self.embedding_service.embed(query)

        scored = []
        for _name, entry in self._tool_index.items():
            if entry["embedding"] is None:
                continue
            similarity = self._cosine_similarity(query_embedding, entry["embedding"])
            scored.append((similarity, entry["schema"]))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [schema for _, schema in scored[:k]]

    def _keyword_search(self, query: str, k: int) -> list[dict]:
        """Simple keyword matching fallback."""
        query_words = set(query.lower().split())
        scored = []

        for _name, entry in self._tool_index.items():
            desc_words = set(entry["description"].lower().split())
            overlap = len(query_words & desc_words)
            scored.append((overlap, entry["schema"]))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [schema for _, schema in scored[:k]]

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        """Compute cosine similarity between two vectors."""
        dot = sum(x * y for x, y in zip(a, b, strict=True))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)
