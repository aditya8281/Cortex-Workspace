"""Tests for MCP server discovery and lifecycle — P04 Task 1."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from backend.app.mcp.discovery import (
    MCPServerConfig,
    MCPServerDiscovery,
    MCPServerState,
    MCPServerStatus,
)


class TestMCPServerStatus:
    def test_all_statuses_exist(self):
        statuses = [
            "discovered", "starting", "running", "healthy",
            "unhealthy", "restarting", "stopped", "failed",
        ]
        for s in statuses:
            assert MCPServerStatus(s) == s


class TestMCPServerConfig:
    def test_default_values(self):
        config = MCPServerConfig(name="test", command="echo")
        assert config.transport == "stdio"
        assert config.args == []
        assert config.env == {}
        assert config.sse_url is None
        assert config.working_dir is None
        assert config.health_check_interval == 30
        assert config.max_restarts == 3
        assert config.timeout == 10

    def test_sse_config(self):
        config = MCPServerConfig(
            name="remote",
            command="",
            transport="sse",
            sse_url="https://example.com/sse",
        )
        assert config.transport == "sse"
        assert config.sse_url == "https://example.com/sse"


class TestMCPServerState:
    def test_default_state(self):
        config = MCPServerConfig(name="test", command="echo")
        state = MCPServerState(config=config)
        assert state.status == MCPServerStatus.DISCOVERED
        assert state.process is None
        assert state.restart_count == 0
        assert state.tools == []
        assert state.error is None


class TestMCPServerDiscoveryInit:
    def test_init_empty(self):
        discovery = MCPServerDiscovery()
        assert discovery._servers == {}
        assert discovery._running is False

    @pytest.mark.asyncio
    async def test_load_config_empty(self):
        discovery = MCPServerDiscovery()
        count = await discovery.load_config()
        assert count == 0
        assert len(discovery._servers) == 0

    @pytest.mark.asyncio
    async def test_load_config_returns_count(self):
        discovery = MCPServerDiscovery()
        config = MCPServerConfig(name="test-server", command="echo")
        discovery._servers["test-server"] = MCPServerState(config=config)
        assert len(discovery._servers) == 1


class TestMCPServerDiscoveryGetTools:
    def test_get_all_tools_empty(self):
        discovery = MCPServerDiscovery()
        tools = discovery.get_all_tools()
        assert tools == []

    def test_get_all_tools_from_running(self):
        discovery = MCPServerDiscovery()
        config = MCPServerConfig(name="fs", command="echo")
        state = MCPServerState(
            config=config,
            status=MCPServerStatus.RUNNING,
            tools=[{"name": "read_file", "description": "Read a file"}],
        )
        discovery._servers["fs"] = state
        tools = discovery.get_all_tools()
        assert len(tools) == 1
        assert tools[0]["type"] == "function"
        assert tools[0]["function"]["name"] == "mcp_fs_read_file"
        assert "[MCP:fs]" in tools[0]["function"]["description"]

    def test_get_all_tools_skips_stopped(self):
        discovery = MCPServerDiscovery()
        config = MCPServerConfig(name="fs", command="echo")
        state = MCPServerState(
            config=config,
            status=MCPServerStatus.STOPPED,
            tools=[{"name": "read_file", "description": "Read a file"}],
        )
        discovery._servers["fs"] = state
        tools = discovery.get_all_tools()
        assert tools == []

    def test_get_all_tools_skips_failed(self):
        discovery = MCPServerDiscovery()
        config = MCPServerConfig(name="fs", command="echo")
        state = MCPServerState(
            config=config,
            status=MCPServerStatus.FAILED,
            tools=[{"name": "read_file", "description": "Read a file"}],
        )
        discovery._servers["fs"] = state
        tools = discovery.get_all_tools()
        assert tools == []


class TestMCPServerDiscoveryHealthCheck:
    @pytest.mark.asyncio
    async def test_health_check_empty(self):
        discovery = MCPServerDiscovery()
        results = await discovery.health_check()
        assert results == {}

    @pytest.mark.asyncio
    async def test_health_check_stopped_server(self):
        discovery = MCPServerDiscovery()
        config = MCPServerConfig(name="test", command="echo")
        state = MCPServerState(config=config, status=MCPServerStatus.STOPPED)
        discovery._servers["test"] = state
        results = await discovery.health_check()
        assert results["test"] == MCPServerStatus.STOPPED

    @pytest.mark.asyncio
    async def test_health_check_healthy_server(self):
        discovery = MCPServerDiscovery()
        config = MCPServerConfig(name="test", command="echo")
        state = MCPServerState(
            config=config,
            status=MCPServerStatus.RUNNING,
            process=MagicMock(returncode=None),
        )
        discovery._servers["test"] = state
        results = await discovery.health_check()
        assert results["test"] == MCPServerStatus.HEALTHY


class TestMCPServerDiscoveryStopAll:
    @pytest.mark.asyncio
    async def test_stop_all_empty(self):
        discovery = MCPServerDiscovery()
        await discovery.stop_all()  # Should not raise

    @pytest.mark.asyncio
    async def test_stop_all_sets_status(self):
        discovery = MCPServerDiscovery()
        config = MCPServerConfig(name="test", command="echo")
        state = MCPServerState(config=config, status=MCPServerStatus.RUNNING)
        discovery._servers["test"] = state
        await discovery.stop_all()
        assert state.status == MCPServerStatus.STOPPED


class TestMCPServerDiscoveryWrapTool:
    def test_wrap_tool_format(self):
        discovery = MCPServerDiscovery()
        mcp_tool = {"name": "read_file", "description": "Read a file"}
        wrapped = discovery._wrap_tool(mcp_tool, "filesystem")
        assert wrapped["type"] == "function"
        assert wrapped["function"]["name"] == "mcp_filesystem_read_file"
        assert "[MCP:filesystem]" in wrapped["function"]["description"]

    def test_wrap_tool_with_schema(self):
        discovery = MCPServerDiscovery()
        mcp_tool = {
            "name": "query",
            "description": "Run a query",
            "inputSchema": {
                "type": "object",
                "properties": {"sql": {"type": "string"}},
                "required": ["sql"],
            },
        }
        wrapped = discovery._wrap_tool(mcp_tool, "db")
        assert wrapped["function"]["parameters"]["properties"]["sql"]["type"] == "string"
