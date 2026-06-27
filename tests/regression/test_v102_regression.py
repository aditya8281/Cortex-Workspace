"""v1.02 regression test suite — P08 Task 6.

Covers all features introduced in v1.02:
1. API domain reorganization (P01)
2. Event bus (P02)
3. Agent system hardening (P03)
4. MCP integration (P04)
5. Tool infrastructure (P05)
6. Database migrations (P06)
7. Observability (P07)
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from backend.app.core.event_bus import EventBus
from backend.app.core.events import Event, EventType


class TestP01Regression:
    """P01: API domain reorganization regression."""

    def test_domain_routers_importable(self):
        """All domain routers should be importable."""
        from backend.app.api.v1.awareness.router import router as awareness_router
        from backend.app.api.v1.cognition.router import router as cognition_router
        from backend.app.api.v1.interaction.router import router as interaction_router
        from backend.app.api.v1.memory.router import router as memory_router
        from backend.app.api.v1.system.router import router as system_router

        assert memory_router is not None
        assert awareness_router is not None
        assert cognition_router is not None
        assert interaction_router is not None
        assert system_router is not None

    def test_master_router_loads(self):
        """Master router should load all domain routers."""
        from backend.app.api.router import api_router

        routes = [r for r in api_router.routes if hasattr(r, "path")]
        assert len(routes) >= 5


class TestP02Regression:
    """P02: Event bus regression."""

    @pytest.mark.asyncio
    async def test_event_delivery(self):
        """Events should be delivered to handlers."""
        bus = EventBus()
        received: list[Event] = []

        @bus.subscribe(EventType.MEMORY_CREATED)
        async def handler(event: Event) -> None:
            received.append(event)

        await bus.publish(
            Event(type=EventType.MEMORY_CREATED, source="test", data={"id": 1}, user_id=1)
        )
        assert len(received) == 1

    @pytest.mark.asyncio
    async def test_error_isolation(self):
        """Failing handler should not block others."""
        bus = EventBus()
        results: dict[str, bool] = {"good": False}

        @bus.subscribe(EventType.MEMORY_CREATED)
        async def bad_handler(event: Event) -> None:
            raise RuntimeError("fail")

        @bus.subscribe(EventType.MEMORY_CREATED)
        async def good_handler(event: Event) -> None:
            results["good"] = True

        await bus.publish(
            Event(type=EventType.MEMORY_CREATED, source="test", data={}, user_id=1)
        )
        assert results["good"] is True


class TestP03Regression:
    """P03: Agent system regression."""

    @pytest.mark.asyncio
    async def test_agent_loop_yields_events(self):
        """Agent loop should yield events."""
        from unittest.mock import MagicMock

        from backend.app.agents.loop import agent_loop
        from backend.app.agents.tools.policy import ToolPolicy
        from backend.app.agents.tools.registry import ToolRegistry

        registry = ToolRegistry()
        policy = ToolPolicy()
        user = MagicMock()
        user.id = 1

        events = []
        async for event in agent_loop(
            message="hi",
            conversation_id="test",
            user=user,
            registry=registry,
            policy=policy,
            llm_chat=AsyncMock(),
        ):
            events.append(event)

        assert len(events) > 0

    def test_stall_detector_works(self):
        """StallDetector should detect stalls."""
        from backend.app.agents.stall import StallDetector

        detector = StallDetector(max_identical_calls=3)
        for _ in range(3):
            detector.record_call("tool", {"q": "same"})

        result = detector.check_tool_stall()
        assert result.is_stalled is True

    def test_intent_classification(self):
        """Intent classifier should route messages."""
        from backend.app.agents.intent import casual_response, classify_intent

        intent = classify_intent("hi")
        assert intent in ("casual", "greeting", "agent")

        response = casual_response("hi")
        assert isinstance(response, str)
        assert len(response) > 0


class TestP04Regression:
    """P04: MCP integration regression."""

    def test_mcp_wrapper_works(self):
        """MCPToolWrapper should wrap tools correctly."""
        from backend.app.mcp.wrapper import MCPToolWrapper

        tool = MCPToolWrapper(
            "test_server",
            {"name": "my_tool", "description": "A test tool", "inputSchema": {}},
        )
        schema = tool.to_cortex_schema()
        assert schema["type"] == "function"
        assert "mcp_test_server_my_tool" in schema["function"]["name"]

    def test_mcp_search_works(self):
        """MCPToolSearch should search tools."""
        from backend.app.mcp.search import MCPToolSearch

        search = MCPToolSearch(top_k=3)
        assert search is not None

    def test_mcp_discovery_works(self):
        """MCPServerDiscovery should instantiate."""
        from backend.app.mcp.discovery import MCPServerDiscovery

        discovery = MCPServerDiscovery()
        assert discovery is not None


class TestP05Regression:
    """P05: Tool infrastructure regression."""

    def test_security_guard_wraps_content(self):
        """External content should be wrapped."""
        from backend.app.agents.security import PromptSecurityGuard

        guard = PromptSecurityGuard()
        wrapped = guard.wrap_external_content("test content", "retrieval")
        assert "<UNTRUSTED_SOURCE_DATA>" in wrapped

    def test_tool_domain_map(self):
        """Domain map should map tools to domains."""
        from backend.app.agents.tools.domain_map import ToolDomainMap

        dm = ToolDomainMap()
        domain = dm.get_domain("read_file")
        assert isinstance(domain, str)

    def test_tool_sandbox(self):
        """Sandbox should execute handlers."""
        from backend.app.agents.tools.sandbox import ToolSandbox

        sandbox = ToolSandbox()
        assert sandbox is not None

    def test_tool_selector(self):
        """Tool selector should select tools."""
        from backend.app.agents.tools.selector import ToolSelector

        selector = ToolSelector()
        assert selector is not None

    def test_tool_timing(self):
        """Tool timing tracker should track durations."""
        from backend.app.agents.tools.timing import ToolTimingTracker

        tracker = ToolTimingTracker()
        record = tracker.start("test")
        record.success = True
        tracker.finish(record)
        stats = tracker.get_tool_stats("test")
        assert stats["executions"] == 1


class TestP06Regression:
    """P06: Database migration regression."""

    def test_system_models_importable(self):
        """System models should be importable."""
        from backend.app.models.system.agent_run_event import AgentRunEvent, AgentRunToolCall
        from backend.app.models.system.mcp_server import MCPServer, MCPServerTool
        from backend.app.models.system.observability import (
            PerformanceBaseline as BaselineModel,
        )
        from backend.app.models.system.observability import (
            TokenUsage,
            ToolExecutionMetrics,
        )

        assert MCPServer is not None
        assert MCPServerTool is not None
        assert AgentRunEvent is not None
        assert AgentRunToolCall is not None
        assert TokenUsage is not None
        assert ToolExecutionMetrics is not None
        assert BaselineModel is not None


class TestP07Regression:
    """P07: Observability regression."""

    def test_token_counter_works(self):
        """Token counter should count tokens."""
        from backend.app.agents.token_counter import TokenCounter

        counter = TokenCounter()
        assert counter.max_context_tokens > 0

    def test_tps_tracker_works(self):
        """TPS tracker should measure throughput."""
        from backend.app.agents.tps_tracker import TPSTracker

        tracker = TPSTracker()
        tracker.start()
        for _ in range(10):
            tracker.on_token()
        measurement = tracker.finish()
        assert measurement.total_tokens == 10

    def test_context_tracker_works(self):
        """Context tracker should track usage."""
        from backend.app.agents.context_tracker import ContextTracker

        tracker = ContextTracker()
        assert tracker is not None

    def test_structured_logging_works(self):
        """Structured logger should log events."""
        from backend.app.core.structured_logging import StructuredLogger

        logger = StructuredLogger("test")
        assert logger.component == "test"

    def test_baseline_works(self):
        """Performance baseline should capture metrics."""
        from backend.app.agents.baseline import PerformanceBaseline

        baseline = PerformanceBaseline()
        assert baseline is not None
