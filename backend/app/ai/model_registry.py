from __future__ import annotations

import json
import httpx
import hashlib
import base64
import logging
import re
import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import keyring
from cryptography.fernet import Fernet

from backend.app.core.config import settings
from backend.app.models.llm_model import CortexProvider, CortexModel, CortexRoutingProfile, CortexTaskRoute
from backend.app.ai.providers.http_clients import (
    build_provider_llm,
    list_provider_models,
    normalize_provider_name,
    provider_default_base_url,
)
from backend.app.ai.model_entity import ModelEntity, ModelEntityBuilder, ProviderType, ModelSource

logger = logging.getLogger(__name__)
MODEL_REGISTRY_CACHE_FILENAME = "model_registry_cache.json"

def get_fernet() -> Fernet:
    key_hash = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(key_hash)
    return Fernet(fernet_key)

def store_key_securely(provider_name: str, key_val: str) -> Optional[bytes]:
    if not key_val:
        try:
            keyring.delete_password("cortex-workspace", provider_name)
        except Exception:
            pass
        return None
    try:
        keyring.set_password("cortex-workspace", provider_name, key_val)
        return None
    except Exception as e:
        logger.warning(f"Keyring failed to save key for {provider_name}, falling back to encryption: {e}")
        f = get_fernet()
        return f.encrypt(key_val.encode())

def retrieve_key_securely(provider_name: str, encrypted_bytes: Optional[bytes]) -> str:
    try:
        val = keyring.get_password("cortex-workspace", provider_name)
        if val:
            return val
    except Exception:
        pass
    if not encrypted_bytes:
        return ""
    try:
        f = get_fernet()
        return f.decrypt(encrypted_bytes).decode()
    except Exception:
        return ""


class ModelRegistry:
    @staticmethod
    def _cache_path():
        from backend.app.services.memory_manager import memory_manager

        return memory_manager.get_path("cache", MODEL_REGISTRY_CACHE_FILENAME)

    @classmethod
    def _load_cache(cls) -> dict[str, Any]:
        cache_path = cls._cache_path()
        if not cache_path.exists():
            return {}
        try:
            return json.loads(cache_path.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.warning("Failed to load cached model registry snapshot: %s", exc)
            return {}

    @classmethod
    def _save_cache(cls, **payload: Any) -> None:
        cache_path = cls._cache_path()
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        snapshot = {
            "updated_at": datetime.now(timezone.utc).isoformat(),
            **payload,
        }
        try:
            cache_path.write_text(json.dumps(snapshot, indent=2, sort_keys=True), encoding="utf-8")
        except Exception as exc:
            logger.warning("Failed to persist model registry snapshot: %s", exc)

    @staticmethod
    def _matches_marketplace_query(model: Dict[str, Any], query: str) -> bool:
        if not query:
            return True
        needle = query.strip().lower()
        if not needle:
            return True

        fields = [
            model.get("name"),
            model.get("display_name"),
            model.get("best_use_case"),
            model.get("source"),
        ]
        for field in fields:
            if isinstance(field, str) and needle in field.lower():
                return True

        for tag in model.get("tags", []) or []:
            if isinstance(tag, str) and needle in tag.lower():
                return True

        for capability in model.get("capabilities", []) or []:
            if isinstance(capability, str) and needle in capability.lower():
                return True

        return False

    @classmethod
    async def prime_ollama_inventory_cache(cls) -> dict[str, Any]:
        """
        Warm the Ollama inventory so app start/reload has an immediate cached catalog.
        """
        local_models, marketplace_models = await asyncio.gather(
            cls.get_local_models(),
            cls.get_dynamic_ollama_marketplace(),
        )
        return {
            "local_models": local_models,
            "marketplace_models": marketplace_models,
        }

    @classmethod
    def seed_if_empty(cls, db: Session):
        if db.query(CortexProvider).first() is None:
            default_providers = [
                {"name": "OpenAI", "base_url": "https://api.openai.com/v1", "is_custom": False},
                {"name": "Anthropic", "base_url": "https://api.anthropic.com/v1", "is_custom": False},
                {"name": "Google Gemini", "base_url": "https://generativelanguage.googleapis.com/v1beta", "is_custom": False},
                {"name": "OpenRouter", "base_url": "https://openrouter.ai/api/v1", "is_custom": False},
                {"name": "Groq", "base_url": "https://api.groq.com/openai/v1", "is_custom": False},
                {"name": "Together AI", "base_url": "https://api.together.xyz/v1", "is_custom": False},
                {"name": "DeepSeek", "base_url": "https://api.deepseek.com/v1", "is_custom": False},
            ]
            for p in default_providers:
                provider = CortexProvider(
                    name=p["name"],
                    base_url=p["base_url"],
                    is_enabled=False,
                    is_custom=p["is_custom"],
                    default_model_name=None,
                )
                db.add(provider)
            db.commit()

            default_models = [
                # OpenAI
                {"name": "gpt-4o-mini", "provider_name": "OpenAI", "context_length": 128000, "parameters": "8B", "quantization": "None", "vram_estimate": "N/A", "is_local": False},
                {"name": "gpt-4o", "provider_name": "OpenAI", "context_length": 128000, "parameters": "unknown", "quantization": "None", "vram_estimate": "N/A", "is_local": False},
                # Anthropic
                {"name": "claude-3-5-sonnet-latest", "provider_name": "Anthropic", "context_length": 200000, "parameters": "unknown", "quantization": "None", "vram_estimate": "N/A", "is_local": False},
                {"name": "claude-3-5-haiku-latest", "provider_name": "Anthropic", "context_length": 200000, "parameters": "unknown", "quantization": "None", "vram_estimate": "N/A", "is_local": False},
                # Google
                {"name": "gemini-1.5-flash", "provider_name": "Google Gemini", "context_length": 1048576, "parameters": "unknown", "quantization": "None", "vram_estimate": "N/A", "is_local": False},
                {"name": "gemini-1.5-pro", "provider_name": "Google Gemini", "context_length": 2097152, "parameters": "unknown", "quantization": "None", "vram_estimate": "N/A", "is_local": False},
                # Groq
                {"name": "llama3-70b-8192", "provider_name": "Groq", "context_length": 8192, "parameters": "70B", "quantization": "None", "vram_estimate": "N/A", "is_local": False},
                {"name": "mixtral-8x7b-32768", "provider_name": "Groq", "context_length": 32768, "parameters": "45B", "quantization": "None", "vram_estimate": "N/A", "is_local": False},
                # DeepSeek
                {"name": "deepseek-chat", "provider_name": "DeepSeek", "context_length": 64000, "parameters": "unknown", "quantization": "None", "vram_estimate": "N/A", "is_local": False},
                {"name": "deepseek-coder", "provider_name": "DeepSeek", "context_length": 64000, "parameters": "unknown", "quantization": "None", "vram_estimate": "N/A", "is_local": False},
            ]
            for m in default_models:
                model = CortexModel(
                    name=m["name"],
                    provider_name=m["provider_name"],
                    context_length=m["context_length"],
                    parameters=m["parameters"],
                    quantization=m["quantization"],
                    vram_estimate=m["vram_estimate"],
                    status="active",
                    is_local=m["is_local"]
                )
                db.add(model)
            db.commit()

        # Normalize any legacy seed data so provider/model routing stays consistent.
        legacy_google_models = db.query(CortexModel).filter(CortexModel.provider_name == "Google").all()
        if legacy_google_models:
            for row in legacy_google_models:
                row.provider_name = "Google Gemini"
            db.commit()

        # Seed routing profiles and default task routes if empty
        if db.query(CortexRoutingProfile).first() is None:
            # Create profiles
            profiles = [
                {"name": "Balanced", "is_active": True},
                {"name": "Coding Heavy", "is_active": False},
                {"name": "Local Only", "is_active": False},
                {"name": "Maximum Quality", "is_active": False},
                {"name": "Custom", "is_active": False}
            ]
            for p_data in profiles:
                p_obj = CortexRoutingProfile(name=p_data["name"], is_active=p_data["is_active"])
                db.add(p_obj)
            db.commit()

            # Create default mappings per profile
            default_routes = {
                "Balanced": {
                    "chat": ("gpt-4o-mini", "gemini-1.5-flash"),
                    "search": ("gpt-4o-mini", "gemini-1.5-flash"),
                    "coding": ("gpt-4o-mini", "deepseek-coder"),
                    "repository_analysis": ("gpt-4o", "claude-3-5-sonnet-latest"),
                    "architecture_review": ("gpt-4o", "claude-3-5-sonnet-latest"),
                    "planning": ("gpt-4o", "claude-3-5-sonnet-latest"),
                    "research": ("gpt-4o-mini", "gemini-1.5-flash"),
                    "debugging": ("gpt-4o", "deepseek-coder"),
                    "multi_file_modification": ("gpt-4o", "claude-3-5-sonnet-latest"),
                    "long_context": ("gemini-1.5-flash", "gpt-4o-mini"),
                },
                "Coding Heavy": {
                    "chat": ("gpt-4o-mini", "deepseek-chat"),
                    "search": ("gpt-4o-mini", "gemini-1.5-flash"),
                    "coding": ("claude-3-5-sonnet-latest", "deepseek-coder"),
                    "repository_analysis": ("claude-3-5-sonnet-latest", "deepseek-coder"),
                    "architecture_review": ("claude-3-5-sonnet-latest", "gpt-4o"),
                    "planning": ("claude-3-5-sonnet-latest", "gpt-4o"),
                    "research": ("gpt-4o-mini", "claude-3-5-haiku-latest"),
                    "debugging": ("claude-3-5-sonnet-latest", "deepseek-coder"),
                    "multi_file_modification": ("claude-3-5-sonnet-latest", "deepseek-coder"),
                    "long_context": ("claude-3-5-sonnet-latest", "gemini-1.5-pro"),
                },
                "Local Only": {
                    "chat": ("llama3", "mistral"),
                    "search": ("llama3", "mistral"),
                    "coding": ("qwen2.5-coder", "llama3"),
                    "repository_analysis": ("qwen2.5-coder", "llama3"),
                    "architecture_review": ("llama3", "mistral"),
                    "planning": ("llama3", "mistral"),
                    "research": ("llama3", "mistral"),
                    "debugging": ("qwen2.5-coder", "llama3"),
                    "multi_file_modification": ("qwen2.5-coder", "llama3"),
                    "long_context": ("llama3", "mistral"),
                },
                "Maximum Quality": {
                    "chat": ("gpt-4o", "claude-3-5-sonnet-latest"),
                    "search": ("gpt-4o", "gemini-1.5-pro"),
                    "coding": ("claude-3-5-sonnet-latest", "gpt-4o"),
                    "repository_analysis": ("claude-3-5-sonnet-latest", "gemini-1.5-pro"),
                    "architecture_review": ("claude-3-5-sonnet-latest", "gpt-4o"),
                    "planning": ("claude-3-5-sonnet-latest", "gpt-4o"),
                    "research": ("gpt-4o", "claude-3-5-sonnet-latest"),
                    "debugging": ("claude-3-5-sonnet-latest", "gpt-4o"),
                    "multi_file_modification": ("claude-3-5-sonnet-latest", "gpt-4o"),
                    "long_context": ("gemini-1.5-pro", "claude-3-5-sonnet-latest"),
                },
                "Custom": {
                    "chat": ("gpt-4o-mini", "gemini-1.5-flash"),
                    "search": ("gpt-4o-mini", "gemini-1.5-flash"),
                    "coding": ("gpt-4o-mini", "deepseek-coder"),
                    "repository_analysis": ("gpt-4o", "claude-3-5-sonnet-latest"),
                    "architecture_review": ("gpt-4o", "claude-3-5-sonnet-latest"),
                    "planning": ("gpt-4o", "claude-3-5-sonnet-latest"),
                    "research": ("gpt-4o-mini", "gemini-1.5-flash"),
                    "debugging": ("gpt-4o", "deepseek-coder"),
                    "multi_file_modification": ("gpt-4o", "claude-3-5-sonnet-latest"),
                    "long_context": ("gemini-1.5-flash", "gpt-4o-mini"),
                }
            }

            for p_name, routes in default_routes.items():
                for t_type, (prim, fallb) in routes.items():
                    route_obj = CortexTaskRoute(
                        profile_name=p_name,
                        task_type=t_type,
                        primary_model=prim,
                        fallback_model=fallb
                    )
                    db.add(route_obj)
            db.commit()

    @classmethod
    async def get_local_models(cls) -> List[ModelEntity]:
        """
        Fetch local models from Ollama and LM Studio.
        Returns ModelEntity objects with proper error handling.
        Falls back to cache if services are unavailable.
        """
        models: List[ModelEntity] = []
        errors: List[str] = []

        # 1. Ollama (Primary source)
        ollama_url = f"{settings.OLLAMA_URL.rstrip('/')}/api/tags"
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(ollama_url)
                if resp.status_code == 200:
                    data = resp.json()
                    for m in data.get("models", []):
                        try:
                            entity = ModelEntityBuilder.from_ollama_model(m)
                            models.append(entity)
                        except Exception as e:
                            logger.debug(f"Failed to parse Ollama model {m.get('name')}: {e}")
                            continue
                elif resp.status_code == 404:
                    errors.append("Ollama service not found (404) - check OLLAMA_URL configuration")
                elif resp.status_code == 500:
                    errors.append("Ollama service returned 500 - service may be down")
                else:
                    errors.append(f"Ollama returned status {resp.status_code}")
        except asyncio.TimeoutError:
            errors.append("Ollama connection timeout - service may be offline")
            logger.warning("Ollama timeout at %s", ollama_url)
        except Exception as exc:
            errors.append(f"Ollama connection failed: {str(exc)}")
            logger.warning("Failed to fetch Ollama models: %s", exc)

        # 2. LM Studio (Secondary source)
        lm_url = "http://localhost:1234/v1/models"
        try:
            async with httpx.AsyncClient(timeout=3) as client:
                resp = await client.get(lm_url)
                if resp.status_code == 200:
                    data = resp.json()
                    for m in data.get("data", []):
                        try:
                            entity = ModelEntity(
                                id=m.get("id"),
                                display_name=m.get("id"),
                                provider_name="LM Studio",
                                provider_type=ProviderType.LOCAL,
                                source=ModelSource.LM_STUDIO,
                                model_identifier=m.get("id"),
                                context_window=4096,
                                status="active",
                                is_downloaded=True,
                            )
                            models.append(entity)
                        except Exception as e:
                            logger.debug(f"Failed to parse LM Studio model: {e}")
                            continue
        except asyncio.TimeoutError:
            logger.debug("LM Studio timeout - service not available")
        except Exception as exc:
            logger.debug("LM Studio not available: %s", exc)

        # Cache if we have models
        if models:
            local_data = [m.to_dict() for m in models]
            cls._save_cache(local_models=local_data)
            return models

        # Fall back to cache
        cached = cls._load_cache().get("local_models", [])
        if cached:
            logger.info("Using cached local model inventory")
            return [ModelEntity.from_dict(m) for m in cached if isinstance(m, dict)]

        # If still no models, log warnings and return empty (but don't fail)
        if errors:
            logger.warning("No local models available. Errors encountered: %s", "; ".join(errors))

        return models

    @classmethod
    def get_custom_models(cls, db: Session) -> List[ModelEntity]:
        """
        Fetch custom models from the database.
        Custom models are user-defined entries.
        """
        models: List[ModelEntity] = []
        
        try:
            rows = db.query(CortexModel).filter(
                CortexModel.is_custom.is_(True),
                CortexModel.is_local.is_(False),
            ).all()
            
            for row in rows:
                entity = ModelEntity(
                    id=row.name,
                    display_name=row.name,
                    provider_name=row.provider_name or "Custom",
                    provider_type=ProviderType.CUSTOM,
                    source=ModelSource.CUSTOM_API,
                    model_identifier=row.model_identifier or row.name,
                    context_window=row.context_length or 8192,
                    parameters=row.parameters,
                    quantization=row.quantization,
                    vram_estimate=row.vram_estimate,
                    status=row.status,
                    api_endpoint=row.api_endpoint,
                    is_custom=True,
                )
                models.append(entity)
        except Exception as exc:
            logger.warning("Failed to fetch custom models: %s", exc)
        
        return models

    @classmethod
    async def get_cloud_models(cls, db: Session) -> List[ModelEntity]:
        """
        Fetch cloud models from enabled providers.
        Only returns models from providers that:
        1. Are enabled
        2. Have valid API keys configured
        """
        models: List[ModelEntity] = []
        providers = db.query(CortexProvider).filter(CortexProvider.is_enabled.is_(True)).all()
        
        for provider in providers:
            # Skip local providers
            if provider.provider_type == "local" or provider.name in {"Ollama", "LM Studio"}:
                continue
            
            # Check if provider has API key
            api_key = retrieve_key_securely(provider.name, provider.api_key_encrypted)
            if not api_key:
                logger.debug(f"Skipping {provider.name} - no API key configured")
                continue
            
            try:
                # Fetch models from provider
                provider_models = await asyncio.wait_for(
                    cls._refresh_provider_models(db, provider),
                    timeout=10,
                )
                
                # Convert to ModelEntity objects
                for model_data in provider_models:
                    try:
                        # Map source name
                        source = cls._get_model_source(provider.name)
                        entity = ModelEntityBuilder.from_cloud_model(
                            model_data,
                            provider.name,
                            source
                        )
                        models.append(entity)
                    except Exception as e:
                        logger.debug(f"Failed to parse model from {provider.name}: {e}")
                        continue
            except asyncio.TimeoutError:
                logger.warning(f"Timeout fetching models from {provider.name}")
                # Fall back to cached models
                try:
                    cached_models = db.query(CortexModel).filter(
                        CortexModel.provider_name == provider.name,
                        CortexModel.is_local.is_(False),
                    ).all()
                    for row in cached_models:
                        entity = ModelEntity(
                            id=row.name,
                            display_name=row.name,
                            provider_name=row.provider_name,
                            provider_type=ProviderType.CLOUD,
                            source=cls._get_model_source(provider.name),
                            model_identifier=row.model_identifier or row.name,
                            context_window=row.context_length or 8192,
                            status=row.status,
                            api_key_required=True,
                        )
                        models.append(entity)
                except Exception as e:
                    logger.debug(f"Failed to load cached models for {provider.name}: {e}")
            except Exception as exc:
                logger.warning(f"Failed to fetch models from {provider.name}: {exc}")
                # Fall back to cached models
                try:
                    cached_models = db.query(CortexModel).filter(
                        CortexModel.provider_name == provider.name,
                        CortexModel.is_local.is_(False),
                    ).all()
                    for row in cached_models:
                        entity = ModelEntity(
                            id=row.name,
                            display_name=row.name,
                            provider_name=row.provider_name,
                            provider_type=ProviderType.CLOUD,
                            source=cls._get_model_source(provider.name),
                            model_identifier=row.model_identifier or row.name,
                            context_window=row.context_length or 8192,
                            status=row.status,
                            api_key_required=True,
                        )
                        models.append(entity)
                except Exception as e:
                    logger.debug(f"Failed to load cached models for {provider.name}: {e}")
        
        return models

    @staticmethod
    def _get_model_source(provider_name: str) -> ModelSource:
        """Map provider name to ModelSource enum"""
        mapping = {
            "OpenAI": ModelSource.OPENAI,
            "Anthropic": ModelSource.ANTHROPIC,
            "Google Gemini": ModelSource.GOOGLE_GEMINI,
            "Groq": ModelSource.GROQ,
            "Together AI": ModelSource.TOGETHER_AI,
            "OpenRouter": ModelSource.OPENROUTER,
            "DeepSeek": ModelSource.DEEPSEEK,
        }
        return mapping.get(provider_name, ModelSource.CUSTOM_API)

    @classmethod
    async def get_dynamic_ollama_marketplace(cls, query: str | None = None, max_pages: int = 100) -> List[Dict[str, Any]]:
        """
        Scrape the public Ollama registry so the marketplace stays dynamic.
        The registry is paginated; we walk pages until they stop yielding models.
        """
        url = "https://registry.ollama.com/search"
        collected: list[dict[str, Any]] = []
        seen: set[str] = set()

        async with httpx.AsyncClient(timeout=5, follow_redirects=True) as client:
            for page in range(1, max_pages + 1):
                params: dict[str, Any] = {"page": page}
                if query:
                    params["q"] = query

                try:
                    response = await client.get(url, params=params)
                    response.raise_for_status()
                except Exception as exc:
                    logger.warning("Failed to fetch Ollama registry page %s: %s", page, exc)
                    break

                html = response.text
                matches = list(
                    re.finditer(
                        r'<li[^>]*x-test-model[^>]*>.*?<a href="/library/(?P<slug>[^"]+)"[^>]*>.*?'
                        r'<span[^>]*x-test-search-response-title[^>]*>(?P<name>.*?)</span>.*?'
                        r'<p class="max-w-lg break-words text-neutral-800 text-md">(?P<desc>.*?)</p>.*?'
                        r'(?P<tags>(?:<span[^>]*x-test-capability[^>]*>.*?</span>|<span class="inline-flex my-1 items-center rounded-md bg-cyan-50[^>]*>.*?</span>|<span[^>]*x-test-size[^>]*>.*?</span>)+)',
                        html,
                        re.S,
                    )
                )

                if not matches:
                    break

                for match in matches:
                    slug = match.group("slug").strip()
                    if slug in seen:
                        continue
                    seen.add(slug)

                    tag_blob = match.group("tags")
                    capabilities = re.findall(r"x-test-capability[^>]*>(.*?)</span>", tag_blob, re.S)
                    capabilities = [re.sub(r"<.*?>", "", cap).strip() for cap in capabilities if cap.strip()]
                    sizes = re.findall(r"x-test-size[^>]*>(.*?)</span>", tag_blob, re.S)
                    sizes = [re.sub(r"<.*?>", "", size).strip() for size in sizes if size.strip()]

                    size_label = ", ".join(sizes[:3]) if sizes else "various"
                    largest_size = cls._largest_size_value(sizes)
                    vram_estimate = cls._estimate_vram_from_size(largest_size)
                    performance_tier = cls._performance_tier(sizes, capabilities)

                    collected.append(
                        {
                            "name": slug,
                            "display_name": re.sub(r"<.*?>", "", match.group("name")).strip(),
                            "size": size_label,
                            "parameters": size_label,
                            "context_length": cls._context_hint_from_capabilities(capabilities),
                            "vram_requirement_gb": vram_estimate,
                            "best_use_case": re.sub(r"<.*?>", "", match.group("desc")).strip(),
                            "tags": cls._marketplace_tags(capabilities),
                            "pull_command": f"ollama pull {slug}",
                            "vram_estimate": f"~{vram_estimate} GB",
                            "performance_tier": performance_tier,
                            "capabilities": capabilities,
                            "source": "Ollama Registry",
                            "is_installed": False,
                            "download_status": "available",
                        }
                    )

        if collected:
            if query:
                cached = cls._load_cache().get("marketplace_models", [])
                cached_by_name = {
                    model.get("name"): model
                    for model in cached
                    if isinstance(model, dict) and model.get("name")
                }
                for model in collected:
                    if isinstance(model, dict) and model.get("name"):
                        cached_by_name[model["name"]] = model
                cls._save_cache(marketplace_models=list(cached_by_name.values()))
            else:
                cls._save_cache(marketplace_models=collected)
            return collected

        cached = cls._load_cache().get("marketplace_models", [])
        if query:
            cached = [model for model in cached if cls._matches_marketplace_query(model, query)]
        if cached:
            logger.info("Using cached Ollama marketplace snapshot")
            return cached

        return []

    @staticmethod
    def _largest_size_value(sizes: List[str]) -> float:
        max_val = 0.0
        for size in sizes:
            cleaned = size.lower().replace("b", "").replace(",", "").strip()
            try:
                max_val = max(max_val, float(cleaned))
            except Exception:
                continue
        return max_val

    @staticmethod
    def _estimate_vram_from_size(size_b: float) -> float:
        if size_b <= 0:
            return 4.0
        # A heuristic estimate that keeps the marketplace useful without pretending
        # to be exact across quantization formats.
        return round(max(2.0, size_b * 1.35), 1)

    @staticmethod
    def _performance_tier(sizes: List[str], capabilities: List[str]) -> str:
        size_b = ModelRegistry._largest_size_value(sizes)
        if "cloud" in {cap.lower() for cap in capabilities}:
            return "cloud"
        if "thinking" in {cap.lower() for cap in capabilities} or size_b >= 30:
            return "high"
        if size_b <= 4:
            return "fast"
        if size_b <= 12:
            return "balanced"
        return "high"

    @staticmethod
    def _marketplace_tags(capabilities: List[str]) -> List[str]:
        tags = []
        cap_lower = {cap.lower() for cap in capabilities}
        if "coding" in cap_lower or "tools" in cap_lower:
            tags.append("Coding")
        if "thinking" in cap_lower:
            tags.append("Reasoning")
        if "vision" in cap_lower:
            tags.append("Vision")
        if "cloud" in cap_lower:
            tags.append("Cloud")
        if not tags:
            tags.append("Chat")
        return tags

    @staticmethod
    def _context_hint_from_capabilities(capabilities: List[str]) -> int:
        cap_lower = {cap.lower() for cap in capabilities}
        if "cloud" in cap_lower:
            return 131072
        if "thinking" in cap_lower:
            return 32768
        if "vision" in cap_lower:
            return 16384
        return 8192

    @classmethod
    def _upsert_provider_models(
        cls,
        db: Session,
        provider_name: str,
        discovered_models: List[Dict[str, Any]],
    ) -> None:
        existing = {
            row.name: row
            for row in db.query(CortexModel).filter(
                CortexModel.provider_name == provider_name,
                CortexModel.is_local.is_(False),
            ).all()
        }
        active_names = {m.get("name") or m.get("id") for m in discovered_models}

        for model_data in discovered_models:
            name = model_data.get("name") or model_data.get("id")
            if not name:
                continue

            row = existing.get(name)
            if row is None:
                row = CortexModel(
                    name=name,
                    provider_name=provider_name,
                    status="active" if model_data.get("active", True) else "unavailable",
                    is_local=False,
                    is_custom=provider_name not in {"OpenAI", "Anthropic", "Google Gemini", "OpenRouter", "Groq", "Together AI", "DeepSeek"},
                )
                db.add(row)

            row.context_length = model_data.get("context_length")
            row.parameters = model_data.get("parameters") or row.parameters
            row.quantization = model_data.get("quantization") or row.quantization
            row.vram_estimate = model_data.get("vram_estimate") or row.vram_estimate
            row.status = "active" if model_data.get("active", True) else "unavailable"

        for row in existing.values():
            if row.name not in active_names:
                row.status = "unavailable"

    @classmethod
    async def _refresh_provider_models(cls, db: Session, provider: CortexProvider) -> List[Dict[str, Any]]:
        api_key = retrieve_key_securely(provider.name, provider.api_key_encrypted)
        base_url = provider.base_url or provider_default_base_url(provider.name) or ""
        if not base_url:
            return []

        try:
            live_models = await list_provider_models(provider.name, base_url, api_key)
        except Exception as exc:
            logger.warning("Provider model sync failed for %s: %s", provider.name, exc)
            return []

        normalized: list[dict[str, Any]] = []
        for model in live_models:
            model_id = model.get("id") or model.get("name")
            if not model_id:
                continue
            normalized.append(
                {
                    "name": model_id,
                    "id": model_id,
                    "provider": provider.name,
                    "context_length": model.get("context_length"),
                    "parameters": model.get("parameters") or "unknown",
                    "quantization": model.get("quantization") or "unknown",
                    "vram_estimate": model.get("vram_estimate") or "N/A",
                    "status": "active" if model.get("active", True) else "unavailable",
                    "is_local": False,
                    "default_for_provider": provider.default_model_name == model_id,
                }
            )

        cls._upsert_provider_models(db, provider.name, normalized)
        db.commit()
        return normalized

    @classmethod
    async def list_models(cls, db: Session) -> List[Dict[str, Any]]:
        """
        List all available models (local, cloud, and custom) from all sources.
        
        Returns a unified list of models with proper source identification.
        Each model includes information about its provider_type and source.
        """
        cls.seed_if_empty(db)
        
        # Auto-enable OpenAI as default provider if no providers are enabled
        cls._auto_enable_default_provider(db)

        # Fetch models from each source separately
        local_entities = await cls.get_local_models()
        cloud_entities = await cls.get_cloud_models(db)
        custom_entities = cls.get_custom_models(db)

        # Combine all models
        all_entities = local_entities + cloud_entities + custom_entities

        # Convert to dictionary format for backward compatibility
        result = []
        for entity in all_entities:
            model_dict = entity.to_dict()
            result.append(model_dict)

        return result

    @classmethod
    def _auto_enable_default_provider(cls, db: Session) -> None:
        """
        Auto-enable at least one provider (OpenAI) if no providers are enabled.
        This ensures users get cloud models by default without manual configuration.
        """
        try:
            enabled_count = db.query(CortexProvider).filter(CortexProvider.is_enabled.is_(True)).count()
            if enabled_count == 0:
                # Enable OpenAI as default if no other provider is enabled
                openai = db.query(CortexProvider).filter(CortexProvider.name == "OpenAI").first()
                if openai and not openai.is_enabled:
                    logger.info("Auto-enabling OpenAI as default provider")
                    openai.is_enabled = True
                    db.commit()
        except Exception as e:
            logger.debug(f"Auto-enable default provider failed: {e}")

    @classmethod
    async def list_models_by_type(cls, db: Session, provider_type: str) -> List[Dict[str, Any]]:
        """
        List models filtered by provider type.
        
        Args:
            provider_type: "local", "cloud", or "custom"
        
        Returns:
            List of model dictionaries for the specified type
        """
        if provider_type == "local":
            entities = await cls.get_local_models()
        elif provider_type == "cloud":
            entities = await cls.get_cloud_models(db)
        elif provider_type == "custom":
            entities = cls.get_custom_models(db)
        else:
            return []

        return [e.to_dict() for e in entities]

    @classmethod
    async def validate_provider(cls, name: str, base_url: str, api_key: str) -> Dict[str, Any]:
        """
        Validate provider endpoint, API key, model list, and run a lightweight completion.
        """
        normalized_name = normalize_provider_name(name)
        if not base_url:
            base_url = provider_default_base_url(normalized_name) or ""
        if not base_url:
            return {"valid": False, "error": "Base URL is required"}

        try:
            models = await asyncio.wait_for(
                list_provider_models(normalized_name, base_url, api_key),
                timeout=10,
            )
        except Exception as exc:
            return {"valid": False, "error": f"Failed to list models: {exc}"}

        test_model = None
        if models:
            test_model = models[0].get("id") or models[0].get("name")

        if not test_model:
            return {
                "valid": False,
                "models": [],
                "default_model": None,
                "error": "Provider did not return any models",
            }

        try:
            llm = build_provider_llm(normalized_name, api_key=api_key, base_url=base_url, model=test_model)
            answer = await asyncio.wait_for(
                llm.generate(
                    prompt="ping",
                    system_prompt="Respond with exactly one short word.",
                    model=test_model,
                ),
                timeout=20,
            )
            return {
                "valid": True,
                "models": [model.get("id") or model.get("name") for model in models if model.get("id") or model.get("name")],
                "default_model": test_model,
                "test_response": answer[:120],
                "error": None,
            }
        except Exception as exc:
            return {
                "valid": False,
                "models": [model.get("id") or model.get("name") for model in models if model.get("id") or model.get("name")],
                "default_model": test_model,
                "error": f"API key accepted, but test completion failed: {exc}",
            }
