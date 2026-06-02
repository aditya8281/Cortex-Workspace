from backend.app.ai.api_llm import APILLM
from backend.app.ai.local_llm import LocalLLM

from backend.app.ai.config import ai_settings


class ProviderRegistry:

    @staticmethod
    def get_provider():

        mode = ai_settings.mode.lower()

        if mode == "api":

            return APILLM(
                api_key=ai_settings.api_key,
                base_url=ai_settings.api_url,
                model=ai_settings.model,
            )

        if mode == "local":

            return LocalLLM(
                model=ai_settings.local_model
            )

        raise ValueError(
            f"Unsupported AI mode: {mode}"
        )