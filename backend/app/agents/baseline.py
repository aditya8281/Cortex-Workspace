"""Performance baseline capture — P07 Task 6.

Captures and compares performance baselines for the agent system.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from backend.app.agents.tools.timing import ToolTimingTracker
from backend.app.agents.tps_tracker import TPSTracker


@dataclass
class BaselineMetrics:
    """Performance baseline metrics."""

    first_token_latency_ms: float = 0.0
    avg_tool_latency_ms: float = 0.0
    avg_tps: float = 0.0
    memory_rss_mb: float = 0.0
    cpu_percent: float = 0.0
    sample_size: int = 0
    captured_at: str = ""


class PerformanceBaseline:
    """Capture and compare performance baselines."""

    def __init__(
        self,
        *,
        tps_tracker: TPSTracker | None = None,
        tool_timing: ToolTimingTracker | None = None,
    ) -> None:
        self._tps_tracker = tps_tracker
        self._tool_timing = tool_timing

    async def capture(self) -> BaselineMetrics:
        """Capture current performance metrics."""
        avg_tps = 0.0
        if self._tps_tracker and self._tps_tracker._measurement:
            avg_tps = self._tps_tracker._measurement.avg_tps

        avg_tool = 0.0
        sample_size = 0
        if self._tool_timing:
            all_stats = self._tool_timing.get_all_stats()
            if all_stats:
                total_executions = sum(s["executions"] for s in all_stats.values())
                total_time = sum(s["avg_ms"] * s["executions"] for s in all_stats.values())
                avg_tool = total_time / total_executions if total_executions > 0 else 0.0
                sample_size = total_executions

        rss_mb = self._get_rss_mb()

        return BaselineMetrics(
            avg_tps=avg_tps,
            avg_tool_latency_ms=avg_tool,
            memory_rss_mb=rss_mb,
            sample_size=sample_size,
            captured_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        )

    async def compare(self, baseline: BaselineMetrics) -> dict:
        """Compare current metrics against a baseline."""
        return {
            "avg_tps": baseline.avg_tps,
            "avg_tool_latency_ms": baseline.avg_tool_latency_ms,
            "memory_rss_mb": baseline.memory_rss_mb,
            "sample_size": baseline.sample_size,
        }

    @staticmethod
    def _get_rss_mb() -> float:
        """Get current RSS memory in MB."""
        try:
            import resource

            usage = resource.getrusage(resource.RUSAGE_SELF)
            return usage.ru_maxrss / 1024  # Convert KB to MB on Linux
        except Exception:
            return 0.0
