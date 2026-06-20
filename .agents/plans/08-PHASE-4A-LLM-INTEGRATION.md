# Phase 4A: LLM Integration & Local Models

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give Cortex a brain. Integrate local LLM inference via llama.cpp and Ollama, build a model management system with download/pause/resume, hardware-aware recommendations, and wire LLM into agents, search, and chat.

**Architecture:** Backend LLM provider abstraction with llama.cpp (primary, local CPU/GPU) and Ollama (optional, model management) backends. Model catalog stored as a JSON file plus Ollama API for available models — no extra database table needed. Frontend model browser with real-time download progress.

**Tech Stack:** Python 3.12+, llama-cpp-python, httpx (Ollama API), SQLAlchemy 2.0, Next.js 15, React 19, Tailwind CSS

---

## Why This Phase First

Without an LLM, Cortex is a sophisticated filing cabinet. Every subsequent phase — conversation memory, agent intelligence, learning loop — requires a brain. This phase is the single biggest unlock.

**What changes after this phase:**
- Agents can reason, plan, and execute with real intelligence
- Search returns AI-synthesized answers, not concatenated titles
- Chat conversations are possible
- Code can be explained, summarized, and generated
- Context builder can generate insights
- Memory entries can be enriched with LLM-generated summaries

---

## Task 1: LLM Provider Abstraction

**Files:**
- Modify: `backend/app/services/llm/provider.py` (keep ABC unchanged, add dataclasses below it)
- Create: `backend/app/services/llm/llama_cpp.py`
- Create: `backend/app/services/llm/ollama.py`
- Create: `backend/app/services/llm/manager.py`
- Modify: `backend/app/core/config.py`

**Interfaces:**
- Consumes: `LLMProvider` ABC (existing — `chat(messages, tools, config) -> tuple[str, list[dict] | None]`)
- Produces: `LLMManager` — singleton that wraps providers with new dataclasses

- [ ] **Step 0: Ensure `__init__.py` exists**

The file `backend/app/services/llm/__init__.py` must exist. If it doesn't, create it:

```python
# backend/app/services/llm/__init__.py
"""LLM provider interfaces."""
```

- [ ] **Step 1: Add dataclasses to provider.py (DO NOT rewrite the ABC)**

The existing `LLMProvider` ABC at `backend/app/services/llm/provider.py` has this interface and must NOT be changed:

```python
class LLMProvider(ABC):
    @abstractmethod
    async def chat(
        self, messages: list[dict], tools: list[dict], config: Any
    ) -> tuple[str, list[dict] | None]:
        ...

    @abstractmethod
    def list_models(self) -> list[dict[str, Any]]:
        ...
```

Append new dataclasses and a helper after the existing class in the same file:

```python
# backend/app/services/llm/provider.py  (append below existing LLMProvider ABC)
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from abc import ABC, abstractmethod

# ── EXISTING ABC (DO NOT MODIFY) ────────────────────────────────
class LLMProvider(ABC):
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


# ── NEW DATACLASSES (added for manager layer) ──────────────────
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
    capabilities: list[str] = field(default_factory=list)  # ["chat", "code", "reasoning", "vision", "embedding"]
    description: str = ""
```

- [ ] **Step 2: Implement llama.cpp provider**

```python
# backend/app/services/llm/llama_cpp.py
from __future__ import annotations
import asyncio
import logging
from typing import Any

from backend.app.services.llm.provider import LLMProvider, LLMModelInfo

logger = logging.getLogger(__name__)


class LlamaCppProvider(LLMProvider):
    def __init__(self, model_path: str, n_ctx: int = 4096, n_gpu_layers: int = 0):
        self._model_path = model_path
        self._n_ctx = n_ctx
        self._n_gpu_layers = n_gpu_layers
        self._llama = None
        self._model_lock = asyncio.Lock()
        self._semaphore = asyncio.Semaphore(4)

    async def _ensure_model(self) -> None:
        """Load model if not already loaded. Thread-safe via lock."""
        if self._llama is not None:
            return
        async with self._model_lock:
            # Double-check after acquiring lock
            if self._llama is not None:
                return
            try:
                from llama_cpp import Llama
            except ImportError:
                raise RuntimeError(
                    "llama-cpp-python not installed. Run: pip install llama-cpp-python"
                )
            loop = asyncio.get_running_loop()
            self._llama = await loop.run_in_executor(
                None,
                lambda: Llama(
                    model_path=self._model_path,
                    n_ctx=self._n_ctx,
                    n_gpu_layers=self._n_gpu_layers,
                    verbose=False,
                ),
            )

    async def chat(
        self, messages: list[dict], tools: list[dict], config: Any
    ) -> tuple[str, list[dict] | None]:
        await self._ensure_model()
        async with self._semaphore:
            loop = asyncio.get_running_loop()
            # Convert dict messages to llama.cpp format
            formatted = [{"role": m["role"], "content": m["content"]} for m in messages]
            max_tokens = 2048
            temperature = 0.7
            if isinstance(config, dict):
                max_tokens = config.get("max_tokens", 2048)
                temperature = config.get("temperature", 0.7)

            result = await loop.run_in_executor(
                None,
                lambda: self._llama.create_chat_completion(
                    messages=formatted,
                    max_tokens=max_tokens,
                    temperature=temperature,
                ),
            )

            choice = result["choices"][0]
            content = choice["message"]["content"]
            # Detect tool calls in response (if any)
            tool_calls = None
            if choice["message"].get("tool_calls"):
                tool_calls = choice["message"]["tool_calls"]
            return content, tool_calls

    async def chat_direct(
        self,
        messages: list,
        model: str | None = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> Any:
        """High-level chat returning LLMResponse-like dict (used by manager)."""
        await self._ensure_model()
        async with self._semaphore:
            loop = asyncio.get_running_loop()
            formatted = [{"role": m.role, "content": m.content} for m in messages]
            result = await loop.run_in_executor(
                None,
                lambda: self._llama.create_chat_completion(
                    messages=formatted,
                    max_tokens=max_tokens,
                    temperature=temperature,
                ),
            )
            choice = result["choices"][0]
            usage = result.get("usage", {})
            return {
                "content": choice["message"]["content"],
                "model": result.get("model", self._model_path),
                "tokens_prompt": usage.get("prompt_tokens", 0),
                "tokens_completion": usage.get("completion_tokens", 0),
                "finish_reason": choice.get("finish_reason", "stop"),
            }

    async def chat_stream(self, messages: list, tools: list, config: Any):
        """Stream chat response token by token."""
        await self._ensure_model()
        async with self._semaphore:
            loop = asyncio.get_running_loop()
            formatted = [{"role": m["role"], "content": m["content"]} for m in messages]
            max_tokens = 2048
            temperature = 0.7
            if isinstance(config, dict):
                max_tokens = config.get("max_tokens", 2048)
                temperature = config.get("temperature", 0.7)

            stream = await loop.run_in_executor(
                None,
                lambda: self._llama.create_chat_completion(
                    messages=formatted,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    stream=True,
                ),
            )
            for chunk in stream:
                delta = chunk["choices"][0].get("delta", {})
                if "content" in delta:
                    yield delta["content"]

    def list_models(self) -> list[dict[str, Any]]:
        import os
        if not os.path.exists(self._model_path):
            return []
        return [{
            "name": os.path.basename(self._model_path),
            "size_bytes": os.path.getsize(self._model_path),
            "quantization": self._detect_quantization(),
            "context_length": self._n_ctx,
            "capabilities": ["chat", "code"],
            "description": f"Local GGUF model at {self._model_path}",
        }]

    def provider_name(self) -> str:
        return "llama.cpp"

    def _detect_quantization(self) -> str | None:
        name = self._model_path.lower()
        for q in ["q4_k_m", "q5_k_m", "q8_0", "q4_k_s", "q5_k_s", "q6_k", "f16", "f32"]:
            if q in name:
                return q.upper()
        return None
```

- [ ] **Step 3: Implement Ollama provider**

```python
# backend/app/services/llm/ollama.py
from __future__ import annotations
import logging
from typing import Any

import httpx

from backend.app.services.llm.provider import LLMProvider, LLMModelInfo

logger = logging.getLogger(__name__)


class OllamaProvider(LLMProvider):
    def __init__(self, base_url: str = "http://localhost:11434"):
        self._base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(base_url=self._base_url, timeout=120.0)

    async def chat(
        self, messages: list[dict], tools: list[dict], config: Any
    ) -> tuple[str, list[dict] | None]:
        model = "llama3.2"
        if isinstance(config, dict) and "model" in config:
            model = config["model"]
        elif tools:
            # Try to pick first available model
            models = self.list_models()
            if models:
                model = models[0]["name"]

        formatted = [{"role": m["role"], "content": m["content"]} for m in messages]
        resp = await self._client.post(
            "/api/chat",
            json={
                "model": model,
                "messages": formatted,
                "stream": False,
                "options": {
                    "num_predict": (config or {}).get("max_tokens", 2048),
                    "temperature": (config or {}).get("temperature", 0.7),
                },
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data["message"]["content"], None

    async def chat_direct(
        self,
        messages: list,
        model: str | None = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> dict:
        """High-level chat returning dict (used by manager)."""
        model = model or await self._default_model()
        formatted = [{"role": m.role, "content": m.content} for m in messages]
        resp = await self._client.post(
            "/api/chat",
            json={
                "model": model,
                "messages": formatted,
                "stream": False,
                "options": {"num_predict": max_tokens, "temperature": temperature},
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return {
            "content": data["message"]["content"],
            "model": model,
            "tokens_prompt": data.get("prompt_eval_count", 0),
            "tokens_completion": data.get("eval_count", 0),
            "finish_reason": "stop",
        }

    async def chat_stream(self, messages: list, tools: list, config: Any):
        model = "llama3.2"
        if isinstance(config, dict) and "model" in config:
            model = config["model"]
        formatted = [{"role": m["role"], "content": m["content"]} for m in messages]
        async with self._client.stream(
            "POST",
            "/api/chat",
            json={
                "model": model,
                "messages": formatted,
                "stream": True,
                "options": {
                    "num_predict": (config or {}).get("max_tokens", 2048),
                    "temperature": (config or {}).get("temperature", 0.7),
                },
            },
        ) as resp:
            resp.raise_for_status()
            import json
            async for line in resp.aiter_lines():
                if line:
                    chunk = json.loads(line)
                    if "message" in chunk and "content" in chunk["message"]:
                        yield chunk["message"]["content"]

    def list_models(self) -> list[dict[str, Any]]:
        """List models — synchronous (Ollama is local, fast enough)."""
        try:
            import httpx as sync_httpx
            resp = sync_httpx.get(f"{self._base_url}/api/tags", timeout=5.0)
            resp.raise_for_status()
            data = resp.json()
            models = []
            for m in data.get("models", []):
                models.append({
                    "name": m["name"],
                    "size_bytes": m.get("size", 0),
                    "quantization": None,
                    "context_length": 4096,
                    "capabilities": self._infer_capabilities(m["name"]),
                    "description": f"Ollama model: {m['name']}",
                })
            return models
        except Exception:
            return []

    async def list_models_async(self) -> list[LLMModelInfo]:
        """Async variant for the manager layer."""
        try:
            resp = await self._client.get("/api/tags")
            resp.raise_for_status()
            data = resp.json()
            models = []
            for m in data.get("models", []):
                models.append(LLMModelInfo(
                    name=m["name"],
                    size_bytes=m.get("size", 0),
                    quantization=None,
                    context_length=4096,
                    capabilities=self._infer_capabilities(m["name"]),
                    description=f"Ollama model: {m['name']}",
                ))
            return models
        except Exception:
            return []

    async def is_available(self) -> bool:
        try:
            resp = await self._client.get("/api/tags")
            return resp.status_code == 200
        except Exception:
            return False

    def provider_name(self) -> str:
        return "ollama"

    async def _default_model(self) -> str:
        models = self.list_models()
        return models[0]["name"] if models else "llama3.2"

    def _infer_capabilities(self, name: str) -> list[str]:
        name_lower = name.lower()
        caps = ["chat"]
        if any(x in name_lower for x in ["code", "coder", "starcoder", "deepseek"]):
            caps.append("code")
        if any(x in name_lower for x in ["vision", "llava", "bakllava"]):
            caps.append("vision")
        if any(x in name_lower for x in ["embed", "nomic", "bge"]):
            caps.append("embedding")
        if any(x in name_lower for x in ["reason", "phi", "qwen"]):
            caps.append("reasoning")
        return caps
```

- [ ] **Step 4: Implement LLMManager**

```python
# backend/app/services/llm/manager.py
from __future__ import annotations
import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Any

from backend.app.core.config import settings
from backend.app.services.llm.provider import LLMProvider, LLMMessage, LLMResponse, LLMModelInfo
from backend.app.services.llm.llama_cpp import LlamaCppProvider
from backend.app.services.llm.ollama import OllamaProvider

logger = logging.getLogger(__name__)

# Model catalog — JSON file, not a database table
MODEL_CATALOG_PATH = Path(
    getattr(settings, "CORTEX_ROOT", None) or "./CortexMemory"
) / "llm_catalog.json"

MODEL_CATALOG = [
    {
        "name": "llama-3.2-3b-instruct",
        "display_name": "Llama 3.2 3B Instruct",
        "provider": "ollama",
        "model_type": "chat",
        "parameter_count": "3B",
        "context_length": 128000,
        "capabilities": ["chat", "code", "reasoning"],
        "description": "Fast, lightweight model ideal for chat and quick coding tasks.",
        "hardware_requirements": {"min_ram_gb": 4, "recommended_ram_gb": 8},
        "recommended": True,
    },
    {
        "name": "llama-3.1-8b-instruct",
        "display_name": "Llama 3.1 8B Instruct",
        "provider": "ollama",
        "model_type": "chat",
        "parameter_count": "8B",
        "context_length": 128000,
        "capabilities": ["chat", "code", "reasoning"],
        "description": "Balanced model for general use with good coding ability.",
        "hardware_requirements": {"min_ram_gb": 8, "recommended_ram_gb": 16},
        "recommended": True,
    },
    {
        "name": "deepseek-coder-v2-lite",
        "display_name": "DeepSeek Coder V2 Lite",
        "provider": "ollama",
        "model_type": "code",
        "parameter_count": "16B",
        "context_length": 128000,
        "capabilities": ["code", "reasoning"],
        "description": "Specialized coding model. Excellent at code generation across 338 languages.",
        "hardware_requirements": {"min_ram_gb": 16, "recommended_ram_gb": 32},
        "recommended": True,
    },
    {
        "name": "qwen2.5-coder-7b",
        "display_name": "Qwen 2.5 Coder 7B",
        "provider": "ollama",
        "model_type": "code",
        "parameter_count": "7B",
        "context_length": 32768,
        "capabilities": ["code", "reasoning"],
        "description": "Strong coding model with multilingual support.",
        "hardware_requirements": {"min_ram_gb": 8, "recommended_ram_gb": 16},
    },
    {
        "name": "llava:latest",
        "display_name": "LLaVA (Vision)",
        "provider": "ollama",
        "model_type": "vision",
        "parameter_count": "7B",
        "context_length": 4096,
        "capabilities": ["chat", "vision"],
        "description": "Vision-language model for understanding images and screenshots.",
        "hardware_requirements": {"min_ram_gb": 8, "recommended_ram_gb": 16},
    },
    {
        "name": "nomic-embed-text",
        "display_name": "Nomic Embed Text",
        "provider": "ollama",
        "model_type": "embedding",
        "parameter_count": "137M",
        "context_length": 8192,
        "capabilities": ["embedding"],
        "description": "High-quality text embeddings for semantic search.",
        "hardware_requirements": {"min_ram_gb": 2, "recommended_ram_gb": 4},
        "recommended": True,
    },
    {
        "name": "phi-3.5-mini",
        "display_name": "Phi 3.5 Mini",
        "provider": "ollama",
        "model_type": "chat",
        "parameter_count": "3.8B",
        "context_length": 128000,
        "capabilities": ["chat", "reasoning"],
        "description": "Microsoft's efficient reasoning model. Capable for its size.",
        "hardware_requirements": {"min_ram_gb": 4, "recommended_ram_gb": 8},
    },
]


class LLMManager:
    """Singleton that routes to the best available LLM provider."""

    def __init__(self):
        self._providers: list[LLMProvider] = []
        self._active: LLMProvider | None = None
        self._semaphore = asyncio.Semaphore(4)

        # Token tracking metrics
        self._total_prompt_tokens: int = 0
        self._total_completion_tokens: int = 0
        self._total_requests: int = 0
        self._total_errors: int = 0

    def configure(
        self,
        llama_model_path: str | None = None,
        ollama_url: str | None = None,
        n_ctx: int = 4096,
        n_gpu_layers: int = 0,
    ):
        """Configure available providers. Called once at startup."""
        self._providers = []

        if ollama_url:
            self._providers.append(OllamaProvider(base_url=ollama_url))

        if llama_model_path:
            self._providers.append(LlamaCppProvider(
                model_path=llama_model_path,
                n_ctx=n_ctx,
                n_gpu_layers=n_gpu_layers,
            ))

    async def _get_active(self) -> LLMProvider:
        if self._active and await self._check_available(self._active):
            return self._active
        for p in self._providers:
            if await self._check_available(p):
                self._active = p
                logger.info("Active LLM provider: %s", p.provider_name())
                return p
        raise RuntimeError("No LLM provider available. Install llama-cpp-python or start Ollama.")

    async def _check_available(self, provider: LLMProvider) -> bool:
        """Check provider availability without blocking the event loop."""
        try:
            if isinstance(provider, OllamaProvider):
                return await provider.is_available()
            elif isinstance(provider, LlamaCppProvider):
                import os
                return os.path.exists(provider._model_path)
        except Exception:
            return False
        return False

    async def chat(
        self,
        messages: list[LLMMessage],
        model: str | None = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """Send chat messages and return response with token tracking."""
        provider = await self._get_active()
        try:
            result = await provider.chat_direct(
                messages=messages,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            self._total_requests += 1
            self._total_prompt_tokens += result.get("tokens_prompt", 0)
            self._total_completion_tokens += result.get("tokens_completion", 0)
            return LLMResponse(
                content=result["content"],
                model=result.get("model", "unknown"),
                tokens_prompt=result.get("tokens_prompt", 0),
                tokens_completion=result.get("tokens_completion", 0),
                finish_reason=result.get("finish_reason", "stop"),
            )
        except Exception as e:
            self._total_errors += 1
            raise RuntimeError(f"LLM chat failed: {e}") from e

    async def chat_stream(self, messages: list[LLMMessage], model: str | None = None, max_tokens: int = 2048, temperature: float = 0.7):
        provider = await self._get_active()
        async for token in provider.chat_stream(
            [{"role": m.role, "content": m.content} for m in messages],
            tools=[],
            config={"model": model, "max_tokens": max_tokens, "temperature": temperature},
        ):
            yield token

    async def list_all_models(self) -> list[LLMModelInfo]:
        all_models: list[LLMModelInfo] = []
        for p in self._providers:
            if await self._check_available(p):
                if hasattr(p, "list_models_async"):
                    all_models.extend(await p.list_models_async())
                else:
                    # Sync fallback for providers that only implement the ABC
                    for m in p.list_models():
                        all_models.append(LLMModelInfo(
                            name=m.get("name", "unknown"),
                            size_bytes=m.get("size_bytes", 0),
                            context_length=m.get("context_length", 4096),
                            capabilities=m.get("capabilities", []),
                            description=m.get("description", ""),
                        ))
        return all_models

    async def health_check(self) -> dict:
        """Check health of all configured providers."""
        status = {}
        for p in self._providers:
            try:
                available = await self._check_available(p)
                status[p.provider_name()] = {
                    "available": available,
                    "is_active": p is self._active,
                }
            except Exception as e:
                status[p.provider_name()] = {
                    "available": False,
                    "is_active": False,
                    "error": str(e),
                }
        return status

    def get_metrics(self) -> dict:
        """Return token usage and request metrics."""
        return {
            "total_requests": self._total_requests,
            "total_errors": self._total_errors,
            "total_prompt_tokens": self._total_prompt_tokens,
            "total_completion_tokens": self._total_completion_tokens,
            "active_provider": self._active.provider_name() if self._active else None,
        }


# Singleton
llm_manager = LLMManager()
```

- [ ] **Step 5: Add LLM config to Settings**

```python
# Add to backend/app/core/config.py Settings class (after EXISTING fields, before model_config):
    # LLM Settings
    LLM_PROVIDER: str = "auto"  # "auto", "llama_cpp", "ollama", "none"
    LLM_MODEL_PATH: str = ""  # Path to GGUF model file
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    LLM_CONTEXT_SIZE: int = 4096
    LLM_GPU_LAYERS: int = 0
```

- [ ] **Step 6: Add dependencies to pyproject.toml**

`psutil` is already in `pyproject.toml`. Add `llama-cpp-python` as an optional dependency:

```toml
# Add to [project.optional-dependencies] in pyproject.toml:
[project.optional-dependencies]
embeddings = ["onnxruntime>=1.18.0"]
llm = ["llama-cpp-python>=0.3.0"]
```

Install with: `uv pip install -e ".[llm]"`

- [ ] **Step 7: Initialize LLM in app lifespan**

```python
# In backend/app/main.py lifespan, add BEFORE the yield:
    # Initialize LLM manager
    from backend.app.services.llm.manager import llm_manager
    llm_manager.configure(
        llama_model_path=settings.LLM_MODEL_PATH or None,
        ollama_url=settings.OLLAMA_BASE_URL if settings.LLM_PROVIDER in ("auto", "ollama") else None,
        n_ctx=settings.LLM_CONTEXT_SIZE,
        n_gpu_layers=settings.LLM_GPU_LAYERS,
    )
    llm_status = await llm_manager.health_check()
    logger.info("LLM providers: %s", llm_status)
```

- [ ] **Step 8: Run backend compile check**

```bash
cd /home/adi/Desktop/Cortex-Workspace && uv run python -m py_compile backend/app/services/llm/provider.py && uv run python -m py_compile backend/app/services/llm/llama_cpp.py && uv run python -m py_compile backend/app/services/llm/ollama.py && uv run python -m py_compile backend/app/services/llm/manager.py && uv run python -m py_compile backend/app/main.py && echo "PASS"
```

- [ ] **Step 9: Commit**

```bash
git add backend/app/services/llm/ backend/app/core/config.py backend/app/main.py
git commit -m "feat: LLM provider abstraction with llama.cpp, Ollama, token metrics, and health checks"
```

---

## Task 2: Model Catalog & API

**Files:**
- Create: `backend/app/api/v1/models.py`
- Modify: `backend/app/api/router.py`

**Interfaces:**
- Consumes: `LLMManager` (Task 1)
- Produces: Model list, recommended models, hardware detection, health endpoints

- [ ] **Step 1: Create model API endpoints**

```python
# backend/app/api/v1/models.py
from __future__ import annotations
import logging

import psutil
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.db import get_current_user, get_db
from backend.app.models.user import User
from backend.app.services.llm.manager import llm_manager, MODEL_CATALOG

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/models")
async def list_models(
    model_type: str | None = None,
    downloaded_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List models from catalog and available providers."""
    # Merge catalog with provider-detected models
    available_models = await llm_manager.list_all_models()
    available_names = {m.name for m in available_models}

    catalog = list(MODEL_CATALOG)
    if model_type:
        catalog = [m for m in catalog if m.get("model_type") == model_type]

    # Enrich catalog entries with provider status
    for entry in catalog:
        entry["downloaded"] = entry["name"] in available_names

    return {
        "models": catalog,
        "available_from_providers": [
            {
                "name": m.name,
                "size_bytes": m.size_bytes,
                "context_length": m.context_length,
                "capabilities": m.capabilities,
            }
            for m in available_models
        ],
    }


@router.get("/models/recommended")
async def recommended_models(
    current_user: User = Depends(get_current_user),
):
    """Return hardware-appropriate model recommendations."""
    hardware = _detect_hardware()
    recommended = [
        m for m in MODEL_CATALOG
        if m.get("recommended")
        and hardware["ram_gb"] >= m.get("hardware_requirements", {}).get("min_ram_gb", 0)
    ]
    return {
        "hardware": hardware,
        "recommended": recommended,
    }


@router.get("/models/hardware")
async def detect_hardware(
    current_user: User = Depends(get_current_user),
):
    """Detect system hardware for model recommendations."""
    return _detect_hardware()


@router.get("/models/health")
async def llm_health(
    current_user: User = Depends(get_current_user),
):
    """Check health of all LLM providers."""
    return await llm_manager.health_check()


@router.get("/models/metrics")
async def llm_metrics(
    current_user: User = Depends(get_current_user),
):
    """Return token usage and request metrics."""
    return llm_manager.get_metrics()


def _detect_hardware() -> dict:
    """Detect system hardware (sync — called from sync endpoint)."""
    ram_gb = psutil.virtual_memory().total / (1024**3)
    cpu_count = psutil.cpu_count() or 1

    gpu_info: dict = {"available": False, "name": None, "vram_gb": 0}
    try:
        import subprocess

        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            parts = result.stdout.strip().split(", ")
            gpu_info = {
                "available": True,
                "name": parts[0],
                "vram_gb": float(parts[1]) / 1024,
            }
    except Exception:
        pass

    return {
        "ram_gb": round(ram_gb, 1),
        "cpu_count": cpu_count,
        "gpu": gpu_info,
    }
```

- [ ] **Step 2: Register router**

```python
# In backend/app/api/router.py, add import and include:
from backend.app.api.v1.models import router as models_router
# ... (after existing includes)
api_router.include_router(models_router, tags=["Models"])
```

- [ ] **Step 3: Compile check**

```bash
cd /home/adi/Desktop/Cortex-Workspace && uv run python -m py_compile backend/app/api/v1/models.py && uv run python -m py_compile backend/app/api/router.py && echo "PASS"
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/api/v1/models.py backend/app/api/router.py
git commit -m "feat: model catalog API with hardware detection, recommendations, and LLM health/metrics endpoints"
```

---

## Task 3: Model Download Service

**Files:**
- Create: `backend/app/services/model_downloader.py`
- Modify: `backend/app/api/v1/models.py` (add download endpoints)

**Interfaces:**
- Consumes: `LLMManager` (Task 1), model catalog
- Produces: Background download with progress tracking via Ollama pull

- [ ] **Step 1: Create model downloader**

```python
# backend/app/services/model_downloader.py
from __future__ import annotations
import asyncio
import logging
from pathlib import Path

from backend.app.core.config import settings

logger = logging.getLogger(__name__)

MODELS_DIR = Path(getattr(settings, "CORTEX_ROOT", None) or "./CortexMemory") / "models"


class ModelDownloader:
    def __init__(self):
        self._active_downloads: dict[str, asyncio.Task] = {}
        self._progress: dict[str, float] = {}

    async def download_model(self, model_name: str, catalog: list[dict]) -> dict:
        """Start downloading a model. Returns immediately."""
        if model_name in self._active_downloads:
            return {"status": "already_downloading", "model": model_name}

        # Check catalog
        model_entry = next((m for m in catalog if m["name"] == model_name), None)
        if not model_entry:
            raise ValueError(f"Model {model_name} not found in catalog")

        # Check if already available via providers
        from backend.app.services.llm.manager import llm_manager
        available = await llm_manager.list_all_models()
        if any(m.name == model_name for m in available):
            return {"status": "already_downloaded", "model": model_name}

        task = asyncio.create_task(self._do_download(model_name, model_entry))
        self._active_downloads[model_name] = task
        return {"status": "started", "model": model_name}

    async def _do_download(self, model_name: str, model_entry: dict):
        """Execute the download via Ollama pull."""
        try:
            self._progress[model_name] = 0.01

            if model_entry.get("provider") == "ollama":
                await self._pull_ollama(model_name)
            else:
                raise ValueError(f"No download method for {model_name} (provider: {model_entry.get('provider')})")

            self._progress[model_name] = 1.0
        except asyncio.CancelledError:
            logger.info("Download cancelled: %s", model_name)
            self._progress.pop(model_name, None)
        except Exception as e:
            logger.error("Download failed for %s: %s", model_name, e)
            self._progress[model_name] = 0.0
        finally:
            self._active_downloads.pop(model_name, None)

    async def _pull_ollama(self, model_name: str):
        """Pull model via Ollama API with progress tracking."""
        import httpx
        from backend.app.core.config import settings
        base_url = settings.OLLAMA_BASE_URL

        async with httpx.AsyncClient(base_url=base_url, timeout=3600.0) as client:
            async with client.stream("POST", "/api/pull", json={"name": model_name}) as resp:
                resp.raise_for_status()
                import json
                async for line in resp.aiter_lines():
                    if line:
                        data = json.loads(line)
                        status = data.get("status", "")
                        if "total" in data and "completed" in data:
                            total = data["total"]
                            completed = data["completed"]
                            if total > 0:
                                self._progress[model_name] = min(completed / total, 0.99)
                        elif status == "success":
                            self._progress[model_name] = 1.0

    def get_progress(self, model_name: str) -> float:
        """Get current download progress for a model."""
        return self._progress.get(model_name, 0.0)

    async def cancel_download(self, model_name: str) -> bool:
        """Cancel an active download."""
        task = self._active_downloads.get(model_name)
        if task and not task.done():
            task.cancel()
            self._active_downloads.pop(model_name, None)
            return True
        return False


model_downloader = ModelDownloader()
```

- [ ] **Step 2: Add download endpoints to models API**

Add these endpoints to `backend/app/api/v1/models.py`:

```python
# Add to backend/app/api/v1/models.py (append):
from backend.app.services.model_downloader import model_downloader

@router.post("/models/{model_name}/download")
async def download_model(
    model_name: str,
    current_user: User = Depends(get_current_user),
):
    """Start downloading a model."""
    try:
        result = await model_downloader.download_model(model_name, MODEL_CATALOG)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/models/{model_name}/progress")
async def download_progress(
    model_name: str,
    current_user: User = Depends(get_current_user),
):
    """Get download progress for a model."""
    progress = model_downloader.get_progress(model_name)
    return {"model": model_name, "progress": progress}


@router.post("/models/{model_name}/cancel")
async def cancel_download(
    model_name: str,
    current_user: User = Depends(get_current_user),
):
    """Cancel an active download."""
    cancelled = await model_downloader.cancel_download(model_name)
    return {"cancelled": cancelled}
```

- [ ] **Step 3: Compile check**

```bash
cd /home/adi/Desktop/Cortex-Workspace && uv run python -m py_compile backend/app/services/model_downloader.py && uv run python -m py_compile backend/app/api/v1/models.py && echo "PASS"
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/services/model_downloader.py backend/app/api/v1/models.py
git commit -m "feat: model download service with Ollama pull, progress tracking, and cancellation"
```

---

## Task 4: Frontend Model Manager UI

**Files:**
- Create: `frontend/app/models/page.tsx`
- Create: `frontend/src/shared/components/ModelCard.tsx`
- Create: `frontend/src/shared/api/models.ts`
- Modify: `frontend/src/shared/layout/DashboardShell.tsx` (add Models nav item)

**Interfaces:**
- Consumes: `/api/v1/models/*` endpoints (Task 2-3)
- Produces: Model browser, download manager, hardware recommendations

- [ ] **Step 1: Create models API client**

```typescript
// frontend/src/shared/api/models.ts
import { api } from "./client";

export interface LLMModel {
  name: string;
  display_name: string;
  provider: string;
  model_type: string;
  parameter_count: string | null;
  context_length: number;
  capabilities: string[];
  description: string | null;
  hardware_requirements: Record<string, unknown>;
  recommended?: boolean;
  downloaded?: boolean;
}

export interface HardwareInfo {
  ram_gb: number;
  cpu_count: number;
  gpu: { available: boolean; name: string | null; vram_gb: number };
}

export const modelsApi = {
  list: (params?: { model_type?: string; downloaded_only?: boolean }) => {
    const query = new URLSearchParams();
    if (params?.model_type) query.set("model_type", params.model_type);
    if (params?.downloaded_only) query.set("downloaded_only", "true");
    const qs = query.toString();
    return api.get<{ models: LLMModel[]; available_from_providers: unknown[] }>(
      `/api/v1/models${qs ? `?${qs}` : ""}`
    );
  },

  recommended: () =>
    api.get<{ hardware: HardwareInfo; recommended: LLMModel[] }>("/api/v1/models/recommended"),

  hardware: () => api.get<HardwareInfo>("/api/v1/models/hardware"),

  health: () => api.get<Record<string, unknown>>("/api/v1/models/health"),

  metrics: () => api.get<Record<string, unknown>>("/api/v1/models/metrics"),

  download: (modelName: string) =>
    api.post<{ status: string }>(`/api/v1/models/${modelName}/download`),

  progress: (modelName: string) =>
    api.get<{ model: string; progress: number }>(`/api/v1/models/${modelName}/progress`),

  cancel: (modelName: string) =>
    api.post<{ cancelled: boolean }>(`/api/v1/models/${modelName}/cancel`),
};
```

- [ ] **Step 2: Create ModelCard component**

```tsx
// frontend/src/shared/components/ModelCard.tsx
"use client";

import { motion } from "framer-motion";
import { Download, Cpu, Zap, Eye, MessageSquare, Code, X } from "lucide-react";
import Card from "@/shared/ui/Card";

interface ModelCardProps {
  model: {
    name: string;
    display_name: string;
    model_type: string;
    parameter_count: string | null;
    description: string | null;
    capabilities: string[];
    downloaded?: boolean;
    download_progress?: number;
    recommended?: boolean;
  };
  onDownload: (name: string) => void;
  onCancel: (name: string) => void;
}

const typeIcons: Record<string, React.ReactNode> = {
  chat: <MessageSquare size={16} />,
  code: <Code size={16} />,
  vision: <Eye size={16} />,
  embedding: <Zap size={16} />,
};

const typeColors: Record<string, string> = {
  chat: "text-accent",
  code: "text-success",
  vision: "text-warning",
  embedding: "text-purple-400",
};

export default function ModelCard({ model, onDownload, onCancel }: ModelCardProps) {
  const progress = model.download_progress ?? 0;
  const isDownloading = progress > 0 && progress < 1;

  return (
    <Card className="p-5" gradient>
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <div
            className={`w-8 h-8 rounded-lg bg-bg-hover flex items-center justify-center ${
              typeColors[model.model_type] || "text-text-muted"
            }`}
          >
            {typeIcons[model.model_type] || <Cpu size={16} />}
          </div>
          <div>
            <h3 className="text-sm font-semibold text-text">{model.display_name}</h3>
            <span className="micro-label">
              {model.parameter_count} · {model.model_type}
            </span>
          </div>
        </div>
        {model.recommended && (
          <span className="px-2 py-0.5 rounded-full bg-accent/10 text-accent text-xs font-medium">
            Recommended
          </span>
        )}
      </div>

      <p className="text-xs text-text-secondary mb-3 line-clamp-2">{model.description}</p>

      <div className="flex flex-wrap gap-1 mb-3">
        {model.capabilities.map((cap) => (
          <span key={cap} className="px-2 py-0.5 rounded-full bg-bg-hover text-text-muted text-xs">
            {cap}
          </span>
        ))}
      </div>

      {isDownloading ? (
        <div className="space-y-2">
          <div className="w-full h-1.5 bg-bg-hover rounded-full overflow-hidden">
            <motion.div
              className="h-full bg-accent rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${progress * 100}%` }}
              transition={{ duration: 0.3 }}
            />
          </div>
          <div className="flex justify-between items-center">
            <span className="text-xs text-text-muted">{Math.round(progress * 100)}%</span>
            <button
              onClick={() => onCancel(model.name)}
              className="text-xs text-text-muted hover:text-danger flex items-center gap-1"
            >
              <X size={12} /> Cancel
            </button>
          </div>
        </div>
      ) : model.downloaded ? (
        <span className="text-xs text-success flex items-center gap-1">
          <div className="w-1.5 h-1.5 rounded-full bg-success" /> Available
        </span>
      ) : (
        <button
          onClick={() => onDownload(model.name)}
          className="w-full py-2 rounded-lg bg-accent/10 text-accent text-sm font-medium hover:bg-accent/20 transition-colors flex items-center justify-center gap-2"
        >
          <Download size={14} /> Download
        </button>
      )}
    </Card>
  );
}
```

- [ ] **Step 3: Create Models page**

```tsx
// frontend/app/models/page.tsx
"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Cpu, Download, HardDrive } from "lucide-react";
import DashboardShell from "@/shared/layout/DashboardShell";
import Card from "@/shared/ui/Card";
import { useAuth } from "@/shared/auth/AuthProvider";
import { modelsApi, type LLMModel, type HardwareInfo } from "@/shared/api/models";
import ModelCard from "@/shared/components/ModelCard";
import { toast } from "sonner";

type FilterType = "all" | "chat" | "code" | "vision" | "embedding";

export default function ModelsPage() {
  const router = useRouter();
  const { user, loading } = useAuth();
  const [models, setModels] = useState<LLMModel[]>([]);
  const [hardware, setHardware] = useState<HardwareInfo | null>(null);
  const [filter, setFilter] = useState<FilterType>("all");
  const [loadingModels, setLoadingModels] = useState(true);

  useEffect(() => {
    if (!loading && !user) router.replace("/auth");
  }, [user, loading, router]);

  const fetchModels = async () => {
    try {
      const [modelsRes, hwRes] = await Promise.all([
        modelsApi.list(filter !== "all" ? { model_type: filter } : undefined),
        modelsApi.hardware(),
      ]);
      setModels(modelsRes.models);
      setHardware(hwRes);
    } catch {
      // silently handle
    }
    setLoadingModels(false);
  };

  useEffect(() => {
    if (user) fetchModels();
  }, [user, filter]);

  // Poll download progress
  useEffect(() => {
    if (!user) return;
    const hasDownloading = models.some((m) => {
      const p = m.download_progress ?? 0;
      return p > 0 && p < 1;
    });
    if (!hasDownloading) return;
    const interval = setInterval(fetchModels, 2000);
    return () => clearInterval(interval);
  }, [user, models]);

  const handleDownload = async (name: string) => {
    try {
      await modelsApi.download(name);
      toast.success("Download started");
      fetchModels();
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Download failed";
      toast.error(msg);
    }
  };

  const handleCancel = async (name: string) => {
    await modelsApi.cancel(name);
    fetchModels();
  };

  if (loading || !user) return null;

  const filters: { id: FilterType; label: string }[] = [
    { id: "all", label: "All Models" },
    { id: "chat", label: "Chat" },
    { id: "code", label: "Code" },
    { id: "vision", label: "Vision" },
    { id: "embedding", label: "Embeddings" },
  ];

  return (
    <DashboardShell>
      <div className="relative z-10 max-w-6xl mx-auto px-4 sm:px-6 py-8">
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
          <h1 className="text-2xl font-semibold text-text mb-2">Local Models</h1>
          <p className="text-text-secondary text-sm">
            Discover, download, and manage AI models for local inference.
          </p>
        </motion.div>

        {/* Hardware Info */}
        {hardware && (
          <Card className="p-4 mb-6" gradient>
            <div className="flex items-center gap-6 flex-wrap">
              <div className="flex items-center gap-2">
                <HardDrive size={16} className="text-accent" />
                <span className="text-sm text-text">{hardware.ram_gb} GB RAM</span>
              </div>
              <div className="flex items-center gap-2">
                <Cpu size={16} className="text-accent" />
                <span className="text-sm text-text">{hardware.cpu_count} CPU cores</span>
              </div>
              {hardware.gpu.available && (
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 rounded bg-success/20 flex items-center justify-center">
                    <div className="w-2 h-2 rounded-full bg-success" />
                  </div>
                  <span className="text-sm text-text">
                    {hardware.gpu.name} ({hardware.gpu.vram_gb} GB VRAM)
                  </span>
                </div>
              )}
            </div>
          </Card>
        )}

        {/* Filters */}
        <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
          {filters.map((f) => (
            <button
              key={f.id}
              onClick={() => setFilter(f.id)}
              className={`px-3 py-1.5 rounded-full text-sm whitespace-nowrap transition-colors ${
                filter === f.id
                  ? "bg-accent text-bg"
                  : "bg-bg-surface text-text-secondary hover:bg-bg-hover"
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>

        {/* Models Grid */}
        {loadingModels ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-48 rounded-xl bg-bg-surface animate-pulse" />
            ))}
          </div>
        ) : models.length === 0 ? (
          <Card className="p-12 text-center" gradient>
            <Download size={32} className="text-text-muted mx-auto mb-3" />
            <p className="text-text-secondary">No models found. Try a different filter.</p>
          </Card>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {models.map((model) => (
              <ModelCard
                key={model.name}
                model={model}
                onDownload={handleDownload}
                onCancel={handleCancel}
              />
            ))}
          </div>
        )}
      </div>
    </DashboardShell>
  );
}
```

- [ ] **Step 4: Add Models to DashboardShell navigation**

In `frontend/src/shared/layout/DashboardShell.tsx`, add to the WORK group navItems array:

```typescript
{ label: "Models", href: "/models", icon: <Cpu size={18} /> },
```

- [ ] **Step 5: Build check**

```bash
cd /home/adi/Desktop/Cortex-Workspace/frontend && npx next build 2>&1 | tail -20
```

- [ ] **Step 6: Commit**

```bash
git add frontend/app/models/ frontend/src/shared/api/models.ts frontend/src/shared/components/ModelCard.tsx frontend/src/shared/layout/DashboardShell.tsx
git commit -m "feat: local model browser UI with download, filters, and hardware detection"
```

---

## Task 5: Wire LLM into Existing Systems

**Files:**
- Modify: `backend/app/agents/executor.py` — use LLM for real reasoning
- Modify: `backend/app/api/v1/search.py` — AI-powered answer synthesis

**Interfaces:**
- Consumes: `LLMManager` (Task 1)
- Produces: Real intelligence in agents, search, and chat

- [ ] **Step 1: Wire LLM into agent executor**

Modify the `_execute_direct` method in `backend/app/agents/executor.py` to use LLM when available:

```python
# In backend/app/agents/executor.py, modify _execute_direct:
    async def _execute_direct(self, task: str, context: dict | None = None) -> str:
        """Execute task using LLM for real reasoning (with keyword fallback)."""
        try:
            from backend.app.services.llm.manager import llm_manager
            from backend.app.services.llm.provider import LLMMessage

            system_prompt = self._build_system_prompt(context)
            messages = [
                LLMMessage(role="system", content=system_prompt),
                LLMMessage(role="user", content=task),
            ]
            response = await llm_manager.chat(messages, max_tokens=2048, temperature=0.3)
            return response.content
        except (RuntimeError, Exception):
            # No LLM available, fall back to keyword routing
            return await self._keyword_fallback(task)

    def _build_system_prompt(self, context: dict | None = None) -> str:
        """Build system prompt with optional context."""
        prompt = EXECUTOR_SYSTEM_PROMPT
        if context:
            prompt += f"\n\nContext:\n{context}"
        return prompt

    async def _keyword_fallback(self, task: str) -> str:
        """Fallback keyword-based routing when no LLM is available."""
        task_lower = task.lower()

        if any(kw in task_lower for kw in ["search", "find", "look for"]):
            query = self._extract_search_query(task)
            results = await self._search_tool(query)
            return f"Search results for '{query}':\n{results}"

        if any(kw in task_lower for kw in ["read", "show", "open", "file"]):
            path = self._extract_path(task)
            if path:
                return await self._read_file_tool(path)
            return "Please specify a file path to read."

        if any(kw in task_lower for kw in ["list", "files in", "directory"]):
            path = self._extract_path(task) or "."
            return await self._list_files_tool(path)

        return (
            f"Task received: {task}\n\n"
            "I can help with:\n"
            "- Searching code (try: 'search for authentication functions')\n"
            "- Reading files (try: 'read backend/app/main.py')\n"
            "- Listing files (try: 'list files in backend/app/')\n"
        )
```

- [ ] **Step 2: Add AI answer synthesis to search**

Add a new endpoint to `backend/app/api/v1/search.py`:

```python
# Add to backend/app/api/v1/search.py (append):

from pydantic import BaseModel

class SearchAnswerRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    repo_id: int | None = None
    max_results: int = Field(default=10, ge=1, le=50)


@router.post("/search/answer")
async def search_with_answer(
    payload: SearchAnswerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Search and synthesize an AI answer from results."""
    from backend.app.services.cross_file_search import CrossFileSearch
    from backend.app.services.memory_manager import MemoryManager
    from backend.app.services.llm.manager import llm_manager
    from backend.app.services.llm.provider import LLMMessage

    # Get code results (CrossFileSearch.search is synchronous)
    code_results: list[dict] = []
    try:
        search = CrossFileSearch(db)
        code_results = search.search(
            query=payload.query,
            repo_id=payload.repo_id,
            limit=payload.max_results or 10,
        )
    except Exception:
        pass

    # Get memory results (MemoryManager.search returns list[dict])
    memory_results: list[dict] = []
    try:
        memory = MemoryManager(db)
        memory_results = memory.search(
            query=payload.query,
            user_id=current_user.id,
            limit=5,
        )
    except Exception:
        pass

    # Build context for LLM
    context_parts: list[str] = []
    for r in code_results:
        context_parts.append(f"[Code: {r.get('file_path', 'unknown')}]\n{r.get('content_preview', '')[:500]}")
    for r in memory_results:
        entry = r.get("entry")
        if entry:
            context_parts.append(f"[Memory: {entry.get('title', 'untitled')}]\n{entry.get('content', '')[:500]}")

    context = "\n\n".join(context_parts[:10])

    try:
        messages = [
            LLMMessage(role="system", content=(
                "You are Cortex, a helpful AI assistant. Answer the user's question using the provided context. "
                "Be concise and cite sources. If the context doesn't contain enough info, say so."
            )),
            LLMMessage(role="user", content=f"Context:\n{context}\n\nQuestion: {payload.query}"),
        ]
        response = await llm_manager.chat(messages, max_tokens=1024, temperature=0.3)
        answer = response.content
    except RuntimeError:
        answer = "LLM not configured. Enable a local model in Settings > Models to get AI-powered answers."

    return {
        "query": payload.query,
        "answer": answer,
        "code_results": code_results[:5],
        "memory_results": memory_results[:5],
    }
```

- [ ] **Step 3: Compile check**

```bash
cd /home/adi/Desktop/Cortex-Workspace && uv run python -m py_compile backend/app/agents/executor.py && uv run python -m py_compile backend/app/api/v1/search.py && echo "PASS"
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/agents/executor.py backend/app/api/v1/search.py
git commit -m "feat: wire LLM into agent executor and search answer synthesis"
```

---

## Exit Criteria

- [ ] LLMManager routes to llama.cpp or Ollama automatically
- [ ] Existing `LLMProvider` ABC unchanged — new dataclasses added alongside it
- [ ] Model catalog stored as JSON (no extra DB table), enriched from Ollama API
- [ ] Hardware detection works (RAM, CPU, GPU via nvidia-smi)
- [ ] Recommended models shown based on detected hardware
- [ ] Model download via Ollama pull with progress tracking
- [ ] Download cancellation works
- [ ] Token usage metrics tracked in LLMManager
- [ ] Health check endpoint returns provider status
- [ ] Models page shows all models with filters (chat/code/vision/embedding)
- [ ] Download progress bars animate in real-time
- [ ] Agent executor uses LLM for real reasoning (with keyword fallback)
- [ ] Search "AI Answer" uses LLM to synthesize responses (memory results accessed via `r["entry"]["title"]`)
- [ ] All code compiles and builds clean
- [ ] Git commit for each task
