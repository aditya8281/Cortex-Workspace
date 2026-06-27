"""Structured logging — P07 Task 5.

Provides structured JSON logging for agent operations.
"""

from __future__ import annotations

import json
import logging
import time
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any


@dataclass
class AgentLogEntry:
    """Structured log entry for agent operations."""

    timestamp: str = ""
    level: str = "info"
    event_type: str = ""
    component: str = ""
    message: str = ""
    duration_ms: float | None = None
    user_id: int | None = None
    metadata: dict[str, Any] | None = None
    run_id: str | None = None
    model: str | None = None
    token_count: int | None = None

    def to_json(self) -> str:
        """Convert to JSON string, stripping None values."""
        data = {}
        for k, v in self.__dict__.items():
            if v is not None:
                data[k] = v
        return json.dumps(data)


class StructuredLogger:
    """Structured JSON logger for agent operations."""

    def __init__(self, component: str) -> None:
        self.component = component
        self._logger = logging.getLogger(f"cortex.{component}")

    def info(self, event_type: str, message: str, **kwargs: Any) -> None:
        """Log an info event."""
        entry = AgentLogEntry(
            timestamp=self._now(),
            level="info",
            event_type=event_type,
            component=self.component,
            message=message,
            **kwargs,
        )
        self._logger.info(entry.to_json())

    def error(self, event_type: str, message: str, **kwargs: Any) -> None:
        """Log an error event."""
        entry = AgentLogEntry(
            timestamp=self._now(),
            level="error",
            event_type=event_type,
            component=self.component,
            message=message,
            **kwargs,
        )
        self._logger.error(entry.to_json())

    def warning(self, event_type: str, message: str, **kwargs: Any) -> None:
        """Log a warning event."""
        entry = AgentLogEntry(
            timestamp=self._now(),
            level="warning",
            event_type=event_type,
            component=self.component,
            message=message,
            **kwargs,
        )
        self._logger.warning(entry.to_json())

    @contextmanager
    def timed(self, operation: str, **kwargs: Any) -> Generator[None, None, None]:
        """Context manager that logs operation duration."""
        extra_metadata = kwargs if kwargs else None
        start = time.monotonic()
        try:
            yield
        except Exception:
            elapsed = (time.monotonic() - start) * 1000
            self.error(operation, "Operation failed", duration_ms=elapsed, metadata=extra_metadata)
            raise
        else:
            elapsed = (time.monotonic() - start) * 1000
            self.info(operation, "Operation completed", duration_ms=elapsed, metadata=extra_metadata)

    @staticmethod
    def _now() -> str:
        from datetime import datetime, timezone

        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
