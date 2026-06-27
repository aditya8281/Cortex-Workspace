"""Tool execution timing — P07 Task 4.

Tracks per-tool execution duration, success/failure, and percentiles.
"""

from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class ToolTimingRecord:
    """Record of a single tool execution."""

    tool_name: str = ""
    start_time: float = 0.0
    end_time: float = 0.0
    duration_ms: float = 0.0
    success: bool = True
    is_mcp: bool = False
    mcp_server: str = ""
    error: str = ""


class ToolTimingTracker:
    """Track tool execution timing with percentile stats."""

    def __init__(self) -> None:
        self._records: dict[str, list[ToolTimingRecord]] = {}

    def start(
        self,
        tool_name: str,
        *,
        is_mcp: bool = False,
        mcp_server: str = "",
    ) -> ToolTimingRecord:
        """Start tracking a tool execution."""
        record = ToolTimingRecord(
            tool_name=tool_name,
            start_time=time.monotonic(),
            is_mcp=is_mcp,
            mcp_server=mcp_server,
        )
        return record

    def finish(self, record: ToolTimingRecord) -> ToolTimingRecord:
        """Finish tracking. Returns the record with duration set.

        If duration_ms was already set manually (e.g. in tests), keep it.
        """
        record.end_time = time.monotonic()
        if record.duration_ms == 0.0:
            record.duration_ms = (record.end_time - record.start_time) * 1000
        self._records.setdefault(record.tool_name, []).append(record)
        return record

    def get_tool_stats(self, tool_name: str) -> dict:
        """Get timing stats for a specific tool."""
        records = self._records.get(tool_name, [])
        if not records:
            return {
                "tool": tool_name,
                "executions": 0,
                "successes": 0,
                "failures": 0,
                "success_rate": 0.0,
                "avg_ms": 0.0,
                "p50_ms": 0.0,
                "p95_ms": 0.0,
                "p99_ms": 0.0,
                "min_ms": 0.0,
                "max_ms": 0.0,
            }
        durations = sorted(r.duration_ms for r in records)
        successes = sum(1 for r in records if r.success)
        return {
            "tool": tool_name,
            "executions": len(records),
            "successes": successes,
            "failures": len(records) - successes,
            "success_rate": successes / len(records),
            "avg_ms": sum(durations) / len(durations),
            "p50_ms": self._percentile(durations, 50),
            "p95_ms": self._percentile(durations, 95),
            "p99_ms": self._percentile(durations, 99),
            "min_ms": durations[0],
            "max_ms": durations[-1],
        }

    def get_all_stats(self) -> dict[str, dict]:
        """Get stats for all tracked tools."""
        return {tool: self.get_tool_stats(tool) for tool in self._records}

    def get_slow_tools(self, *, threshold_ms: float = 1000) -> list[dict]:
        """Get tools with avg latency above threshold."""
        slow = []
        for tool_name in self._records:
            stats = self.get_tool_stats(tool_name)
            if stats["avg_ms"] >= threshold_ms:
                slow.append(stats)
        return slow

    def reset(self) -> None:
        """Clear all records."""
        self._records.clear()

    @staticmethod
    def _percentile(sorted_values: list[float], pct: int) -> float:
        """Calculate percentile from sorted values."""
        if not sorted_values:
            return 0.0
        idx = int(len(sorted_values) * pct / 100)
        idx = min(idx, len(sorted_values) - 1)
        return sorted_values[idx]
