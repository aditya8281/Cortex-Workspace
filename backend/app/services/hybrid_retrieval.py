"""Enhanced hybrid retrieval with multi-collection search, RRF, and MMR."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from sqlalchemy.orm import Session

from backend.app.core.vector_db import VectorDB, get_vector_db
from backend.app.services.embedding_service import EmbeddingService, get_embedding_service
from backend.app.services.fulltext_search import FullTextSearch, get_fulltext_search

logger = logging.getLogger(__name__)

CODE_COLLECTION = "cortex_code"
MEMORY_COLLECTION = "cortex_memory"
K_RRF = 60  # RRF constant


@dataclass
class RetrievalResult:
    content: str
    source: str  # "vector", "keyword", "graph", "fulltext"
    score: float
    file_path: str = ""
    node_id: int | None = None
    document_id: int | None = None
    chunk_id: int | None = None
    language: str | None = None
    chunk_type: str | None = None
    context: str = ""
    rank: int = 0


class HybridRetrievalV2:
    """Enhanced hybrid retrieval with Reciprocal Rank Fusion and MMR diversity."""

    def __init__(
        self,
        db: Session,
        embedding_service: EmbeddingService | None = None,
        vector_db: VectorDB | None = None,
        fulltext_search: FullTextSearch | None = None,
    ):
        self._db = db
        self._embedder = embedding_service or get_embedding_service()
        self._vector_db = vector_db or get_vector_db()
        self._fulltext = fulltext_search or get_fulltext_search(db)

    def retrieve(
        self,
        query: str,
        repo_id: int | None = None,
        limit: int = 10,
        sources: list[str] | None = None,
        diversity_penalty: float = 0.3,
    ) -> list[RetrievalResult]:
        if sources is None:
            sources = ["vector", "fulltext"]

        all_results: dict[str, list[RetrievalResult]] = {}

        if "vector" in sources:
            all_results["vector"] = self._vector_search(query, repo_id, limit * 3)
        if "fulltext" in sources:
            all_results["fulltext"] = self._fulltext_search(query, repo_id, limit * 3)
        if "graph" in sources:
            all_results["graph"] = self._graph_search(query, limit)

        merged = self._rrf_merge(all_results, limit * 3)
        diverse = self._mmr_rerank(merged, limit, diversity_penalty)
        return diverse

    def _vector_search(
        self, query: str, repo_id: int | None, limit: int
    ) -> list[RetrievalResult]:
        query_vector = self._embedder.embed_single(query)
        results = []

        for collection in [CODE_COLLECTION, MEMORY_COLLECTION]:
            try:
                filter_payload = {}
                if repo_id and collection == CODE_COLLECTION:
                    filter_payload["repo_id"] = repo_id

                hits = self._vector_db.search(
                    collection, query_vector, limit=limit,
                    filter_payload=filter_payload if filter_payload else None,
                )

                for hit in hits:
                    payload = hit.get("payload", {})
                    results.append(RetrievalResult(
                        content=payload.get("content", ""),
                        source="vector",
                        score=hit.get("score", 0.0),
                        file_path=payload.get("file_path", payload.get("path", "")),
                        document_id=payload.get("document_id"),
                        chunk_id=payload.get("chunk_id"),
                        language=payload.get("language"),
                        chunk_type=payload.get("chunk_type"),
                    ))
            except Exception as e:
                logger.warning("Vector search failed on %s: %s", collection, e)

        return results

    def _fulltext_search(
        self, query: str, repo_id: int | None, limit: int
    ) -> list[RetrievalResult]:
        results = []

        code_results = self._fulltext.search_code(query, repo_id=repo_id, limit=limit)
        for r in code_results:
            results.append(RetrievalResult(
                content=r.content,
                source="fulltext",
                score=min(1.0, r.rank),
                file_path=r.file_path,
                chunk_id=r.chunk_id,
                language=r.language,
            ))

        doc_results = self._fulltext.search_documents(query, limit=limit)
        for r in doc_results:
            results.append(RetrievalResult(
                content=r.content,
                source="fulltext",
                score=min(1.0, r.rank),
                document_id=r.document_id,
            ))

        return results

    def _graph_search(self, query: str, limit: int) -> list[RetrievalResult]:
        try:
            from backend.app.models.graph import GraphEdge, GraphNode

            terms = query.lower().split()
            results = []

            for term in terms[:3]:
                nodes = (
                    self._db.query(GraphNode)
                    .filter(GraphNode.name.ilike(f"%{term}%"))
                    .limit(5)
                    .all()
                )

                for node in nodes:
                    edges = (
                        self._db.query(GraphEdge)
                        .filter(
                            (GraphEdge.source_id == node.id) | (GraphEdge.target_id == node.id)
                        )
                        .limit(5)
                        .all()
                    )

                    connected_names = set()
                    for edge in edges:
                        other_id = edge.target_id if edge.source_id == node.id else edge.source_id
                        other = self._db.query(GraphNode).filter(GraphNode.id == other_id).first()
                        if other:
                            connected_names.add(other.name)

                    results.append(RetrievalResult(
                        content=f"{node.name} ({node.node_type}): {', '.join(connected_names)}",
                        source="graph",
                        score=0.4,
                        file_path=node.file_path,
                        node_id=node.id,
                    ))

            return results[:limit]
        except Exception as e:
            logger.warning("Graph search failed: %s", e)
            return []

    def _rrf_merge(
        self,
        source_results: dict[str, list[RetrievalResult]],
        limit: int,
    ) -> list[RetrievalResult]:
        doc_scores: dict[str, float] = {}
        doc_results: dict[str, RetrievalResult] = {}

        for _source_name, results in source_results.items():
            for rank, result in enumerate(results):
                key = self._result_key(result)
                rrf_score = 1.0 / (K_RRF + rank + 1)

                if key in doc_scores:
                    doc_scores[key] += rrf_score
                else:
                    doc_scores[key] = rrf_score
                    doc_results[key] = result

        sorted_keys = sorted(doc_scores.keys(), key=lambda k: doc_scores[k], reverse=True)

        merged = []
        for key in sorted_keys[:limit]:
            result = doc_results[key]
            result.score = doc_scores[key]
            merged.append(result)

        return merged

    def _mmr_rerank(
        self,
        results: list[RetrievalResult],
        limit: int,
        lambda_param: float = 0.3,
    ) -> list[RetrievalResult]:
        if len(results) <= limit:
            return results

        selected = [results[0]]
        remaining = results[1:]

        while len(selected) < limit and remaining:
            best_idx = 0
            best_mmr = -1

            for i, candidate in enumerate(remaining):
                relevance = candidate.score
                max_similarity = max(
                    self._text_similarity(candidate.content, s.content)
                    for s in selected
                )
                mmr = lambda_param * relevance - (1 - lambda_param) * max_similarity

                if mmr > best_mmr:
                    best_mmr = mmr
                    best_idx = i

            selected.append(remaining.pop(best_idx))

        return selected

    @staticmethod
    def _result_key(result: RetrievalResult) -> str:
        if result.document_id:
            return f"doc_{result.document_id}_{result.file_path}"
        if result.file_path:
            return f"file_{result.file_path}"
        return f"node_{result.node_id}_{result.content[:50]}"

    @staticmethod
    def _text_similarity(a: str, b: str) -> float:
        words_a = set(a.lower().split())
        words_b = set(b.lower().split())
        if not words_a or not words_b:
            return 0.0
        intersection = words_a & words_b
        return len(intersection) / max(len(words_a), len(words_b))
