"""Stall detector — detects when the agent is stuck in a loop.

Tracks recent tool calls and LLM responses to identify stall patterns:
- 3+ consecutive identical tool calls
- Tool returning the same error repeatedly
- No progress after N iterations (same output structure repeating)
"""

from __future__ import annotations

import logging
from collections import deque
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class StallDetector:
    """Detects stall patterns in agent execution.

    Args:
        max_identical_calls: Max identical consecutive tool calls before stall (default 3).
        lookback: How many recent calls to track (default 10).
    """

    max_identical_calls: int = 3
    lookback: int = 10

    def __post_init__(self) -> None:
        """Initialize mutable state that depends on init parameters."""
        self._recent_tool_calls: deque[dict] = deque(maxlen=self.lookback)
        self._consecutive_identical: int = 0
        self._last_tool_name: str = ""
        self._last_tool_args_hash: int = 0

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

    def is_stalled(self) -> bool:
        """Check if the agent is stalled based on recorded call patterns."""
        # 3+ identical consecutive tool calls
        if self._consecutive_identical >= self.max_identical_calls:
            logger.warning(
                "Stall detected: %d identical calls to '%s'",
                self._consecutive_identical,
                self._last_tool_name,
            )
            return True

        # All lookback slots filled and same tool repeating
        if len(self._recent_tool_calls) >= self.lookback:
            names = {e["name"] for e in self._recent_tool_calls}
            if len(names) <= 1:
                logger.warning("Stall detected: only one tool used in last %d calls", self.lookback)
                return True

        return False

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

    @property
    def total_calls(self) -> int:
        """Total number of tool calls recorded."""
        return len(self._recent_tool_calls)
