from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

from backend.app.services.intelligence.llm.provider import LLMProvider

logger = logging.getLogger(__name__)


class LlamaCppProvider(LLMProvider):
    def __init__(
        self,
        model_path: str,
        n_ctx: int = 8192,
        n_gpu_layers: int = 0,
        n_threads: int = 8,
        n_batch: int = 2048,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        concurrency: int = 4,
        use_mmap: bool = True,
    ):
        self._model_path = model_path
        self._n_ctx = n_ctx
        self._n_gpu_layers = n_gpu_layers
        self._n_threads = n_threads
        self._n_batch = n_batch
        self._max_tokens = max_tokens
        self._temperature = temperature
        self._use_mmap = use_mmap
        self._llama: Any = None
        self._model_lock = asyncio.Lock()
        self._semaphore = asyncio.Semaphore(concurrency)

    async def _ensure_model(self) -> None:
        if self._llama is not None:
            return
        async with self._model_lock:
            if self._llama is not None:
                return
            try:
                from llama_cpp import Llama  # type: ignore[import-not-found]
            except ImportError:
                raise RuntimeError("llama-cpp-python not installed. Run: pip install llama-cpp-python")
            loop = asyncio.get_running_loop()
            self._llama = await loop.run_in_executor(
                None,
                lambda: Llama(
                    model_path=self._model_path,
                    n_ctx=self._n_ctx,
                    n_gpu_layers=self._n_gpu_layers,
                    n_threads=self._n_threads,
                    n_batch=self._n_batch,
                    use_mmap=self._use_mmap,
                    verbose=False,
                ),
            )
            logger.info(
                "llama.cpp loaded: model=%s, ctx=%d, threads=%d, batch=%d, gpu_layers=%d, mmap=%s",
                self._model_path,
                self._n_ctx,
                self._n_threads,
                self._n_batch,
                self._n_gpu_layers,
                self._use_mmap,
            )

    async def chat(self, messages: list[dict], tools: list[dict], config: Any) -> tuple[str, list[dict] | None]:
        await self._ensure_model()
        async with self._semaphore:
            loop = asyncio.get_running_loop()
            formatted = [{"role": m["role"], "content": m["content"]} for m in messages]
            if isinstance(config, dict):
                max_tokens = config.get("max_tokens", self._max_tokens)
                temperature = config.get("temperature", self._temperature)
            else:
                max_tokens = self._max_tokens
                temperature = self._temperature

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
            usage = result.get("usage", {})
            logger.info(
                "llama.cpp inference: prompt_tokens=%d, completion_tokens=%d, finish=%s",
                usage.get("prompt_tokens", 0),
                usage.get("completion_tokens", 0),
                choice.get("finish_reason", "stop"),
            )
            return content, tool_calls

    async def chat_direct(
        self,
        messages: list,
        model: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> Any:
        await self._ensure_model()
        mt = max_tokens if max_tokens is not None else self._max_tokens
        tp = temperature if temperature is not None else self._temperature
        async with self._semaphore:
            loop = asyncio.get_running_loop()
            formatted = [{"role": m.role, "content": m.content} for m in messages]
            result = await loop.run_in_executor(
                None,
                lambda: self._llama.create_chat_completion(
                    messages=formatted,
                    max_tokens=mt,
                    temperature=tp,
                ),
            )
            choice = result["choices"][0]
            usage = result.get("usage", {})
            pt = usage.get("prompt_tokens", 0)
            ct = usage.get("completion_tokens", 0)
            logger.info(
                "llama.cpp inference: prompt_tokens=%d, completion_tokens=%d, finish=%s",
                pt,
                ct,
                choice.get("finish_reason", "stop"),
            )
            return {
                "content": choice["message"]["content"],
                "model": result.get("model", self._model_path),
                "tokens_prompt": pt,
                "tokens_completion": ct,
                "finish_reason": choice.get("finish_reason", "stop"),
            }

    async def chat_stream(self, messages: list, tools: list, config: Any):
        await self._ensure_model()
        async with self._semaphore:
            loop = asyncio.get_running_loop()
            formatted = [{"role": m["role"], "content": m["content"]} for m in messages]
            if isinstance(config, dict):
                max_tokens = config.get("max_tokens", self._max_tokens)
                temperature = config.get("temperature", self._temperature)
            else:
                max_tokens = self._max_tokens
                temperature = self._temperature

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
                    yield {"type": "content", "text": delta["content"]}

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
                "description": f"Local GGUF · {self._n_ctx}ctx · {self._n_threads}th · batch {self._n_batch} · mmap={self._use_mmap}",
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
