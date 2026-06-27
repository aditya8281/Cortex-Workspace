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

    def test_max_uses_enforced(self):
        policy = ToolPolicy(max_uses_per_tool=2)
        # First use allowed
        assert policy.evaluate("any_tool") == "allow"
        # Second use allowed
        assert policy.evaluate("any_tool") == "allow"
        # Third use denied (exceeds limit)
        assert policy.evaluate("any_tool") == "deny"

    def test_max_uses_respected_per_tool(self):
        policy = ToolPolicy(max_uses_per_tool=1)
        # tool_a consumes its single use
        assert policy.evaluate("tool_a") == "allow"
        assert policy.evaluate("tool_a") == "deny"
        # tool_b still has its use
        assert policy.evaluate("tool_b") == "allow"
        assert policy.evaluate("tool_b") == "deny"

    def test_reset_use_counts(self):
        policy = ToolPolicy(max_uses_per_tool=1)
        assert policy.evaluate("tool") == "allow"
        assert policy.evaluate("tool") == "deny"
        policy.reset_use_counts()
        assert policy.evaluate("tool") == "allow"  # reset

    def test_copy_has_fresh_counts(self):
        policy = ToolPolicy(max_uses_per_tool=1)
        assert policy.evaluate("tool") == "allow"
        assert policy.evaluate("tool") == "deny"
        copied = policy.copy()
        assert copied.evaluate("tool") == "allow"  # fresh counts

    def test_rules_still_respected_with_max_uses(self):
        policy = ToolPolicy(
            rules=[ToolRule("dangerous_*", "deny", "Always blocked")],
            max_uses_per_tool=3,
        )
        # Rule evaluation happens regardless of use count
        assert policy.evaluate("dangerous_thing") == "deny"

    def test_uses_not_exceeded_under_limit(self):
        policy = ToolPolicy(max_uses_per_tool=5)
        for _ in range(5):
            assert policy.evaluate("tool") == "allow"


class TestDefaultPolicy:
    def test_default_policy_has_rules(self):
        policy = default_policy()
        assert len(policy.rules) > 0

    def test_default_policy_asks_for_exec(self):
        policy = default_policy()
        assert policy.evaluate("exec_command") == "ask"

    def test_default_policy_allows_write(self):
        policy = default_policy()
        assert policy.evaluate("write_file") == "allow"

    def test_default_policy_allows_web_fetch(self):
        policy = default_policy()
        assert policy.evaluate("web_fetch") == "allow"

    def test_default_policy_asks_for_delete(self):
        policy = default_policy()
        assert policy.evaluate("delete_file") == "ask"

    def test_default_policy_allows_unknown(self):
        policy = default_policy()
        assert policy.evaluate("ask_user") == "allow"

    def test_default_policy_allows_read(self):
        policy = default_policy()
        assert policy.evaluate("read_file") == "allow"
