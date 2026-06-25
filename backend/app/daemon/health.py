"""Health checks: DB, Redis, Qdrant probing.

Provides functions to probe each dependency and a composite health report.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

from backend.app.core.logging import get_logger

logger = get_logger(__name__)

DEFAULT_PROBE_TIMEOUT = 5.0  # seconds per probe


@dataclass
class HealthProbeResult:
    """Result of a single health probe."""

    name: str
    healthy: bool
    detail: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class HealthReport:
    """Composite health report from all probes."""

    healthy: bool
    probes: list[HealthProbeResult] = field(default_factory=list)

    @property
    def summary(self) -> str:
        total = len(self.probes)
        ok = sum(1 for p in self.probes if p.healthy)
        return f"{ok}/{total} dependencies healthy"

    def to_dict(self) -> dict:
        return {
            "healthy": self.healthy,
            "summary": self.summary,
            "probes": [
                {
                    "name": p.name,
                    "healthy": p.healthy,
                    "detail": p.detail,
                    "metadata": p.metadata,
                }
                for p in self.probes
            ],
        }


async def probe_database(timeout: float = DEFAULT_PROBE_TIMEOUT) -> HealthProbeResult:
    """Probe PostgreSQL via SQLAlchemy."""
    try:
        from backend.app.db.session import SessionLocal

        db = SessionLocal()
        try:
            result = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: db.execute("SELECT 1").scalar(),
                ),
                timeout=timeout,
            )
            if result == 1:
                return HealthProbeResult(
                    name="database",
                    healthy=True,
                    detail="PostgreSQL responsive",
                )
            return HealthProbeResult(
                name="database",
                healthy=False,
                detail=f"Unexpected query result: {result}",
            )
        finally:
            db.close()
    except asyncio.TimeoutError:
        return HealthProbeResult(name="database", healthy=False, detail="Probe timed out")
    except Exception as exc:
        return HealthProbeResult(name="database", healthy=False, detail=str(exc))


async def probe_redis(timeout: float = DEFAULT_PROBE_TIMEOUT) -> HealthProbeResult:
    """Probe Redis via ping."""
    try:
        from backend.app.core.redis import redis_cache

        if redis_cache is None:
            return HealthProbeResult(name="redis", healthy=False, detail="Redis not configured")

        result = await asyncio.wait_for(redis_cache.ping(), timeout=timeout)
        if result:
            return HealthProbeResult(name="redis", healthy=True, detail="Redis responsive")
        return HealthProbeResult(name="redis", healthy=False, detail="PING returned false")
    except asyncio.TimeoutError:
        return HealthProbeResult(name="redis", healthy=False, detail="Probe timed out")
    except Exception as exc:
        return HealthProbeResult(name="redis", healthy=False, detail=str(exc))


async def probe_qdrant(timeout: float = DEFAULT_PROBE_TIMEOUT) -> HealthProbeResult:
    """Probe Qdrant via collection list."""
    try:
        vector_db = await asyncio.wait_for(
            _get_qdrant_client(),
            timeout=timeout,
        )
        if vector_db is None:
            return HealthProbeResult(name="qdrant", healthy=False, detail="Qdrant not available")

        # Check collection existence
        collections = await asyncio.wait_for(
            asyncio.get_event_loop().run_in_executor(
                None,
                lambda: vector_db.list_collections() if hasattr(vector_db, "list_collections") else [],
            ),
            timeout=timeout,
        )
        return HealthProbeResult(
            name="qdrant",
            healthy=True,
            detail=f"Qdrant responsive ({len(collections)} collections)",
            metadata={"collection_count": len(collections)},
        )
    except asyncio.TimeoutError:
        return HealthProbeResult(name="qdrant", healthy=False, detail="Probe timed out")
    except Exception as exc:
        return HealthProbeResult(name="qdrant", healthy=False, detail=str(exc))


async def _get_qdrant_client():
    """Get Qdrant client, gracefully returning None if unavailable."""
    try:
        from backend.app.services.memory_manager import get_vector_db

        return get_vector_db()
    except Exception:
        return None


async def check_all(timeout: float | None = None) -> HealthReport:
    """Run all health probes and return composite report.

    Args:
        timeout: Timeout per probe in seconds (default: DEFAULT_PROBE_TIMEOUT).
    """
    t = timeout or DEFAULT_PROBE_TIMEOUT
    probes = await asyncio.gather(
        probe_database(t),
        probe_redis(t),
        probe_qdrant(t),
        return_exceptions=True,
    )

    results: list[HealthProbeResult] = []
    for probe in probes:
        if isinstance(probe, Exception):
            results.append(
                HealthProbeResult(
                    name="unknown",
                    healthy=False,
                    detail=f"Probe raised: {probe}",
                )
            )
        elif isinstance(probe, HealthProbeResult):
            results.append(probe)

    all_healthy = all(r.healthy for r in results)
    return HealthReport(healthy=all_healthy, probes=results)
