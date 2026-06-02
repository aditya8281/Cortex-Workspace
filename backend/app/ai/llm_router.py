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
    ) -> str:

        return await self.llm.generate(
            prompt,
            system_prompt,
        )