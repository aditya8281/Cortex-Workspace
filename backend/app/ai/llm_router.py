from backend.app.ai.api_llm import APILLM
from backend.app.ai.local_llm import LocalLLM

from backend.app.ai.config import ai_settings


class LLMRouter:
    """
    Routes requests to either Local LLM or API LLM.
    """

    def __init__(self):

        if ai_settings.mode == "api":

            self.llm = APILLM(
                api_key=ai_settings.api_key,
                base_url=ai_settings.api_url,
                model=ai_settings.model,
            )

        else:

            self.llm = LocalLLM(
                model=ai_settings.local_model
            )

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> str:

        return await self.llm.generate(
            prompt,
            system_prompt,
        )