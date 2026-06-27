"""Tests for MCP bridge — register MCP tools into Cortex ToolRegistry."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from backend.app.agents.tools.registry import ToolRegistry
from backend.app.mcp.bridge import register_mcp_tools


class TestRegisterMCPTools:
    def test_registers_tools(self):
        registry = ToolRegistry()
        mcp_tools = [
            {"name": "read_file", "description": "Read a file", "inputSchema": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}},
            {"name": "write_file", "description": "Write a file", "inputSchema": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}},
        ]
        count = register_mcp_tools(registry, mcp_tools, "filesystem")
        assert count == 2
        assert registry.count == 2
        assert registry.get("mcp_filesystem_read_file") is not None
        assert registry.get("mcp_filesystem_write_file") is not None

    def test_tool_schema_is_valid(self):
        registry = ToolRegistry()
        mcp_tools = [
            {"name": "query", "description": "Run SQL", "inputSchema": {"type": "object", "properties": {"sql": {"type": "string"}}, "required": ["sql"]}},
        ]
        register_mcp_tools(registry, mcp_tools, "db")
        tool = registry.get("mcp_db_query")
        assert tool is not None
        assert tool.schema["type"] == "function"
        assert tool.schema["function"]["name"] == "mcp_db_query"
        assert "[MCP:db]" in tool.schema["function"]["description"]

    def test_tool_handler_is_callable(self):
        registry = ToolRegistry()
        mcp_tools = [
            {"name": "greet", "description": "Greet someone", "inputSchema": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}},
        ]
        register_mcp_tools(registry, mcp_tools, "test")
        tool = registry.get("mcp_test_greet")
        assert tool is not None
        assert callable(tool.handler)

    @pytest.mark.asyncio
    async def test_tool_handler_executes_via_transport(self):
        registry = ToolRegistry()
        mcp_tools = [
            {"name": "greet", "description": "Greet someone", "inputSchema": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}},
        ]
        mock_transport = AsyncMock()
        mock_transport.send_request.return_value = {
            "result": {"content": [{"type": "text", "text": '{"message": "Hello, Alice!"}'}]}
        }
        register_mcp_tools(registry, mcp_tools, "test", transport=mock_transport)
        tool = registry.get("mcp_test_greet")
        result = await tool.handler(name="Alice")
        assert result == {"message": "Hello, Alice!"}
        mock_transport.send_request.assert_called_once()

    def test_empty_tools_returns_zero(self):
        registry = ToolRegistry()
        count = register_mcp_tools(registry, [], "empty")
        assert count == 0
        assert registry.count == 0

    def test_namespacing_prevents_collision(self):
        registry = ToolRegistry()
        mcp_tools = [{"name": "read", "description": "Read", "inputSchema": {}}]
        register_mcp_tools(registry, mcp_tools, "server_a")
        register_mcp_tools(registry, mcp_tools, "server_b")
        assert registry.count == 2
        assert registry.get("mcp_server_a_read") is not None
        assert registry.get("mcp_server_b_read") is not None
