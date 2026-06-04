from __future__ import annotations

import httpx
import hashlib
import base64
import logging
import re
import asyncio
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

logger = logging.getLogger(__name__)

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
    async def get_local_models(cls) -> List[Dict[str, Any]]:
        models = []

        # 1. Ollama
        ollama_url = f"{settings.OLLAMA_URL.rstrip('/')}/api/tags"
        try:
            async with httpx.AsyncClient(timeout=3) as client:
                resp = await client.get(ollama_url)
                if resp.status_code == 200:
                    data = resp.json()
                    for m in data.get("models", []):
                        name = m.get("name")
                        details = m.get("details", {})
                        param_size = details.get("parameter_size", "unknown")
                        quant = details.get("quantization_level", "unknown")
                        
                        # VRAM Estimation
                        vram = "unknown"
                        if "B" in param_size:
                            try:
                                size_val = float(param_size.replace("B", ""))
                                vram = f"{round(size_val * 0.7, 1)} GB"
                            except Exception:
                                pass

                        # Context Length Estimation
                        context_len = 8192
                        if "qwen" in name.lower():
                            context_len = 32768
                        elif "llama3" in name.lower():
                            context_len = 8192
                        elif "phi" in name.lower():
                            context_len = 128000

                        models.append({
                            "name": name,
                            "provider": "Ollama",
                            "context_length": context_len,
                            "parameters": param_size,
                            "quantization": quant,
                            "vram_estimate": vram,
                            "status": "active",
                            "is_local": True
                        })
        except Exception:
            pass

        # 2. LM Studio
        lm_url = "http://localhost:1234/v1/models"
        try:
            async with httpx.AsyncClient(timeout=3) as client:
                resp = await client.get(lm_url)
                if resp.status_code == 200:
                    data = resp.json()
                    for m in data.get("data", []):
                        name = m.get("id")
                        models.append({
                            "name": name,
                            "provider": "LM Studio",
                            "context_length": 4096,
                            "parameters": "unknown",
                            "quantization": "unknown",
                            "vram_estimate": "unknown",
                            "status": "active",
                            "is_local": True
                        })
        except Exception:
            pass

        return models

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

        return collected

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
        cls.seed_if_empty(db)

        local_models = await cls.get_local_models()
        for row in local_models:
            row.setdefault("id", row.get("name"))
            row.setdefault("display_name", row.get("name"))
            row.setdefault("pull_command", f"ollama pull {row.get('name')}")
            row.setdefault("tags", ["Chat"])
            row.setdefault("best_use_case", "Local model")
            row.setdefault("performance_tier", "balanced")

        cloud_models: list[dict[str, Any]] = []
        providers = db.query(CortexProvider).all()
        for provider in providers:
            if not provider.is_enabled:
                continue

            try:
                provider_models = await asyncio.wait_for(
                    cls._refresh_provider_models(db, provider),
                    timeout=10,
                )
            except Exception as exc:
                logger.warning("Timed out refreshing provider models for %s: %s", provider.name, exc)
                provider_models = []
            if not provider_models:
                provider_models = []
                for model in db.query(CortexModel).filter(
                    CortexModel.provider_name == provider.name,
                    CortexModel.is_local.is_(False),
                ).all():
                    provider_models.append(
                        {
                            "id": model.name,
                            "name": model.name,
                            "display_name": model.name,
                            "provider": provider.name,
                            "context_length": model.context_length,
                            "parameters": model.parameters,
                            "quantization": model.quantization,
                            "vram_estimate": model.vram_estimate,
                            "status": model.status,
                            "is_local": False,
                            "default_for_provider": provider.default_model_name == model.name,
                        }
                    )

            cloud_models.extend(provider_models)

        return local_models + cloud_models

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
