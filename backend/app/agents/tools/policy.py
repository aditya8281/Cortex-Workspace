"""Per-turn tool policy — allow/deny/ask composition.

Policies control which tools the agent can use at each iteration.
Rules are evaluated in order; the first match wins.
Default decision (if no rule matches) is configurable.

Enhancements:
- Plan mode: only read-only tools allowed
- MCP tool gating: MCP tools denied by default
- Approve/revoke flow for "ask" tools
- Reset clears all state
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


# Read-only tools allowed in plan mode
READ_ONLY_TOOLS = {"search_memory", "read_file", "web_search", "plan_task"}

# MCP tool prefix
MCP_PREFIX = "mcp__"


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
    _plan_mode: bool = field(default=False, repr=False)
    _enabled_mcp_tools: set[str] = field(default_factory=set, repr=False)
    _approved_tools: set[str] = field(default_factory=set, repr=False)

    def evaluate(self, tool_name: str, iteration: int = 0) -> Decision:
        """Evaluate policy for a tool call at the given iteration.

        Evaluation order:
        1. Plan mode override (if enabled, only read-only tools allowed)
        2. MCP tool gating (MCP tools denied unless explicitly enabled)
        3. Approved tools (approved "ask" tools become "allow")
        4. Explicit rules (first match wins)
        5. Per-tool usage limit
        6. Default decision
        """
        # 1. Plan mode: only read-only tools allowed
        if self._plan_mode:
            if tool_name in READ_ONLY_TOOLS:
                return "allow"
            return "deny"

        # 2. MCP tool gating
        if tool_name.startswith(MCP_PREFIX):
            if tool_name in self._enabled_mcp_tools:
                # Check if it has an explicit rule
                for rule in self.rules:
                    if rule.matches(tool_name):
                        return rule.decision
                return "allow"
            return "deny"

        # 3. Approved tools bypass "ask" rules
        if tool_name in self._approved_tools:
            # Still check explicit rules first
            for rule in self.rules:
                if rule.matches(tool_name):
                    if rule.decision == "ask":
                        return "allow"
                    return rule.decision
            return "allow"

        # 4. Explicit rules (first match wins)
        for rule in self.rules:
            if rule.matches(tool_name):
                return rule.decision

        # 5. Per-tool usage limit
        if self.max_uses_per_tool > 0:
            self._use_counts[tool_name] += 1
            if self._use_counts[tool_name] > self.max_uses_per_tool:
                return "deny"

        # 6. Default decision
        return self.default_decision

    def reset_use_counts(self) -> None:
        """Reset per-tool use counters (e.g. at the start of a new agent run)."""
        self._use_counts.clear()

    def enable_plan_mode(self) -> None:
        """Enable plan mode — only read-only tools allowed."""
        self._plan_mode = True

    def disable_plan_mode(self) -> None:
        """Disable plan mode — normal tool access restored."""
        self._plan_mode = False

    @property
    def is_plan_mode(self) -> bool:
        """Check if plan mode is active."""
        return self._plan_mode

    def enable_mcp_tool(self, tool_name: str) -> None:
        """Explicitly enable an MCP tool."""
        self._enabled_mcp_tools.add(tool_name)

    def disable_mcp_tool(self, tool_name: str) -> None:
        """Disable an MCP tool (revoke explicit enable)."""
        self._enabled_mcp_tools.discard(tool_name)

    def approve(self, tool_name: str) -> None:
        """Approve a tool that requires approval (changes "ask" to "allow")."""
        self._approved_tools.add(tool_name)

    def revoke_approval(self, tool_name: str) -> None:
        """Revoke approval for a tool."""
        self._approved_tools.discard(tool_name)

    def allow(self, pattern: str, reason: str = "") -> None:
        """Add an allow rule."""
        self.rules.append(ToolRule(pattern=pattern, decision="allow", reason=reason))

    def deny(self, pattern: str, reason: str = "") -> None:
        """Add a deny rule."""
        self.rules.append(ToolRule(pattern=pattern, decision="deny", reason=reason))

    def ask(self, pattern: str, reason: str = "") -> None:
        """Add an ask rule (require approval)."""
        self.rules.append(ToolRule(pattern=pattern, decision="ask", reason=reason))

    def reset(self) -> None:
        """Reset all state: plan mode, approvals, MCP tools, use counts, rules."""
        self._plan_mode = False
        self._enabled_mcp_tools.clear()
        self._approved_tools.clear()
        self._use_counts.clear()
        self.rules.clear()

    def copy(self) -> ToolPolicy:
        """Create an independent copy of this policy."""
        return ToolPolicy(
            rules=list(self.rules),
            default_decision=self.default_decision,
            max_uses_per_tool=self.max_uses_per_tool,
            _plan_mode=self._plan_mode,
            _enabled_mcp_tools=set(self._enabled_mcp_tools),
            _approved_tools=set(self._approved_tools),
        )


def default_policy() -> ToolPolicy:
    """Return the default tool policy for the agent system.

    - Read-only tools: ALLOW (search_memory, read_file, web_search, plan_task)
    - Write tools: ALLOW (create_memory, write_file)
    - Dangerous tools: ASK (exec_command, delete_file)
    - Unknown tools: ALLOW (default)
    - MCP tools: DENY by default
    """
    return ToolPolicy(
        rules=[
            ToolRule("exec_command", "ask", "Shell commands require approval"),
            ToolRule("exec_*", "ask", "Execution tools require approval"),
            ToolRule("delete_file", "ask", "File deletion requires approval"),
        ],
        default_decision="allow",
        max_uses_per_tool=0,
    )
