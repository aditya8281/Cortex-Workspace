"""Tests for agent event types."""

from __future__ import annotations

from backend.app.agents.events import (
    AgentMessage,
    Compaction,
    Done,
    Thinking,
    ToolCall,
    ToolDenied,
    ToolResult,
)


class TestAgentEvents:
    """AgentEvent dataclass construction and basic attributes."""

    def test_agent_message(self):
        e = AgentMessage(text="Hello")
        assert e.text == "Hello"

    def test_tool_call(self):
        e = ToolCall(name="search", args={"q": "test"})
        assert e.name == "search"
        assert e.args == {"q": "test"}

    def test_tool_call_empty_args(self):
        e = ToolCall(name="search")
        assert e.args == {}

    def test_tool_result(self):
        e = ToolResult(name="search", result="found it")
        assert e.name == "search"
        assert e.result == "found it"

    def test_tool_denied(self):
        e = ToolDenied(name="exec_command", reason="Blocked by policy")
        assert e.name == "exec_command"
        assert e.reason == "Blocked by policy"

    def test_compaction(self):
        e = Compaction(summary="Summarized conversation")
        assert e.summary == "Summarized conversation"

    def test_thinking(self):
        e = Thinking(text="Analyzing request...")
        assert e.text == "Analyzing request..."

    def test_done(self):
        e = Done(summary="Task complete", status="completed")
        assert e.summary == "Task complete"
        assert e.status == "completed"

    def test_done_defaults(self):
        e = Done()
        assert e.summary == ""
        assert e.status == "completed"
