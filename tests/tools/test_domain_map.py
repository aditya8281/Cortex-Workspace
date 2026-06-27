"""Tests for tool domain mapping — P05 Task 3."""

from __future__ import annotations

from backend.app.agents.tools.domain_map import TOOL_DOMAINS, ToolDomainMap


class TestToolDomainMap:
    def test_known_tool_memory(self):
        dm = ToolDomainMap()
        assert dm.get_domain("search_memory") == "memory"
        assert dm.get_domain("create_memory") == "memory"

    def test_known_tool_awareness(self):
        dm = ToolDomainMap()
        assert dm.get_domain("read_file") == "awareness"
        assert dm.get_domain("write_file") == "awareness"

    def test_known_tool_system(self):
        dm = ToolDomainMap()
        assert dm.get_domain("execute_command") == "system"

    def test_unknown_tool(self):
        dm = ToolDomainMap()
        assert dm.get_domain("nonexistent_tool") == "unknown"

    def test_read_only_detection(self):
        dm = ToolDomainMap()
        assert dm.is_read_only("search_memory") is True
        assert dm.is_read_only("read_file") is True
        assert dm.is_read_only("web_search") is True

    def test_non_read_only_detection(self):
        dm = ToolDomainMap()
        assert dm.is_read_only("write_file") is False
        assert dm.is_read_only("create_memory") is False
        assert dm.is_read_only("execute_command") is False

    def test_unknown_tool_not_read_only(self):
        dm = ToolDomainMap()
        assert dm.is_read_only("nonexistent_tool") is False

    def test_get_tools_for_domains(self):
        dm = ToolDomainMap()
        tools = dm.get_tools_for_domains(["memory"])
        assert "search_memory" in tools
        assert "create_memory" in tools
        assert "read_file" not in tools

    def test_get_tools_for_multiple_domains(self):
        dm = ToolDomainMap()
        tools = dm.get_tools_for_domains(["memory", "awareness"])
        assert "search_memory" in tools
        assert "read_file" in tools

    def test_get_tools_for_unknown_domain(self):
        dm = ToolDomainMap()
        tools = dm.get_tools_for_domains(["nonexistent"])
        assert tools == []

    def test_domain_summary(self):
        dm = ToolDomainMap()
        summary = dm.get_domain_summary()
        assert "memory" in summary
        assert summary["memory"]["tool_count"] > 0
        assert summary["memory"]["read_only_count"] > 0

    def test_all_domains_in_summary(self):
        dm = ToolDomainMap()
        summary = dm.get_domain_summary()
        for domain in TOOL_DOMAINS:
            assert domain in summary
