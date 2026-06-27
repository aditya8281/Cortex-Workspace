"""Token counting using tiktoken with graceful fallback.

Provides accurate token counting for LLM context management.
Falls back to character-based estimation (4 chars = 1 token) when
tiktoken is unavailable (optional dependency).

Usage:

    from backend.app.agents.token_counter import TokenCounter, count_tokens, count_message_tokens

    counter = TokenCounter(model="gpt-4o")
    count = await counter.count_tokens([{"role": "user", "content": "Hi"}])

    # Legacy API
    tokens = count_tokens("Hello, world!")
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

# Default encoding for chat models (GPT-4, GPT-3.5-turbo, etc.)
_DEFAULT_ENCODING = "cl100k_base"

# Approximate fallback ratio
_CHARS_PER_TOKEN = 4.0
_FORMATTING_OVERHEAD = 10  # chars per message for role markers, formatting
APPROX_CHARS_PER_TOKEN = 4


# ---------------------------------------------------------------------------
# Legacy functional API
# ---------------------------------------------------------------------------


def _init_encoder() -> Any | None:
    """Try to initialise the tiktoken encoder. Returns None if unavailable."""
    try:
        import tiktoken

        return tiktoken.get_encoding(_DEFAULT_ENCODING)
    except Exception:
        logger.debug("tiktoken not available — using character-based fallback")
        return None


_encoder: Any | None = None


def _get_encoder() -> Any | None:
    global _encoder
    if _encoder is None:
        _encoder = _init_encoder()
    return _encoder


def count_tokens(text: str) -> int:
    """Count tokens in *text* using tiktoken, falling back to character estimation."""
    if not text:
        return 0
    enc = _get_encoder()
    if enc is not None:
        return len(enc.encode(text))
    return max(1, len(text) // int(_CHARS_PER_TOKEN))


def count_message_tokens(
    messages: list[dict[str, str]],
    *,
    approx_chars_per_token: float = _CHARS_PER_TOKEN,
) -> int:
    """Count tokens across a list of message dicts."""
    if not messages:
        return 0
    enc = _get_encoder()
    if enc is not None:
        total = 0
        for m in messages:
            content = m.get("content", "")
            if content:
                total += len(enc.encode(content))
            total += 2
        return total
    total_chars = sum(len(m.get("content", "")) for m in messages)
    total_chars += len(messages) * _FORMATTING_OVERHEAD
    return int(total_chars / approx_chars_per_token)


# ---------------------------------------------------------------------------
# Class-based API — P07 Task 1 + Task 3
# ---------------------------------------------------------------------------


@dataclass
class TokenCount:
    """Token count for a single request."""

    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    model: str = ""
    context_window: int = 0
    context_usage_pct: float = 0.0


@dataclass
class CumulativeUsage:
    """Cumulative token usage over time."""

    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_requests: int = 0
    request_count: int = 0
    avg_input_tokens: float = 0.0
    avg_output_tokens: float = 0.0


class TokenCounter:
    """Count tokens for LLM requests with tiktoken or estimation fallback."""

    CONTEXT_WINDOWS: dict[str, int] = {
        "gpt-4": 8192,
        "gpt-4-turbo": 128_000,
        "gpt-4o": 128_000,
        "gpt-4o-mini": 128_000,
        "claude-3-opus": 200_000,
        "claude-3-sonnet": 200_000,
        "claude-3-haiku": 200_000,
        "claude-3.5-sonnet": 200_000,
        "llama3": 8192,
        "mistral": 32_768,
        "default": 8192,
    }

    def __init__(self, model: str = "default"):
        self.model = model
        self.max_context_tokens = self.CONTEXT_WINDOWS.get(model, 8192)
        self._tokenizer: Any | None = None
        self._cumulative = CumulativeUsage()

        try:
            import tiktoken

            self._tokenizer = tiktoken.encoding_for_model(model)
        except (ImportError, KeyError):
            logger.info("tiktoken not available for %s, using estimation", model)

    async def count_tokens(self, messages: list[dict]) -> int:
        """Count total tokens in a list of messages."""
        total = 0
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, str):
                total += self._count_text_tokens(content)
            elif isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and "text" in part:
                        total += self._count_text_tokens(part["text"])
            total += 4  # per-message overhead
        return total

    def _count_text_tokens(self, text: str) -> int:
        """Count tokens in a text string.

        For very large texts (>100KB), use estimation — tiktoken compression
        of repetitive data underestimates real-world token usage, and
        estimation is faster at this scale.
        """
        if self._tokenizer and len(text) < 100_000:
            try:
                return len(self._tokenizer.encode(text))
            except Exception:
                pass
        return max(1, len(text) // APPROX_CHARS_PER_TOKEN)

    async def count_request(
        self,
        input_messages: list[dict],
        output_text: str,
        model: str | None = None,
    ) -> TokenCount:
        """Count tokens for a full request (input + output)."""
        model = model or self.model
        context_window = self.CONTEXT_WINDOWS.get(model, 8192)

        input_tokens = await self.count_tokens(input_messages)
        output_tokens = self._count_text_tokens(output_text)
        total = input_tokens + output_tokens

        count = TokenCount(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total,
            model=model,
            context_window=context_window,
            context_usage_pct=input_tokens / context_window if context_window > 0 else 0,
        )

        self._cumulative.total_input_tokens += input_tokens
        self._cumulative.total_output_tokens += output_tokens
        self._cumulative.total_requests += 1
        self._cumulative.request_count = self._cumulative.total_requests
        self._cumulative.avg_input_tokens = self._cumulative.total_input_tokens / self._cumulative.total_requests
        self._cumulative.avg_output_tokens = self._cumulative.total_output_tokens / self._cumulative.total_requests

        return count

    def get_cumulative_usage(self) -> CumulativeUsage:
        """Get cumulative token usage."""
        return self._cumulative

    def get_context_usage(self, messages: list[dict]) -> float:
        """Get current context window usage as a percentage."""
        total = 0
        for msg in messages:
            content = str(msg.get("content", ""))
            total += max(1, len(content) // APPROX_CHARS_PER_TOKEN)
            total += 4
        return total / self.max_context_tokens if self.max_context_tokens > 0 else 0

    def set_model(self, model: str) -> None:
        """Change the model (updates context window)."""
        self.model = model
        self.max_context_tokens = self.CONTEXT_WINDOWS.get(model, 8192)
        try:
            import tiktoken

            self._tokenizer = tiktoken.encoding_for_model(model)
        except (ImportError, KeyError):
            self._tokenizer = None
