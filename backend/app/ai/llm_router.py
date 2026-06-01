import os

from backend.app.ai.local_llm import LocalLLM
from backend.app.ai.api_llm import APILLM


class LLMRouter:
    """
    Routes requests to either Local LLM or API LLM based on config.
    """

    def __init__(self):
        self.mode = os.getenv("AI_MODE", "local")

        if self.mode == "api":
            self.llm = APILLM(
                api_key=os.getenv("AI_API_KEY"),
                base_url=os.getenv("AI_API_URL"),
                model=os.getenv("AI_MODEL", "gpt-4o-mini")
            )
        else:
            self.llm = LocalLLM(
                model=os.getenv("LOCAL_MODEL", "llama3")
            )

    async def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        return await self.llm.generate(prompt, system_prompt)