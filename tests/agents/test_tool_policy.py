"""Tests for tool policy system."""

from __future__ import annotations

from backend.app.agents.tools.policy import ToolPolicy, ToolRule, default_policy


class TestToolRule:
    def test_exact_match(self):
        rule = ToolRule("exec_command", "deny", "No shell")
        assert rule.matches("exec_command") is True
        assert rule.matches("exec_other") is False
        assert rule.matches("web_fetch") is False

    def test_glob_match(self):
        rule = ToolRule("exec_*", "ask")
        assert rule.matches("exec_command") is True
        assert rule.matches("exec_script") is True
        assert rule.matches("web_fetch") is False

    def test_wildcard_match(self):
        rule = ToolRule("*", "allow")
        assert rule.matches("anything") is True

    def test_specific_pattern(self):
        rule = ToolRule("write_file", "deny")
        assert rule.matches("write_file") is True
        assert rule.matches("read_file") is False


class TestToolPolicy:
    def test_default_allow(self):
        policy = ToolPolicy()
        assert policy.evaluate("anything") == "allow"

    def test_default_deny(self):
        policy = ToolPolicy(default_decision="deny")
        assert policy.evaluate("anything") == "deny"

    def test_first_rule_wins(self):
        policy = ToolPolicy(
            rules=[
                ToolRule("exec_*", "ask"),
                ToolRule("exec_command", "deny"),  # more specific, but later
            ]
        )
        assert policy.evaluate("exec_command") == "ask"  # first match wins

    def test_no_match_falls_to_default(self):
        policy = ToolPolicy(
            rules=[
                ToolRule("exec_*", "deny"),
            ],
            default_decision="allow",
        )
        assert policy.evaluate("web_fetch") == "allow"

    def test_allow_helper(self):
        policy = ToolPolicy()
        policy.allow("read_*", "Read tools allowed")
        assert policy.evaluate("read_file") == "allow"

    def test_deny_helper(self):
        policy = ToolPolicy()
        policy.deny("exec_*", "No exec")
        assert policy.evaluate("exec_command") == "deny"

    def test_ask_helper(self):
        policy = ToolPolicy()
        policy.ask("web_*", "Web needs approval")
        assert policy.evaluate("web_fetch") == "ask"

    def test_copy_is_independent(self):
        policy = ToolPolicy(rules=[ToolRule("exec_*", "deny")])
        copied = policy.copy()
        copied.deny("web_*")  # Only affects copy
        assert policy.evaluate("web_fetch") == "allow"  # Original has no web rule
        assert copied.evaluate("web_fetch") == "deny"  # Copy has web rule
        # Original deny rule still in copy
        assert copied.evaluate("exec_command") == "deny"

    def test_max_uses_per_tool_is_zero_by_default(self):
        policy = ToolPolicy()
        assert policy.max_uses_per_tool == 0


class TestDefaultPolicy:
    def test_default_policy_has_rules(self):
        policy = default_policy()
        assert len(policy.rules) > 0

    def test_default_policy_asks_for_exec(self):
        policy = default_policy()
        assert policy.evaluate("exec_command") == "ask"

    def test_default_policy_asks_for_write(self):
        policy = default_policy()
        assert policy.evaluate("write_file") == "ask"

    def test_default_policy_asks_for_web_fetch(self):
        policy = default_policy()
        assert policy.evaluate("web_fetch") == "ask"

    def test_default_policy_denies_ask_user(self):
        policy = default_policy()
        assert policy.evaluate("ask_user") == "deny"

    def test_default_policy_allows_read(self):
        policy = default_policy()
        assert policy.evaluate("read_file") == "allow"
