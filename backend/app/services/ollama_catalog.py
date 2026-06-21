"""Unified Ollama model catalog — three-source discovery pipeline.

Sources:
  1. OCI Registry (registry.ollama.ai) — no auth, no weight download
  2. Cloud API (ollama.com) — /api/tags + /api/show
  3. Local API (localhost:11434) — /api/tags + /api/show
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger(__name__)

CACHE_DIR = Path("CortexMemory")
CACHE_FILE = CACHE_DIR / "ollama_catalog.json"
DEFAULT_CACHE_TTL_HOURS = 24

REGISTRY_URL = "https://registry.ollama.ai"
CLOUD_URL = "https://ollama.com"
LOCAL_URL = "http://localhost:11434"

CONCURRENCY_LIMIT = 10

# OCI layer types
LAYER_MODEL = "application/vnd.ollama.image.model"
LAYER_TEMPLATE = "application/vnd.ollama.image.template"
LAYER_PARAMS = "application/vnd.ollama.image.params"
LAYER_LICENSE = "application/vnd.ollama.image.license"
LAYER_PROJECTOR = "application/vnd.ollama.image.projector"

# Capability detection markers
TOOL_MARKERS = ["{{ .Tools }}", "{{ if .Tools }}", "[AVAILABLE_TOOLS]", '"tool_calls"']
VISION_MARKERS = ["{{ .Images }}", "{{ if .Images }}", "image_url"]
THINKING_MARKERS = [
    "{{ if .ThinkingEnabled }}",
    "{{ .ThinkingEnabled }}",
    "<think>",
    "reasoning_content",
]

POPULAR_MODELS: list[dict[str, Any]] = [
    {"name": "llama3.1", "tags": ["8b", "70b", "405b"]},
    {"name": "llama3.2", "tags": ["1b", "3b", "11b"]},
    {"name": "llama3.3", "tags": ["70b"]},
    {"name": "qwen2.5", "tags": ["0.5b", "3b", "7b", "14b", "32b", "72b"]},
    {"name": "qwen2.5-coder", "tags": ["0.5b", "3b", "7b", "14b", "32b"]},
    {"name": "deepseek-r1", "tags": ["1.5b", "7b", "8b", "14b", "32b", "70b"]},
    {"name": "deepseek-v2", "tags": ["16b"]},
    {"name": "deepseek-coder-v2", "tags": ["16b"]},
    {"name": "gemma2", "tags": ["2b", "9b", "27b"]},
    {"name": "gemma3", "tags": ["1b", "4b", "12b", "27b"]},
    {"name": "mistral", "tags": ["7b"]},
    {"name": "mistral-nemo", "tags": ["12b"]},
    {"name": "mixtral", "tags": ["8x7b", "8x22b"]},
    {"name": "phi3", "tags": ["mini", "small", "medium"]},
    {"name": "phi3.5", "tags": ["mini"]},
    {"name": "codellama", "tags": ["7b", "13b", "34b", "70b"]},
    {"name": "starcoder2", "tags": ["3b", "7b", "15b"]},
    {"name": "nomic-embed-text", "tags": ["latest"]},
    {"name": "mxbai-embed-large", "tags": ["latest"]},
    {"name": "bge-large", "tags": ["latest"]},
    {"name": "bge-base", "tags": ["latest"]},
    {"name": "allminilm", "tags": ["latest"]},
    {"name": "llava", "tags": ["7b", "13b"]},
    {"name": "llava-llama3", "tags": ["8b"]},
    {"name": "bakllava", "tags": ["latest"]},
    {"name": "moondream", "tags": ["latest"]},
    {"name": "command-r", "tags": ["35b"]},
    {"name": "command-r-plus", "tags": ["104b"]},
    {"name": "wizardlm2", "tags": ["8x22b"]},
    {"name": "orca2", "tags": ["7b", "13b"]},
    {"name": "neural-chat", "tags": ["7b"]},
    {"name": "aya", "tags": ["8b", "35b"]},
    {"name": "tinyllama", "tags": ["latest"]},
    {"name": "falcon", "tags": ["7b", "40b"]},
]


class OllamaCatalogService:
    """Unified Ollama model catalog with three-source discovery pipeline."""

    def __init__(self) -> None:
        """Initialize with empty client, no setup yet."""
        self._client: httpx.AsyncClient | None = None
        self._semaphore: asyncio.Semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)

    async def get_client(self) -> httpx.AsyncClient:
        """Lazy-init singleton httpx.AsyncClient."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0, connect=10.0),
                follow_redirects=True,
                limits=httpx.Limits(max_connections=CONCURRENCY_LIMIT),
            )
        return self._client

    async def close(self) -> None:
        """Close the httpx client."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def fetch_catalog(
        self,
        force_refresh: bool = False,
        include_cloud: bool = True,
        include_local: bool = True,
        include_registry: bool = True,
    ) -> list[dict[str, Any]]:
        """Fetch the unified model catalog from all enabled sources.

        Checks cache first unless force_refresh is True. Deduplicates models
        with cloud/local sources taking priority over registry entries.

        Args:
            force_refresh: If True, bypass cache and fetch fresh data.
            include_cloud: Whether to probe the cloud API.
            include_local: Whether to probe the local Ollama API.
            include_registry: Whether to probe the OCI registry.

        Returns:
            List of unified model dictionaries.
        """
        if not force_refresh:
            cached = self._load_cache()
            if cached is not None and self._is_cache_valid(cached):
                models = cached.get("models", [])
                logger.debug("Returning %d cached catalog models", len(models))
                return models

        tasks: list[asyncio.Task] = []
        source_priority: dict[str, int] = {}

        if include_cloud:
            tasks.append(asyncio.create_task(self.fetch_cloud_models()))
            source_priority["cloud"] = 3
        if include_local:
            tasks.append(asyncio.create_task(self.fetch_local_models()))
            source_priority["local"] = 2
        if include_registry:
            tasks.append(asyncio.create_task(self.fetch_registry_models()))
            source_priority["registry"] = 1

        results = await asyncio.gather(*tasks, return_exceptions=True)

        merged: dict[str, dict[str, Any]] = {}
        for result in results:
            if isinstance(result, Exception):
                logger.warning("Source failed: %s", result)
                continue
            for model in result:
                key = model.get("name", "")
                existing = merged.get(key)
                if existing is None:
                    merged[key] = model
                else:
                    existing_priority = source_priority.get(existing.get("source", ""), 0)
                    new_priority = source_priority.get(model.get("source", ""), 0)
                    if new_priority > existing_priority:
                        merged[key] = model

        models = list(merged.values())
        models.sort(key=lambda m: m.get("name", ""))

        self._save_cache(models)
        logger.info("Fetched and cached %d unique models", len(models))
        return models

    async def fetch_cloud_models(self) -> list[dict[str, Any]]:
        """Probe the cloud API (ollama.com) for available models.

        Returns:
            List of model dicts from the cloud source.
        """
        try:
            return await self._probe_api_source(
                CLOUD_URL,
                headers={"Accept": "application/json"},
            )
        except Exception as e:
            logger.warning("Cloud API probe failed: %s", e)
            return []

    async def fetch_local_models(self) -> list[dict[str, Any]]:
        """Probe the local Ollama API for available models.

        Returns:
            List of model dicts from the local source.
        """
        try:
            return await self._probe_api_source(
                LOCAL_URL,
                headers={},
            )
        except Exception as e:
            logger.warning("Local API probe failed: %s", e)
            return []

    async def fetch_registry_models(self) -> list[dict[str, Any]]:
        """Probe the OCI registry for popular models.

        Iterates over POPULAR_MODELS and probes each model:tag combination.

        Returns:
            List of model dicts from the registry source.
        """
        await self.get_client()
        models: list[dict[str, Any]] = []

        async def _probe_one(model_entry: dict[str, Any], tag: str) -> None:
            async with self._semaphore:
                result = await self._probe_registry_model(model_entry["name"], tag)
                if result is not None:
                    models.append(result)

        tasks = [_probe_one(entry, tag) for entry in POPULAR_MODELS for tag in entry["tags"]]

        await asyncio.gather(*tasks, return_exceptions=True)
        return models

    async def _probe_api_source(self, base_url: str, headers: dict[str, str]) -> list[dict[str, Any]]:
        """Shared logic for cloud/local API probing.

        GET /api/tags then POST /api/show for each model.

        Args:
            base_url: The API base URL (cloud or local).
            headers: Request headers.

        Returns:
            List of model dicts.
        """
        client = await self.get_client()
        tags_url = f"{base_url}/api/tags"

        resp = await client.get(tags_url, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        raw_models = data.get("models", [])

        if not raw_models:
            return []

        async def _fetch_show(tag_info: dict[str, Any]) -> dict[str, Any] | None:
            model_name = tag_info.get("name", "")
            show_url = f"{base_url}/api/show"
            try:
                show_resp = await client.post(
                    show_url,
                    json={"name": model_name},
                    headers=headers,
                )
                show_resp.raise_for_status()
                return show_resp.json()
            except Exception as e:
                logger.debug("Show failed for %s: %s", model_name, e)
                return None

        show_tasks = [_fetch_show(m) for m in raw_models]
        show_results = await asyncio.gather(*show_tasks)

        entries: list[dict[str, Any]] = []
        source = "cloud" if "ollama.com" in base_url else "local"
        for tag_info, show_info in zip(raw_models, show_results, strict=False):
            entries.append(self._build_api_entry(tag_info, show_info, source))

        return entries

    async def _probe_registry_model(self, model: str, tag: str) -> dict[str, Any] | None:
        """Probe a single model from the OCI registry.

        Fetches the manifest, identifies small metadata blobs, and fetches
        only template/params/license — never downloads model weights.

        Args:
            model: Model name (e.g. "llama3.1").
            tag: Model tag (e.g. "8b").

        Returns:
            Model dict or None if not found.
        """
        client = await self.get_client()
        manifest_url = f"{REGISTRY_URL}/v2/library/{model}/manifests/{tag}"

        try:
            resp = await client.get(
                manifest_url,
                headers={"Accept": "application/vnd.oci.image.manifest.v1+json"},
            )
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            manifest = resp.json()
        except httpx.HTTPStatusError:
            return None
        except Exception as e:
            logger.debug("Registry manifest fetch failed for %s:%s: %s", model, tag, e)
            return None

        layers = manifest.get("layers", [])
        media_type_map: dict[str, str] = {}
        for layer in layers:
            mt = layer.get("mediaType", "")
            digest = layer.get("digest", "")
            layer.get("size", 0)
            if digest:
                media_type_map[mt] = digest

        template_text = ""
        params_text = ""
        license_text = ""

        for layer_type, digest in media_type_map.items():
            if layer_type == LAYER_TEMPLATE:
                blob = await self._fetch_registry_blob(model, digest)
                if blob:
                    template_text = blob
            elif layer_type == LAYER_PARAMS:
                blob = await self._fetch_registry_blob(model, digest)
                if blob:
                    params_text = blob
            elif layer_type == LAYER_LICENSE:
                blob = await self._fetch_registry_blob(model, digest)
                if blob:
                    license_text = blob

        capabilities = self._detect_capabilities(template_text)

        has_model_layer = any(layer.get("mediaType") == LAYER_MODEL for layer in layers)

        return {
            "name": f"{model}:{tag}",
            "model": f"{model}:{tag}",
            "source": "registry",
            "registry_model": model,
            "registry_tag": tag,
            "template": template_text,
            "parameters": params_text,
            "license": license_text,
            "capabilities": capabilities,
            "has_model_layer": has_model_layer,
        }

    async def _fetch_registry_blob(self, model: str, digest: str) -> str:
        """Fetch a blob from the OCI registry (follows redirects).

        Args:
            model: Model name.
            digest: Blob digest (e.g. "sha256:abc...").

        Returns:
            Blob content as string, or empty string on failure.
        """
        client = await self.get_client()
        blob_url = f"{REGISTRY_URL}/v2/library/{model}/blobs/{digest}"

        try:
            resp = await client.get(blob_url)
            resp.raise_for_status()
            content = resp.content
            try:
                return content.decode("utf-8")
            except UnicodeDecodeError:
                return ""
        except Exception as e:
            logger.debug("Registry blob fetch failed for %s %s: %s", model, digest, e)
            return ""

    @staticmethod
    def _detect_capabilities(template: str) -> list[str]:
        """Detect capabilities from a template blob via pattern matching.

        Args:
            template: The template text content.

        Returns:
            List of capability strings ("tools", "vision", "thinking").
        """
        if not template:
            return []

        capabilities: list[str] = []

        if any(marker in template for marker in TOOL_MARKERS):
            capabilities.append("tools")

        if any(marker in template for marker in VISION_MARKERS):
            capabilities.append("vision")

        if any(marker in template for marker in THINKING_MARKERS):
            capabilities.append("thinking")

        return capabilities

    @staticmethod
    def _build_api_entry(
        tag_info: dict[str, Any],
        show_info: dict[str, Any] | None,
        source: str,
    ) -> dict[str, Any]:
        """Build a unified entry from API data.

        Args:
            tag_info: The model info from /api/tags.
            show_info: The model info from /api/show (or None).
            source: The source identifier ("cloud" or "local").

        Returns:
            Unified model dict.
        """
        name = tag_info.get("name", "")
        details = tag_info.get("details", {})

        entry: dict[str, Any] = {
            "name": name,
            "source": source,
            "model": name,
            "size": tag_info.get("size", 0),
            "digest": tag_info.get("digest", ""),
            "modified_at": tag_info.get("modified_at", ""),
            "family": details.get("family", ""),
            "parameter_size": details.get("parameter_size", ""),
            "quantization": details.get("quantization_level", ""),
        }

        if show_info is not None:
            template = show_info.get("template", "")
            parameters = show_info.get("parameters", "")
            license_text = show_info.get("license", "")

            entry["template"] = template
            entry["parameters"] = parameters
            entry["license"] = license_text
            entry["capabilities"] = OllamaCatalogService._detect_capabilities(template)

            details_from_show = show_info.get("details", {})
            if details_from_show:
                entry["family"] = entry.get("family") or details_from_show.get("family", "")
                entry["parameter_size"] = entry.get("parameter_size") or details_from_show.get("parameter_size", "")
                entry["quantization"] = entry.get("quantization") or details_from_show.get("quantization_level", "")
        else:
            entry["template"] = ""
            entry["parameters"] = ""
            entry["license"] = ""
            entry["capabilities"] = []

        return entry

    def _load_cache(self) -> dict | None:
        """Load catalog from disk cache.

        Returns:
            Cached dict with 'models' and 'fetched_at' keys, or None.
        """
        try:
            if CACHE_FILE.exists():
                with open(CACHE_FILE, encoding="utf-8") as f:
                    return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.debug("Failed to load cache: %s", e)
        return None

    def _save_cache(self, models: list[dict[str, Any]]) -> None:
        """Save catalog to disk cache.

        Args:
            models: List of model dicts to cache.
        """
        try:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            cache_data = {
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "models": models,
            }
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
        except OSError as e:
            logger.warning("Failed to save cache: %s", e)

    def _is_cache_valid(self, cache: dict) -> bool:
        """Check if the cache is still within TTL.

        Args:
            cache: The cached dict.

        Returns:
            True if cache is valid, False otherwise.
        """
        fetched_at_str = cache.get("fetched_at")
        if not fetched_at_str:
            return False
        try:
            fetched_at = datetime.fromisoformat(fetched_at_str)
            now = datetime.now(timezone.utc)
            age = now - fetched_at
            return age < timedelta(hours=DEFAULT_CACHE_TTL_HOURS)
        except (ValueError, TypeError):
            return False

    def fetch_catalog_sync(self, force_refresh: bool = False) -> list[dict[str, Any]]:
        """Sync wrapper for backward compatibility.

        Runs fetch_catalog in a new event loop if no loop is running,
        otherwise creates a task.

        Args:
            force_refresh: If True, bypass cache and fetch fresh data.

        Returns:
            List of model dicts.
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop is None:
            return asyncio.run(self.fetch_catalog(force_refresh=force_refresh))

        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(
                asyncio.run,
                self.fetch_catalog(force_refresh=force_refresh),
            )
            return future.result(timeout=120)


_default_service: OllamaCatalogService | None = None


def get_catalog_service() -> OllamaCatalogService:
    """Get or create the default catalog service singleton.

    Returns:
        The default OllamaCatalogService instance.
    """
    global _default_service
    if _default_service is None:
        _default_service = OllamaCatalogService()
    return _default_service


async def get_ollama_catalog(
    force_refresh: bool = False,
) -> list[dict[str, Any]]:
    """Async convenience function to get the Ollama catalog.

    Args:
        force_refresh: If True, bypass cache and fetch fresh data.

    Returns:
        List of model dicts.
    """
    return await get_catalog_service().fetch_catalog(force_refresh=force_refresh)


def get_ollama_catalog_sync(
    force_refresh: bool = False,
) -> list[dict[str, Any]]:
    """Sync convenience function to get the Ollama catalog.

    Args:
        force_refresh: If True, bypass cache and fetch fresh data.

    Returns:
        List of model dicts.
    """
    return get_catalog_service().fetch_catalog_sync(force_refresh=force_refresh)
