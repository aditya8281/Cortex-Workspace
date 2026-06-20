"""HuggingFace GGUF model discovery."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)

HF_API_BASE = "https://huggingface.co/api"
HF_SEARCH_URL = f"{HF_API_BASE}/models"


@dataclass
class GgufVariant:
    repo_id: str
    filename: str
    quantization: str
    size_bytes: int
    parameter_count: float | None


# Known GGUF repos per model family
KNOWN_GGUF_REPOS: dict[str, list[str]] = {
    "llama": [
        "bartowski/Meta-Llama-3.1-8B-Instruct-GGUF",
        "bartowski/Meta-Llama-3.1-70B-Instruct-GGUF",
        "bartowski/Meta-Llama-3.1-405B-Instruct-GGUF",
        "bartowski/Meta-Llama-3.2-3B-Instruct-GGUF",
        "bartowski/Meta-Llama-3.2-11B-Vision-Instruct-GGUF",
    ],
    "qwen": [
        "bartowski/Qwen2.5-0.5B-Instruct-GGUF",
        "bartowski/Qwen2.5-1.5B-Instruct-GGUF",
        "bartowski/Qwen2.5-3B-Instruct-GGUF",
        "bartowski/Qwen2.5-7B-Instruct-GGUF",
        "bartowski/Qwen2.5-14B-Instruct-GGUF",
        "bartowski/Qwen2.5-32B-Instruct-GGUF",
        "bartowski/Qwen2.5-72B-Instruct-GGUF",
        "bartowski/Qwen2.5-Coder-7B-Instruct-GGUF",
        "bartowski/Qwen2.5-Coder-14B-Instruct-GGUF",
        "bartowski/Qwen2.5-Coder-32B-Instruct-GGUF",
    ],
    "deepseek": [
        "bartowski/DeepSeek-Coder-V2-Lite-Instruct-GGUF",
        "bartowski/DeepSeek-R1-Distill-Qwen-1.5B-GGUF",
        "bartowski/DeepSeek-R1-Distill-Qwen-7B-GGUF",
        "bartowski/DeepSeek-R1-Distill-Llama-8B-GGUF",
        "bartowski/DeepSeek-R1-Distill-Llama-70B-GGUF",
    ],
    "phi": [
        "bartowski/Phi-3.5-mini-instruct-GGUF",
        "bartowski/Phi-4-mini-instruct-GGUF",
    ],
    "gemma": [
        "bartowski/gemma-2-2b-it-GGUF",
        "bartowski/gemma-2-9b-it-GGUF",
        "bartowski/gemma-2-27b-it-GGUF",
    ],
    "mistral": [
        "bartowski/Mistral-7B-Instruct-v0.3-GGUF",
        "TheBloke/Mistral-7B-Instruct-v0.2-GGUF",
    ],
    "mixtral": [
        "bartowski/Mixtral-8x7B-Instruct-v0.1-GGUF",
    ],
    "codellama": [
        "bartowski/codellama-7b-Instruct-GGUF",
        "bartowski/codellama-13b-Instruct-GGUF",
        "bartowski/codellama-34b-Instruct-GGUF",
    ],
    "starcoder": [
        "bartowski/starcoder2-3b-GGUF",
        "bartowski/starcoder2-7b-GGUF",
        "bartowski/starcoder2-15b-GGUF",
    ],
}


def _parse_gguf_filename(filename: str) -> GgufVariant | None:
    """Parse a GGUF filename to extract quantization and size info."""
    if not filename.endswith(".gguf"):
        return None

    name = filename.replace(".gguf", "")

    # Extract quantization (e.g., Q4_K_M, Q8_0, F16)
    quant_match = re.search(r"(Q\d+[K_SML_]*\w*|F\d+|IQ\d+\w*)", name, re.IGNORECASE)
    quantization = quant_match.group(1).upper() if quant_match else "UNKNOWN"

    # Estimate size from filename
    size_match = re.search(r"(\d+(?:\.\d+)?)\s*[bB]", name)
    param_count = float(size_match.group(1)) if size_match else None

    return GgufVariant(
        repo_id="",
        filename=filename,
        quantization=quantization,
        size_bytes=0,  # Will be populated from API
        parameter_count=param_count,
    )


async def discover_gguf_variants(family: str) -> list[GgufVariant]:
    """Discover GGUF variants for a model family from HuggingFace."""
    repos = KNOWN_GGUF_REPOS.get(family, [])
    variants: list[GgufVariant] = []

    async with httpx.AsyncClient(timeout=30.0) as client:
        for repo_id in repos:
            try:
                resp = await client.get(
                    f"{HF_API_BASE}/models/{repo_id}/tree/main",
                    headers={"User-Agent": "Cortex/1.0"},
                )
                if resp.status_code != 200:
                    continue

                files = resp.json()
                for file_info in files:
                    fname = file_info.get("path", "")
                    variant = _parse_gguf_filename(fname)
                    if variant:
                        variant.repo_id = repo_id
                        variant.size_bytes = file_info.get("size", 0)
                        variants.append(variant)

            except Exception as e:
                logger.warning("Failed to fetch GGUF variants from %s: %s", repo_id, e)
                continue

    return variants


async def search_huggingface_gguf(query: str, limit: int = 20) -> list[dict]:
    """Search HuggingFace for GGUF models."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                HF_SEARCH_URL,
                params={
                    "search": query,
                    "filter": "gguf",
                    "sort": "downloads",
                    "direction": "-1",
                    "limit": limit,
                },
                headers={"User-Agent": "Cortex/1.0"},
            )
            if resp.status_code != 200:
                return []
            return resp.json()
    except Exception as e:
        logger.warning("HuggingFace search failed: %s", e)
        return []
