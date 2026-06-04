from backend.app.ai.api_llm import APILLM
from backend.app.ai.local_llm import LocalLLM

from backend.app.ai.config import ai_settings


class ProviderRegistry:

    @staticmethod
    def get_provider():

        mode = ai_settings.mode.lower()

        if mode == "api":
            api_key = ai_settings.api_key or ai_settings.get_model_api_key("openai")
            base_url = ai_settings.api_url
            if not base_url:
                cloud_config = ai_settings.get_cloud_provider_config("openai") or {}
                base_url = cloud_config.get("api_url") or cloud_config.get("base_url")
            if not api_key:
                raise ValueError("API key is required when AI mode is set to 'api'")
            if not base_url:
                raise ValueError("API base URL is required when AI mode is set to 'api'")

            return APILLM(
                api_key=api_key,
                base_url=base_url,
                model=ai_settings.model,
            )

        if mode == "local":

            return LocalLLM(
                model=ai_settings.local_model
            )

        raise ValueError(
            f"Unsupported AI mode: {mode}"
        )
