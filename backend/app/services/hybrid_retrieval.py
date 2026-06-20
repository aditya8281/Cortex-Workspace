from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass

from sqlalchemy.orm import Session

from backend.app.core.vector_db import get_vector_db
from backend.app.models.graph import GraphEdge, GraphNode
from backend.app.models.repo_index import CodeChunk

logger = logging.getLogger(__name__)

CODE_COLLECTION = "cortex_code"


@dataclass
class RetrievalResult:
    content: str
    source: str  # "vector", "keyword", "graph"
    score: float
    file_path: str | None = None
    node_id: int | None = None
    context: dict | None = None


class HybridRetrieval:
    """Combines vector similarity, keyword matching, and graph traversal for retrieval."""

    def __init__(self, db: Session):
        self._db = db

    async def retrieve(
        self,
        query: str,
        repo_id: int | None = None,
        max_results: int = 20,
        use_reranking: bool = True,
    ) -> list[RetrievalResult]:
        """Hybrid retrieval: vector + keyword + graph, then rerank."""
        vector_results = await self._vector_search(query, repo_id, max_results)
        keyword_results = await self._keyword_search(query, repo_id, max_results)
        graph_results = await self._graph_search(query, repo_id, max_results)

        all_results = self._merge_results(vector_results, keyword_results, graph_results)

        if use_reranking and len(all_results) > 3:
            all_results = await self._rerank(query, all_results)

        return all_results[:max_results]

    async def _vector_search(self, query: str, repo_id: int | None, limit: int) -> list[RetrievalResult]:
        """Semantic vector search."""
        try:
            from backend.app.services.embedding_service import get_embedding_service
            embedding_svc = get_embedding_service()
            vdb = get_vector_db()

            query_vector = embedding_svc.embed_single(query)

            filter_payload: dict[str, str | int] = {}
            if repo_id is not None:
                filter_payload["repo_id"] = repo_id

            results = vdb.search(
                CODE_COLLECTION,
                query_vector,
                limit=limit,
                filter_payload=filter_payload if filter_payload else None,
            )
            return [
                RetrievalResult(
                    content=r.get("payload", {}).get("content", ""),
                    source="vector",
                    score=r.get("score", 0.0),
                    file_path=r.get("payload", {}).get("file_path"),
                    node_id=r.get("payload", {}).get("chunk_id"),
                )
                for r in results
            ]
        except Exception as e:
            logger.warning("Vector search failed: %s", e)
            return []

    async def _keyword_search(self, query: str, repo_id: int | None, limit: int) -> list[RetrievalResult]:
        """PostgreSQL full-text search."""
        try:
            query_lower = query.lower()
            q = self._db.query(CodeChunk).filter(
                CodeChunk.content.ilike(f"%{query_lower}%")
            )
            if repo_id is not None:
                q = q.filter(CodeChunk.repo_id == repo_id)
            chunks = q.limit(limit).all()
            return [
                RetrievalResult(
                    content=c.content[:500],
                    source="keyword",
                    score=0.5,
                    file_path=c.file_path,
                )
                for c in chunks
            ]
        except Exception as e:
            logger.warning("Keyword search failed: %s", e)
            return []

    async def _graph_search(self, query: str, repo_id: int | None, limit: int) -> list[RetrievalResult]:
        """Graph-based retrieval — find nodes related to query and traverse edges."""
        try:
            query_terms = query.lower().split()
            q = self._db.query(GraphNode)
            if repo_id is not None:
                q = q.filter(GraphNode.repo_id == repo_id)
            nodes = q.limit(200).all()

            matched_nodes = []
            for node in nodes:
                name = (node.name or "").lower()
                if any(term in name for term in query_terms):
                    matched_nodes.append(node)

            results = []
            for node in matched_nodes[:limit]:
                edges = self._db.query(GraphEdge).filter(
                    (GraphEdge.source_id == node.id) | (GraphEdge.target_id == node.id)
                ).limit(5).all()

                context = {
                    "node_name": node.name,
                    "node_type": node.node_type,
                    "edges": [
                        {
                            "type": e.edge_type,
                            "target": e.target_id,
                        }
                        for e in edges
                    ],
                }
                results.append(RetrievalResult(
                    content=f"Symbol: {node.name} ({node.node_type})",
                    source="graph",
                    score=0.4,
                    node_id=node.id,
                    context=context,
                ))

            return results
        except Exception as e:
            logger.warning("Graph search failed: %s", e)
            return []

    def _merge_results(
        self,
        vector: list[RetrievalResult],
        keyword: list[RetrievalResult],
        graph: list[RetrievalResult],
    ) -> list[RetrievalResult]:
        """Merge results with score boosting for multi-source matches."""
        seen: dict[str, RetrievalResult] = {}
        for result in vector + keyword + graph:
            key = result.file_path or str(result.node_id) or result.content[:100]
            if key in seen:
                existing = seen[key]
                existing.score = min(existing.score + 0.2, 1.0)
                existing.source = f"{existing.source}+{result.source}"
            else:
                seen[key] = result

        return sorted(seen.values(), key=lambda r: r.score, reverse=True)

    async def _rerank(self, query: str, results: list[RetrievalResult]) -> list[RetrievalResult]:
        """Use LLM to rerank results by relevance with robust JSON parsing."""
        try:
            from backend.app.services.llm.manager import llm_manager
            from backend.app.services.llm.provider import LLMMessage

            # Take top 10 for reranking
            candidates = results[:10]
            context_text = "\n\n".join(
                f"[{i+1}] ({r.source}) {r.content[:200]}"
                for i, r in enumerate(candidates)
            )

            messages = [
                LLMMessage(role="system", content=(
                    "You are a search ranking assistant. Given a query and search results, "
                    "return a JSON array of result indices ranked by relevance (most relevant first). "
                    "Only return the JSON array, nothing else. Example: [3, 1, 5, 2, 4]"
                )),
                LLMMessage(role="user", content=f"Query: {query}\n\nResults:\n{context_text}"),
            ]

            response = await llm_manager.chat(messages, max_tokens=256, temperature=0.1)
            ranking = self._parse_ranking(response.content)
            if not ranking:
                return results

            reranked = [candidates[i - 1] for i in ranking if 0 < i <= len(candidates)]
            ranked_ids = {id(r) for r in reranked}
            reranked.extend(r for r in candidates if id(r) not in ranked_ids)

            return reranked
        except Exception as e:
            logger.warning("LLM reranking failed, using original order: %s", e)
            return results

    @staticmethod
    def _parse_ranking(text: str) -> list[int] | None:
        """Robustly parse a JSON array of integers from LLM output."""
        text = text.strip()
        # Try direct JSON parse
        try:
            result = json.loads(text)
            if isinstance(result, list):
                return [int(x) for x in result]
        except (json.JSONDecodeError, ValueError):
            pass
        # Fallback: regex extract all integers from the response
        match = re.search(r"\[[\d\s,]+\]", text)
        if match:
            try:
                result = json.loads(match.group())
                return [int(x) for x in result]
            except (json.JSONDecodeError, ValueError):
                pass
        return None
