"""Per-turn tool policy — allow/deny/ask composition.

Policies control which tools the agent can use at each iteration.
Rules are evaluated in order; the first match wins.
Default decision (if no rule matches) is configurable.
"""

from __future__ import annotations

import fnmatch
from collections import Counter
from dataclasses import dataclass, field
from typing import Literal

Decision = Literal["allow", "deny", "ask"]


@dataclass
class ToolRule:
    """A single policy rule controlling a tool or tool pattern."""

    pattern: str  # Glob pattern matching tool name(s), e.g. "exec_*", "web_*"
    decision: Decision
    reason: str = ""  # Why this rule exists (for UI/audit)

    def matches(self, tool_name: str) -> bool:
        """Check if this rule applies to the given tool name."""
        return fnmatch.fnmatch(tool_name, self.pattern)


@dataclass
class ToolPolicy:
    """A composable tool policy with ordered rules.

    Example:
        policy = ToolPolicy(rules=[
            ToolRule("exec_*", "ask", "Shell commands need approval"),
            ToolRule("web_*", "deny", "Web fetch disabled"),
        ])

        decision = policy.evaluate("exec_command", iteration=0)
        # → "ask"
    """

    rules: list[ToolRule] = field(default_factory=list)
    default_decision: Decision = "allow"
    max_uses_per_tool: int = 0  # 0 = unlimited
    _use_counts: Counter[str] = field(default_factory=Counter, repr=False, init=False)

    def evaluate(self, tool_name: str, iteration: int = 0) -> Decision:
        """Evaluate policy for a tool call at the given iteration.

        If max_uses_per_tool is set (> 0), denies the tool when its
        use count exceeds the limit. The `iteration` param is reserved
        for iteration-aware policies (e.g. "ask on first use, allow
        subsequently") and is not currently consumed by any built-in rule.
        """
        # Enforce per-tool usage limit
        if self.max_uses_per_tool > 0:
            self._use_counts[tool_name] += 1
            if self._use_counts[tool_name] > self.max_uses_per_tool:
                return "deny"

        for rule in self.rules:
            if rule.matches(tool_name):
                return rule.decision

        return self.default_decision

    def reset_use_counts(self) -> None:
        """Reset per-tool use counters (e.g. at the start of a new agent run)."""
        self._use_counts.clear()

    def allow(self, pattern: str, reason: str = "") -> None:
        """Add an allow rule."""
        self.rules.append(ToolRule(pattern=pattern, decision="allow", reason=reason))

    def deny(self, pattern: str, reason: str = "") -> None:
        """Add a deny rule."""
        self.rules.append(ToolRule(pattern=pattern, decision="deny", reason=reason))

    def ask(self, pattern: str, reason: str = "") -> None:
        """Add an ask rule (require approval)."""
        self.rules.append(ToolRule(pattern=pattern, decision="ask", reason=reason))

    def copy(self) -> ToolPolicy:
        """Create an independent copy of this policy."""
        return ToolPolicy(
            rules=list(self.rules),
            default_decision=self.default_decision,
            max_uses_per_tool=self.max_uses_per_tool,
        )


def default_policy() -> ToolPolicy:
    """Return the default tool policy for the agent system.

    - High-risk tools (shell, write, network) require approval.
    - Read-only, search, and informational tools are allowed by default.
    """
    return ToolPolicy(
        rules=[
            ToolRule("exec_command", "ask", "Shell commands require approval"),
            ToolRule("exec_*", "ask", "Execution tools require approval"),
            ToolRule("write_file", "ask", "File writes require approval"),
            ToolRule("web_fetch", "ask", "Network fetches require approval"),
            ToolRule("ask_user", "deny", "Cannot ask user — use in API context only"),
        ],
        default_decision="allow",
        max_uses_per_tool=0,
    )
