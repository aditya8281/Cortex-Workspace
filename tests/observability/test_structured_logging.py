"""Tests for structured logging — P07 Task 5."""

from __future__ import annotations

import json
import logging
import time

import pytest

from backend.app.core.structured_logging import AgentLogEntry, StructuredLogger


class TestAgentLogEntry:
    def test_to_json(self):
        entry = AgentLogEntry(
            timestamp="2026-06-27T10:00:00Z",
            level="info",
            event_type="test_event",
            component="test",
            message="test message",
        )
        result = entry.to_json()
        parsed = json.loads(result)
        assert parsed["timestamp"] == "2026-06-27T10:00:00Z"
        assert parsed["level"] == "info"
        assert parsed["event_type"] == "test_event"
        assert parsed["component"] == "test"
        assert parsed["message"] == "test message"

    def test_to_json_strips_none(self):
        entry = AgentLogEntry(
            timestamp="2026-06-27T10:00:00Z",
            level="info",
            event_type="test",
            component="test",
            message="msg",
            duration_ms=None,
            user_id=None,
        )
        result = entry.to_json()
        parsed = json.loads(result)
        assert "duration_ms" not in parsed
        assert "user_id" not in parsed

    def test_to_json_with_metadata(self):
        entry = AgentLogEntry(
            timestamp="2026-06-27T10:00:00Z",
            level="info",
            event_type="test",
            component="test",
            message="msg",
            metadata={"model": "gpt-4o", "tokens": 100},
        )
        result = entry.to_json()
        parsed = json.loads(result)
        assert parsed["metadata"]["model"] == "gpt-4o"


class TestStructuredLogger:
    def test_logger_creates(self):
        logger = StructuredLogger("test_component")
        assert logger.component == "test_component"

    def test_logger_info(self, caplog):
        logger = StructuredLogger("test")
        with caplog.at_level(logging.INFO, logger="cortex.test"):
            logger.info("test_event", "test message", user_id=42)
        # Should not raise

    def test_logger_error(self, caplog):
        logger = StructuredLogger("test")
        with caplog.at_level(logging.ERROR, logger="cortex.test"):
            logger.error("error_event", "something failed")
        # Should not raise


class TestStructuredLoggerTimed:
    def test_timed_context_manager(self):
        logger = StructuredLogger("test")
        with logger.timed("operation", tool_name="test_tool"):
            time.sleep(0.01)
        # Should complete without error

    def test_timed_logs_exception(self):
        logger = StructuredLogger("test")
        with pytest.raises(ValueError), logger.timed("failing_op"):
            raise ValueError("boom")
        # Exception should propagate, not be swallowed
