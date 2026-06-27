"""Tests for P06 v1.02 system domain models."""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.db.base import Base
from backend.app.models.system.agent_run_event import AgentRunEvent, AgentRunToolCall
from backend.app.models.system.mcp_server import MCPServer, MCPServerTool
from backend.app.models.system.observability import (
    PerformanceBaseline,
    TokenUsage,
    ToolExecutionMetrics,
)


@pytest.fixture()
def engine():
    """In-memory SQLite engine with all tables."""
    eng = create_engine("sqlite:///:memory:")
    # Import all models so they register with Base.metadata
    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture()
def session(engine):
    """Session bound to in-memory engine."""
    with Session(engine) as s:
        yield s


class TestMCPServerModel:
    def test_create_server(self, session):
        server = MCPServer(
            name="test-server",
            command="npx",
            args=["-y", "@modelcontextprotocol/server"],
            transport="stdio",
            enabled=True,
        )
        session.add(server)
        session.commit()
        assert server.id is not None

    def test_create_server_sse(self, session):
        server = MCPServer(
            name="sse-server",
            transport="sse",
            sse_url="http://localhost:8080/sse",
        )
        session.add(server)
        session.commit()
        assert server.id is not None

    def test_unique_name_constraint(self, session):
        session.add(MCPServer(name="dup", transport="stdio"))
        session.commit()
        session.add(MCPServer(name="dup", transport="stdio"))
        with pytest.raises(IntegrityError):
            session.commit()

    def test_create_tool(self, session):
        server = MCPServer(name="srv", transport="stdio")
        session.add(server)
        session.flush()
        tool = MCPServerTool(
            server_id=server.id,
            tool_name="read_file",
            tool_description="Read a file",
            tool_schema={"type": "object", "properties": {"path": {"type": "string"}}},
        )
        session.add(tool)
        session.commit()
        assert tool.id is not None

    def test_tool_server_relationship(self, session):
        server = MCPServer(name="rel-srv", transport="stdio")
        session.add(server)
        session.flush()
        tool = MCPServerTool(server_id=server.id, tool_name="t1")
        session.add(tool)
        session.commit()

        # Refresh and check relationship
        session.refresh(server)
        assert len(server.tools) == 1
        assert server.tools[0].tool_name == "t1"


class TestAgentRunEventModel:
    def _make_run(self, session):
        """Create a minimal agent run for FK testing."""
        from backend.app.models.cognition.agent import AgentRun

        # Create user first (FK target)
        from backend.app.models.interaction.user import User

        user = User(username="test_user", full_name="Test User", hashed_password="x")
        session.add(user)
        session.flush()

        agent_run = AgentRun(
            agent_id=1,
            user_id=user.id,
            input_text="test",
            status="running",
        )
        session.add(agent_run)
        session.flush()
        return agent_run

    def test_create_event(self, session):
        run = self._make_run(session)
        event = AgentRunEvent(
            run_id=run.id,
            event_type="tool_call",
            event_data={"tool": "read_file"},
            sequence_num=1,
        )
        session.add(event)
        session.commit()
        assert event.id is not None

    def test_create_tool_call(self, session):
        run = self._make_run(session)
        tc = AgentRunToolCall(
            run_id=run.id,
            tool_name="read_file",
            tool_args={"path": "/tmp/test"},
            tool_result="file contents",
            success=True,
            duration_ms=42.5,
        )
        session.add(tc)
        session.commit()
        assert tc.id is not None


class TestObservabilityModels:
    def test_create_token_usage(self, session):
        tu = TokenUsage(
            model="gpt-4",
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
            context_window=8192,
            context_usage_pct=1.83,
        )
        session.add(tu)
        session.commit()
        assert tu.id is not None

    def test_create_tool_metrics(self, session):
        tm = ToolExecutionMetrics(
            tool_name="read_file",
            is_mcp=False,
            success=True,
            duration_ms=12.3,
            output_size_bytes=1024,
        )
        session.add(tm)
        session.commit()
        assert tm.id is not None

    def test_create_tool_metrics_mcp(self, session):
        tm = ToolExecutionMetrics(
            tool_name="mcp_srv_read",
            is_mcp=True,
            mcp_server="srv",
            success=False,
            duration_ms=5000.0,
            error_type="TimeoutError",
        )
        session.add(tm)
        session.commit()
        assert tm.id is not None

    def test_create_baseline(self, session):
        pb = PerformanceBaseline(
            metric_name="avg_tps",
            metric_value=42.5,
            metric_unit="tokens/sec",
            context={"model": "gpt-4", "version": "v1.02"},
        )
        session.add(pb)
        session.commit()
        assert pb.id is not None


class TestSchemaIntrospection:
    """Verify all expected tables and indexes exist after create_all."""

    def test_all_tables_exist(self, engine):
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())
        expected = {
            "mcp_servers",
            "mcp_server_tools",
            "agent_run_events",
            "agent_run_tool_calls",
            "token_usage",
            "tool_execution_metrics",
            "performance_baselines",
        }
        assert expected.issubset(tables), f"Missing tables: {expected - tables}"

    def test_mcp_servers_indexes(self, engine):
        inspector = inspect(engine)
        indexes = {idx["name"] for idx in inspector.get_indexes("mcp_servers")}
        assert "ix_mcp_servers_name" in indexes

    def test_agent_run_events_indexes(self, engine):
        inspector = inspect(engine)
        indexes = {idx["name"] for idx in inspector.get_indexes("agent_run_events")}
        assert "ix_agent_run_events_run_id" in indexes
        assert "ix_agent_run_events_sequence" in indexes
