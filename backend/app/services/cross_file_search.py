"""Cross-file search — semantic search enriched with graph context."""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from backend.app.core.vector_db import get_vector_db
from backend.app.models.graph import GraphEdge, GraphNode
from backend.app.services.embedding_service import get_embedding_service

logger = logging.getLogger(__name__)

CODE_COLLECTION = "cortex_code"


class CrossFileSearch:
    """Semantic search across indexed code with graph enrichment."""

    def __init__(self, db: Session):
        self.db = db

    def search(
        self,
        query: str,
        repo_id: int | None = None,
        node_type: str | None = None,
        language: str | None = None,
        limit: int = 10,
    ) -> list[dict]:
        """Search code chunks using semantic similarity, enriched with graph context."""
        embedding_svc = get_embedding_service()
        vdb = get_vector_db()

        query_vector = embedding_svc.embed_single(query)

        # Build filter
        filter_payload: dict[str, str | int] = {}
        if repo_id is not None:
            filter_payload["repo_id"] = repo_id
        if language is not None:
            filter_payload["language"] = language

        results = vdb.search(
            CODE_COLLECTION,
            query_vector,
            limit=limit * 3,  # Over-fetch for filtering
            filter_payload=filter_payload if filter_payload else None,
        )

        enriched: list[dict] = []
        seen_files: set[str] = set()

        for r in results:
            payload = r.get("payload", {})
            file_path = payload.get("file_path", "")
            chunk_id = payload.get("chunk_id")

            # Find corresponding graph node
            node = None
            if chunk_id:
                node = self.db.query(GraphNode).filter(GraphNode.chunk_id == chunk_id).first()

            # Filter by node_type if specified
            if node_type and node and node.node_type != node_type:
                continue
            if node_type and not node:
                continue

            # Deduplicate by file (keep highest score per file)
            if file_path in seen_files:
                continue
            seen_files.add(file_path)

            # Get graph context
            context = {}
            if node:
                context = self._get_graph_context(node.id)

            name = payload.get("symbol_name") or file_path.split("/")[-1]
            content_preview = payload.get("content", "")[:300]

            enriched.append(
                {
                    "score": r["score"],
                    "chunk_id": chunk_id,
                    "entry_id": chunk_id,  # Alias for compatibility
                    "file_path": file_path,
                    "name": name,
                    "node_type": node.node_type if node else "code",
                    "language": payload.get("language"),
                    "content_preview": content_preview,
                    "start_line": payload.get("start_line"),
                    "end_line": payload.get("end_line"),
                    "context": context,
                }
            )

            if len(enriched) >= limit:
                break

        return enriched

    def _get_graph_context(self, node_id: int) -> dict:
        """Get graph relationships for a node."""
        outgoing = self.db.query(GraphEdge).filter(GraphEdge.source_id == node_id).all()
        incoming = self.db.query(GraphEdge).filter(GraphEdge.target_id == node_id).all()

        return {
            "calls": [e.target.name for e in outgoing if e.edge_type == "calls"],
            "called_by": [e.source.name for e in incoming if e.edge_type == "calls"],
            "imports": [e.target.name for e in outgoing if e.edge_type == "imports"],
            "inherits": [e.target.name for e in outgoing if e.edge_type == "inherits"],
            "contains": [e.target.name for e in outgoing if e.edge_type == "contains"],
        }

    async def hybrid_search(self, query: str, repo_id: int | None = None, max_results: int = 20):
        """Use hybrid retrieval for better results."""
        from backend.app.services.hybrid_retrieval import HybridRetrievalV2 as HybridRetrieval

        retrieval = HybridRetrieval(self.db)
        return await retrieval.retrieve(query, repo_id, max_results)

    def get_file_graph(self, file_path: str, repo_id: int | None = None) -> dict:
        """Get the graph for a specific file."""
        query = self.db.query(GraphNode).filter(GraphNode.file_path == file_path)
        if repo_id is not None:
            query = query.filter(GraphNode.repo_id == repo_id)

        nodes = query.all()
        node_ids = [n.id for n in nodes]

        if not node_ids:
            return {"nodes": [], "edges": []}

        edges = (
            self.db.query(GraphEdge)
            .filter((GraphEdge.source_id.in_(node_ids)) | (GraphEdge.target_id.in_(node_ids)))
            .all()
        )

        return {
            "nodes": [
                {
                    "id": n.id,
                    "name": n.name,
                    "node_type": n.node_type,
                    "file_path": n.file_path,
                    "language": n.language,
                    "start_line": n.start_line,
                    "end_line": n.end_line,
                }
                for n in nodes
            ],
            "edges": [
                {
                    "id": e.id,
                    "source_id": e.source_id,
                    "target_id": e.target_id,
                    "edge_type": e.edge_type,
                    "weight": e.weight,
                }
                for e in edges
            ],
        }
