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

            # Record usage (fire and forget)
            try:
                from backend.app.db import SessionLocal
                from backend.app.services.usage_tracker import UsageTracker

                db = SessionLocal()
                tracker = UsageTracker(db)
                tracker.record_usage(
                    model_name=result.get("model", "unknown"),
                    usage_type="chat",
                    tokens_prompt=result.get("tokens_prompt", 0),
                    tokens_completion=result.get("tokens_completion", 0),
                )
                db.close()
            except Exception:
                pass  # Don't fail chat on usage tracking errors

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

    async def fetch_ollama_catalog(self, force_refresh: bool = False) -> list[LLMModelInfo]:
        """Fetch the Ollama model catalog with a multi-source fallback chain:

        1. Local file cache (if fresh)
        2. Ollama library web scraper (ollama.com/library)
        3. Local Ollama API (/api/tags)
        4. Hardcoded fallback list
        """
        import json
        from datetime import datetime, timedelta, timezone

        CACHE_MAX_AGE = timedelta(hours=24)
        MODEL_CATALOG_PATH.parent.mkdir(parents=True, exist_ok=True)

        # ── 1. Check local file cache ──────────────────────────────
        if not force_refresh and MODEL_CATALOG_PATH.exists():
            try:
                with open(MODEL_CATALOG_PATH) as f:
                    cache_data = json.load(f)
                fetched_at = datetime.fromisoformat(cache_data.get("fetched_at", ""))
                if datetime.now(timezone.utc) - fetched_at < CACHE_MAX_AGE:
                    return self._parse_cached_models(cache_data.get("models", []))
            except Exception as e:
                logger.warning("Failed to load catalog cache: %s", e)

        # ── 2. Try Ollama library web scraper ───────────────────────
        try:
            from backend.app.services.ollama_library_scraper import (
                get_ollama_library_models_async,
            )
            scraped = await get_ollama_library_models_async(force_refresh=force_refresh)
            if scraped:
                models_data = self._normalize_scraper_models(scraped)
                self._save_catalog_cache(models_data)
                logger.info("Ollama catalog from web scraper: %d models", len(models_data))
                return self._parse_cached_models(models_data)
        except Exception as e:
            logger.warning("Ollama library scraper failed: %s", e)

        # ── 3. Try local Ollama API ────────────────────────────────
        try:
            import httpx
            async with httpx.AsyncClient(base_url=settings.OLLAMA_BASE_URL, timeout=10.0) as client:
                resp = await client.get("/api/tags")
                resp.raise_for_status()
                data = resp.json()
                models_data = []
                for m in data.get("models", []):
                    name = m["name"]
                    models_data.append({
                        "name": name,
                        "size_bytes": m.get("size", 0),
                        "context_length": 4096,
                        "capabilities": self._infer_capabilities(name),
                        "description": f"Ollama model: {name}",
                        "parameter_count": self._guess_parameter_count(name),
                        "variants": [],
                        "hardware_requirements": {"min_ram_gb": 4, "recommended_ram_gb": 8},
                    })
                self._save_catalog_cache(models_data)
                logger.info("Ollama catalog from local API: %d models", len(models_data))
                return self._parse_cached_models(models_data)
        except Exception as e:
            logger.warning("Local Ollama API catalog fetch failed: %s", e)

        # ── 4. Hardcoded fallback ───────────────────────────────────
        logger.info("Using hardcoded model catalog as fallback")
        fallback = self._get_hardcoded_catalog()
        self._save_catalog_cache(fallback)
        return self._parse_cached_models(fallback)

    # ── Catalog helper methods ──────────────────────────────────────

    @staticmethod
    def _parse_cached_models(models_data: list[dict]) -> list[LLMModelInfo]:
        """Parse cached model dicts into LLMModelInfo objects.

        Preserves metadata (variants, hardware_requirements,
        parameter_count) via the dataclass fields on LLMModelInfo.
        """
        results: list[LLMModelInfo] = []
        for m in models_data:
            if not m.get("name"):
                continue
            results.append(LLMModelInfo(
                name=m["name"],
                size_bytes=m.get("size_bytes", 0),
                context_length=m.get("context_length", 4096),
                capabilities=m.get("capabilities", ["chat"]),
                description=m.get("description", ""),
                parameter_count=m.get("parameter_count"),
                variants=m.get("variants", []),
                hardware_requirements=m.get("hardware_requirements", {"min_ram_gb": 4, "recommended_ram_gb": 8}),
            ))
        return results

    @staticmethod
    def _normalize_scraper_models(scraped: list[dict]) -> list[dict]:
        """Normalize scraper output to a standard cache format.

        Groups models by base name (e.g. all ``llama3.1:*`` variants become
        a single entry with a ``variants`` list), so the UI shows one card
        per model family with a variant dropdown.
        """
        families: dict[str, dict] = {}  # base_name -> merged entry
        for model in scraped:
            base = model["name"].split(":")[0]
            param_variants = model.get("parameter_variants", [])

            if base not in families:
                families[base] = {
                    "name": base,
                    "size_bytes": 0,
                    "context_length": 4096,
                    "capabilities": model.get("capabilities", ["chat"]),
                    "description": model.get("description", ""),
                    "parameter_count": None,
                    "variants": [],
                    "hardware_requirements": {"min_ram_gb": 4, "recommended_ram_gb": 8},
                }

            entry = families[base]
            # Collect variant tags
            for v in param_variants:
                tag = v.get("name", model["name"])
                if tag not in entry["variants"]:
                    entry["variants"].append(tag)
                vsize = v.get("size_bytes", 0)
                if vsize > entry["size_bytes"]:
                    entry["size_bytes"] = vsize
                    entry["parameter_count"] = v.get("parameters", entry["parameter_count"])

            # If no param_variants, add the model name itself as a variant
            if not param_variants and model["name"] not in entry["variants"]:
                entry["variants"].append(model["name"])

        return list(families.values())

    @staticmethod
    def _save_catalog_cache(models_data: list[dict]) -> None:
        """Persist the catalog to disk."""
        import json
        from datetime import datetime, timezone

        try:
            MODEL_CATALOG_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(MODEL_CATALOG_PATH, "w") as f:
                json.dump(
                    {"fetched_at": datetime.now(timezone.utc).isoformat(), "models": models_data},
                    f,
                )
        except Exception as e:
            logger.warning("Failed to save catalog cache: %s", e)

    @staticmethod
    def _infer_capabilities(name: str) -> list[str]:
        """Guess model capabilities from its name."""
        n = name.lower()
        caps = ["chat"]
        if any(x in n for x in ("code", "coder", "starcoder", "deepseek", "codellama")):
            caps.append("code")
        if any(x in n for x in ("vision", "llava", "bakllava")):
            caps.append("vision")
        if any(x in n for x in ("embed", "nomic", "bge", "mxbai", "bert", "allminilm")):
            caps.append("embedding")
        if any(x in n for x in ("reason", "phi", "orca", "qwen")):
            caps.append("reasoning")
        return caps

    @staticmethod
    def _guess_parameter_count(name: str) -> str | None:
        """Try to extract a parameter count string from the model name."""
        import re
        m = re.search(r"(\d+\.?\d*)b", name, re.IGNORECASE)
        if m:
            return f"{m.group(1)}B"
        m = re.search(r"(\d+\.?\d*)m", name, re.IGNORECASE)
        if m:
            return f"{m.group(1)}M"
        return None

    @staticmethod
    def _get_hardcoded_catalog() -> list[dict]:
        """Return a small curated list of models when everything else fails."""
        return [
            {"name": "llama3.2:3b", "size_bytes": 2_000_000_000_000, "context_length": 128000,
             "capabilities": ["chat"], "description": "Meta Llama 3.2 3B — fast and lightweight.",
             "parameter_count": "3B", "variants": ["llama3.2:3b", "llama3.2:11b"],
             "hardware_requirements": {"min_ram_gb": 4, "recommended_ram_gb": 8}},
            {"name": "llama3.1:8b", "size_bytes": 4_700_000_000_000, "context_length": 128000,
             "capabilities": ["chat", "code"], "description": "Meta Llama 3.1 8B — balanced performance.",
             "parameter_count": "8B", "variants": ["llama3.1:8b", "llama3.1:70b"],
             "hardware_requirements": {"min_ram_gb": 8, "recommended_ram_gb": 16}},
            {"name": "codellama:7b", "size_bytes": 3_800_000_000_000, "context_length": 128000,
             "capabilities": ["chat", "code"], "description": "Code-specialized Llama model.",
             "parameter_count": "7B", "variants": ["codellama:7b", "codellama:13b", "codellama:34b"],
             "hardware_requirements": {"min_ram_gb": 8, "recommended_ram_gb": 16}},
            {"name": "qwen2.5:7b", "size_bytes": 4_500_000_000_000, "context_length": 32768,
             "capabilities": ["chat", "code"], "description": "Alibaba Qwen 2.5 7B — multilingual and capable.",
             "parameter_count": "7B", "variants": ["qwen2.5:0.5b", "qwen2.5:3b", "qwen2.5:7b", "qwen2.5:14b", "qwen2.5:32b", "qwen2.5:72b"],
             "hardware_requirements": {"min_ram_gb": 8, "recommended_ram_gb": 16}},
            {"name": "nomic-embed-text:1.5", "size_bytes": 275_000_000_000, "context_length": 8192,
             "capabilities": ["embedding"], "description": "Nomic text embeddings for semantic search.",
             "parameter_count": "137M", "variants": ["nomic-embed-text:1.5"],
             "hardware_requirements": {"min_ram_gb": 2, "recommended_ram_gb": 4}},
            {"name": "gemma2:9b", "size_bytes": 5_500_000_000_000, "context_length": 8192,
             "capabilities": ["chat"], "description": "Google Gemma 2 9B — lightweight and fast.",
             "parameter_count": "9B", "variants": ["gemma2:2b", "gemma2:9b", "gemma2:27b"],
             "hardware_requirements": {"min_ram_gb": 8, "recommended_ram_gb": 16}},
            {"name": "mistral:7b", "size_bytes": 4_100_000_000_000, "context_length": 32768,
             "capabilities": ["chat"], "description": "Mistral 7B — efficient and capable.",
             "parameter_count": "7B", "variants": ["mistral:7b"],
             "hardware_requirements": {"min_ram_gb": 6, "recommended_ram_gb": 8}},
            {"name": "llava:7b", "size_bytes": 4_200_000_000_000, "context_length": 4096,
             "capabilities": ["chat", "vision"], "description": "LLaVA vision-language model.",
             "parameter_count": "7B", "variants": ["llava:7b", "llava:13b"],
             "hardware_requirements": {"min_ram_gb": 8, "recommended_ram_gb": 16}},
        ]

    async def refresh_ollama_catalog(self) -> list[LLMModelInfo]:
        """Force refresh the Ollama catalog cache."""
        return await self.fetch_ollama_catalog(force_refresh=True)

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
