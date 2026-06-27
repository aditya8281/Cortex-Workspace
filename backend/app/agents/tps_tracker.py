"""TPS (tokens per second) tracker — P07 Task 2.

Tracks streaming response throughput for performance monitoring.
"""

from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class TPSMeasurement:
    """A single TPS measurement."""

    total_tokens: int = 0
    total_duration: float = 0.0
    avg_tps: float = 0.0
    first_token_latency_ms: float = 0.0
    start_time: float = 0.0


class TPSTracker:
    """Track tokens per second for streaming LLM responses."""

    def __init__(self) -> None:
        self._measurement: TPSMeasurement | None = None
        self._last_token_time: float = 0.0
        self._first_token_recorded: bool = False
        self._instantaneous_window: list[tuple[float, int]] = []

    def start(self) -> None:
        """Start a new tracking session."""
        self._measurement = TPSMeasurement(start_time=time.monotonic())
        self._last_token_time = self._measurement.start_time
        self._first_token_recorded = False
        self._instantaneous_window = []

    def on_token(self, count: int = 1) -> None:
        """Record token(s) received during streaming."""
        if self._measurement is None:
            return
        now = time.monotonic()
        if not self._first_token_recorded:
            self._measurement.first_token_latency_ms = (now - self._measurement.start_time) * 1000
            self._first_token_recorded = True
        self._measurement.total_tokens += count
        self._last_token_time = now
        self._instantaneous_window.append((now, count))

    def finish(self) -> TPSMeasurement:
        """Finish tracking and return the overall TPS measurement."""
        if self._measurement is None:
            return TPSMeasurement()
        elapsed = time.monotonic() - self._measurement.start_time
        self._measurement.total_duration = elapsed
        self._measurement.avg_tps = self._measurement.total_tokens / elapsed if elapsed > 0 else 0.0
        return self._measurement

    def get_instantaneous_tps(self) -> float:
        """Get the current instantaneous TPS based on recent window."""
        if not self._instantaneous_window:
            return 0.0
        total = sum(count for _, count in self._instantaneous_window)
        return float(total)

    def reset(self) -> None:
        """Reset all tracking state."""
        self._measurement = TPSMeasurement()
        self._last_token_time = 0.0
        self._first_token_recorded = False
        self._instantaneous_window = []
