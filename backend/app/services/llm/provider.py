"""Abstract LLM provider interface."""

from abc import ABC, abstractmethod
from typing import Any


class LLMProvider(ABC):
    """Abstract interface for LLM providers."""

    @abstractmethod
    async def chat(
        self, messages: list[dict], tools: list[dict], config: Any
    ) -> tuple[str, list[dict] | None]:
        """Send messages to LLM, return (text, optional_tool_calls)."""
        ...

    @abstractmethod
    def list_models(self) -> list[dict[str, Any]]:
        """List available models."""
        ...
