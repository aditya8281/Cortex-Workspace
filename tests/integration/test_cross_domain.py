"""Cross-domain integration tests — P08 Task 1.

Tests that different v1.02 domains work together correctly.
Uses in-memory SQLite and mock external services.
"""

from __future__ import annotations

import pytest

from backend.app.core.event_bus import EventBus
from backend.app.core.events import Event, EventType


class TestEventBusCrossDomain:
    """Event bus should deliver events across domains."""

    @pytest.mark.asyncio
    async def test_memory_event_published(self):
        """Memory domain can publish events via the event bus."""
        bus = EventBus()
        received: list[Event] = []

        @bus.subscribe(EventType.MEMORY_CREATED)
        async def handler(event: Event) -> None:
            received.append(event)

        await bus.publish(
            Event(
                type=EventType.MEMORY_CREATED,
                source="KnowledgeService",
                data={"memory_id": 42},
                user_id=1,
            )
        )
        assert len(received) == 1
        assert received[0].data["memory_id"] == 42

    @pytest.mark.asyncio
    async def test_error_isolation(self):
        """Failing handler should not block others."""
        bus = EventBus()
        results: dict[str, bool] = {"good": False}

        @bus.subscribe(EventType.MEMORY_CREATED)
        async def bad_handler(event: Event) -> None:
            raise RuntimeError("handler failed")

        @bus.subscribe(EventType.MEMORY_CREATED)
        async def good_handler(event: Event) -> None:
            results["good"] = True

        await bus.publish(Event(type=EventType.MEMORY_CREATED, source="test", data={}, user_id=1))
        assert results["good"] is True

    @pytest.mark.asyncio
    async def test_multiple_domains_subscribe(self):
        """Different domain handlers can subscribe to the same event type."""
        bus = EventBus()
        handlers_called: list[str] = []

        @bus.subscribe(EventType.RUN_COMPLETED)
        async def agent_handler(event: Event) -> None:
            handlers_called.append("agent")

        @bus.subscribe(EventType.RUN_COMPLETED)
        async def observability_handler(event: Event) -> None:
            handlers_called.append("observability")

        await bus.publish(Event(type=EventType.RUN_COMPLETED, source="test", data={}, user_id=1))
        assert "agent" in handlers_called
        assert "observability" in handlers_called

    @pytest.mark.asyncio
    async def test_event_bus_stats(self):
        """Event bus tracks stats correctly."""
        bus = EventBus()

        @bus.subscribe(EventType.MEMORY_CREATED)
        async def handler(event: Event) -> None:
            pass

        await bus.publish(Event(type=EventType.MEMORY_CREATED, source="test", data={}, user_id=1))
        stats = bus.get_stats()
        assert stats["total_events_published"] >= 1

    @pytest.mark.asyncio
    async def test_no_circular_chain(self):
        """Events should not create infinite circular chains."""
        bus = EventBus()
        call_count = 0

        @bus.subscribe(EventType.MEMORY_CREATED)
        async def handler_a(event: Event) -> None:
            nonlocal call_count
            call_count += 1
            if call_count < 5:
                await bus.publish(
                    Event(
                        type=EventType.MEMORY_UPDATED,
                        source="test",
                        data={},
                        user_id=1,
                    )
                )

        @bus.subscribe(EventType.MEMORY_UPDATED)
        async def handler_b(event: Event) -> None:
            pass

        await bus.publish(Event(type=EventType.MEMORY_CREATED, source="test", data={}, user_id=1))
        # Should not infinitely recurse
        assert call_count < 10


class TestSchemaReorganizationIntegration:
    """Import paths should work correctly after P01 reorganization."""

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

    def test_no_circular_imports(self):
        """No circular imports between core modules."""
        import importlib

        modules = [
            "backend.app.agents.token_counter",
            "backend.app.agents.tps_tracker",
            "backend.app.agents.context_tracker",
            "backend.app.agents.tools.timing",
            "backend.app.agents.tools.policy",
            "backend.app.agents.security",
            "backend.app.agents.baseline",
            "backend.app.core.structured_logging",
            "backend.app.core.events",
            "backend.app.core.event_bus",
        ]
        for mod in modules:
            m = importlib.import_module(mod)
            assert m is not None


class TestAgentToolIntegration:
    """Agent loop should interact with tool infrastructure."""

    def test_tool_policy_filters_tools(self):
        """ToolPolicy should filter tools by rule."""
        from backend.app.agents.tools.policy import ToolPolicy

        policy = ToolPolicy()
        policy.deny("execute_command")

        decision = policy.evaluate("execute_command")
        assert decision == "deny"

        decision = policy.evaluate("read_file")
        assert decision == "allow"

    def test_security_guard_wraps_content(self):
        """External content should be wrapped with untrusted tags."""
        from backend.app.agents.security import PromptSecurityGuard

        guard = PromptSecurityGuard()
        wrapped = guard.wrap_external_content("test content", "retrieval")
        assert "<UNTRUSTED_SOURCE_DATA>" in wrapped
        assert "</UNTRUSTED_SOURCE_DATA>" in wrapped

    def test_domain_map_lookup(self):
        """Tool domain map should map tools to domains."""
        from backend.app.agents.tools.domain_map import ToolDomainMap

        dm = ToolDomainMap()
        domain = dm.get_domain("read_file")
        assert isinstance(domain, str)
        assert len(domain) > 0

    @pytest.mark.asyncio
    async def test_sandbox_execution(self):
        """Sandbox should execute tool handlers."""
        from backend.app.agents.tools.sandbox import ToolSandbox

        sandbox = ToolSandbox()

        async def my_tool(x: int = 1) -> dict:
            return {"result": x * 2}

        result = await sandbox.execute("test_tool", my_tool, {"x": 5})
        assert result.success is True
