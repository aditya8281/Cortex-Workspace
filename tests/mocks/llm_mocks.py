"""Mock LLM responses for testing agent system."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock


def create_mock_llm_response(
    content: str = "Test response",
    model: str = "test-model",
    tokens_used: int = 100,
) -> dict:
    """Create a mock LLM response dict."""
    return {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": content,
                },
                "finish_reason": "stop",
            }
        ],
        "model": model,
        "usage": {
            "prompt_tokens": 50,
            "completion_tokens": tokens_used,
            "total_tokens": 50 + tokens_used,
        },
    }


def create_mock_streaming_response(
    chunks: list[str] | None = None,
) -> Generator[dict, None, None]:
    """Create a mock streaming LLM response."""
    if chunks is None:
        chunks = ["Hello", " ", "world", "!"]

    for i, chunk in enumerate(chunks):
        yield {
            "choices": [
                {
                    "delta": {"content": chunk},
                    "finish_reason": "stop" if i == len(chunks) - 1 else None,
                }
            ],
            "model": "test-model",
        }


def create_mock_llm_client() -> MagicMock:
    """Create a fully mocked LLM client for testing."""
    client = MagicMock()
    client.chat.completions.create = AsyncMock(return_value=create_mock_llm_response())
    return client


def create_mock_redis() -> AsyncMock:
    """Create a mocked Redis client for testing."""
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock(return_value=True)
    redis.delete = AsyncMock(return_value=1)
    redis.exists = AsyncMock(return_value=0)
    redis.ttl = AsyncMock(return_value=-1)
    return redis


def create_mock_qdrant() -> MagicMock:
    """Create a mocked Qdrant client for testing."""
    qdrant = MagicMock()
    qdrant.search = MagicMock(return_value=[])
    qdrant.upsert = MagicMock(return_value=True)
    qdrant.delete = MagicMock(return_value=True)
    qdrant.get_collection = MagicMock(return_value={"vectors_count": 0})
    return qdrant
