from __future__ import annotations

import logging
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams

from backend.app.core.config import settings

logger = logging.getLogger(__name__)

QDRANT_HOST = getattr(settings, "QDRANT_HOST", "localhost")
QDRANT_PORT = getattr(settings, "QDRANT_PORT", 6333)
VECTOR_SIZE = getattr(settings, "EMBEDDING_DIM", 768)


class VectorDB:
    """Qdrant-based vector database for semantic search."""

    def __init__(self, host: str = QDRANT_HOST, port: int = QDRANT_PORT):
        self.client = QdrantClient(host=host, port=port, prefer_grpc=False)

    def upsert(self, collection: str, points: list[dict[str, Any]]) -> None:
        if not self.client.collection_exists(collection):
            self.client.create_collection(
                collection_name=collection,
                vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
            )
        qdrant_points = [
            models.PointStruct(id=p.get("id"), vector=p.get("vector"), payload=p.get("payload", {}))
            for p in points
        ]
        self.client.upsert(collection_name=collection, points=qdrant_points)

    def search(self, collection: str, vector: list[float], limit: int = 10) -> list[dict[str, Any]]:
        if not self.client.collection_exists(collection):
            return []
        hits = self.client.search(
            collection_name=collection,
            query_vector=vector,
            limit=limit,
        )
        return [{"id": h.id, "score": h.score, "payload": h.payload} for h in hits]

    def delete(self, collection: str, point_ids: list[str]) -> None:
        if self.client.collection_exists(collection):
            self.client.delete(
                collection_name=collection,
                points_selector=models.PointIdsList(points=point_ids),
            )

    def list_collections(self) -> list[str]:
        return [c.name for c in self.client.get_collections().collections]
