"""Token counting using tiktoken with graceful fallback.

Provides accurate token counting for LLM context management.
Falls back to character-based estimation (4 chars = 1 token) when
tiktoken is unavailable (optional dependency).

Usage:

    from backend.app.agents.token_counter import count_tokens, count_message_tokens

    tokens = count_tokens("Hello, world!")
    msg_tokens = count_message_tokens([{"role": "user", "content": "Hi"}])
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Default encoding for chat models (GPT-4, GPT-3.5-turbo, etc.)
_DEFAULT_ENCODING = "cl100k_base"

# Approximate fallback ratio
_CHARS_PER_TOKEN = 4.0
_FORMATTING_OVERHEAD = 10  # chars per message for role markers, formatting


def _init_encoder() -> Any | None:
    """Try to initialise the tiktoken encoder. Returns None if unavailable."""
    try:
        import tiktoken

        return tiktoken.get_encoding(_DEFAULT_ENCODING)
    except Exception:
        logger.debug("tiktoken not available — using character-based fallback")
        return None


# Module-level cached encoder — initialised once on first use.
_encoder: Any | None = None


def _get_encoder() -> Any | None:
    global _encoder
    if _encoder is None:
        _encoder = _init_encoder()
    return _encoder


def count_tokens(text: str) -> int:
    """Count tokens in *text* using tiktoken, falling back to character estimation.

    Parameters
    ----------
    text:
        The text to count tokens for.

    Returns
    -------
    int
        Token count (always >= 1 for non-empty text, or 0 for empty).
    """
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
    """Count tokens across a list of message dicts.

    Each message's content is counted individually. A small formatting
    overhead is added per message to account for role markers, JSON
    framing, etc. (applied only in the fallback path — tiktoken handles
    this naturally).

    Parameters
    ----------
    messages:
        List of message dicts with at least a ``"content"`` key.
    approx_chars_per_token:
        Fallback ratio used only when tiktoken is unavailable (default 4.0).

    Returns
    -------
    int
        Total token count for all messages.
    """
    if not messages:
        return 0
    enc = _get_encoder()
    if enc is not None:
        total = 0
        for m in messages:
            content = m.get("content", "")
            if content:
                total += len(enc.encode(content))
            # Small overhead for role markers / framing
            total += 2
        return total
    # Fallback: character-based
    total_chars = sum(len(m.get("content", "")) for m in messages)
    total_chars += len(messages) * _FORMATTING_OVERHEAD
    return int(total_chars / approx_chars_per_token)
