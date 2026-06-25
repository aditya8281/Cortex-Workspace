"""@tool decorator and ToolRegistry — declarative tool registration.

Usage:
    @tool(name="my_tool", description="Does something useful")
    async def my_tool(query: str, limit: int = 10) -> str:
        \"\"\"Does something useful.

        Args:
            query: The search query
            limit: Max results to return
        \"\"\"
        return f"Results for {query}"
"""

from __future__ import annotations

import inspect
import logging
from dataclasses import dataclass, field
from functools import wraps
from typing import Any

from backend.app.agents.tools.schemas import generate_schema

logger = logging.getLogger(__name__)


@dataclass
class Tool:
    """Describes a registered tool."""

    name: str
    description: str
    handler: Any
    schema: dict = field(default_factory=dict)
    requires_approval: bool = False
    category: str = "general"


class ToolRegistry:
    """Registry for agent tools with schema generation."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Register a tool. Overwrites if name already exists."""
        if tool.name in self._tools:
            logger.warning("Overwriting existing tool: %s", tool.name)
        self._tools[tool.name] = tool
        logger.debug("Registered tool: %s (category: %s)", tool.name, tool.category)

    def get(self, name: str) -> Tool | None:
        """Look up a tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> dict[str, str]:
        """Return {name: description} for all tools."""
        return {name: tool.description for name, tool in self._tools.items()}

    def get_all(self) -> list[Tool]:
        """Return all tools as a list."""
        return list(self._tools.values())

    def schemas_for(self, names: list[str] | None = None) -> list[dict]:
        """Return OpenAI-compatible schemas for tools.

        Args:
            names: Optional filter — only return schemas for named tools.
                   If None, returns all tools.
        """
        matched = self._tools.values()
        if names is not None:
            filtered: list[Tool] = [t for t in matched if t.name in names]
        else:
            filtered = list(matched)
        return [t.schema for t in filtered if t.schema]

    async def execute(self, name: str, **kwargs: Any) -> str:
        """Execute a registered tool by name, returning its result as a string.

        Handles both sync and async tool handlers automatically.
        Raises ValueError if the tool is not found.
        """
        tool = self.get(name)
        if not tool:
            raise ValueError(f"Unknown tool: {name}")

        handler = tool.handler
        if inspect.iscoroutinefunction(handler):
            result = await handler(**kwargs)
        else:
            result = handler(**kwargs)

        # Coerce result to string for consistent LLM context injection
        if result is None:
            return ""
        if isinstance(result, str):
            return result
        return str(result)

    def remove(self, name: str) -> None:
        """Remove a tool by name. No-op if not found."""
        self._tools.pop(name, None)

    def clear(self) -> None:
        """Remove all registered tools."""
        self._tools.clear()

    @property
    def count(self) -> int:
        return len(self._tools)


# Module-level singleton registry
_TOOL_REGISTRY = ToolRegistry()


def get_tool_registry() -> ToolRegistry:
    """Return the global tool registry singleton."""
    return _TOOL_REGISTRY


def tool(
    name: str | None = None,
    description: str | None = None,
    *,
    requires_approval: bool = False,
    category: str = "general",
    auto_schema: bool = True,
) -> Any:
    """Decorator that registers a function as an agent tool.

    The decorated function's type hints + docstring are automatically
    converted to JSON Schema for LLM function-calling.

    Args:
        name: Tool name (defaults to function name).
        description: Tool description (defaults to function docstring first line).
        requires_approval: If True, user must approve before execution.
        category: Tool category for grouping (general, code, files, web, system).
        auto_schema: If True (default), generate JSON Schema from type hints.

    Returns:
        The original function (unchanged).
    """

    def decorator(func: Any) -> Any:
        tool_name = name or func.__name__
        tool_desc = description or (func.__doc__ or "").split("\n\n")[0].strip() or f"Tool: {tool_name}"

        # Generate schema
        schema: dict = {}
        if auto_schema:
            try:
                schema = generate_schema(func)
            except Exception as exc:
                logger.warning("Schema generation failed for %s: %s", tool_name, exc)
                schema = _fallback_schema(tool_name, tool_desc)

        reg = Tool(
            name=tool_name,
            description=tool_desc,
            handler=func,
            schema=schema,
            requires_approval=requires_approval,
            category=category,
        )
        _TOOL_REGISTRY.register(reg)

        # Match the original function's sync/async nature so direct calls work
        # without surprise coroutine objects from wrapped sync functions.
        if inspect.iscoroutinefunction(func):

            @wraps(func)
            async def async_wrapper(**kwargs: Any) -> Any:  # type: ignore[misc]
                return await func(**kwargs)

            return async_wrapper
        else:
            # Return the original function directly for sync tools so that
            # inspect.signature(func) preserves the real parameter names.
            return func

    return decorator


def _fallback_schema(name: str, desc: str) -> dict:
    """Minimal fallback schema when automatic generation fails."""
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": desc,
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    }
