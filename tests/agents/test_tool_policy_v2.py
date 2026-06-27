"""Tests for enhanced tool policy — P03 Task 8.

Enhancements over v1.01:
- Plan mode: only read-only tools allowed
- MCP tool gating: MCP tools denied by default
- Policy composition: default + per-turn overrides + context overrides
"""

from __future__ import annotations

from backend.app.agents.tools.policy import ToolPolicy, ToolRule, default_policy


class TestPlanMode:
    """Plan mode restricts to read-only tools."""

    def test_plan_mode_allows_read_tools(self):
        policy = default_policy()
        policy.enable_plan_mode()
        assert policy.is_plan_mode is True
        # Read-only tools should be allowed
        assert policy.evaluate("search_memory", iteration=0) == "allow"
        assert policy.evaluate("read_file", iteration=0) == "allow"
        assert policy.evaluate("web_search", iteration=0) == "allow"

    def test_plan_mode_denies_write_tools(self):
        policy = default_policy()
        policy.enable_plan_mode()
        assert policy.evaluate("write_file", iteration=0) == "deny"
        assert policy.evaluate("exec_command", iteration=0) == "deny"
        assert policy.evaluate("create_memory", iteration=0) == "deny"

    def test_plan_mode_toggle(self):
        policy = default_policy()
        policy.enable_plan_mode()
        assert policy.is_plan_mode is True
        policy.disable_plan_mode()
        assert policy.is_plan_mode is False
        # Now write tools should follow default rules
        assert policy.evaluate("write_file", iteration=0) == "allow"


class TestMCPGating:
    """MCP tools are denied by default unless explicitly enabled."""

    def test_mcp_tool_denied_by_default(self):
        policy = default_policy()
        assert policy.evaluate("mcp__slack__send_message", iteration=0) == "deny"

    def test_mcp_tool_enabled_explicitly(self):
        policy = default_policy()
        policy.enable_mcp_tool("mcp__slack__send_message")
        assert policy.evaluate("mcp__slack__send_message", iteration=0) == "allow"

    def test_mcp_tool_disable(self):
        policy = default_policy()
        policy.enable_mcp_tool("mcp__slack__send_message")
        policy.disable_mcp_tool("mcp__slack__send_message")
        assert policy.evaluate("mcp__slack__send_message", iteration=0) == "deny"

    def test_non_mcp_tool_unaffected(self):
        policy = default_policy()
        # Built-in tools should not be affected by MCP gating
        assert policy.evaluate("read_file", iteration=0) == "allow"


class TestPolicyComposition:
    """Policy composition: default + overrides."""

    def test_custom_rule_overrides_default(self):
        policy = default_policy()
        policy.deny("read_file", reason="Temporarily disabled")
        assert policy.evaluate("read_file", iteration=0) == "deny"

    def test_approve_ask_tool(self):
        policy = default_policy()
        # exec_command defaults to "ask"
        assert policy.evaluate("exec_command", iteration=0) == "ask"
        policy.approve("exec_command")
        assert policy.evaluate("exec_command", iteration=0) == "allow"

    def test_reset_clears_all(self):
        policy = default_policy()
        policy.enable_plan_mode()
        policy.deny("read_file")
        policy.approve("exec_command")
        policy.enable_mcp_tool("mcp__test")
        policy.reset()
        assert policy.is_plan_mode is False
        # After reset, all rules/approvals/state are cleared
        assert policy.evaluate("read_file", iteration=0) == "allow"
        assert policy.evaluate("exec_command", iteration=0) == "allow"
        assert policy.evaluate("mcp__test", iteration=0) == "deny"


class TestDefaultPolicy:
    """Default policy behavior."""

    def test_read_tools_allowed(self):
        policy = default_policy()
        for tool in ["search_memory", "read_file", "web_search", "plan_task"]:
            assert policy.evaluate(tool, iteration=0) == "allow"

    def test_write_tools_allowed(self):
        policy = default_policy()
        for tool in ["write_file", "create_memory"]:
            assert policy.evaluate(tool, iteration=0) == "allow"

    def test_dangerous_tools_ask(self):
        policy = default_policy()
        for tool in ["exec_command", "delete_file"]:
            assert policy.evaluate(tool, iteration=0) == "ask"

    def test_unknown_tool_default(self):
        policy = default_policy()
        assert policy.evaluate("unknown_tool_xyz", iteration=0) == "allow"
