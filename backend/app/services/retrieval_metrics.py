"""Retrieval quality metrics and logging."""

from __future__ import annotations

import logging
import time
from collections import deque
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

MAX_HISTORY = 1000


@dataclass
class SearchEvent:
    query: str
    result_count: int
    sources_used: list[str]
    latency_ms: float
    top_score: float
    timestamp: float = field(default_factory=time.time)


class RetrievalMetrics:
    """Track retrieval quality metrics for monitoring."""

    def __init__(self):
        self._history: deque[SearchEvent] = deque(maxlen=MAX_HISTORY)
        self._total_searches = 0
        self._total_results = 0

    def log_search(
        self,
        query: str,
        result_count: int,
        sources_used: list[str],
        latency_ms: float,
        top_score: float = 0.0,
    ) -> None:
        event = SearchEvent(
            query=query,
            result_count=result_count,
            sources_used=sources_used,
            latency_ms=latency_ms,
            top_score=top_score,
        )
        self._history.append(event)
        self._total_searches += 1
        self._total_results += result_count

        logger.info(
            "Search: %d results in %.1fms (sources=%s, top_score=%.3f)",
            result_count, latency_ms, sources_used, top_score,
        )

    def get_stats(self) -> dict:
        if not self._history:
            return {
                "total_searches": 0,
                "avg_results": 0,
                "avg_latency_ms": 0,
                "avg_top_score": 0,
                "zero_result_rate": 0,
            }

        latencies = [e.latency_ms for e in self._history]
        scores = [e.top_score for e in self._history]
        zero_results = sum(1 for e in self._history if e.result_count == 0)

        return {
            "total_searches": self._total_searches,
            "avg_results": round(self._total_results / max(self._total_searches, 1), 1),
            "avg_latency_ms": round(sum(latencies) / len(latencies), 1),
            "avg_top_score": round(sum(scores) / len(scores), 3),
            "zero_result_rate": round(zero_results / max(len(self._history), 1), 3),
        }


_retrieval_metrics: RetrievalMetrics | None = None


def get_retrieval_metrics() -> RetrievalMetrics:
    global _retrieval_metrics
    if _retrieval_metrics is None:
        _retrieval_metrics = RetrievalMetrics()
    return _retrieval_metrics
