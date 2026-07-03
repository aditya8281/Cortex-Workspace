from __future__ import annotations

import json
import logging
import re
from typing import Any

import httpx

from backend.app.core.config import settings
from backend.app.services.intelligence.llm.provider import LLMModelInfo, LLMProvider

logger = logging.getLogger(__name__)


# Regex to strip Ollama session toggle commands from user messages.
# Matches: /think, /no_think, /nothink (standalone or leading, with optional trailing whitespace/newline)
_THINK_TOGGLE_RE = re.compile(
    r"^\s*/(?:no_think|nothink|think)\s*\n?",
    re.IGNORECASE,
)


class OllamaProvider(LLMProvider):
    def __init__(self, base_url: str = "http://localhost:11434"):
        self._base_url = base_url.rstrip("/")
        timeout = getattr(settings, "LLM_TIMEOUT", 120.0)
        self._client = httpx.AsyncClient(base_url=self._base_url, timeout=timeout)

    @staticmethod
    def _strip_toggle_commands(content: str) -> str:
        """Remove Ollama session toggle commands (e.g. /think, /no_think) from a message.

        Thinking is always enabled for reasoning models via the API, so these
        commands are not needed and only clutter the prompt.
        """
        return _THINK_TOGGLE_RE.sub("", content).lstrip("\n")

    async def chat(self, messages: list[dict], tools: list[dict], config: Any) -> tuple[str, list[dict] | None]:
        model = await self._default_model()
        if isinstance(config, dict) and config.get("model"):
            model = config["model"]

        formatted = [{"role": m["role"], "content": self._strip_toggle_commands(m["content"])} for m in messages]
        resp = await self._client.post(
            "/api/chat",
            json={
                "model": model,
                "messages": formatted,
                "stream": False,
                "options": {
                    "num_predict": (config or {}).get("max_tokens", 2048),
                    "temperature": (config or {}).get("temperature", 0.7),
                    "top_p": 0.9,
                    "repeat_penalty": 1.3,
                    "repeat_last_n": 256,
                    "top_k": 40,
                    "mirostat": 2,
                    "mirostat_tau": 5.0,
                    "mirostat_eta": 0.1,
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
        formatted = [{"role": m.role, "content": self._strip_toggle_commands(m.content)} for m in messages]
        resp = await self._client.post(
            "/api/chat",
            json={
                "model": model,
                "messages": formatted,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": temperature,
                    "top_p": 0.9,
                    "repeat_penalty": 1.3,
                    "repeat_last_n": 256,
                    "top_k": 40,
                    "mirostat": 2,
                    "mirostat_tau": 5.0,
                    "mirostat_eta": 0.1,
                },
            },
        )
        resp.raise_for_status()
        data = resp.json()
        pt = data.get("prompt_eval_count", 0)
        ct = data.get("eval_count", 0)
        logger.info(
            "Ollama inference: model=%s, prompt_tokens=%d, completion_tokens=%d",
            model,
            pt,
            ct,
        )
        return {
            "content": data["message"]["content"],
            "model": model,
            "tokens_prompt": pt,
            "tokens_completion": ct,
            "finish_reason": "stop",
        }

    async def chat_with_tools(
        self,
        messages: list,
        tools: list[dict],
        model: str | None = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> dict:
        """Native Ollama tool calling — uses message.tool_calls format.

        Returns:
            {
                "content": str,              # Text response (may be empty if tool call)
                "tool_calls": list[dict] | None,  # [{function: {name, arguments}}]
                "model": str,
                "tokens_prompt": int,
                "tokens_completion": int,
            }
        """
        model = model or await self._default_model()
        formatted = [{"role": m.role, "content": self._strip_toggle_commands(m.content)} for m in messages]

        body: dict[str, Any] = {
            "model": model,
            "messages": formatted,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
                "top_p": 0.9,
                "repeat_penalty": 1.3,
                "repeat_last_n": 256,
                "top_k": 40,
                "mirostat": 2,
                "mirostat_tau": 5.0,
                "mirostat_eta": 0.1,
            },
        }
        if tools:
            body["tools"] = tools

        resp = await self._client.post("/api/chat", json=body)
        resp.raise_for_status()
        data = resp.json()

        msg = data.get("message", {})
        content = msg.get("content", "")
        raw_tool_calls = msg.get("tool_calls")

        # Normalize tool_calls to standard format
        tool_calls = None
        if raw_tool_calls:
            tool_calls = []
            for tc in raw_tool_calls:
                func = tc.get("function", {})
                tool_calls.append(
                    {
                        "function": {
                            "name": func.get("name", ""),
                            "arguments": func.get("arguments", {}),
                        }
                    }
                )

        pt = data.get("prompt_eval_count", 0)
        ct = data.get("eval_count", 0)
        logger.info(
            "Ollama chat_with_tools: model=%s, prompt=%d, completion=%d, tool_calls=%s",
            model,
            pt,
            ct,
            bool(tool_calls),
        )
        return {
            "content": content,
            "tool_calls": tool_calls,
            "model": model,
            "tokens_prompt": pt,
            "tokens_completion": ct,
        }

    async def chat_stream(self, messages: list, tools: list, config: Any):
        model = await self._default_model()
        if isinstance(config, dict) and config.get("model"):
            model = config["model"]
        formatted = [{"role": m["role"], "content": self._strip_toggle_commands(m["content"])} for m in messages]
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
                    "top_p": 0.9,
                    "repeat_penalty": 1.3,
                    "repeat_last_n": 256,
                    "top_k": 40,
                    "mirostat": 2,
                    "mirostat_tau": 5.0,
                    "mirostat_eta": 0.1,
                },
            },
        ) as resp:
            resp.raise_for_status()
            # State: 0=normal, 1=in-tag-think-block, 2=post-tag-think
            tag_state = 0
            async for line in resp.aiter_lines():
                if line:
                    chunk = json.loads(line)
                    if "message" not in chunk:
                        continue
                    msg = chunk["message"]

                    # ── Path A: separate "thinking" field (Ollama 0.6+ with
                    # Qwen3 / DeepSeek R1 / etc.) ────────────────────────
                    thinking_field = msg.get("thinking", "")
                    if thinking_field:
                        yield {"type": "thinking", "text": thinking_field}

                    # ── Path B:<think> tags embedded in "content"
                    # (older Ollama or models that inline thinking) ────
                    token = msg.get("content", "")
                    if not token:
                        continue

                    if tag_state == 0:
                        # Look for opening tag — it may arrive mid-token
                        open_idx = token.find("<think>")
                        if open_idx != -1:
                            tag_state = 1
                            before = token[:open_idx]
                            after = token[open_idx + 7 :]
                            if before:
                                yield {"type": "content", "text": before}
                            if after:
                                # Could contain the end tag too — recurse logic
                                end_idx = after.find("</think>")
                                if end_idx != -1:
                                    yield {"type": "thinking", "text": after[:end_idx]}
                                    tag_state = 2
                                    rest = after[end_idx + 8 :]
                                    if rest:
                                        yield {"type": "content", "text": rest}
                                else:
                                    yield {"type": "thinking", "text": after}
                            continue
                        yield {"type": "content", "text": token}
                    elif tag_state == 1:
                        end_idx = token.find("</think>")
                        if end_idx != -1:
                            before = token[:end_idx]
                            after = token[end_idx + 8 :]
                            if before:
                                yield {"type": "thinking", "text": before}
                            tag_state = 2
                            if after:
                                yield {"type": "content", "text": after}
                        else:
                            yield {"type": "thinking", "text": token}
                    else:  # tag_state == 2 — normal content after think block
                        yield {"type": "content", "text": token}

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
