from __future__ import annotations

import asyncio
import logging

from backend.app.services.llm.llama_cpp import LlamaCppProvider
from backend.app.services.llm.ollama import OllamaProvider
from backend.app.services.llm.provider import LLMMessage, LLMModelInfo, LLMProvider, LLMResponse

logger = logging.getLogger(__name__)


class LLMManager:
    """Singleton that routes to the best available LLM provider."""

    def __init__(self) -> None:
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
    ) -> None:
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
                logger.info("Active LLM provider: %s", p.provider_name())  # type: ignore[attr-defined]
                return p
        raise RuntimeError("No LLM provider available. Install llama-cpp-python or start Ollama.")

    @staticmethod
    def _is_retryable(exc: Exception) -> bool:
        if isinstance(exc, (ConnectionError, TimeoutError)):
            return True
        if isinstance(exc, OSError):
            return True
        if hasattr(exc, "request"):
            return True
        msg = str(exc).lower()
        return any(kw in msg for kw in ("connection", "timeout", "connect", "eof", "reset"))

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
        db=None,
    ) -> LLMResponse:
        async with self._semaphore:
            provider = await self._get_active()
        max_retries = 3
        last_error = None

        for attempt in range(max_retries + 1):
            try:
                result = await provider.chat_direct(  # type: ignore[attr-defined]
                    messages=messages,
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                self._total_requests += 1
                self._total_prompt_tokens += result.get("tokens_prompt", 0)
                self._total_completion_tokens += result.get("tokens_completion", 0)

                try:
                    if db is None:
                        from backend.app.db.session import SessionLocal

                        db = SessionLocal()
                        close_db = True
                    else:
                        close_db = False
                    try:
                        from backend.app.services.usage_tracker import UsageTracker

                        tracker = UsageTracker(db)
                        tracker.record_usage(
                            model_name=result.get("model", "unknown"),
                            usage_type="chat",
                            tokens_prompt=result.get("tokens_prompt", 0),
                            tokens_completion=result.get("tokens_completion", 0),
                        )
                    finally:
                        if close_db:
                            db.close()
                except Exception:
                    logger.debug("Failed to record LLM usage tracking", exc_info=True)

                return LLMResponse(
                    content=result["content"],
                    model=result.get("model", "unknown"),
                    tokens_prompt=result.get("tokens_prompt", 0),
                    tokens_completion=result.get("tokens_completion", 0),
                    finish_reason=result.get("finish_reason", "stop"),
                )
            except Exception as e:
                last_error = e
                if attempt < max_retries and self._is_retryable(e):
                    delay = 2**attempt
                    logger.warning(
                        "LLM chat attempt %d/%d failed: %s. Retrying in %ds...",
                        attempt + 1,
                        max_retries + 1,
                        e,
                        delay,
                    )
                    await asyncio.sleep(delay)
                else:
                    break

        self._total_errors += 1
        raise RuntimeError(f"LLM chat failed after {max_retries + 1} attempts: {last_error}") from last_error

    async def chat_stream(
        self,
        messages: list[LLMMessage],
        model: str | None = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        db=None,
    ):
        async with self._semaphore:
            provider = await self._get_active()
        max_retries = 3
        last_error = None

        for attempt in range(max_retries + 1):
            full_response = ""
            try:
                async for token in provider.chat_stream(  # type: ignore[attr-defined]
                    [{"role": m.role, "content": m.content} for m in messages],
                    tools=[],
                    config={"model": model, "max_tokens": max_tokens, "temperature": temperature},
                ):
                    full_response += token
                    yield token

                self._total_requests += 1
                prompt_tokens = sum(len(m.content) for m in messages) // 4
                completion_tokens = len(full_response) // 4
                self._total_prompt_tokens += prompt_tokens
                self._total_completion_tokens += completion_tokens

                try:
                    if db is None:
                        from backend.app.db.session import SessionLocal

                        db = SessionLocal()
                        close_db = True
                    else:
                        close_db = False
                    try:
                        from backend.app.services.usage_tracker import UsageTracker

                        tracker = UsageTracker(db)
                        tracker.record_usage(
                            model_name=model or "unknown",
                            usage_type="chat_stream",
                            tokens_prompt=prompt_tokens,
                            tokens_completion=completion_tokens,
                        )
                    finally:
                        if close_db:
                            db.close()
                except Exception:
                    logger.debug("Failed to record LLM stream usage tracking", exc_info=True)
                return
            except Exception as e:
                last_error = e
                if attempt < max_retries and self._is_retryable(e):
                    delay = 2**attempt
                    logger.warning(
                        "LLM stream attempt %d/%d failed: %s. Retrying in %ds...",
                        attempt + 1,
                        max_retries + 1,
                        e,
                        delay,
                    )
                    await asyncio.sleep(delay)
                else:
                    break

        self._total_errors += 1
        raise RuntimeError(f"LLM stream failed after {max_retries + 1} attempts: {last_error}") from last_error

    async def fetch_ollama_catalog(self, force_refresh: bool = False) -> list[LLMModelInfo]:
        """Fetch the Ollama model catalog using the unified three-source pipeline.

        Uses ollama_catalog.OllamaCatalogService which probes:
          1. OCI Registry (registry.ollama.ai) — no auth, no weight download
          2. Cloud API (ollama.com) — /api/tags + /api/show
          3. Local API (localhost:11434) — /api/tags + /api/show
        """
        try:
            from backend.app.services.ollama_catalog import get_ollama_catalog

            scraped, _source_status = await get_ollama_catalog(force_refresh=force_refresh)
            if scraped:
                models_data = self._normalize_catalog_models(scraped)
                logger.info("Ollama catalog from unified pipeline: %d models", len(models_data))
                return self._parse_cached_models(models_data)
        except Exception as e:
            logger.warning("Unified catalog fetch failed: %s", e)

        return []

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
            results.append(
                LLMModelInfo(
                    name=m["name"],
                    size_bytes=m.get("size_bytes", 0),
                    context_length=m.get("context_length", 4096),
                    capabilities=m.get("capabilities", ["chat"]),
                    description=m.get("description", ""),
                    parameter_count=m.get("parameter_count"),
                    variants=m.get("variants", []),
                    hardware_requirements=m.get("hardware_requirements", {"min_ram_gb": 4, "recommended_ram_gb": 8}),
                )
            )
        return results

    @staticmethod
    def _normalize_catalog_models(scraped: list[dict]) -> list[dict]:
        """Normalize catalog output to a standard cache format.

        Groups models by base name (e.g. all ``llama3.1:*`` variants become
        a single entry with a ``variants`` list), so the UI shows one card
        per model family with a variant dropdown.
        """
        families: dict[str, dict] = {}  # base_name -> merged entry
        for model in scraped:
            name = model.get("name", "")
            base = name.split(":")[0]
            size = model.get("size", 0) or model.get("size_bytes", 0)

            if base not in families:
                families[base] = {
                    "name": base,
                    "size_bytes": 0,
                    "context_length": 4096,
                    "capabilities": model.get("capabilities", ["chat"]),
                    "description": model.get("description", ""),
                    "parameter_count": model.get("parameter_size"),
                    "variants": [],
                    "hardware_requirements": {"min_ram_gb": 4, "recommended_ram_gb": 8},
                }

            entry = families[base]
            if name not in entry["variants"]:
                entry["variants"].append(name)
            if size > entry["size_bytes"]:
                entry["size_bytes"] = size
                if model.get("parameter_size"):
                    entry["parameter_count"] = model["parameter_size"]

        return list(families.values())

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
        status: dict[str, object] = {}
        for p in self._providers:
            try:
                available = await self._check_available(p)
                status[p.provider_name()] = {  # type: ignore[attr-defined]
                    "available": available,
                    "is_active": p is self._active,
                }
            except Exception as e:
                status[p.provider_name()] = {  # type: ignore[attr-defined]
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
            "active_provider": self._active.provider_name() if self._active else None,  # type: ignore[attr-defined]
        }


llm_manager = LLMManager()
