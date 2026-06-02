from abc import ABC, abstractmethod


class BaseLLM(ABC):
    """
    Unified interface for all LLM providers (local or API).
    """

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None
    ) -> str:
        raise NotImplementedError