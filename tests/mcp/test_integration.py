"""Integration tests for MCP — end-to-end with mock server subprocess."""

from __future__ import annotations

import asyncio
import json
import os
import sys

import pytest

from backend.app.agents.tools.registry import ToolRegistry
from backend.app.mcp.bridge import register_mcp_tools
from backend.app.mcp.search import MCPToolSearch
from backend.app.mcp.transport import StdioTransport
from backend.app.mcp.wrapper import MCPToolWrapper

MOCK_SERVER = os.path.join(
    os.path.dirname(__file__), "..", "fixtures", "mock_mcp_server.py"
)


@pytest.fixture
def mock_server_script():
    """Path to mock MCP server script."""
    return os.path.abspath(MOCK_SERVER)


class TestMockMCPServer:
    """Validate the mock MCP server works correctly via subprocess."""

    @pytest.mark.asyncio
    async def test_initialize(self, mock_server_script):
        proc = await asyncio.create_subprocess_exec(
            sys.executable, mock_server_script,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            request = json.dumps({
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0.0"}},
            }) + "\n"
            proc.stdin.write(request.encode())
            await proc.stdin.drain()

            response_line = await asyncio.wait_for(proc.stdout.readline(), timeout=5)
            response = json.loads(response_line.decode())
            assert "result" in response
            assert response["result"]["serverInfo"]["name"] == "mock-mcp-server"
        finally:
            proc.terminate()
            await proc.wait()

    @pytest.mark.asyncio
    async def test_tools_list(self, mock_server_script):
        proc = await asyncio.create_subprocess_exec(
            sys.executable, mock_server_script,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            # Initialize first
            init = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}) + "\n"
            proc.stdin.write(init.encode())
            await proc.stdin.drain()
            await proc.stdout.readline()

            # List tools
            tools_req = json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}) + "\n"
            proc.stdin.write(tools_req.encode())
            await proc.stdin.drain()

            response_line = await asyncio.wait_for(proc.stdout.readline(), timeout=5)
            response = json.loads(response_line.decode())
            tools = response["result"]["tools"]
            assert len(tools) == 2
            assert tools[0]["name"] == "mock_tool"
            assert tools[1]["name"] == "add_numbers"
        finally:
            proc.terminate()
            await proc.wait()

    @pytest.mark.asyncio
    async def test_tool_call(self, mock_server_script):
        proc = await asyncio.create_subprocess_exec(
            sys.executable, mock_server_script,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            # Initialize
            init = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}) + "\n"
            proc.stdin.write(init.encode())
            await proc.stdin.drain()
            await proc.stdout.readline()

            # Call mock_tool
            call = json.dumps({
                "jsonrpc": "2.0", "id": 3,
                "method": "tools/call",
                "params": {"name": "mock_tool", "arguments": {"input": "hello world"}},
            }) + "\n"
            proc.stdin.write(call.encode())
            await proc.stdin.drain()

            response_line = await asyncio.wait_for(proc.stdout.readline(), timeout=5)
            response = json.loads(response_line.decode())
            assert "result" in response
            content = response["result"]["content"]
            assert len(content) == 1
            assert content[0]["text"] == "Mock result: hello world"
        finally:
            proc.terminate()
            await proc.wait()

    @pytest.mark.asyncio
    async def test_add_numbers_tool(self, mock_server_script):
        proc = await asyncio.create_subprocess_exec(
            sys.executable, mock_server_script,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            # Initialize
            init = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}) + "\n"
            proc.stdin.write(init.encode())
            await proc.stdin.drain()
            await proc.stdout.readline()

            # Call add_numbers
            call = json.dumps({
                "jsonrpc": "2.0", "id": 4,
                "method": "tools/call",
                "params": {"name": "add_numbers", "arguments": {"a": 3, "b": 7}},
            }) + "\n"
            proc.stdin.write(call.encode())
            await proc.stdin.drain()

            response_line = await asyncio.wait_for(proc.stdout.readline(), timeout=5)
            response = json.loads(response_line.decode())
            assert "result" in response
            assert response["result"]["content"][0]["text"] == "10"
        finally:
            proc.terminate()
            await proc.wait()


class TestMCPToolWrapperWithMockServer:
    """Test MCPToolWrapper end-to-end with mock server subprocess."""

    @pytest.mark.asyncio
    async def test_execute_mock_tool(self, mock_server_script):
        proc = await asyncio.create_subprocess_exec(
            sys.executable, mock_server_script,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            # Initialize
            init = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}) + "\n"
            proc.stdin.write(init.encode())
            await proc.stdin.drain()
            await proc.stdout.readline()

            transport = StdioTransport(proc)
            await transport.start()

            wrapper = MCPToolWrapper("test-server", {
                "name": "mock_tool",
                "description": "A mock tool",
                "inputSchema": {"type": "object", "properties": {"input": {"type": "string"}}, "required": ["input"]},
            })

            result = await wrapper.execute({"input": "test data"}, transport)
            assert result == {"text": "Mock result: test data"}

            await transport.close()
        finally:
            proc.terminate()
            await proc.wait()


class TestRegisterMCPToolsEndToEnd:
    """End-to-end test: mock server -> discovery -> bridge -> registry."""

    @pytest.mark.asyncio
    async def test_full_pipeline(self, mock_server_script):
        proc = await asyncio.create_subprocess_exec(
            sys.executable, mock_server_script,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            # Initialize
            init = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}) + "\n"
            proc.stdin.write(init.encode())
            await proc.stdin.drain()
            await proc.stdout.readline()

            # List tools
            tools_req = json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}) + "\n"
            proc.stdin.write(tools_req.encode())
            await proc.stdin.drain()
            response_line = await proc.stdout.readline()
            response = json.loads(response_line.decode())
            mcp_tools = response["result"]["tools"]

            transport = StdioTransport(proc)
            await transport.start()

            # Register in Cortex ToolRegistry
            registry = ToolRegistry()
            count = register_mcp_tools(registry, mcp_tools, "mock-server", transport=transport)
            assert count == 2
            assert registry.count == 2

            # Execute via registry (ToolRegistry.execute converts dicts to str)
            result = await registry.execute("mcp_mock-server_mock_tool", input="hello")
            assert "Mock result: hello" in result

            result = await registry.execute("mcp_mock-server_add_numbers", a=10, b=20)
            assert "30" in result

            await transport.close()
        finally:
            proc.terminate()
            await proc.wait()


class TestMCPToolSearchIntegration:
    """Integration test for MCPToolSearch with real tool schemas."""

    @pytest.mark.asyncio
    async def test_search_finds_mcp_tools(self):
        search = MCPToolSearch(top_k=3)
        tools = [
            {"function": {"name": "mcp_fs_read_file", "description": "[MCP:filesystem] Read a file from disk", "parameters": {}}},
            {"function": {"name": "mcp_fs_write_file", "description": "[MCP:filesystem] Write content to a file", "parameters": {}}},
            {"function": {"name": "mcp_db_query", "description": "[MCP:database] Execute a SQL query", "parameters": {}}},
            {"function": {"name": "mcp_github_list_prs", "description": "[MCP:github] List pull requests", "parameters": {}}},
        ]
        await search.index_tools(tools)

        # Query about files
        results = await search.search("file contents")
        result_names = [r["function"]["name"] for r in results]
        assert "mcp_fs_read_file" in result_names[:2]
        assert "mcp_fs_write_file" in result_names[:2]

        # Query about database
        results = await search.search("database query SQL")
        result_names = [r["function"]["name"] for r in results]
        assert "mcp_db_query" in result_names[:2]
