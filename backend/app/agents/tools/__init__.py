"""Agent tool system — @tool decorator, registry, schemas, policy, security.

Usage:
    from backend.app.agents.tools import tool, get_tool_registry

    @tool(description="Search the codebase")
    async def search(query: str, limit: int = 10) -> str:
        \"\"\"Search the codebase for matching code.\"\"\"
        ...

    registry = get_tool_registry()
    tool = registry.get("search")
    schemas = registry.schemas_for()
"""

from __future__ import annotations

from backend.app.agents.tools.policy import ToolPolicy, ToolRule, default_policy
from backend.app.agents.tools.registry import Tool, ToolRegistry, get_tool_registry, tool
from backend.app.agents.tools.schemas import generate_schema
from backend.app.agents.tools.security import (
    BLOCKED_COMMANDS,
    BLOCKED_URL_SCHEMES,
    ensure_within_workspace,
    has_blocked_command,
    is_private_url,
)

__all__ = [
    "Tool",
    "ToolPolicy",
    "ToolRegistry",
    "ToolRule",
    "default_policy",
    "ensure_within_workspace",
    "generate_schema",
    "get_tool_registry",
    "has_blocked_command",
    "is_private_url",
    "tool",
    "BLOCKED_COMMANDS",
    "BLOCKED_URL_SCHEMES",
]
