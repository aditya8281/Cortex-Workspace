"""Vector database abstraction over Qdrant with graceful fallback.

Uses circuit breaker for resilience — if Qdrant is down, operations silently
fall back to no-op / empty results instead of crashing.
"""
from __future__ import annotations

import logging
from uuid import UUID

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, FieldCondition, Filter, MatchValue, VectorParams

from backend.app.core.config import settings
from backend.app.core.circuit_breaker import qdrant_circuit_breaker

logger = logging.getLogger(__name__)

VECTOR_SIZE = settings.EMBEDDING_DIM

PointId = int | str | UUID


class VectorDB:
    """Qdrant-based vector database with circuit-breaker protected access.

    Gracefully degrades when Qdrant is unavailable — all operations become
    no-ops and return empty results. Reconnects on first use after recovery.
    """

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        prefer_grpc: bool | None = None,
    ):
        self._host = host or settings.QDRANT_HOST
        self._port = port or settings.QDRANT_PORT
        self._prefer_grpc = prefer_grpc if prefer_grpc is not None else settings.QDRANT_PREFER_GRPC
        self._client: QdrantClient | None = None
        self._available: bool | None = None  # None = not yet checked
        self._connect()

    # ── Connection management ──────────────────────────────────────────────

    def _connect(self) -> bool:
        """Try to connect to Qdrant. Returns True if successful."""
        if not qdrant_circuit_breaker.allow_request():
            self._available = False
            return False

        try:
            self._client = QdrantClient(
                host=self._host,
                port=self._port,
                prefer_grpc=self._prefer_grpc,
                timeout=5.0,  # Fast fail — don't hang startup
            )
            # Probe the connection
            self._client.get_collections()
            self._available = True
            qdrant_circuit_breaker.record_success()
            if self._available is None or not self._available:
                logger.info("Qdrant connection established at %s:%s", self._host, self._port)
            return True
        except Exception as e:
            self._client = None
            self._available = False
            qdrant_circuit_breaker.record_failure()
            logger.warning(
                "Qdrant not available at %s:%s — vector search disabled (%s)",
                self._host, self._port, e,
            )
            return False

    def _ensure_connected(self) -> bool:
        """Re-check connection if previously unavailable.

        Returns True if Qdrant is available (now or still), False to degrade.
        """
        if self._available:
            return True
        # Try to reconnect (circuit breaker gates this)
        return self._connect()

    @property
    def is_available(self) -> bool:
        """Whether Qdrant is currently reachable."""
        return self._available is True

    # ── Operations ─────────────────────────────────────────────────────────

    def upsert(self, collection: str, points: list[dict]) -> None:
        if not self._ensure_connected():
            logger.debug("Qdrant unavailable — skipping upsert to '%s'", collection)
            return
        try:
            if not self._client.collection_exists(collection):
                self._client.create_collection(
                    collection_name=collection,
                    vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
                )
            qdrant_points = [
                models.PointStruct(
                    id=p["id"] if isinstance(p.get("id"), (int, str, UUID)) else str(p.get("id", "")),
                    vector=(p["vector"] if isinstance(p.get("vector"), (list, dict)) else []),
                    payload=p.get("payload", {}),
                )
                for p in points
            ]
            self._client.upsert(collection_name=collection, points=qdrant_points)
            qdrant_circuit_breaker.record_success()
        except Exception as e:
            logger.error("Qdrant upsert failed: %s", e)
            self._available = False
            qdrant_circuit_breaker.record_failure()

    def search(
        self,
        collection: str,
        query: list[float],
        limit: int = 10,
        filter_payload: dict | None = None,
    ) -> list[dict]:
        if not self._ensure_connected():
            return []

        try:
            if not self._client.collection_exists(collection):
                return []

            query_filter = None
            if filter_payload:
                conditions = [
                    FieldCondition(key=k, match=MatchValue(value=v))
                    for k, v in filter_payload.items()
                ]
                query_filter = Filter(must=list(conditions))

            result = self._client.query_points(
                collection_name=collection,
                query=query,
                limit=limit,
                query_filter=query_filter,
            )
            qdrant_circuit_breaker.record_success()
            return [{"id": p.id, "score": p.score, "payload": p.payload or {}} for p in result.points]
        except Exception as e:
            logger.error("Qdrant search failed: %s", e)
            self._available = False
            qdrant_circuit_breaker.record_failure()
            return []

    def delete(self, collection: str, point_ids: list[str]) -> None:
        if not self._ensure_connected():
            return
        try:
            if self._client.collection_exists(collection):
                self._client.delete(
                    collection_name=collection,
                    points_selector=models.PointIdsList(points=list(point_ids)),
                )
            qdrant_circuit_breaker.record_success()
        except Exception as e:
            logger.error("Qdrant delete failed: %s", e)
            self._available = False
            qdrant_circuit_breaker.record_failure()

    def list_collections(self) -> list[str]:
        if not self._ensure_connected():
            return []
        try:
            cols = [c.name for c in self._client.get_collections().collections]
            qdrant_circuit_breaker.record_success()
            return cols
        except Exception as e:
            logger.error("Qdrant list_collections failed: %s", e)
            self._available = False
            qdrant_circuit_breaker.record_failure()
            return []


_vector_db: VectorDB | None = None


def get_vector_db() -> VectorDB:
    """Get or create the global VectorDB singleton."""
    global _vector_db
    if _vector_db is None:
        _vector_db = VectorDB()
    return _vector_db
