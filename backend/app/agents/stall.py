"""Stall detector — detects when the agent is stuck in a loop.

Tracks recent tool calls and LLM responses to identify stall patterns:
- 3+ consecutive identical tool calls
- Repeated identical LLM responses
- Wall clock timeout
- Max iteration count
"""

from __future__ import annotations

import logging
import time
from collections import deque
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class StallDetection:
    """Structured result of a stall check."""

    is_stalled: bool
    reason: str
    stall_type: str = ""  # "repeated_tool", "repeated_response", "timeout", "max_iterations"
    iteration: int = 0
    details: dict = field(default_factory=dict)


@dataclass
class StallDetector:
    """Detects stall patterns in agent execution.

    Args:
        max_identical_calls: Max identical consecutive tool calls before stall (default 3).
        lookback: How many recent calls to track (default 10).
        repeated_response_threshold: How many repeated identical LLM responses before stall (default 2).
        timeout_seconds: Wall clock timeout in seconds (default 300).
        max_iterations: Hard limit on iterations (default 25).
        max_response_history: Max LLM responses to track for repetition (default 20).
    """

    max_identical_calls: int = 3
    lookback: int = 10
    repeated_response_threshold: int = 2
    timeout_seconds: int = 300
    max_iterations: int = 25
    max_response_history: int = 20

    def __post_init__(self) -> None:
        """Initialize mutable state that depends on init parameters."""
        self._recent_tool_calls: deque[dict] = deque(maxlen=self.lookback)
        self._consecutive_identical: int = 0
        self._last_tool_name: str = ""
        self._last_tool_args_hash: int = 0
        self._response_history: deque[str] = deque(maxlen=self.max_response_history)

    # ── Individual checks (return StallDetection) ───────────────────────

    def check_timeout(self, start_time: float | None = None) -> StallDetection:
        """Check if the agent has exceeded the wall clock timeout."""
        if start_time is None:
            return StallDetection(is_stalled=False, reason="", stall_type="timeout")
        elapsed = time.time() - start_time
        if elapsed > self.timeout_seconds:
            return StallDetection(
                is_stalled=True,
                reason=f"Timeout after {elapsed:.0f}s (limit: {self.timeout_seconds}s)",
                stall_type="timeout",
                details={"elapsed_seconds": elapsed},
            )
        return StallDetection(is_stalled=False, reason="", stall_type="timeout")

    def check_repeated_response(self) -> StallDetection:
        """Check if the agent is repeating the same LLM response."""
        recent = list(self._response_history)[-self.repeated_response_threshold :]
        if len(recent) >= self.repeated_response_threshold and len(set(recent)) == 1:
            return StallDetection(
                is_stalled=True,
                reason=f"Repeated identical LLM response x{self.repeated_response_threshold}",
                stall_type="repeated_response",
            )
        return StallDetection(is_stalled=False, reason="", stall_type="repeated_response")

    def check_max_iterations(self, iteration: int) -> StallDetection:
        """Check if the agent has exceeded the maximum iteration count."""
        if iteration >= self.max_iterations:
            return StallDetection(
                is_stalled=True,
                reason=f"Reached maximum iterations ({self.max_iterations})",
                stall_type="max_iterations",
                iteration=iteration,
            )
        return StallDetection(is_stalled=False, reason="", stall_type="max_iterations")

    def check_tool_stall(self, tool_calls: list[dict] | None = None) -> StallDetection:
        """Check for repeated identical tool calls."""
        if tool_calls:
            for tc in tool_calls:
                self.record_call(
                    tc.get("function", {}).get("name", ""),
                    tc.get("function", {}).get("arguments", ""),
                )

        # 3+ identical consecutive tool calls
        if self._consecutive_identical >= self.max_identical_calls:
            return StallDetection(
                is_stalled=True,
                reason=f"Repeated identical tool call {self._last_tool_name} x{self._consecutive_identical}",
                stall_type="repeated_tool",
                details={"tool_name": self._last_tool_name, "count": self._consecutive_identical},
            )

        # All lookback slots filled and same tool repeating
        if len(self._recent_tool_calls) >= self.lookback:
            names = {e["name"] for e in self._recent_tool_calls}
            if len(names) <= 1:
                return StallDetection(
                    is_stalled=True,
                    reason=f"Only one tool used in last {self.lookback} calls",
                    stall_type="repeated_tool",
                )

        return StallDetection(is_stalled=False, reason="", stall_type="repeated_tool")

    # ── Combined check ──────────────────────────────────────────────────

    def check(
        self,
        tool_calls: list[dict] | None = None,
        iteration: int = 0,
        start_time: float | None = None,
    ) -> StallDetection:
        """Run all stall checks in priority order. Returns first stall found."""
        # 1. Max iterations (hard limit)
        result = self.check_max_iterations(iteration)
        if result.is_stalled:
            return result

        # 2. Timeout
        result = self.check_timeout(start_time)
        if result.is_stalled:
            return result

        # 3. Repeated tool calls
        result = self.check_tool_stall(tool_calls)
        if result.is_stalled:
            return result

        # 4. Repeated responses
        result = self.check_repeated_response()
        if result.is_stalled:
            return result

        return StallDetection(is_stalled=False, reason="", iteration=iteration)

    # ── Recording methods ───────────────────────────────────────────────

    def record_call(self, tool_name: str, tool_args: dict | None = None) -> None:
        """Record a tool call for stall analysis."""
        args_hash = hash(str(tool_args or {}))
        entry = {"name": tool_name, "args_hash": args_hash}
        self._recent_tool_calls.append(entry)

        # Track consecutive identical calls
        if tool_name == self._last_tool_name and args_hash == self._last_tool_args_hash:
            self._consecutive_identical += 1
        else:
            self._consecutive_identical = 1
            self._last_tool_name = tool_name
            self._last_tool_args_hash = args_hash

    def record_response(self, response: str) -> None:
        """Record an LLM response for repetition detection."""
        self._response_history.append(response)

    def force_answer_prompt(self) -> str:
        """Return an instruction to force the LLM to provide its best answer.

        Call this when is_stalled() returns True.
        """
        return (
            "You appear to be repeating the same tool calls without making progress. "
            "Based on what you've gathered so far, please provide your best answer to the user's request. "
            "Do not call any more tools. Synthesize your findings into a response."
        )

    def reset(self) -> None:
        """Reset stall state (e.g., after a stall is handled)."""
        self._recent_tool_calls.clear()
        self._consecutive_identical = 0
        self._last_tool_name = ""
        self._last_tool_args_hash = 0
        self._response_history.clear()

    @property
    def total_calls(self) -> int:
        """Total number of tool calls recorded."""
        return len(self._recent_tool_calls)

    # ── Backward compatibility ──────────────────────────────────────────

    def is_stalled(self) -> bool:
        """Legacy: check if stalled (tool-call-based only)."""
        return self.check_tool_stall().is_stalled
