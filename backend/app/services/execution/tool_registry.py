"""Tool registry — central catalog of callable tools with validation."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any


class ToolValidationError(Exception):
    """Raised when tool parameters fail validation."""


class ToolNotFoundError(Exception):
    """Raised when a requested tool is not registered."""


class ToolRegistry:
    """Central registry of available tools for the execution engine.

    Features:
    - Tool registration with typed parameter schemas
    - Parameter validation against JSON-Schema-like definitions
    - Confirmation gate for dangerous operations
    - Execution timeout enforcement
    """

    def __init__(self) -> None:
        self._tools: dict[str, dict[str, Any]] = {}

    def register(
        self,
        name: str,
        func: Callable[..., Any],
        description: str,
        parameters: dict[str, Any],
        requires_confirmation: bool = False,
        max_timeout_ms: int = 60000,
        category: str = "general",
    ) -> None:
        if name in self._tools:
            raise ValueError(f"Tool '{name}' is already registered")
        if not callable(func):
            raise ValueError(f"Tool function must be callable, got {type(func)}")

        self._tools[name] = {
            "name": name,
            "func": func,
            "description": description,
            "parameters": parameters,
            "requires_confirmation": requires_confirmation,
            "max_timeout_ms": max_timeout_ms,
            "category": category,
        }

    def unregister(self, name: str) -> bool:
        if name in self._tools:
            del self._tools[name]
            return True
        return False

    def get_tool(self, name: str) -> dict[str, Any] | None:
        tool = self._tools.get(name)
        if not tool:
            return None
        return {
            "name": tool["name"],
            "description": tool["description"],
            "parameters": tool["parameters"],
            "requires_confirmation": tool["requires_confirmation"],
            "max_timeout_ms": tool["max_timeout_ms"],
            "category": tool["category"],
        }

    def list_tools(self, category: str | None = None) -> list[dict[str, Any]]:
        tools = []
        for _name, tool in self._tools.items():
            if category and tool["category"] != category:
                continue
            tools.append(
                {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["parameters"],
                    "requires_confirmation": tool["requires_confirmation"],
                    "category": tool["category"],
                }
            )
        return tools

    def has_tool(self, name: str) -> bool:
        return name in self._tools

    def validate_params(self, name: str, params: dict[str, Any]) -> list[str]:
        """Validate parameters. Returns list of errors (empty if valid)."""
        tool = self._tools.get(name)
        if not tool:
            return [f"Tool '{name}' not found"]

        errors: list[str] = []
        schema = tool["parameters"]

        type_map: dict[str, type | tuple[type, ...]] = {
            "string": str,
            "str": str,
            "integer": int,
            "int": int,
            "number": (int, float),
            "float": (int, float),
            "boolean": bool,
            "bool": bool,
            "array": list,
            "list": list,
            "object": dict,
            "dict": dict,
        }

        for param_name, param_def in schema.items():
            if param_def.get("required", False) and param_name not in params:
                errors.append(f"Missing required parameter: {param_name}")
            if param_name in params:
                expected_type = param_def.get("type")
                value = params[param_name]
                if expected_type and expected_type in type_map:
                    expected = type_map[expected_type]
                    if not isinstance(value, expected):
                        errors.append(f"Parameter '{param_name}' expected {expected_type}, got {type(value).__name__}")

        for param_name in params:
            if param_name not in schema:
                errors.append(f"Unexpected parameter: {param_name}")

        return errors

    async def execute(
        self,
        name: str,
        params: dict[str, Any],
        confirmed: bool = False,
    ) -> Any:
        tool = self._tools.get(name)
        if not tool:
            raise ToolNotFoundError(f"Tool '{name}' is not registered")

        errors = self.validate_params(name, params)
        if errors:
            raise ToolValidationError(f"Parameter validation failed: {'; '.join(errors)}")

        if tool["requires_confirmation"] and not confirmed:
            raise PermissionError(f"Tool '{name}' requires confirmation. Set confirmed=True to proceed.")

        timeout = tool["max_timeout_ms"] / 1000.0
        func = tool["func"]

        if asyncio.iscoroutinefunction(func):
            result = await asyncio.wait_for(func(**params), timeout=timeout)
        else:
            result = func(**params)
        return result

    def execute_sync(
        self,
        name: str,
        params: dict[str, Any],
        confirmed: bool = False,
    ) -> Any:
        """Synchronous execute — used by ExecutionEngine which runs outside async."""
        tool = self._tools.get(name)
        if not tool:
            raise ToolNotFoundError(f"Tool '{name}' is not registered")

        errors = self.validate_params(name, params)
        if errors:
            raise ToolValidationError(f"Parameter validation failed: {'; '.join(errors)}")

        if tool["requires_confirmation"] and not confirmed:
            raise PermissionError(f"Tool '{name}' requires confirmation. Set confirmed=True to proceed.")

        func = tool["func"]
        if asyncio.iscoroutinefunction(func):
            raise RuntimeError(f"Tool '{name}' is async — use async execute() instead")
        return func(**params)


# Global singleton
_tool_registry: ToolRegistry | None = None


def get_tool_registry() -> ToolRegistry:
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = ToolRegistry()
    return _tool_registry


def register_default_tools(registry: ToolRegistry) -> None:
    """Register built-in tools."""

    async def echo_tool(message: str = "ok") -> dict:
        return {"echo": message}

    async def add_numbers(a: float = 0, b: float = 0) -> dict:
        return {"result": a + b}

    registry.register(
        name="echo",
        func=echo_tool,
        description="Echoes a message back",
        parameters={"message": {"type": "string", "required": False, "default": "ok"}},
        category="general",
    )
    registry.register(
        name="add_numbers",
        func=add_numbers,
        description="Adds two numbers",
        parameters={
            "a": {"type": "number", "required": True},
            "b": {"type": "number", "required": True},
        },
        category="math",
    )
