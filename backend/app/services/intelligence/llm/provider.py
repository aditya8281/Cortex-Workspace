"""Abstract LLM provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


class LLMProvider(ABC):
    """Abstract interface for LLM providers."""

    @abstractmethod
    async def chat(self, messages: list[dict], tools: list[dict], config: Any) -> tuple[str, list[dict] | None]:
        """Send messages to LLM, return (text, optional_tool_calls)."""
        ...

    async def chat_with_tools(
        self,
        messages: list[LLMMessage],
        tools: list[dict],
        model: str | None = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> dict:
        """Native function-calling API. Returns dict with content, tool_calls, model, tokens.

        Subclasses that support native tool calling override this.
        Default raises NotImplementedError so callers can fall back to text-based TOOL_CALL.
        """
        raise NotImplementedError(f"{type(self).__name__} does not support native tool calling")

    @abstractmethod
    def list_models(self) -> list[dict[str, Any]]:
        """List available models."""
        ...


@dataclass
class LLMMessage:
    role: str  # "system", "user", "assistant"
    content: str


@dataclass
class LLMResponse:
    content: str
    model: str
    tokens_prompt: int = 0
    tokens_completion: int = 0
    finish_reason: str = "stop"  # "stop", "length"


@dataclass
class LLMModelInfo:
    name: str
    size_bytes: int = 0
    quantization: str | None = None
    context_length: int = 4096
    capabilities: list[str] = field(default_factory=list)
    description: str = ""
    # Enriched metadata (populated from scraper/cache)
    parameter_count: str | None = None
    variants: list[str] = field(default_factory=list)
    hardware_requirements: dict = field(default_factory=lambda: {"min_ram_gb": 4, "recommended_ram_gb": 8})
