from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

from backend.app.services.llm.provider import LLMProvider

logger = logging.getLogger(__name__)


class LlamaCppProvider(LLMProvider):
    def __init__(self, model_path: str, n_ctx: int = 4096, n_gpu_layers: int = 0):
        self._model_path = model_path
        self._n_ctx = n_ctx
        self._n_gpu_layers = n_gpu_layers
        self._llama = None
        self._model_lock = asyncio.Lock()
        self._semaphore = asyncio.Semaphore(4)

    async def _ensure_model(self) -> None:
        if self._llama is not None:
            return
        async with self._model_lock:
            if self._llama is not None:
                return
            try:
                from llama_cpp import Llama
            except ImportError:
                raise RuntimeError("llama-cpp-python not installed. Run: pip install llama-cpp-python")
            loop = asyncio.get_running_loop()
            self._llama = await loop.run_in_executor(
                None,
                lambda: Llama(
                    model_path=self._model_path,
                    n_ctx=self._n_ctx,
                    n_gpu_layers=self._n_gpu_layers,
                    verbose=False,
                ),
            )

    async def chat(self, messages: list[dict], tools: list[dict], config: Any) -> tuple[str, list[dict] | None]:
        await self._ensure_model()
        async with self._semaphore:
            loop = asyncio.get_running_loop()
            formatted = [{"role": m["role"], "content": m["content"]} for m in messages]
            max_tokens = 2048
            temperature = 0.7
            if isinstance(config, dict):
                max_tokens = config.get("max_tokens", 2048)
                temperature = config.get("temperature", 0.7)

            result = await loop.run_in_executor(
                None,
                lambda: self._llama.create_chat_completion(
                    messages=formatted,
                    max_tokens=max_tokens,
                    temperature=temperature,
                ),
            )

            choice = result["choices"][0]
            content = choice["message"]["content"]
            tool_calls = None
            if choice["message"].get("tool_calls"):
                tool_calls = choice["message"]["tool_calls"]
            return content, tool_calls

    async def chat_direct(
        self,
        messages: list,
        model: str | None = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> Any:
        await self._ensure_model()
        async with self._semaphore:
            loop = asyncio.get_running_loop()
            formatted = [{"role": m.role, "content": m.content} for m in messages]
            result = await loop.run_in_executor(
                None,
                lambda: self._llama.create_chat_completion(
                    messages=formatted,
                    max_tokens=max_tokens,
                    temperature=temperature,
                ),
            )
            choice = result["choices"][0]
            usage = result.get("usage", {})
            return {
                "content": choice["message"]["content"],
                "model": result.get("model", self._model_path),
                "tokens_prompt": usage.get("prompt_tokens", 0),
                "tokens_completion": usage.get("completion_tokens", 0),
                "finish_reason": choice.get("finish_reason", "stop"),
            }

    async def chat_stream(self, messages: list, tools: list, config: Any):
        await self._ensure_model()
        async with self._semaphore:
            loop = asyncio.get_running_loop()
            formatted = [{"role": m["role"], "content": m["content"]} for m in messages]
            max_tokens = 2048
            temperature = 0.7
            if isinstance(config, dict):
                max_tokens = config.get("max_tokens", 2048)
                temperature = config.get("temperature", 0.7)

            stream = await loop.run_in_executor(
                None,
                lambda: self._llama.create_chat_completion(
                    messages=formatted,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    stream=True,
                ),
            )
            for chunk in stream:
                delta = chunk["choices"][0].get("delta", {})
                if "content" in delta:
                    yield delta["content"]

    def list_models(self) -> list[dict[str, Any]]:
        if not os.path.exists(self._model_path):
            return []
        return [
            {
                "name": os.path.basename(self._model_path),
                "size_bytes": os.path.getsize(self._model_path),
                "quantization": self._detect_quantization(),
                "context_length": self._n_ctx,
                "capabilities": ["chat", "code"],
                "description": f"Local GGUF model at {self._model_path}",
            }
        ]

    def provider_name(self) -> str:
        return "llama.cpp"

    def _detect_quantization(self) -> str | None:
        name = self._model_path.lower()
        for q in ["q4_k_m", "q5_k_m", "q8_0", "q4_k_s", "q5_k_s", "q6_k", "f16", "f32"]:
            if q in name:
                return q.upper()
        return None
