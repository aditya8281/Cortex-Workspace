"""Tests for MCP tool wrapper — P04 Task 2."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from backend.app.mcp.wrapper import MCPToolWrapper


class TestMCPToolWrapperSchema:
    def test_basic_schema_translation(self):
        mcp_tool = {
            "name": "read_file",
            "description": "Read a file",
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
        assert "[MCP:filesystem]" in schema["function"]["description"]
        assert "path" in schema["function"]["parameters"]["properties"]

    def test_namespacing_prevents_collision(self):
        mcp_tool = {"name": "read_file", "description": "Read"}
        w1 = MCPToolWrapper("server_a", mcp_tool)
        w2 = MCPToolWrapper("server_b", mcp_tool)
        assert w1.tool_name != w2.tool_name
        assert w1.tool_name == "mcp_server_a_read_file"
        assert w2.tool_name == "mcp_server_b_read_file"

    def test_missing_name_defaults(self):
        mcp_tool = {"description": "A tool"}
        wrapper = MCPToolWrapper("srv", mcp_tool)
        assert wrapper.tool_name == "mcp_srv_unknown"
        assert wrapper.original_name == ""

    def test_description_adds_server_prefix(self):
        mcp_tool = {"name": "do_thing", "description": "Does things"}
        wrapper = MCPToolWrapper("myserver", mcp_tool)
        desc = wrapper._translate_description()
        assert desc == "[MCP:myserver] Does things"


class TestMCPToolWrapperParameters:
    def test_translates_properties(self):
        schema = MCPToolWrapper("s", {})._translate_parameters(
            {
                "type": "object",
                "properties": {
                    "count": {"type": "integer", "description": "How many"},
                    "mode": {"type": "string", "description": "Mode", "enum": ["a", "b"]},
                },
                "required": ["count"],
            }
        )
        assert schema["type"] == "object"
        assert schema["required"] == ["count"]
        assert schema["properties"]["count"]["type"] == "integer"
        assert schema["properties"]["mode"]["enum"] == ["a", "b"]

    def test_preserves_default(self):
        schema = MCPToolWrapper("s", {})._translate_parameters(
            {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "default": 10, "description": "Limit"},
                },
                "required": [],
            }
        )
        assert schema["properties"]["limit"]["default"] == 10

    def test_empty_schema(self):
        schema = MCPToolWrapper("s", {})._translate_parameters({})
        assert schema["type"] == "object"
        assert schema["properties"] == {}
        assert schema["required"] == []


class TestMCPToolWrapperResult:
    def test_single_text_json(self):
        mcp_result = {"result": {"content": [{"type": "text", "text": '{"key": "val"}'}]}}
        wrapper = MCPToolWrapper("s", {"name": "t"})
        result = wrapper._translate_result(mcp_result)
        assert result == {"key": "val"}

    def test_single_text_plain(self):
        mcp_result = {"result": {"content": [{"type": "text", "text": "hello world"}]}}
        wrapper = MCPToolWrapper("s", {"name": "t"})
        result = wrapper._translate_result(mcp_result)
        assert result == {"text": "hello world"}

    def test_multiple_text(self):
        mcp_result = {
            "result": {
                "content": [
                    {"type": "text", "text": "line1"},
                    {"type": "text", "text": "line2"},
                ]
            }
        }
        wrapper = MCPToolWrapper("s", {"name": "t"})
        result = wrapper._translate_result(mcp_result)
        assert result == {"text": "line1\nline2"}

    def test_empty_content(self):
        mcp_result = {"result": {"content": []}}
        wrapper = MCPToolWrapper("s", {"name": "t"})
        result = wrapper._translate_result(mcp_result)
        assert result == {"content": []}

    def test_non_text_content(self):
        mcp_result = {"result": {"content": [{"type": "image", "data": "abc"}]}}
        wrapper = MCPToolWrapper("s", {"name": "t"})
        result = wrapper._translate_result(mcp_result)
        assert result == {"content": [{"type": "image", "data": "abc"}]}

    def test_no_content_field(self):
        mcp_result = {"result": {"data": "something"}}
        wrapper = MCPToolWrapper("s", {"name": "t"})
        result = wrapper._translate_result(mcp_result)
        assert result == {"data": "something"}


class TestMCPToolWrapperExecute:
    @pytest.mark.asyncio
    async def test_execute_sends_request(self):
        wrapper = MCPToolWrapper("srv", {"name": "do_thing"})
        mock_transport = AsyncMock()
        mock_transport.send_request.return_value = {"result": {"content": [{"type": "text", "text": "ok"}]}}
        await wrapper.execute({"arg1": "val"}, mock_transport)
        mock_transport.send_request.assert_called_once()
        call_args = mock_transport.send_request.call_args[0][0]
        assert call_args["method"] == "tools/call"
        assert call_args["params"]["name"] == "do_thing"
        assert call_args["params"]["arguments"] == {"arg1": "val"}

    @pytest.mark.asyncio
    async def test_execute_returns_error_on_exception(self):
        wrapper = MCPToolWrapper("srv", {"name": "fail"})
        mock_transport = AsyncMock()
        mock_transport.send_request.side_effect = RuntimeError("timeout")
        result = await wrapper.execute({}, mock_transport)
        assert "error" in result
        assert "timeout" in result["error"]
