from backend.app.ai.providers.registry import (
    ProviderRegistry,
)


class LLMRouter:

    def __init__(self):

        self.llm = (
            ProviderRegistry.get_provider()
        )

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        model: str | None = None,
        inference_engine: str | None = None,
        api_key: str | None = None,
        api_base_url: str | None = None
    ) -> str:

        llm = self.llm
        if inference_engine:
            engine_lower = inference_engine.lower()
            if "ollama" in engine_lower:
                from backend.app.ai.local_llm import LocalLLM
                from backend.app.ai.config import ai_settings
                llm = LocalLLM(model=model or ai_settings.local_model)
            elif "api" in engine_lower or "openai" in engine_lower:
                from backend.app.ai.api_llm import APILLM
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

        return await llm.generate(
            prompt,
            system_prompt,
            model=model
        )