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
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import httpx

from backend.app.core.config import settings

logger = logging.getLogger(__name__)

CACHE_DIR = Path("CortexMemory")
CACHE_FILE = CACHE_DIR / "ollama_catalog.json"
FALLBACK_FILE = CACHE_DIR / "ollama_catalog_fallback.json"
DEFAULT_CACHE_TTL_HOURS = 24

REGISTRY_URL = "https://registry.ollama.ai"
CLOUD_URL = "https://ollama.com"
LOCAL_URL = settings.OLLAMA_BASE_URL

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

_LIBRARY_JSON = Path(__file__).resolve().parent.parent / "data" / "library.json"
_SEED_CATALOG_JSON = Path(__file__).resolve().parent.parent / "data" / "catalog_seed.json"


def _load_library_json() -> list[dict[str, Any]]:
    """Load full model list from backend/app/data/library.json.

    Returns list of dicts with 'name' and 'tags' keys.
    Falls back to empty list if file not found.
    """
    if not _LIBRARY_JSON.exists():
        logger.warning("library.json not found at %s", _LIBRARY_JSON)
        return []
    try:
        data = json.loads(_LIBRARY_JSON.read_text())
        models = data.get("models", [])
        total_tags = sum(len(m.get("tags", ["latest"])) for m in models)
        logger.info(
            "Loaded %d models (%d tags) from library.json",
            len(models),
            total_tags,
        )
        return models
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Failed to load library.json: %s", e)
        return []


def _load_seed_catalog() -> list[dict[str, Any]]:
    """Load the pre-built catalog from catalog_seed.json.

    This is a snapshot from the reference ollama-catalog project
    (773 models from registry.ollama.ai). Used as the instant
    baseline so the catalog isn't empty while live probes run.
    """
    if not _SEED_CATALOG_JSON.exists():
        logger.debug("No seed catalog found at %s", _SEED_CATALOG_JSON)
        return []
    try:
        data = json.loads(_SEED_CATALOG_JSON.read_text())
        models = data.get("models", [])
        logger.info("Loaded %d models from seed catalog", len(models))
        return models
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Failed to load seed catalog: %s", e)
        return []


@dataclass
class CatalogSourceStatus:
    """Track health status of each catalog source."""

    cloud: str = "pending"  # "ok", "unavailable", "timeout", "pending"
    local: str = "pending"
    registry: str = "pending"
    last_updated: str = ""
    from_fallback: bool = False
    errors: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "cloud": self.cloud,
            "local": self.local,
            "registry": self.registry,
            "last_updated": self.last_updated,
            "from_fallback": self.from_fallback,
            "errors": self.errors,
        }


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
    ) -> tuple[list[dict[str, Any]], CatalogSourceStatus]:
        """Fetch the unified model catalog from all enabled sources.

        Pipeline:
          1. Load seed catalog (773 models from registry snapshot) — instant
          2. Probe live cloud + local APIs — overlay richer metadata
          3. If registry enabled, fill any remaining gaps via OCI probe

        Returns:
            Tuple of (models list, source status).
        """
        status = CatalogSourceStatus()

        # Check cache first (unless force refresh)
        if not force_refresh:
            cached = self._load_cache()
            if cached is not None and self._is_cache_valid(cached):
                models = cached.get("models", [])
                logger.debug("Returning %d cached catalog models", len(models))
                status.from_fallback = False
                status.last_updated = cached.get("fetched_at", "")
                return models, status

        # --- Step 1: Seed catalog (instant baseline) ---
        merged: dict[str, dict[str, Any]] = {}
        seed_models = _load_seed_catalog()
        for model in seed_models:
            key = model.get("name", "")
            if key:
                merged[key] = model
        logger.info("Seed baseline: %d models loaded", len(merged))

        # --- Step 2: Live cloud + local probes ---
        live_tasks: list[asyncio.Task] = []
        live_sources: list[str] = []

        if include_cloud:
            live_tasks.append(asyncio.create_task(self.fetch_cloud_models()))
            live_sources.append("cloud")
        if include_local:
            live_tasks.append(asyncio.create_task(self.fetch_local_models()))
            live_sources.append("local")

        if live_tasks:
            live_results = await asyncio.gather(*live_tasks, return_exceptions=True)

            for result, source_name in zip(live_results, live_sources, strict=False):
                if isinstance(result, Exception):
                    status.errors[source_name] = str(result)
                    logger.warning("Live source %s failed: %s", source_name, result)
                    continue

                if not result:
                    status.errors[source_name] = "no models returned"
                    continue

                status.cloud = "ok" if source_name == "cloud" else status.cloud
                status.local = "ok" if source_name == "local" else status.local

                for model in result:  # type: ignore[union-attr]
                    key = model.get("name", "")
                    if not key:
                        continue
                    existing = merged.get(key)
                    if existing is None:
                        merged[key] = model
                    else:
                        # Live data always wins over seed data
                        merged[key] = model

        # --- Step 3: Registry fill (if enabled and we have seed, skip heavy probe) ---
        if include_registry and not merged:
            try:
                registry_models = await self.fetch_registry_models()
                for model in registry_models:
                    key = model.get("name", "")
                    if key:
                        merged[key] = model
                status.registry = "ok"
            except Exception as exc:
                status.registry = "error"
                status.errors["registry"] = str(exc)
                logger.warning("Registry probe failed: %s", exc)

        models = list(merged.values())
        models.sort(key=lambda m: m.get("name", ""))

        # Normalize all models for consistent data presentation
        models = self._normalize_all(models)

        if not models:
            logger.warning("All catalog sources failed, attempting fallback")
            fallback = self._load_fallback()
            if fallback:
                models = fallback
                status.from_fallback = True
                status.errors["_fallback"] = "All sources failed, using cached fallback"

        if models:
            self._save_cache(models)
            self._save_fallback(models)
            status.last_updated = datetime.now(timezone.utc).isoformat()

        logger.info(
            "Catalog ready: %d models (seed=%d, cloud=%s, local=%s, registry=%s, fallback=%s)",
            len(models),
            len(seed_models),
            status.cloud,
            status.local,
            status.registry,
            status.from_fallback,
        )
        return models, status

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
        """Probe the OCI registry for ALL models from library.json.

        Iterates over all model families and their tags,
        probing each model:tag combination via OCI manifest + blob.
        No model weights are downloaded.

        Returns:
            List of model dicts from the registry source.
        """
        await self.get_client()
        models: list[dict[str, Any]] = []

        library_models = _load_library_json()
        if not library_models:
            logger.warning("No library.json models available for registry probe")
            return []

        probe_list: list[tuple[str, str, list[str]]] = []
        for m in library_models:
            name = m["name"]
            tags = m.get("tags", ["latest"])
            for tag in tags:
                probe_list.append((name, tag, tags))

        logger.info(
            "Probing %d model:tag pairs from registry (concurrency=%d)",
            len(probe_list),
            CONCURRENCY_LIMIT,
        )

        async def _probe_one(model_name: str, tag: str, all_tags: list[str]) -> None:
            async with self._semaphore:
                result = await self._probe_registry_model(model_name, tag)
            if result is not None:
                result["available_tags"] = all_tags
                models.append(result)

        await asyncio.gather(*[_probe_one(name, tag, tags) for name, tag, tags in probe_list])

        logger.info("Registry probe complete: %d models found", len(models))
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

        capabilities = self._detect_capabilities(template_text, f"{model}:{tag}")

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

    # Model names that indicate code-specialized models.
    # Used to infer "code" capability when the source didn't provide it.
    _CODE_NAME_PATTERNS: list[str] = [
        "code",
        "coder",
        "codellama",
        "codestral",
        "deepcoder",
        "phind",
        "wizardcoder",
        "starcoder",
        "granite-code",
        "codebooga",
        "dolphincoder",
        "sqlcoder",
        "codeqwen",
        "deepseek-coder",
        "qwen-coder",
        "magicoder",
        "codegeex",
        "codegemma",
        "codeup",
        "opencoder",
        "stable-code",
    ]

    # Embedding model detection patterns — checked against model name
    EMBEDDING_NAME_PATTERNS = ["embed", "bert", "bge", "gte", "e5", "instructor", "minilm", "mxbai", "snowflake-arctic"]

    KNOWN_EMBEDDING_DIMS = {
        "nomic-bert": 768,
        "nomic-bert-moe": 768,
        "nomic-embed": 768,
        "bge-m3": 1024,
        "bge-large": 1024,
        "bge-base": 768,
        "bge-small": 384,
        "qwen3-embedding": 1024,
        "all-minilm": 384,
        "mxbai-embed": 1024,
        "snowflake-arctic": 1024,
    }

    @staticmethod
    def _normalize_model(model: dict[str, Any]) -> dict[str, Any]:
        """Normalize a single model dict for consistent presentation.

        Handles format differences across sources (seed, cloud, local, registry):
          - parameter_size: raw numbers ("675000000000") → human-readable ("675B")
          - quantization_level → quantization field
          - size=0 → None (unknown, not "0 B")
          - capabilities: ["completion"] → ["chat"], code-inference from name
        """
        # --- parameter_size normalization ---
        param_size = model.get("parameter_size", "")
        if param_size:
            raw = param_size.strip()
            # Already human-readable (e.g. "8B", "7B", "137M")
            if raw.upper().endswith("B") or raw.upper().endswith("M"):
                model["parameter_size"] = raw
            else:
                # Try numeric parse — raw count like "675000000000"
                try:
                    count = float(raw)
                    if count >= 1_000_000_000_000:
                        model["parameter_size"] = f"{count / 1_000_000_000_000:.0f}T"
                    elif count >= 1_000_000_000:
                        model["parameter_size"] = f"{count / 1_000_000_000:.0f}B"
                    elif count >= 1_000_000:
                        model["parameter_size"] = f"{count / 1_000_000:.0f}M"
                    else:
                        model["parameter_size"] = raw  # too small to simplify
                except (ValueError, TypeError):
                    model["parameter_size"] = raw  # leave as-is

        # --- quantization normalization ---
        # Seed uses "quantization_level", live API uses "quantization"
        quant = model.get("quantization", "") or model.get("quantization_level", "")
        model["quantization"] = quant.upper() if quant else ""
        # Remove the duplicate key if both existed
        model.pop("quantization_level", None)

        # --- size normalization ---
        size = model.get("size", 0) or model.get("size_bytes", 0)
        if size and size > 0:
            model["size"] = size
            model["size_bytes"] = size
        else:
            model["size"] = 0
            model["size_bytes"] = 0

        # --- capabilities normalization ---
        caps = model.get("capabilities", [])
        # "completion" is the registry's only cap — translate to "chat"
        if caps == ["completion"] or not caps:
            caps = ["chat"]

        # Infer "code" capability from model name for code-specialized models
        name_lower = model.get("name", "").lower()
        if any(pat in name_lower for pat in OllamaCatalogService._CODE_NAME_PATTERNS) and "code" not in caps:
            caps.append("code")

        # Detect embedding capability from model name
        if (
            "embedding" not in caps
            and any(p in name_lower for p in OllamaCatalogService.EMBEDDING_NAME_PATTERNS)
            and ("embed" in name_lower or "bert" in name_lower or "bge" in name_lower)
        ):
            caps.append("embedding")

        model["capabilities"] = caps

        # Parse embedding dimension if model supports embeddings
        if "embedding" in caps:
            dim = OllamaCatalogService._parse_embedding_dim(model.get("parameters"))
            if not dim:
                dim = OllamaCatalogService._get_embedding_dim_fallback(model.get("name", ""))
            model["embedding_dim"] = dim
            model["capabilities"] = [c for c in caps if c != "chat"]
        else:
            model["embedding_dim"] = None

        # Parse context length from parameters if available
        if "parameters" in model:
            num_ctx = OllamaCatalogService._parse_num_ctx(model.get("parameters", ""))
            if num_ctx:
                model["context_length"] = num_ctx

        return model

    @staticmethod
    def _normalize_all(models: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Normalize all models in the catalog and remove cloud-only models.

        Cloud models (names ending in ``-cloud``) are Ollama cloud-hosted
        inference endpoints that cannot be downloaded locally.
        """
        normalized: list[dict[str, Any]] = []
        for model in models:
            name = model.get("name", "")
            # Skip cloud-only models — they can't be downloaded locally
            if name.endswith("-cloud") or name.endswith(":cloud"):
                continue
            normalized.append(OllamaCatalogService._normalize_model(model))
        return normalized

    @staticmethod
    def _detect_capabilities(template: str, model_name: str = "") -> list[str]:
        """Detect capabilities from a template blob and model name.

        Args:
            template: The template text content.
            model_name: The model name for name-based capability inference.

        Returns:
            List of capability strings ("tools", "vision", "thinking", "embedding").
        """
        capabilities: list[str] = []

        if template:
            if any(marker in template for marker in TOOL_MARKERS):
                capabilities.append("tools")

            if any(marker in template for marker in VISION_MARKERS):
                capabilities.append("vision")

            if any(marker in template for marker in THINKING_MARKERS):
                capabilities.append("thinking")

        # Detect embedding from model name
        if model_name:
            name_lower = model_name.lower()
            if any(p in name_lower for p in OllamaCatalogService.EMBEDDING_NAME_PATTERNS) and (
                "embed" in name_lower or "bert" in name_lower or "bge" in name_lower
            ):
                capabilities.append("embedding")

        return capabilities

    @staticmethod
    def _parse_num_ctx(parameters: str | None) -> int | None:
        """Parse num_ctx from Ollama parameters blob.

        Args:
            parameters: The parameters blob text (e.g. "num_ctx=8192\\ntemperature=0.7").

        Returns:
            The context length as int, or None if not found.
        """
        if not parameters:
            return None
        match = re.search(r"num_ctx[=\s]+(\d+)", parameters)
        return int(match.group(1)) if match else None

    @staticmethod
    def _parse_embedding_dim(parameters: str | None) -> int | None:
        """Parse embedding dimension from Ollama parameters blob.

        Args:
            parameters: The parameters blob text.

        Returns:
            The embedding dimension as int, or None if not found.
        """
        if not parameters:
            return None
        for pattern in [r"embedding_dim[=\s]+(\d+)", r"hidden_size[=\s]+(\d+)", r"n_embd[=\s]+(\d+)"]:
            match = re.search(pattern, parameters)
            if match:
                return int(match.group(1))
        return None

    @staticmethod
    def _get_embedding_dim_fallback(model_name: str) -> int | None:
        """Get known embedding dimension for a model by name lookup.

        Args:
            model_name: The model name to look up.

        Returns:
            Known embedding dimension, or None if not found.
        """
        name_lower = model_name.lower()
        for key, dim in OllamaCatalogService.KNOWN_EMBEDDING_DIMS.items():
            if key in name_lower:
                return dim
        return None

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
            entry["capabilities"] = OllamaCatalogService._detect_capabilities(template, name)

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

    def _save_fallback(self, models: list[dict[str, Any]]) -> None:
        """Save catalog to fallback file after successful fetch."""
        try:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            data = {
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "models": models,
            }
            with open(FALLBACK_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.debug("Saved fallback catalog (%d models)", len(models))
        except OSError as e:
            logger.warning("Failed to save fallback catalog: %s", e)

    def _load_fallback(self) -> list[dict[str, Any]] | None:
        """Load catalog from fallback file."""
        try:
            if FALLBACK_FILE.exists():
                with open(FALLBACK_FILE, encoding="utf-8") as f:
                    data = json.load(f)
                models = data.get("models", [])
                logger.info("Loaded fallback catalog (%d models)", len(models))
                return models
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Failed to load fallback catalog: %s", e)
        return None

    def fetch_catalog_sync(self, force_refresh: bool = False) -> tuple[list[dict[str, Any]], CatalogSourceStatus]:
        """Sync wrapper for backward compatibility.

        Runs fetch_catalog in a new event loop if no loop is running,
        otherwise creates a task.

        Args:
            force_refresh: If True, bypass cache and fetch fresh data.

        Returns:
            Tuple of (models list, source status).
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
) -> tuple[list[dict[str, Any]], CatalogSourceStatus]:
    """Async convenience function to get the Ollama catalog.

    Args:
        force_refresh: If True, bypass cache and fetch fresh data.

    Returns:
        Tuple of (models list, source status).
    """
    return await get_catalog_service().fetch_catalog(force_refresh=force_refresh)


def get_ollama_catalog_sync(
    force_refresh: bool = False,
) -> tuple[list[dict[str, Any]], CatalogSourceStatus]:
    """Sync convenience function to get the Ollama catalog.

    Args:
        force_refresh: If True, bypass cache and fetch fresh data.

    Returns:
        Tuple of (models list, source status).
    """
    return get_catalog_service().fetch_catalog_sync(force_refresh=force_refresh)
