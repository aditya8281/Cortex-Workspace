from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from backend.app.core.config import settings
from backend.app.services.llm.llama_cpp import LlamaCppProvider
from backend.app.services.llm.ollama import OllamaProvider
from backend.app.services.llm.provider import LLMMessage, LLMModelInfo, LLMProvider, LLMResponse

logger = logging.getLogger(__name__)

MODEL_CATALOG_PATH = Path(getattr(settings, "CORTEX_ROOT", None) or "./CortexMemory") / "llm_catalog.json"

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
        self._providers = []

        if ollama_url:
            self._providers.append(OllamaProvider(base_url=ollama_url))

        if llama_model_path:
            self._providers.append(
                LlamaCppProvider(
                    model_path=llama_model_path,
                    n_ctx=n_ctx,
                    n_gpu_layers=n_gpu_layers,
                )
            )

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

    async def chat_stream(
        self,
        messages: list[LLMMessage],
        model: str | None = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ):
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
                    for m in p.list_models():
                        all_models.append(
                            LLMModelInfo(
                                name=m.get("name", "unknown"),
                                size_bytes=m.get("size_bytes", 0),
                                context_length=m.get("context_length", 4096),
                                capabilities=m.get("capabilities", []),
                                description=m.get("description", ""),
                            )
                        )
        return all_models

    async def health_check(self) -> dict:
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
        return {
            "total_requests": self._total_requests,
            "total_errors": self._total_errors,
            "total_prompt_tokens": self._total_prompt_tokens,
            "total_completion_tokens": self._total_completion_tokens,
            "active_provider": self._active.provider_name() if self._active else None,
        }


llm_manager = LLMManager()
