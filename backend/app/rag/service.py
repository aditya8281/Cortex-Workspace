from __future__ import annotations

import hashlib
import logging

from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.redis import redis_cache
from backend.app.db.session import SessionLocal
from backend.app.rag.index_manager import IndexManager
from backend.app.rag.retriever import RepoRetriever
from backend.app.services.hierarchical_rag import HierarchicalRAGService


class RAGService:

    def __init__(
        self,
        repo_path: str
    ):
        self.repo_path = repo_path
        # Cache retrievers per config key to avoid re-building on every call
        self._retrievers: dict = {}
        # Keep a default retriever for backward-compat warm-up calls with no config
        self._default_key = "BAAI/bge-small-en-v1.5|FAISS|Tree-sitter"
        self._hierarchical_rag = HierarchicalRAGService()

    def _get_retriever(
        self,
        embedding_model: str = None,
        vector_db: str = None,
        code_parsing: str = None
    ) -> RepoRetriever:
        em = embedding_model or "BAAI/bge-small-en-v1.5"
        vd = vector_db or "FAISS"
        cp = code_parsing or "Tree-sitter"
        key = f"{em}|{vd}|{cp}"

        if key not in self._retrievers:
            retriever = RepoRetriever(
                embedding_model=em,
                vector_db=vd,
                code_parsing=cp
            )
            manager = IndexManager(
                repo_path=self.repo_path,
                embedding_model=em,
                vector_db=vd,
                code_parsing=cp
            )
            retriever.vector_store = manager.get_store()
            self._retrievers[key] = retriever

        return self._retrievers[key]

    def initialize(
        self,
        embedding_model: str = None,
        vector_db: str = None,
        code_parsing: str = None
    ):
        """Pre-warm retrieval backends for the given (or default) config."""
        self._hierarchical_rag = HierarchicalRAGService()
        self._get_retriever(embedding_model, vector_db, code_parsing)

    async def search(
        self,
        query: str,
        top_k: int = 5,
        embedding_model: str = None,
        vector_db: str = None,
        code_parsing: str = None
    ):
        em = embedding_model or "BAAI/bge-small-en-v1.5"
        vd = vector_db or "FAISS"
        cp = code_parsing or "Tree-sitter"

        cache_payload = f"{query}||{top_k}||{em}||{vd}||{cp}"
        cache_hash = hashlib.md5(cache_payload.encode("utf-8")).hexdigest()
        cache_key = f"rag_search:{cache_hash}"

        cached_results = await redis_cache.get(cache_key)
        if cached_results is not None:
            logging.getLogger(__name__).info(f"RAG search cache HIT for key {cache_key}")
            return cached_results

        logging.getLogger(__name__).info(
            f"RAG search cache MISS for key {cache_key}. Executing hierarchical retrieval..."
        )

        results = await self._search_hierarchical(query, top_k)
        if not results:
            logging.getLogger(__name__).info(
                "Hierarchical retrieval returned no results; falling back to legacy vector store."
            )
            retriever = self._get_retriever(em, vd, cp)
            legacy_results = retriever.retrieve(query, top_k)
            results = [
                {
                    "score": item.get("score", 0.0),
                    "id": idx,
                    "node_type": "chunk",
                    "text": item.get("data", {}).get("chunk", ""),
                    "file_path": item.get("data", {}).get("file", ""),
                    "metadata": item.get("data", {}),
                    "data": item.get("data", {}),
                }
                for idx, item in enumerate(legacy_results)
            ]

        if results:
            await redis_cache.set(cache_key, results, expire_seconds=settings.LLM_CACHE_TTL_SECONDS)

        return results

    async def _search_hierarchical(self, query: str, top_k: int) -> list[dict]:
        db = SessionLocal()
        try:
            results = await self._hierarchical_rag.search(query, db, top_k=top_k)
        finally:
            db.close()

        transformed: list[dict] = []
        for result in results:
            file_path = result.get("file_path") or ""
            text = result.get("text") or ""
            transformed.append(
                {
                    "score": result.get("score", 0.0),
                    "id": result.get("id"),
                    "node_type": result.get("node_type", "chunk"),
                    "text": text,
                    "file_path": file_path,
                    "metadata": result.get("metadata", {}) or {},
                    "data": {
                        "chunk": text,
                        "file": file_path,
                        "file_path": file_path,
                        "metadata": result.get("metadata", {}) or {},
                    },
                }
            )
        return transformed
