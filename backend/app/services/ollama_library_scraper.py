from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

logger = logging.getLogger(__name__)

CACHE_FILE = "CortexMemory/ollama_library_catalog.json"
CACHE_TTL_HOURS = 24

BASE_URL = "https://ollama.com/library"
TIMEOUT_SECONDS = 30.0

HARDCODED_MODELS = [
    {
        "name": "llama3.1",
        "description": "Meta's Llama 3.1 instruction-tuned model. Supports general conversation, coding, and reasoning.",
        "capabilities": ["chat"],
        "suggested_ram": "8GB+",
        "parameter_variants": [
            {"name": "llama3.1:8b", "parameters": "8B", "size_bytes": 4700000000000},
            {"name": "llama3.1:70b", "parameters": "70B", "size_bytes": 40000000000000},
            {"name": "llama3.1:405b", "parameters": "405B", "size_bytes": 230000000000000},
        ],
    },
    {
        "name": "llama3.2",
        "description": "Meta's Llama 3.2 instruction-tuned model with improved reasoning and instruction following.",
        "capabilities": ["chat"],
        "suggested_ram": "8GB+",
        "parameter_variants": [
            {"name": "llama3.2:3b", "parameters": "3B", "size_bytes": 2000000000000},
            {"name": "llama3.2:11b", "parameters": "11B", "size_bytes": 7800000000000},
        ],
    },
    {
        "name": "llama3",
        "description": "Meta's Llama 3 base model. Powerful general-purpose model for conversation and coding.",
        "capabilities": ["chat"],
        "suggested_ram": "8GB+",
        "parameter_variants": [
            {"name": "llama3:8b", "parameters": "8B", "size_bytes": 4700000000000},
            {"name": "llama3:70b", "parameters": "70B", "size_bytes": 40000000000000},
        ],
    },
    {
        "name": "llama2",
        "description": "Meta's Llama 2 base model. Good for various language tasks and conversation.",
        "capabilities": ["chat"],
        "suggested_ram": "8GB+",
        "parameter_variants": [
            {"name": "llama2:7b", "parameters": "7B", "size_bytes": 3800000000000},
            {"name": "llama2:13b", "parameters": "13B", "size_bytes": 7400000000000},
            {"name": "llama2:70b", "parameters": "70B", "size_bytes": 40000000000000},
        ],
    },
    {
        "name": "codellama",
        "description": "Code-specialized Llama model for code generation and completion.",
        "capabilities": ["chat", "code"],
        "suggested_ram": "8GB+",
        "parameter_variants": [
            {"name": "codellama:7b", "parameters": "7B", "size_bytes": 3800000000000},
            {"name": "codellama:13b", "parameters": "13B", "size_bytes": 7400000000000},
            {"name": "codellama:34b", "parameters": "34B", "size_bytes": 19000000000000},
            {"name": "codellama:70b", "parameters": "70B", "size_bytes": 40000000000000},
        ],
    },
    {
        "name": "codellama:python",
        "description": "Code Llama specialized for Python code generation.",
        "capabilities": ["chat", "code"],
        "suggested_ram": "8GB+",
        "parameter_variants": [
            {"name": "codellama:python:7b", "parameters": "7B", "size_bytes": 3900000000000},
            {"name": "codellama:python:13b", "parameters": "13B", "size_bytes": 7600000000000},
            {"name": "codellama:python:34b", "parameters": "34B", "size_bytes": 19500000000000},
        ],
    },
    {
        "name": "mistral",
        "description": "Mistral AI's 7B model. Excellent performance for its size, great for instruction following.",
        "capabilities": ["chat"],
        "suggested_ram": "6GB+",
        "parameter_variants": [
            {"name": "mistral:7b", "parameters": "7B", "size_bytes": 4100000000000},
        ],
    },
    {
        "name": "mistral-nemo",
        "description": "Mistral AI's 12B model with improved reasoning and instruction following.",
        "capabilities": ["chat"],
        "suggested_ram": "8GB+",
        "parameter_variants": [
            {"name": "mistral-nemo:12b", "parameters": "12B", "size_bytes": 7000000000000},
        ],
    },
    {
        "name": "mixtral",
        "description": "Mistral AI's Mixture of Experts model. Efficient MoE architecture with strong performance.",
        "capabilities": ["chat"],
        "suggested_ram": "12GB+",
        "parameter_variants": [
            {"name": "mixtral:8x7b", "parameters": "8x7B", "size_bytes": 26000000000000},
        ],
    },
    {
        "name": "mixtral:instuct",
        "description": "Instruction-tuned Mixtral model for following complex instructions.",
        "capabilities": ["chat"],
        "suggested_ram": "12GB+",
        "parameter_variants": [
            {"name": "mixtral:8x7b-instruct", "parameters": "8x7B", "size_bytes": 26000000000000},
        ],
    },
    {
        "name": "phi",
        "description": "Microsoft's Phi-3 mini model. Small but capable for reasoning and chat.",
        "capabilities": ["chat", "reasoning"],
        "suggested_ram": "2GB+",
        "parameter_variants": [
            {"name": "phi:2.7b", "parameters": "2.7B", "size_bytes": 1600000000000},
        ],
    },
    {
        "name": "phi3",
        "description": "Microsoft Phi-3 small language model with strong reasoning capabilities.",
        "capabilities": ["chat", "reasoning"],
        "suggested_ram": "4GB+",
        "parameter_variants": [
            {"name": "phi3:3.8b", "parameters": "3.8B", "size_bytes": 2200000000000},
            {"name": "phi3:14b", "parameters": "14B", "size_bytes": 8000000000000},
        ],
    },
    {
        "name": "gemma",
        "description": "Google's Gemma model. Lightweight, high-quality language model.",
        "capabilities": ["chat"],
        "suggested_ram": "6GB+",
        "parameter_variants": [
            {"name": "gemma:2b", "parameters": "2B", "size_bytes": 1400000000000},
            {"name": "gemma:7b", "parameters": "7B", "size_bytes": 5000000000000},
        ],
    },
    {
        "name": "gemma2",
        "description": "Google's Gemma 2 model with improved architecture and performance.",
        "capabilities": ["chat"],
        "suggested_ram": "6GB+",
        "parameter_variants": [
            {"name": "gemma2:2b", "parameters": "2B", "size_bytes": 1600000000000},
            {"name": "gemma2:9b", "parameters": "9B", "size_bytes": 5500000000000},
            {"name": "gemma2:27b", "parameters": "27B", "size_bytes": 16000000000000},
        ],
    },
    {
        "name": "qwen",
        "description": "Alibaba's Qwen model. Strong multilingual and coding capabilities.",
        "capabilities": ["chat", "code"],
        "suggested_ram": "6GB+",
        "parameter_variants": [
            {"name": "qwen:0.5b", "parameters": "0.5B", "size_bytes": 400000000000},
            {"name": "qwen:1.8b", "parameters": "1.8B", "size_bytes": 1100000000000},
            {"name": "qwen:4b", "parameters": "4B", "size_bytes": 2400000000000},
            {"name": "qwen:7b", "parameters": "7B", "size_bytes": 4100000000000},
            {"name": "qwen:14b", "parameters": "14B", "size_bytes": 8000000000000},
            {"name": "qwen:32b", "parameters": "32B", "size_bytes": 18000000000000},
        ],
    },
    {
        "name": "qwen2",
        "description": "Alibaba's Qwen 2 model with improved multilingual and reasoning capabilities.",
        "capabilities": ["chat", "code"],
        "suggested_ram": "6GB+",
        "parameter_variants": [
            {"name": "qwen2:0.5b", "parameters": "0.5B", "size_bytes": 500000000000},
            {"name": "qwen2:1.5b", "parameters": "1.5B", "size_bytes": 1000000000000},
            {"name": "qwen2:7b", "parameters": "7B", "size_bytes": 4400000000000},
            {"name": "qwen2:72b", "parameters": "72B", "size_bytes": 41000000000000},
        ],
    },
    {
        "name": "qwen2.5",
        "description": "Alibaba's Qwen 2.5 model with enhanced instruction following and knowledge.",
        "capabilities": ["chat", "code"],
        "suggested_ram": "6GB+",
        "parameter_variants": [
            {"name": "qwen2.5:0.5b", "parameters": "0.5B", "size_bytes": 500000000000},
            {"name": "qwen2.5:1.5b", "parameters": "1.5B", "size_bytes": 1000000000000},
            {"name": "qwen2.5:3b", "parameters": "3B", "size_bytes": 2000000000000},
            {"name": "qwen2.5:7b", "parameters": "7B", "size_bytes": 4500000000000},
            {"name": "qwen2.5:14b", "parameters": "14B", "size_bytes": 9000000000000},
            {"name": "qwen2.5:32b", "parameters": "32B", "size_bytes": 19000000000000},
            {"name": "qwen2.5:72b", "parameters": "72B", "size_bytes": 42000000000000},
        ],
    },
    {
        "name": "deepseek-coder",
        "description": "DeepSeek's code generation model. Specialized for programming tasks.",
        "capabilities": ["chat", "code"],
        "suggested_ram": "6GB+",
        "parameter_variants": [
            {"name": "deepseek-coder:1.3b", "parameters": "1.3B", "size_bytes": 800000000000},
            {"name": "deepseek-coder:6.7b", "parameters": "6.7B", "size_bytes": 3800000000000},
            {"name": "deepseek-coder:33b", "parameters": "33B", "size_bytes": 19000000000000},
        ],
    },
    {
        "name": "deepseek-v2",
        "description": "DeepSeek's V2 model with Mixture of Experts architecture.",
        "capabilities": ["chat", "code"],
        "suggested_ram": "12GB+",
        "parameter_variants": [
            {"name": "deepseek-v2:16b", "parameters": "16B", "size_bytes": 9000000000000},
            {"name": "deepseek-v2:236b", "parameters": "236B", "size_bytes": 140000000000000},
        ],
    },
    {
        "name": "nomic-embed-text",
        "description": "Nomic's text embedding model. High-quality embeddings for retrieval.",
        "capabilities": ["embedding"],
        "suggested_ram": "2GB+",
        "parameter_variants": [
            {"name": "nomic-embed-text:1.5", "parameters": "137M", "size_bytes": 275000000000},
        ],
    },
    {
        "name": "mxbai-embed-large",
        "description": "MixedBread's large embedding model for high-quality semantic search.",
        "capabilities": ["embedding"],
        "suggested_ram": "2GB+",
        "parameter_variants": [
            {"name": "mxbai-embed-large:1.5b", "parameters": "1.5B", "size_bytes": 900000000000},
        ],
    },
    {
        "name": "llava",
        "description": "Large Language and Vision Assistant. Supports image understanding.",
        "capabilities": ["chat", "vision"],
        "suggested_ram": "6GB+",
        "parameter_variants": [
            {"name": "llava:7b", "parameters": "7B", "size_bytes": 4200000000000},
            {"name": "llava:13b", "parameters": "13B", "size_bytes": 7800000000000},
            {"name": "llava:34b", "parameters": "34B", "size_bytes": 20000000000000},
        ],
    },
    {
        "name": "llava-llama3",
        "description": "LLaVA combined with Llama 3 for improved vision-language capabilities.",
        "capabilities": ["chat", "vision"],
        "suggested_ram": "8GB+",
        "parameter_variants": [
            {"name": "llava-llama3:8b", "parameters": "8B", "size_bytes": 4800000000000},
        ],
    },
    {
        "name": "bakllava",
        "description": "BakLLaVA model with enhanced vision capabilities.",
        "capabilities": ["chat", "vision"],
        "suggested_ram": "6GB+",
        "parameter_variants": [
            {"name": "bakllava:7b", "parameters": "7B", "size_bytes": 4200000000000},
        ],
    },
    {
        "name": "starcoder2",
        "description": "StarCoder 2 code generation model from HuggingFace.",
        "capabilities": ["chat", "code"],
        "suggested_ram": "6GB+",
        "parameter_variants": [
            {"name": "starcoder2:3b", "parameters": "3B", "size_bytes": 1700000000000},
            {"name": "starcoder2:7b", "parameters": "7B", "size_bytes": 4000000000000},
            {"name": "starcoder2:15b", "parameters": "15B", "size_bytes": 9000000000000},
        ],
    },
    {
        "name": "starcoder",
        "description": "StarCoder code generation model. Supports 80+ programming languages.",
        "capabilities": ["chat", "code"],
        "suggested_ram": "8GB+",
        "parameter_variants": [
            {"name": "starcoder:1b", "parameters": "1B", "size_bytes": 600000000000},
            {"name": "starcoder:3b", "parameters": "3B", "size_bytes": 1700000000000},
            {"name": "starcoder:7b", "parameters": "7B", "size_bytes": 4000000000000},
            {"name": "starcoder:15b", "parameters": "15B", "size_bytes": 9000000000000},
        ],
    },
    {
        "name": "wizardlm2",
        "description": "WizardLM 2 with improved instruction following and reasoning.",
        "capabilities": ["chat"],
        "suggested_ram": "6GB+",
        "parameter_variants": [
            {"name": "wizardlm2:7b", "parameters": "7B", "size_bytes": 4100000000000},
            {"name": "wizardlm2:8x22b", "parameters": "8x22B", "size_bytes": 52000000000000},
        ],
    },
    {
        "name": "wizardlm2-llama3",
        "description": "WizardLM 2 based on Llama 3 architecture.",
        "capabilities": ["chat"],
        "suggested_ram": "8GB+",
        "parameter_variants": [
            {"name": "wizardlm2-llama3:8b", "parameters": "8B", "size_bytes": 4700000000000},
        ],
    },
    {
        "name": "orca2",
        "description": "Microsoft's Orca 2 model with improved reasoning capabilities.",
        "capabilities": ["chat", "reasoning"],
        "suggested_ram": "8GB+",
        "parameter_variants": [
            {"name": "orca2:7b", "parameters": "7B", "size_bytes": 4100000000000},
            {"name": "orca2:13b", "parameters": "13B", "size_bytes": 7400000000000},
        ],
    },
    {
        "name": "neural-chat",
        "description": "Intel's Neural Chat model optimized for conversation.",
        "capabilities": ["chat"],
        "suggested_ram": "6GB+",
        "parameter_variants": [
            {"name": "neural-chat:7b", "parameters": "7B", "size_bytes": 4000000000000},
        ],
    },
    {
        "name": "samantha-mistral",
        "description": "A conversational model based on Mistral, designed for open dialogue.",
        "capabilities": ["chat"],
        "suggested_ram": "6GB+",
        "parameter_variants": [
            {"name": "samantha-mistral:7b", "parameters": "7B", "size_bytes": 4100000000000},
        ],
    },
    {
        "name": "dolphin-mistral",
        "description": "Dolphin model based on Mistral. Uncensored and good for coding.",
        "capabilities": ["chat", "code"],
        "suggested_ram": "6GB+",
        "parameter_variants": [
            {"name": "dolphin-mistral:7b", "parameters": "7B", "size_bytes": 4100000000000},
            {"name": "dolphin-mistral:7b-v2.5", "parameters": "7B", "size_bytes": 4100000000000},
        ],
    },
    {
        "name": "command-r",
        "description": "Cohere's Command R model for retrieval-augmented generation.",
        "capabilities": ["chat"],
        "suggested_ram": "8GB+",
        "parameter_variants": [
            {"name": "command-r:35b", "parameters": "35B", "size_bytes": 20000000000000},
        ],
    },
    {
        "name": "command-r-plus",
        "description": "Cohere's Command R+ model with enhanced capabilities.",
        "capabilities": ["chat"],
        "suggested_ram": "12GB+",
        "parameter_variants": [
            {"name": "command-r-plus:8b", "parameters": "8B", "size_bytes": 5000000000000},
            {"name": "command-r-plus:104b", "parameters": "104B", "size_bytes": 60000000000000},
        ],
    },
    {
        "name": "aya",
        "description": "Cohere's Aya model for multilingual conversation.",
        "capabilities": ["chat"],
        "suggested_ram": "6GB+",
        "parameter_variants": [
            {"name": "aya:8b", "parameters": "8B", "size_bytes": 4800000000000},
            {"name": "aya:32b", "parameters": "32B", "size_bytes": 19000000000000},
        ],
    },
    {
        "name": "gpt4",
        "description": "OpenAI GPT-4 model emulation via Ollama.",
        "capabilities": ["chat"],
        "suggested_ram": "8GB+",
        "parameter_variants": [
            {"name": "gpt4:8b", "parameters": "8B", "size_bytes": 4800000000000},
        ],
    },
    {
        "name": "bert",
        "description": "BERT model for embeddings and text classification.",
        "capabilities": ["embedding"],
        "suggested_ram": "2GB+",
        "parameter_variants": [
            {"name": "bert:base", "parameters": "110M", "size_bytes": 420000000000},
            {"name": "bert:large", "parameters": "340M", "size_bytes": 1300000000000},
        ],
    },
    {
        "name": "bge-large",
        "description": "BAAI's BGE large embedding model for semantic search.",
        "capabilities": ["embedding"],
        "suggested_ram": "2GB+",
        "parameter_variants": [
            {"name": "bge-large:1.5", "parameters": "340M", "size_bytes": 670000000000},
        ],
    },
    {
        "name": "bge-base",
        "description": "BAAI's BGE base embedding model.",
        "capabilities": ["embedding"],
        "suggested_ram": "2GB+",
        "parameter_variants": [
            {"name": "bge-base:1.5", "parameters": "110M", "size_bytes": 220000000000},
        ],
    },
    {
        "name": "allminilm",
        "description": "All MiniLM models for fast and efficient embeddings.",
        "capabilities": ["embedding"],
        "suggested_ram": "1GB+",
        "parameter_variants": [
            {"name": "allminilm:6b", "parameters": "22M", "size_bytes": 43000000000},
            {"name": "allminilm:12b", "parameters": "33M", "size_bytes": 130000000000},
        ],
    },
]


def _load_cache() -> dict[str, Any] | None:
    try:
        if not os.path.exists(CACHE_FILE):
            return None
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Failed to load cache: {e}")
        return None


def _save_cache(data: dict[str, Any]) -> None:
    try:
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.warning(f"Failed to save cache: {e}")


def _is_cache_valid(cache: dict[str, Any]) -> bool:
    if not cache or "fetched_at" not in cache:
        return False
    try:
        fetched_at = datetime.fromisoformat(cache["fetched_at"])
        age = datetime.now(timezone.utc) - fetched_at
        return age < timedelta(hours=CACHE_TTL_HOURS)
    except Exception:
        return False


def _extract_model_name(url: str) -> str | None:
    match = re.search(r"/library/([^/]+)", url)
    return match.group(1) if match else None


def _parse_page_models(html: str) -> list[dict[str, Any]]:
    models = []
    card_pattern = re.compile(
        r'<a href="/library/([^"]+)"[^>]*>.*?<h2[^>]*>([^<]+)</h2>.*?<p>([^<]+)</p>',
        re.DOTALL,
    )
    for match in card_pattern.finditer(html):
        name = match.group(1).strip()
        title = match.group(2).strip()
        description = match.group(3).strip()
        if name and description:
            description = re.sub(r"<[^>]+>", "", description).strip()
            capabilities = _infer_capabilities(name)
            suggested_ram = _estimate_ram(name, capabilities)
            models.append(
                {
                    "name": name,
                    "display_name": title,
                    "description": description,
                    "capabilities": capabilities,
                    "suggested_ram": suggested_ram,
                    "parameter_variants": _extract_parameter_variants(name),
                }
            )
    return models


def _infer_capabilities(model_name: str) -> list[str]:
    name_lower = model_name.lower()
    caps = ["chat"]
    if any(x in name_lower for x in ["code", "coder", "starcoder", "deepseek", "codellama"]):
        caps.append("code")
    if any(x in name_lower for x in ["vision", "llava", "bakllava", "vision"]):
        caps.append("vision")
    if any(x in name_lower for x in ["embed", "nomic", "bge", "mxbai", "bert", "allminilm"]):
        caps.append("embedding")
    if any(x in name_lower for x in ["reason", "phi", "orca", "qwen"]):
        caps.append("reasoning")
    return list(set(caps))


def _estimate_ram(model_name: str, capabilities: list[str]) -> str:
    name_lower = model_name.lower()
    if "embedding" in capabilities:
        return "1-2GB"
    if any(x in name_lower for x in ["phi", ":0.5b", ":1b", ":2b", ":2.7b", ":3b"]):
        return "2-4GB"
    if any(x in name_lower for x in [":3b", ":4b", ":7b", ":8b"]):
        return "6-8GB"
    if any(x in name_lower for x in [":14b", ":13b", ":12b"]):
        return "12-16GB"
    if any(x in name_lower for x in [":34b", ":32b", ":30b"]):
        return "24-32GB"
    if any(x in name_lower for x in [":70b", ":72b", ":65b"]):
        return "48-64GB"
    if any(x in name_lower for x in [":405b", ":236b", ":180b"]):
        return "128GB+"
    return "6-8GB"


def _extract_parameter_variants(name: str) -> list[dict[str, Any]]:
    variants = []
    base_name = name
    size_match = re.search(r":(\d+(\.\d+)?b)", name.lower())
    if size_match:
        base_name = name[: size_match.start()]
    pattern = re.compile(r"(\d+(\.\d+)?b)", re.IGNORECASE)
    if pattern.search(name):
        for match in pattern.finditer(name):
            variant_name = f"{base_name}:{match.group(1)}"
            size_bytes = _estimate_model_size(match.group(1))
            variants.append(
                {
                    "name": variant_name,
                    "parameters": match.group(1).upper(),
                    "size_bytes": size_bytes,
                }
            )
    if not variants:
        variants.append(
            {
                "name": name,
                "parameters": "Unknown",
                "size_bytes": 0,
            }
        )
    return variants


def _estimate_model_size(size_str: str) -> int:
    try:
        size_str = size_str.lower().rstrip("b")
        if "x" in size_str:
            parts = size_str.split("x")
            num = float(parts[0]) * float(parts[1])
        else:
            num = float(size_str)
        if num >= 100:
            return int(num * 1000000000)
        else:
            return int(num * 1000000000000)
    except Exception:
        return 0


async def _fetch_page(page: int = 1) -> str | None:
    url = f"{BASE_URL}?page={page}" if page > 1 else BASE_URL
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()
            return resp.text
    except Exception as e:
        logger.error(f"Failed to fetch page {page}: {e}")
        return None


def _has_next_page(html: str) -> bool:
    next_pattern = re.compile(r'<a[^>]+href="/library\?page=\d+"[^>]*>\s*Next', re.IGNORECASE)
    return bool(next_pattern.search(html)) or '"next"' in html.lower()


async def _scrape_all_pages() -> list[dict[str, Any]]:
    all_models = []
    page = 1
    max_pages = 50
    while page <= max_pages:
        html = await _fetch_page(page)
        if not html:
            break
        models = _parse_page_models(html)
        if not models:
            break
        all_models.extend(models)
        if not _has_next_page(html):
            break
        page += 1
    seen = set()
    unique_models = []
    for model in all_models:
        if model["name"] not in seen:
            seen.add(model["name"])
            unique_models.append(model)
    return unique_models


def get_ollama_library_models(force_refresh: bool = False) -> list[dict[str, Any]]:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(get_ollama_library_models_async(force_refresh))
        finally:
            loop.close()
    else:
        raise RuntimeError("get_ollama_library_models() cannot be called from an async context. Use get_ollama_library_models_async() instead.")


async def get_ollama_library_models_async(force_refresh: bool = False) -> list[dict[str, Any]]:
    cache = _load_cache()
    if cache and not force_refresh and _is_cache_valid(cache):
        return cache.get("models", [])
    try:
        models = await _scrape_all_pages()
        if models:
            data = {"fetched_at": datetime.now(timezone.utc).isoformat(), "models": models}
            _save_cache(data)
            return models
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
    if cache and "models" in cache:
        logger.info("Returning stale cache due to scraping failure")
        return cache["models"]
    logger.info("Using hardcoded fallback model list")
    data = {"fetched_at": datetime.now(timezone.utc).isoformat(), "models": HARDCODED_MODELS}
    _save_cache(data)
    return HARDCODED_MODELS


if __name__ == "__main__":
    import asyncio

    logging.basicConfig(level=logging.INFO)
    models = asyncio.run(get_ollama_library_models_async())
    print(f"Found {len(models)} models")
    for model in models[:5]:
        print(f"  - {model['name']}: {model['description'][:50]}...")