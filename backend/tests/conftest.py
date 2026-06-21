"""Conftest for backend/tests — mocks the Ollama catalog for deterministic seeding."""

from unittest.mock import patch

import pytest

FAKE_CATALOG = [
    {
        "name": "llama3.1:8b",
        "family": "llama",
        "parameter_size": "8B",
        "capabilities": ["chat"],
        "source": "registry",
        "size": 4_700_000_000,
        "description": "Llama 3.1 8B general chat model.",
        "quantization": "Q4_0",
    },
    {
        "name": "llama3.2:1b",
        "family": "llama",
        "parameter_size": "1B",
        "capabilities": ["chat"],
        "source": "registry",
        "size": 700_000_000,
        "description": "Llama 3.2 1B lightweight model.",
        "quantization": "Q4_0",
    },
    {
        "name": "llama3.1:405b",
        "family": "llama",
        "parameter_size": "405B",
        "capabilities": ["chat", "reasoning"],
        "source": "registry",
        "size": 230_000_000_000,
        "description": "Llama 3.1 405B large model.",
        "quantization": "Q4_0",
    },
    {
        "name": "qwen2.5-coder:7b",
        "family": "qwen",
        "parameter_size": "7B",
        "capabilities": ["chat", "code"],
        "source": "registry",
        "size": 4_400_000_000,
        "description": "Qwen 2.5 Coder 7B for code generation.",
        "quantization": "Q4_0",
    },
    {
        "name": "qwen2.5-coder:32b",
        "family": "qwen",
        "parameter_size": "32B",
        "capabilities": ["chat", "code"],
        "source": "registry",
        "size": 19_000_000_000,
        "description": "Qwen 2.5 Coder 32B code model.",
        "quantization": "Q4_0",
    },
    {
        "name": "qwen2.5:72b",
        "family": "qwen",
        "parameter_size": "72B",
        "capabilities": ["chat", "reasoning"],
        "source": "registry",
        "size": 42_000_000_000,
        "description": "Qwen 2.5 72B general model.",
        "quantization": "Q4_0",
    },
    {
        "name": "qwen2.5:0.5b",
        "family": "qwen",
        "parameter_size": "0.5B",
        "capabilities": ["chat"],
        "source": "registry",
        "size": 400_000_000,
        "description": "Qwen 2.5 0.5B tiny model.",
        "quantization": "Q4_0",
    },
    {
        "name": "deepseek-r1:32b",
        "family": "deepseek",
        "parameter_size": "32B",
        "capabilities": ["chat", "reasoning"],
        "source": "registry",
        "size": 19_000_000_000,
        "description": "DeepSeek R1 32B reasoning model.",
        "quantization": "Q4_0",
    },
    {
        "name": "deepseek-coder-v2:16b",
        "family": "deepseek",
        "parameter_size": "16B",
        "capabilities": ["chat", "code"],
        "source": "registry",
        "size": 9_500_000_000,
        "description": "DeepSeek Coder V2 16B coding model.",
        "quantization": "Q4_0",
    },
    {
        "name": "llava:7b",
        "family": "llava",
        "parameter_size": "7B",
        "capabilities": ["chat", "vision"],
        "source": "registry",
        "size": 4_500_000_000,
        "description": "LLaVA 7B vision model.",
        "quantization": "Q4_0",
    },
    {
        "name": "nomic-embed-text:latest",
        "family": "nomic-embed-text",
        "parameter_size": "137M",
        "capabilities": ["embedding"],
        "source": "registry",
        "size": 274_000_000,
        "description": "Nomic Embed Text embedding model.",
        "quantization": "F16",
    },
]


@pytest.fixture(autouse=True, scope="session")
def _mock_ollama_catalog():
    """Replace the Ollama catalog fetch with deterministic test data."""
    with patch(
        "backend.app.services.ollama_catalog.get_ollama_catalog_sync",
        return_value=FAKE_CATALOG,
    ):
        yield
