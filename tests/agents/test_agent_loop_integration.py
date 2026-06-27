"""Integration tests for the agent loop — P03 Task 1.

Tests the complete agent flow: intent → stall → verify → done.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.app.agents.events import (
    AgentMessage,
    Done,
    ToolCall,
)
from backend.app.agents.loop import (
    _coerce_args,
    _is_completion_signal,
    _parse_tool_calls,
    _strip_tool_calls,
)


class TestToolCallParsing:
    """Test TOOL_CALL directive parsing."""

    def test_simple_tool_call(self):
        text = 'TOOL_CALL: read_file(path="/etc/hosts")'
        calls = _parse_tool_calls(text)
        assert len(calls) == 1
        assert calls[0]["name"] == "read_file"
        assert calls[0]["args"]["path"] == "/etc/hosts"

    def test_multiple_tool_calls(self):
        text = 'TOOL_CALL: search_memory(query="auth bug")\nTOOL_CALL: read_file(path="/app/main.py")'
        calls = _parse_tool_calls(text)
        assert len(calls) == 2
        assert calls[0]["name"] == "search_memory"
        assert calls[1]["name"] == "read_file"

    def test_no_tool_calls(self):
        text = "I found the bug in the auth module."
        calls = _parse_tool_calls(text)
        assert len(calls) == 0

    def test_nested_parens_in_args(self):
        text = 'TOOL_CALL: read_file(path="file(1).txt")'
        calls = _parse_tool_calls(text)
        assert len(calls) == 1
        assert calls[0]["args"]["path"] == "file(1).txt"


class TestStripToolCalls:
    """Test tool call removal from text."""

    def test_strip_preserves_text(self):
        text = 'Let me check.\nTOOL_CALL: read_file(path="/app/main.py")\nDone.'
        result = _strip_tool_calls(text)
        assert "Let me check." in result
        assert "Done." in result
        assert "TOOL_CALL" not in result

    def test_strip_no_calls(self):
        text = "No tool calls here."
        result = _strip_tool_calls(text)
        assert result == text


class TestCoerceArgs:
    """Test argument type coercion from tool schema."""

    def test_integer_coercion(self):
        schema = {
            "function": {
                "parameters": {
                    "properties": {
                        "limit": {"type": "integer"},
                    }
                }
            }
        }
        result = _coerce_args({"limit": "5"}, schema)
        assert result["limit"] == 5
        assert isinstance(result["limit"], int)

    def test_boolean_coercion(self):
        schema = {
            "function": {
                "parameters": {
                    "properties": {
                        "verbose": {"type": "boolean"},
                    }
                }
            }
        }
        result = _coerce_args({"verbose": "true"}, schema)
        assert result["verbose"] is True

    def test_none_coercion(self):
        schema = {
            "function": {
                "parameters": {
                    "properties": {
                        "optional": {"type": "string"},
                    }
                }
            }
        }
        result = _coerce_args({"optional": "none"}, schema)
        assert result["optional"] is None


class TestCompletionSignal:
    """Test natural completion detection."""

    def test_completion_detected(self):
        assert _is_completion_signal("Task complete.") is True
        assert _is_completion_signal("All done!") is True
        assert _is_completion_signal("Finished.") is True

    def test_no_completion(self):
        assert _is_completion_signal("Let me check the file.") is False
        assert _is_completion_signal("I found an issue.") is False


class TestAgentLoopFlow:
    """Test the agent loop yields correct event sequence."""

    @pytest.mark.asyncio
    async def test_casual_intent_shortcircuits(self):
        """Casual message → AgentMessage + Done, no LLM call."""
        from backend.app.agents.loop import agent_loop
        from backend.app.agents.tools.policy import ToolPolicy
        from backend.app.agents.tools.registry import ToolRegistry

        registry = ToolRegistry()
        policy = ToolPolicy()

        events = []
        async for event in agent_loop(
            message="hello",
            conversation_id="test-1",
            user=MagicMock(id=1),
            registry=registry,
            policy=policy,
            llm_chat=AsyncMock(),
        ):
            events.append(event)

        # Should get AgentMessage (greeting) + Done
        assert any(isinstance(e, AgentMessage) for e in events)
        assert any(isinstance(e, Done) for e in events)
        # No tool calls
        assert not any(isinstance(e, ToolCall) for e in events)

    @pytest.mark.asyncio
    async def test_max_iterations_enforced(self):
        """Loop should stop at max_iterations."""
        from backend.app.agents.loop import agent_loop
        from backend.app.agents.tools.policy import ToolPolicy
        from backend.app.agents.tools.registry import Tool, ToolRegistry

        # Mock LLM that always returns a tool call (infinite loop)
        async def mock_chat(**kwargs):
            result = MagicMock()
            result.content = 'TOOL_CALL: search_memory(query="test")'
            return result

        registry = ToolRegistry()
        policy = ToolPolicy()
        policy.allow("search_memory")

        # Create a mock tool that returns something
        async def mock_handler(**kwargs):
            return "No results"

        tool_obj = Tool(
            name="search_memory",
            description="Search memory",
            handler=mock_handler,
            schema={},
        )
        registry.register(tool_obj)

        events = []
        async for event in agent_loop(
            message="find everything",
            conversation_id="test-2",
            user=MagicMock(id=1),
            registry=registry,
            policy=policy,
            llm_chat=mock_chat,
            max_iterations=3,
        ):
            events.append(event)

        # Should have Done event
        done_events = [e for e in events if isinstance(e, Done)]
        assert len(done_events) == 1
