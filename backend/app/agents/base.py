"""Base agent class — all agents inherit from this."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Abstract base for all agents.

    Provides a common interface for LLM-powered agents that can
    plan, execute, and report results.
    """

    def __init__(self, system_prompt: str | None = None):
        self.system_prompt = system_prompt or self._default_prompt()
        self._tools: dict[str, Any] = {}

    @abstractmethod
    def _default_prompt(self) -> str:
        """Return the default system prompt for this agent."""
        ...

    @abstractmethod
    async def run(self, input_text: str, context: dict | None = None) -> str:
        """Execute the agent's main logic and return a result string."""
        ...

    def register_tool(self, name: str, handler: Any) -> None:
        """Register a callable tool that the agent can use."""
        self._tools[name] = handler

    def get_tool_schemas(self) -> list[dict]:
        """Return tool schemas for LLM function calling."""
        return [
            {
                "type": "function",
                "function": {
                    "name": name,
                    "description": getattr(handler, "__doc__", f"Tool: {name}"),
                },
            }
            for name, handler in self._tools.items()
        ]

    async def execute_tool(self, name: str, **kwargs: Any) -> Any:
        """Execute a registered tool by name."""
        handler = self._tools.get(name)
        if not handler:
            raise ValueError(f"Unknown tool: {name}")

        import inspect

        if inspect.iscoroutinefunction(handler):
            return await handler(**kwargs)
        return handler(**kwargs)
