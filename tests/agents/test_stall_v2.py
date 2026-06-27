"""Tests for enhanced stall detection — P03 Task 5.

Enhancements over v1.01:
- StallDetection dataclass with structured output
- Timeout detection (wall clock)
- Repeated identical LLM response detection
- Max iteration detection
"""

from __future__ import annotations

import time

from backend.app.agents.stall import StallDetection, StallDetector


class TestStallDetectionDataclass:
    """Structured stall detection result."""

    def test_stall_detection_fields(self):
        sd = StallDetection(
            is_stalled=True,
            reason="Repeated tool call",
            stall_type="repeated_tool",
            iteration=5,
            details={"tool": "read_file"},
        )
        assert sd.is_stalled is True
        assert sd.reason == "Repeated tool call"
        assert sd.stall_type == "repeated_tool"
        assert sd.iteration == 5
        assert sd.details["tool"] == "read_file"

    def test_stall_detection_not_stalled(self):
        sd = StallDetection(is_stalled=False, reason="", iteration=1)
        assert sd.is_stalled is False
        assert sd.stall_type == ""


class TestStallDetectorTimeout:
    """Timeout-based stall detection."""

    def test_no_timeout_when_fast(self):
        detector = StallDetector(timeout_seconds=300)
        start = time.time()
        result = detector.check_timeout(start)
        assert result.is_stalled is False

    def test_timeout_detected(self):
        detector = StallDetector(timeout_seconds=1)
        start = time.time() - 2  # Simulate 2 seconds elapsed
        result = detector.check_timeout(start)
        assert result.is_stalled is True
        assert result.stall_type == "timeout"
        assert "2" in result.reason or "elapsed" in result.reason.lower()

    def test_timeout_custom_threshold(self):
        detector = StallDetector(timeout_seconds=10)
        start = time.time() - 11
        result = detector.check_timeout(start)
        assert result.is_stalled is True


class TestStallDetectorRepeatedResponse:
    """Repeated identical LLM response detection."""

    def test_no_stall_single_response(self):
        detector = StallDetector(repeated_response_threshold=2)
        detector.record_response("I found the answer.")
        result = detector.check_repeated_response()
        assert result.is_stalled is False

    def test_stall_on_repeated_response(self):
        detector = StallDetector(repeated_response_threshold=2)
        detector.record_response("I found the answer.")
        detector.record_response("I found the answer.")
        result = detector.check_repeated_response()
        assert result.is_stalled is True
        assert result.stall_type == "repeated_response"

    def test_no_stall_different_responses(self):
        detector = StallDetector(repeated_response_threshold=2)
        detector.record_response("Response A")
        detector.record_response("Response B")
        result = detector.check_repeated_response()
        assert result.is_stalled is False

    def test_response_history_bounded(self):
        detector = StallDetector(repeated_response_threshold=2, max_response_history=5)
        for i in range(10):
            detector.record_response(f"Response {i}")
        assert len(detector._response_history) <= 5


class TestStallDetectorMaxIterations:
    """Max iteration detection."""

    def test_no_stall_under_limit(self):
        detector = StallDetector(max_iterations=25)
        result = detector.check_max_iterations(10)
        assert result.is_stalled is False

    def test_stall_at_limit(self):
        detector = StallDetector(max_iterations=25)
        result = detector.check_max_iterations(25)
        assert result.is_stalled is True
        assert result.stall_type == "max_iterations"

    def test_stall_over_limit(self):
        detector = StallDetector(max_iterations=25)
        result = detector.check_max_iterations(30)
        assert result.is_stalled is True


class TestStallDetectorCombined:
    """Combined stall check (all conditions)."""

    def test_combined_no_stall(self):
        detector = StallDetector(timeout_seconds=300, max_iterations=25)
        result = detector.check(tool_calls=[], iteration=5, start_time=time.time())
        assert result.is_stalled is False

    def test_combined_tool_stall(self):
        detector = StallDetector(max_identical_calls=3)
        for _ in range(3):
            detector.record_call("read_file", {"path": "/same"})
        result = detector.check(tool_calls=[], iteration=5, start_time=time.time())
        assert result.is_stalled is True
        assert result.stall_type == "repeated_tool"

    def test_combined_timeout_stall(self):
        detector = StallDetector(timeout_seconds=1, max_iterations=25)
        start = time.time() - 5
        result = detector.check(tool_calls=[], iteration=3, start_time=start)
        assert result.is_stalled is True
        assert result.stall_type == "timeout"

    def test_combined_max_iterations(self):
        detector = StallDetector(max_iterations=10, timeout_seconds=300)
        result = detector.check(tool_calls=[], iteration=10, start_time=time.time())
        assert result.is_stalled is True
        assert result.stall_type == "max_iterations"

    def test_reset_clears_all(self):
        detector = StallDetector(max_identical_calls=3)
        for _ in range(3):
            detector.record_call("exec", {"cmd": "ls"})
        detector.record_response("same")
        detector.reset()
        result = detector.check(tool_calls=[], iteration=5, start_time=time.time())
        assert result.is_stalled is False
