"""Agent event types for the streaming loop.

All events yield from the agent loop as an async generator.
Consumers (API endpoints, SSE streams) iterate over these events.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentMessage:
    """Streaming text output from the agent."""

    text: str


@dataclass
class ToolCall:
    """Tool invocation started — yielded before execution."""

    name: str
    args: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolResult:
    """Tool invocation completed — yielded after execution."""

    name: str
    result: str


@dataclass
class ToolDenied:
    """Tool was denied by policy — no execution happened."""

    name: str
    reason: str = ""


@dataclass
class Compaction:
    """Context was compacted to stay within token budget."""

    summary: str = ""


@dataclass
class Thinking:
    """Agent reasoning step — not user-facing output."""

    text: str = ""


@dataclass
class Done:
    """Task complete — summary of what was accomplished."""

    summary: str = ""
    status: str = "completed"  # "completed", "failed", "incomplete"


AgentEvent = AgentMessage | ToolCall | ToolResult | ToolDenied | Compaction | Thinking | Done
