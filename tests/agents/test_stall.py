"""Tests for stall detector — repeated call detection, force answer."""

from __future__ import annotations

from backend.app.agents.stall import StallDetector


class TestStallDetector:
    """Stall detection logic."""

    def test_no_stall_initially(self):
        sd = StallDetector()
        assert sd.is_stalled() is False
        assert sd.total_calls == 0

    def test_no_stall_with_different_calls(self):
        sd = StallDetector()
        sd.record_call("search", {"q": "hello"})
        sd.record_call("read_file", {"path": "foo.py"})
        sd.record_call("search", {"q": "world"})
        assert sd.is_stalled() is False

    def test_stall_on_identical_calls(self):
        sd = StallDetector(max_identical_calls=3)
        sd.record_call("search", {"q": "hello"})
        sd.record_call("search", {"q": "hello"})
        assert sd.is_stalled() is False  # not yet
        sd.record_call("search", {"q": "hello"})
        assert sd.is_stalled() is True  # 3rd identical

    def test_no_stall_on_same_name_different_args(self):
        sd = StallDetector(max_identical_calls=3)
        sd.record_call("search", {"q": "hello"})
        sd.record_call("search", {"q": "world"})
        sd.record_call("search", {"q": "foo"})
        assert sd.is_stalled() is False  # different args

    def test_no_stall_on_different_names_repeating(self):
        sd = StallDetector(max_identical_calls=3)
        sd.record_call("search", {"q": "x"})
        sd.record_call("read_file", {"path": "y"})
        sd.record_call("search", {"q": "x"})
        sd.record_call("read_file", {"path": "y"})
        sd.record_call("search", {"q": "x"})
        sd.record_call("read_file", {"path": "y"})
        assert sd.is_stalled() is False  # alternating, not same consecutive 3x

    def test_stall_detected_with_none_args(self):
        sd = StallDetector(max_identical_calls=3)
        sd.record_call("search")
        sd.record_call("search")
        sd.record_call("search")
        assert sd.is_stalled() is True

    def test_force_answer_prompt_returns_string(self):
        sd = StallDetector()
        prompt = sd.force_answer_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 20
        assert "provide your best answer" in prompt

    def test_reset_clears_state(self):
        sd = StallDetector(max_identical_calls=3)
        sd.record_call("search", {"q": "x"})
        sd.record_call("search", {"q": "x"})
        sd.record_call("search", {"q": "x"})
        assert sd.is_stalled() is True
        sd.reset()
        assert sd.is_stalled() is False
        assert sd.total_calls == 0

    def test_total_calls_count(self):
        sd = StallDetector()
        assert sd.total_calls == 0
        sd.record_call("a")
        assert sd.total_calls == 1
        sd.record_call("b")
        sd.record_call("c")
        assert sd.total_calls == 3

    def test_lookback_exhaustion_stall(self):
        """All lookback slots filled with same tool."""
        sd = StallDetector(max_identical_calls=5, lookback=5)
        for _ in range(5):
            sd.record_call("search", {"q": "x"})
        assert sd.is_stalled() is True  # 5 identical hit both thresholds

    def test_lookback_only_one_tool(self):
        """All lookback slots filled with same tool but different args."""
        sd = StallDetector(max_identical_calls=10, lookback=4)
        sd.record_call("search", {"q": "a"})
        sd.record_call("search", {"q": "b"})
        sd.record_call("search", {"q": "c"})
        sd.record_call("search", {"q": "d"})
        # 4 calls, all 'search' but different args → only one tool type
        assert sd.is_stalled() is True
