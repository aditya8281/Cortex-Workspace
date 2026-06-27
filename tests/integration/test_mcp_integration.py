"""MCP integration tests — P08 Task 3.

Tests MCP tool wrapping, search, and discovery with mock servers.
No real MCP servers needed.
"""

from __future__ import annotations

import pytest

from backend.app.mcp.discovery import (
    MCPServerConfig,
    MCPServerDiscovery,
    MCPServerState,
    MCPServerStatus,
)
from backend.app.mcp.search import MCPToolSearch
from backend.app.mcp.wrapper import MCPToolWrapper


class TestMCPToolWrapping:
    """MCP tool wrapping into Cortex format."""

    def test_wrap_tool_schema(self):
        """MCP tool should be wrapped into OpenAI function format."""
        mcp_tool = {
            "name": "read_file",
            "description": "Read a file from disk",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path"},
                },
                "required": ["path"],
            },
        }
        wrapper = MCPToolWrapper("filesystem", mcp_tool)
        schema = wrapper.to_cortex_schema()

        assert schema["type"] == "function"
        assert schema["function"]["name"] == "mcp_filesystem_read_file"
        assert "path" in schema["function"]["parameters"]["properties"]
        assert "[MCP:filesystem]" in schema["function"]["description"]

    def test_wrap_tool_namespacing(self):
        """MCP tools from different servers should be namespaced."""
        tool1 = MCPToolWrapper("server_a", {"name": "search", "description": "Search A"})
        tool2 = MCPToolWrapper("server_b", {"name": "search", "description": "Search B"})
        schema1 = tool1.to_cortex_schema()
        schema2 = tool2.to_cortex_schema()

        assert schema1["function"]["name"] != schema2["function"]["name"]
        assert "server_a" in schema1["function"]["name"]
        assert "server_b" in schema2["function"]["name"]


class TestMCPToolSearch:
    """Keyword-based MCP tool search."""

    @pytest.mark.asyncio
    async def test_tool_indexing(self):
        """Tools should be indexed for search."""
        search = MCPToolSearch(top_k=3)
        tools = [
            {
                "function": {
                    "name": "read_file",
                    "description": "Read a file from disk",
                    "parameters": {},
                }
            },
            {
                "function": {
                    "name": "write_file",
                    "description": "Write content to a file",
                    "parameters": {},
                }
            },
            {
                "function": {
                    "name": "search_memory",
                    "description": "Search long-term memory",
                    "parameters": {},
                }
            },
        ]
        await search.index_tools(tools)
        assert search._indexed is True

    @pytest.mark.asyncio
    async def test_keyword_search_relevance(self):
        """Keyword search should find relevant tools."""
        search = MCPToolSearch(top_k=3)
        tools = [
            {
                "function": {
                    "name": "read_file",
                    "description": "Read a file from disk",
                    "parameters": {},
                }
            },
            {
                "function": {
                    "name": "write_file",
                    "description": "Write content to a file",
                    "parameters": {},
                }
            },
            {
                "function": {
                    "name": "search_memory",
                    "description": "Search long-term memory",
                    "parameters": {},
                }
            },
        ]
        await search.index_tools(tools)
        results = await search.search("file contents")

        assert len(results) <= 3
        result_names = [r["function"]["name"] for r in results]
        assert "read_file" in result_names or "write_file" in result_names

    @pytest.mark.asyncio
    async def test_top_k_limit(self):
        """Search should respect top_k limit."""
        search = MCPToolSearch(top_k=2)
        tools = [
            {
                "function": {
                    "name": f"tool_{i}",
                    "description": f"Tool number {i}",
                    "parameters": {},
                }
            }
            for i in range(10)
        ]
        await search.index_tools(tools)
        results = await search.search("tool")
        assert len(results) <= 2


class TestMCPDiscovery:
    """MCP server discovery and lifecycle."""

    def test_discovery_creates(self):
        """MCPServerDiscovery should instantiate."""
        discovery = MCPServerDiscovery()
        assert discovery is not None

    @pytest.mark.asyncio
    async def test_get_all_tools_empty(self):
        """Should return empty list when no servers are running."""
        discovery = MCPServerDiscovery()
        tools = discovery.get_all_tools()
        assert tools == []

    @pytest.mark.asyncio
    async def test_get_all_tools_with_mock_server(self):
        """Should aggregate tools from healthy servers."""
        discovery = MCPServerDiscovery()
        state = MCPServerState(
            config=MCPServerConfig(name="test", command="echo"),
            status=MCPServerStatus.RUNNING,
            tools=[
                {"name": "tool1", "description": "Test tool 1"},
                {"name": "tool2", "description": "Test tool 2"},
            ],
        )
        discovery._servers["test"] = state

        tools = discovery.get_all_tools()
        assert len(tools) == 2
        assert tools[0]["function"]["name"] == "mcp_test_tool1"

    @pytest.mark.asyncio
    async def test_health_check_empty(self):
        """Health check with no servers should return empty dict."""
        discovery = MCPServerDiscovery()
        results = await discovery.health_check()
        assert results == {}
