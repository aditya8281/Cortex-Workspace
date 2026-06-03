import httpx
from backend.app.ai.base import BaseLLM


class APILLM(BaseLLM):
    """
    External LLM provider (OpenAI / Claude / compatible APIs)
    """

    def __init__(self, api_key: str, base_url: str, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model

    async def generate(self, prompt: str, system_prompt: str | None = None, model: str | None = None) -> str:
        model_name = model or self.model
        if model_name == "Qwen3 8B (Q4_K_M quantization)":
            model_name = "qwen3:8b"

        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt or "You are a helpful AI assistant."},
                {"role": "user", "content": prompt}
            ]
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(self.base_url, json=payload, headers=headers)

        response.raise_for_status()
        data = response.json()

        return data["choices"][0]["message"]["content"]