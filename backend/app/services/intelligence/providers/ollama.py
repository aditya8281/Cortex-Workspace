"""Ollama provider adapter."""

from __future__ import annotations

import json
from collections.abc import Callable

import httpx
import structlog

from backend.app.services.providers.base import (
    ProviderAdapter,
    ProviderDownloadResult,
    ProviderModelInfo,
    ProviderVariantInfo,
)

logger = structlog.get_logger()


class OllamaProvider(ProviderAdapter):
    """Ollama local model server provider."""

    def __init__(self, base_url: str = "http://localhost:11434"):
        self._base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(base_url=self._base_url, timeout=30.0)

    @property
    def name(self) -> str:
        return "ollama"

    @property
    def display_name(self) -> str:
        return "Ollama"

    async def health_check(self) -> bool:
        try:
            resp = await self._client.get("/api/tags")
            return resp.status_code == 200
        except Exception:
            return False

    async def list_models(self) -> list[ProviderModelInfo]:
        try:
            resp = await self._client.get("/api/tags")
            resp.raise_for_status()
            data = resp.json()
            models = []
            for m in data.get("models", []):
                name = m.get("name", "")
                display_name = name.split(":")[0] if ":" in name else name
                family = display_name.lower().replace(" ", "")
                models.append(
                    ProviderModelInfo(
                        provider_model_id=name,
                        display_name=display_name,
                        family=family,
                        size_bytes=m.get("size"),
                        source_url=f"https://ollama.com/library/{display_name}",
                        extra_metadata={"modified_at": m.get("modified_at"), "digest": m.get("digest")},
                    )
                )
            return models
        except Exception as e:
            logger.error("ollama_list_models_failed", error=str(e))
            return []

    async def get_model_variants(self, model_id: str) -> list[ProviderVariantInfo]:
        return []

    async def get_model_detail(self, model_id: str) -> ProviderModelInfo | None:
        try:
            resp = await self._client.post("/api/show", json={"name": model_id})
            resp.raise_for_status()
            data = resp.json()
            details = data.get("details", {})
            return ProviderModelInfo(
                provider_model_id=model_id,
                display_name=model_id.split(":")[0],
                family=details.get("family", ""),
                architecture=details.get("architecture"),
                parameter_count=details.get("parameter_size"),
                context_length=details.get("context_length"),
                capabilities=self._infer_capabilities(details),
                license=details.get("license"),
                tags=details.get("tags", []),
            )
        except Exception as e:
            logger.error("ollama_get_detail_failed", model_id=model_id, error=str(e))
            return None

    async def download_model(
        self,
        model_id: str,
        variant_id: str | None = None,
        on_progress: Callable[[float], None] | None = None,
    ) -> ProviderDownloadResult:
        try:
            async with self._client.stream("POST", "/api/pull", json={"name": model_id}) as resp:
                if resp.status_code != 200:
                    return ProviderDownloadResult(success=False, error_message=f"HTTP {resp.status_code}")

                async for line in resp.aiter_lines():
                    try:
                        data = json.loads(line)
                        if "completed" in data and "total" in data:
                            progress = data["completed"] / data["total"]
                            if on_progress:
                                on_progress(progress)
                    except json.JSONDecodeError:
                        continue

            return ProviderDownloadResult(success=True, model_name=model_id)
        except Exception as e:
            logger.error("ollama_download_failed", model_id=model_id, error=str(e))
            return ProviderDownloadResult(success=False, error_message=str(e))

    async def cancel_download(self, model_id: str) -> bool:
        return False

    async def delete_model(self, model_id: str) -> bool:
        try:
            resp = await self._client.request("DELETE", "/api/delete", json={"name": model_id})
            return resp.status_code == 200
        except Exception:
            return False

    async def list_installed(self) -> list[ProviderModelInfo]:
        return await self.list_models()

    def _infer_capabilities(self, details: dict) -> list[str]:
        caps = ["chat"]
        family = details.get("family", "").lower()
        if family in ("llava", "bakllava", "moondream"):
            caps.append("vision")
        if "code" in family or "starcoder" in family:
            caps.append("code")
        if "embed" in family or "nomic" in family or "bge" in family:
            caps.append("embedding")
        return caps
