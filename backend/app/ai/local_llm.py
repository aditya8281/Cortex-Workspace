import httpx
from backend.app.ai.base import BaseLLM
from backend.app.core.config import settings
from backend.app.ai.exceptions import ModelNotInstalledError


class LocalLLM(BaseLLM):
    """
    Local LLM via Ollama (fully offline option)
    """

    def __init__(self, model: str = "llama3"):
        self.model = model

    async def generate(self, prompt: str, system_prompt: str | None = None, model: str | None = None) -> str:
        full_prompt = prompt

        if system_prompt:
            full_prompt = f"{system_prompt}\n\nUser: {prompt}"

        model_name = model or self.model
        if model_name == "Qwen3 8B (Q4_K_M quantization)":
            model_name = "qwen3:8b"

        payload = {
            "model": model_name,
            "prompt": full_prompt,
            "stream": False
        }

        url = f"{settings.OLLAMA_URL.rstrip('/')}/api/generate"

        async with httpx.AsyncClient(timeout=120) as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    raise ModelNotInstalledError(model_name) from e
                raise e

        data = response.json()

        return data.get("response", "")