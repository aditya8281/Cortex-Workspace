import logging
from typing import Any

from backend.app.ai.providers.registry import ProviderRegistry
from backend.app.ai.providers.http_clients import (
    build_provider_llm,
    normalize_provider_name,
    provider_default_base_url,
)
from backend.app.db.session import SessionLocal
from backend.app.models.llm_model import CortexProvider, CortexModel
from backend.app.ai.model_registry import retrieve_key_securely
from backend.app.ai.local_llm import LocalLLM
from backend.app.ai.api_llm import APILLM

logger = logging.getLogger(__name__)


class LLMRouter:

    def __init__(self):
        # Default fallback provider
        self.fallback_llm = ProviderRegistry.get_provider()

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        model: str | None = None,
        inference_engine: str | None = None,
        api_key: str | None = None,
        api_base_url: str | None = None
    ) -> str:
        llm: Any = None
        db = SessionLocal()
        key: str | None = None
        base_url: str | None = None
        
        try:
            model_name = model
            if model_name:
                # 1. Resolve from database
                db_model = db.query(CortexModel).filter(CortexModel.name == model_name).first()
                if db_model:
                    if db_model.is_local:
                        if db_model.provider_name.lower() == "lm studio" or db_model.provider_name.lower() == "lm-studio":
                            llm = APILLM(
                                api_key="lm-studio",
                                base_url="http://localhost:1234/v1",
                                model=model_name
                            )
                        else:
                            llm = LocalLLM(model=model_name)
                    else:
                        provider = db.query(CortexProvider).filter(CortexProvider.name == db_model.provider_name).first()
                        if provider:
                            if not provider.is_enabled:
                                raise ValueError(f"Provider {provider.name} is disabled. Enable it in Models settings.")
                            key = api_key or retrieve_key_securely(provider.name, provider.api_key_encrypted)
                            base_url = api_base_url or provider.base_url or provider_default_base_url(provider.name)
                            
                            if not key:
                                raise ValueError(f"API Key is missing for provider {provider.name}")
                            if not base_url:
                                raise ValueError(f"Base URL is missing for provider {provider.name}")
                            llm = build_provider_llm(provider.name, api_key=key, base_url=base_url, model=model_name)
                else:
                    # Let's check if the model name contains a provider prefix (e.g. "openai/gpt-4o")
                    # or is detected in local tags
                    if "/" in model_name:
                        parts = model_name.split("/", 1)
                        prov_name = parts[0]
                        mod_name = parts[1]
                        provider = db.query(CortexProvider).filter(CortexProvider.name.ilike(normalize_provider_name(prov_name))).first()
                        if provider and provider.is_enabled:
                            key = api_key or retrieve_key_securely(provider.name, provider.api_key_encrypted)
                            base_url = api_base_url or provider.base_url or provider_default_base_url(provider.name)
                            if key and base_url:
                                llm = build_provider_llm(provider.name, api_key=key, base_url=base_url, model=mod_name)
        except Exception as e:
            logger.warning(f"Failed to route model {model} through registry, falling back: {e}")
        finally:
            db.close()

        # 2. Fall back to manual parameters if passed
        if llm is None and inference_engine:
            engine_lower = inference_engine.lower()
            if "ollama" in engine_lower:
                llm = LocalLLM(model=model or "")
            elif "api" in engine_lower or "openai" in engine_lower:
                from backend.app.ai.config import ai_settings
                key = api_key or ai_settings.api_key
                base_url = api_base_url or ai_settings.api_url
                if not key:
                    raise ValueError("API Key is required for External API engine")
                if not base_url:
                    raise ValueError("API Base URL is required for External API engine")
                llm = APILLM(
                    api_key=key,
                    base_url=base_url,
                    model=model or ai_settings.model
                )

        # 3. Final default fallback
        if llm is None:
            llm = self.fallback_llm

        return await llm.generate(
            prompt,
            system_prompt,
            model=model
        )
