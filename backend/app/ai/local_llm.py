import httpx
from backend.app.ai.base import BaseLLM


class LocalLLM(BaseLLM):
    """
    Local LLM via Ollama (fully offline option)
    """

    def __init__(self, model: str = "llama3"):
        self.model = model
        self.url = "http://localhost:11434/api/generate"

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

        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(self.url, json=payload)

        response.raise_for_status()
        data = response.json()

        return data.get("response", "")