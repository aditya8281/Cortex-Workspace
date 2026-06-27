"""Tests for MCP configuration management — P04 Task 4."""

from __future__ import annotations

import tempfile
from pathlib import Path

from backend.app.mcp.config import MCPConfig, MCPConfigManager


class TestMCPConfig:
    def test_default_values(self):
        config = MCPConfig()
        assert config.servers == []
        assert config.tool_allowlist == {}
        assert config.tool_denylist == {}


class TestMCPConfigManager:
    def test_init_default(self):
        manager = MCPConfigManager()
        assert manager.config_dir == Path.home() / ".cortex"

    def test_init_custom_dir(self):
        manager = MCPConfigManager(config_dir="/tmp/mcp_test")
        assert manager.config_dir == Path("/tmp/mcp_test")

    def test_load_system_config_no_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = MCPConfigManager(config_dir=tmpdir)
            config = manager.load_system_config()
            assert config.servers == []

    def test_load_system_config_with_file(self):
        yaml_content = """
servers:
  - name: filesystem
    command: npx
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
    transport: stdio
  - name: remote-tools
    transport: sse
    sse_url: https://mcp.example.com/sse
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "mcp_servers.yaml"
            config_file.write_text(yaml_content)
            manager = MCPConfigManager(config_dir=tmpdir)
            config = manager.load_system_config()
            assert len(config.servers) == 2
            assert config.servers[0].name == "filesystem"
            assert config.servers[0].transport == "stdio"
            assert config.servers[1].name == "remote-tools"
            assert config.servers[1].sse_url == "https://mcp.example.com/sse"


class TestMCPConfigManagerToolFiltering:
    def test_no_filters_returns_all(self):
        manager = MCPConfigManager()
        tools = [
            {"function": {"name": "mcp_fs_read", "description": "Read"}},
            {"function": {"name": "mcp_db_query", "description": "Query"}},
        ]
        result = manager.get_user_tools(user_id=1, all_tools=tools)
        assert len(result) == 2

    def test_allowlist_filters(self):
        manager = MCPConfigManager()
        manager._user_configs[1] = MCPConfig(tool_allowlist={1: ["mcp_fs_read"]})
        tools = [
            {"function": {"name": "mcp_fs_read", "description": "Read"}},
            {"function": {"name": "mcp_db_query", "description": "Query"}},
        ]
        result = manager.get_user_tools(user_id=1, all_tools=tools)
        assert len(result) == 1
        assert result[0]["function"]["name"] == "mcp_fs_read"

    def test_denylist_filters(self):
        manager = MCPConfigManager()
        manager._user_configs[1] = MCPConfig(tool_denylist={1: ["mcp_db_query"]})
        tools = [
            {"function": {"name": "mcp_fs_read", "description": "Read"}},
            {"function": {"name": "mcp_db_query", "description": "Query"}},
        ]
        result = manager.get_user_tools(user_id=1, all_tools=tools)
        assert len(result) == 1
        assert result[0]["function"]["name"] == "mcp_fs_read"

    def test_allowlist_takes_priority_over_denylist(self):
        manager = MCPConfigManager()
        manager._user_configs[1] = MCPConfig(
            tool_allowlist={1: ["mcp_fs_read"]},
            tool_denylist={1: ["mcp_fs_read"]},  # deny is ignored when allowlist present
        )
        tools = [
            {"function": {"name": "mcp_fs_read", "description": "Read"}},
            {"function": {"name": "mcp_db_query", "description": "Query"}},
        ]
        result = manager.get_user_tools(user_id=1, all_tools=tools)
        assert len(result) == 1
        assert result[0]["function"]["name"] == "mcp_fs_read"
