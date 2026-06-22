from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from backend.app.core.config import settings
from backend.app.services.llm.provider import LLMModelInfo, LLMProvider

logger = logging.getLogger(__name__)


class OllamaProvider(LLMProvider):
    def __init__(self, base_url: str = "http://localhost:11434"):
        self._base_url = base_url.rstrip("/")
        timeout = getattr(settings, "LLM_TIMEOUT", 120.0)
        self._client = httpx.AsyncClient(base_url=self._base_url, timeout=timeout)

    async def chat(self, messages: list[dict], tools: list[dict], config: Any) -> tuple[str, list[dict] | None]:
        model = "llama3.2"
        if isinstance(config, dict) and "model" in config:
            model = config["model"]
        elif tools:
            models = self.list_models()
            if models:
                model = models[0]["name"]

        formatted = [{"role": m["role"], "content": m["content"]} for m in messages]
        resp = await self._client.post(
            "/api/chat",
            json={
                "model": model,
                "messages": formatted,
                "stream": False,
                "options": {
                    "num_predict": (config or {}).get("max_tokens", 2048),
                    "temperature": (config or {}).get("temperature", 0.7),
                },
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data["message"]["content"], None

    async def chat_direct(
        self,
        messages: list,
        model: str | None = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> dict:
        model = model or await self._default_model()
        formatted = [{"role": m.role, "content": m.content} for m in messages]
        resp = await self._client.post(
            "/api/chat",
            json={
                "model": model,
                "messages": formatted,
                "stream": False,
                "options": {"num_predict": max_tokens, "temperature": temperature},
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return {
            "content": data["message"]["content"],
            "model": model,
            "tokens_prompt": data.get("prompt_eval_count", 0),
            "tokens_completion": data.get("eval_count", 0),
            "finish_reason": "stop",
        }

    async def chat_stream(self, messages: list, tools: list, config: Any):
        model = "llama3.2"
        if isinstance(config, dict) and "model" in config:
            model = config["model"]
        formatted = [{"role": m["role"], "content": m["content"]} for m in messages]
        async with self._client.stream(
            "POST",
            "/api/chat",
            json={
                "model": model,
                "messages": formatted,
                "stream": True,
                "options": {
                    "num_predict": (config or {}).get("max_tokens", 2048),
                    "temperature": (config or {}).get("temperature", 0.7),
                },
            },
        ) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if line:
                    chunk = json.loads(line)
                    if "message" in chunk and "content" in chunk["message"]:
                        yield chunk["message"]["content"]

    def list_models(self) -> list[dict[str, Any]]:
        for attempt in range(3):
            try:
                resp = httpx.get(f"{self._base_url}/api/tags", timeout=5.0)
                resp.raise_for_status()
                data = resp.json()
                models = []
                for m in data.get("models", []):
                    name = m["name"]
                    quantization = self._parse_quantization(name)
                    models.append(
                        {
                            "name": name,
                            "size_bytes": m.get("size", 0),
                            "quantization": quantization,
                            "context_length": 4096,
                            "capabilities": self._infer_capabilities(name),
                            "description": f"Ollama model: {name}",
                        }
                    )
                return models
            except Exception:
                if attempt == 2:
                    logger.warning("Failed to list Ollama models after 3 attempts", exc_info=True)
                    return []
        return []

    def _parse_quantization(self, name: str) -> str | None:
        """Parse quantization from Ollama model tag."""
        name_lower = name.lower()
        for q in ["q4_k_m", "q5_k_m", "q8_0", "q4_k_s", "q5_k_s", "q6_k", "f16", "f32", "q4_0", "q3_k_m", "iq4_xs"]:
            if q in name_lower:
                return q.upper()
        return None

    async def list_models_async(self) -> list[LLMModelInfo]:
        for attempt in range(3):
            try:
                resp = await self._client.get("/api/tags")
                resp.raise_for_status()
                data = resp.json()
                models = []
                for m in data.get("models", []):
                    name = m["name"]
                    quantization = self._parse_quantization(name)
                    models.append(
                        LLMModelInfo(
                            name=name,
                            size_bytes=m.get("size", 0),
                            quantization=quantization,
                            context_length=4096,
                            capabilities=self._infer_capabilities(name),
                            description=f"Ollama model: {name}",
                        )
                    )
                return models
            except Exception:
                if attempt == 2:
                    logger.warning("Failed to list Ollama models (async) after 3 attempts", exc_info=True)
                    return []
        return []

    async def is_available(self) -> bool:
        for attempt in range(3):
            try:
                resp = await self._client.get("/api/tags")
                return resp.status_code == 200
            except Exception:
                if attempt == 2:
                    return False
        return False

    def provider_name(self) -> str:
        return "ollama"

    async def _default_model(self) -> str:
        models = self.list_models()
        return models[0]["name"] if models else "llama3.2"

    def _infer_capabilities(self, name: str) -> list[str]:
        name_lower = name.lower()
        caps = ["chat"]
        if any(x in name_lower for x in ["code", "coder", "starcoder", "deepseek"]):
            caps.append("code")
        if any(x in name_lower for x in ["vision", "llava", "bakllava"]):
            caps.append("vision")
        if any(x in name_lower for x in ["embed", "nomic", "bge"]):
            caps.append("embedding")
        if any(x in name_lower for x in ["reason", "phi", "qwen"]):
            caps.append("reasoning")
        return caps
