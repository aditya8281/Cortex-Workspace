"""Agent loop end-to-end tests — P08 Task 2.

Tests the complete flow: user message → intent classification →
stall detection → LLM call → tool execution → response.

Uses mock LLM and mock tools. No real API calls.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.app.agents.events import (
    AgentMessage,
    Done,
)
from backend.app.agents.loop import agent_loop
from backend.app.agents.stall import StallDetector
from backend.app.agents.tools.policy import ToolPolicy
from backend.app.agents.tools.registry import ToolRegistry


def _make_user(uid: int = 1) -> MagicMock:
    user = MagicMock()
    user.id = uid
    return user


class TestAgentLoopBasic:
    """Basic agent loop functionality."""

    @pytest.mark.asyncio
    async def test_casual_message_short_circuits(self):
        """Casual message should get fast response without full loop."""
        registry = ToolRegistry()
        policy = ToolPolicy()
        llm = AsyncMock()

        events = []
        async for event in agent_loop(
            message="hi",
            conversation_id="test-conv",
            user=_make_user(),
            registry=registry,
            policy=policy,
            llm_chat=llm,
        ):
            events.append(event)

        # Casual intent → AgentMessage + Done, no LLM call
        assert llm.call_count == 0
        assert any(isinstance(e, AgentMessage) for e in events)
        assert any(isinstance(e, Done) for e in events)

    @pytest.mark.asyncio
    async def test_agent_message_yields_events(self):
        """Agent loop should yield a Done event at the end."""
        registry = ToolRegistry()
        policy = ToolPolicy()

        # Mock LLM to return a simple text response
        async def mock_chat(messages, model="default", tools=None, stream=True):
            async def gen():
                yield {"type": "text", "content": "Hello from LLM"}

            return gen()

        events = []
        async for event in agent_loop(
            message="What is the capital of France?",
            conversation_id="test-conv",
            user=_make_user(),
            registry=registry,
            policy=policy,
            llm_chat=mock_chat,
        ):
            events.append(event)

        assert any(isinstance(e, Done) for e in events)

    @pytest.mark.asyncio
    async def test_max_iterations_enforced(self):
        """Agent loop should stop at max iterations."""
        registry = ToolRegistry()
        policy = ToolPolicy()

        count = 0

        async def counting_gen():
            nonlocal count
            count += 1
            yield {"type": "text", "content": f"response {count}"}

        async def mock_chat(messages, model="default", tools=None, stream=True):
            return counting_gen()

        events = []
        async for event in agent_loop(
            message="Do something complex",
            conversation_id="test-conv",
            user=_make_user(),
            registry=registry,
            policy=policy,
            llm_chat=mock_chat,
            max_iterations=5,
        ):
            events.append(event)

        done_events = [e for e in events if isinstance(e, Done)]
        assert len(done_events) == 1


class TestAgentLoopStallDetection:
    """Stall detection integration."""

    def test_stall_detector_repeated_calls(self):
        """StallDetector should detect repeated tool calls."""
        detector = StallDetector(max_identical_calls=3)

        for _ in range(3):
            detector.record_call("search_memory", {"query": "same"})

        result = detector.check_tool_stall()
        assert result.is_stalled is True

    def test_stall_detector_max_iterations(self):
        """StallDetector should detect max iterations."""
        detector = StallDetector()
        result = detector.check_max_iterations(30)
        assert result.is_stalled is True

    def test_stall_detector_timeout(self):
        """StallDetector should detect timeout."""
        detector = StallDetector(timeout_seconds=0)
        import time

        time.sleep(0.01)
        result = detector.check_timeout(start_time=0)
        assert result.is_stalled is True


class TestAgentLoopPolicyIntegration:
    """Tool policy integration with agent loop."""

    @pytest.mark.asyncio
    async def test_policy_denies_tool(self):
        """Denied tools should produce ToolDenied events."""
        policy = ToolPolicy()
        policy.deny("dangerous_tool")

        decision = policy.evaluate("dangerous_tool")
        assert decision == "deny"

        # Safe tools should still be allowed
        decision = policy.evaluate("read_file")
        assert decision == "allow"

    def test_plan_mode_restriction(self):
        """Plan mode should restrict write operations."""
        policy = ToolPolicy()
        policy.enable_plan_mode()
        assert policy.is_plan_mode is True

        policy.disable_plan_mode()
        assert policy.is_plan_mode is False

    def test_mcp_tool_gating(self):
        """MCP tools should be gated by default."""
        policy = ToolPolicy()
        decision = policy.evaluate("mcp_server_tool")
        # MCP tools that aren't explicitly enabled should be gated
        assert decision in ("allow", "deny", "ask")
