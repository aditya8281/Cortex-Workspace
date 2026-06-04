from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Literal

import httpx

from backend.app.ai.api_llm import APILLM
from backend.app.ai.base import BaseLLM

logger = logging.getLogger(__name__)

ProviderFamily = Literal["openai_compatible", "anthropic", "gemini"]


PROVIDER_ALIASES: dict[str, str] = {
    "google": "Google Gemini",
    "gemini": "Google Gemini",
    "google gemini": "Google Gemini",
    "openai": "OpenAI",
    "openrouter": "OpenRouter",
    "groq": "Groq",
    "together": "Together AI",
    "together ai": "Together AI",
    "anthropic": "Anthropic",
    "claude": "Anthropic",
    "custom": "Custom OpenAI-compatible",
    "custom openai-compatible": "Custom OpenAI-compatible",
    "custom openai compatible": "Custom OpenAI-compatible",
}


def normalize_provider_name(provider_name: str | None) -> str:
    if not provider_name:
        return ""
    key = provider_name.strip().lower()
    return PROVIDER_ALIASES.get(key, provider_name.strip())


def provider_family(provider_name: str | None) -> ProviderFamily:
    normalized = normalize_provider_name(provider_name).lower()
    if normalized in {"anthropic"}:
        return "anthropic"
    if normalized in {"google gemini"}:
        return "gemini"
    return "openai_compatible"


def provider_default_base_url(provider_name: str | None) -> str | None:
    normalized = normalize_provider_name(provider_name)
    defaults = {
        "OpenAI": "https://api.openai.com/v1",
        "OpenRouter": "https://openrouter.ai/api/v1",
        "Groq": "https://api.groq.com/openai/v1",
        "Together AI": "https://api.together.xyz/v1",
        "Anthropic": "https://api.anthropic.com/v1",
        "Google Gemini": "https://generativelanguage.googleapis.com/v1beta",
        "Custom OpenAI-compatible": None,
    }
    return defaults.get(normalized)


def build_provider_llm(provider_name: str, api_key: str, base_url: str, model: str) -> BaseLLM:
    normalized = normalize_provider_name(provider_name)
    family = provider_family(normalized)

    if family == "anthropic":
        return AnthropicLLM(api_key=api_key, base_url=base_url, model=model)
    if family == "gemini":
        return GeminiLLM(api_key=api_key, base_url=base_url, model=model)
    return APILLM(api_key=api_key, base_url=base_url, model=model)


async def list_provider_models(provider_name: str, base_url: str, api_key: str) -> list[dict[str, Any]]:
    normalized = normalize_provider_name(provider_name)
    family = provider_family(normalized)

    if family == "anthropic":
        return await _list_anthropic_models(base_url, api_key)
    if family == "gemini":
        return await _list_gemini_models(base_url, api_key)
    return await _list_openai_compatible_models(base_url, api_key)


def _openai_headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


async def _list_openai_compatible_models(base_url: str, api_key: str) -> list[dict[str, Any]]:
    url = f"{base_url.rstrip('/')}/models"
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(url, headers=_openai_headers(api_key))
        response.raise_for_status()
        data = response.json()

    models: list[dict[str, Any]] = []
    for model in data.get("data", []):
        if not isinstance(model, dict) or not model.get("id"):
            continue
        models.append(
            {
                "id": model["id"],
                "name": model["id"],
                "context_length": model.get("context_window") or model.get("context_length"),
                "owned_by": model.get("owned_by"),
                "active": model.get("active", True),
            }
        )
    return models


async def _list_anthropic_models(base_url: str, api_key: str) -> list[dict[str, Any]]:
    url = f"{base_url.rstrip('/')}/models"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

    models: list[dict[str, Any]] = []
    for model in data.get("data", []):
        if not isinstance(model, dict) or not model.get("id"):
            continue
        models.append(
            {
                "id": model["id"],
                "name": model["id"],
                "context_length": model.get("context_length"),
                "owned_by": model.get("display_name") or model.get("owned_by"),
                "active": model.get("type") != "deprecated",
            }
        )
    return models


async def _list_gemini_models(base_url: str, api_key: str) -> list[dict[str, Any]]:
    url = f"{base_url.rstrip('/')}/models"
    params = {"key": api_key}
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

    models: list[dict[str, Any]] = []
    for model in data.get("models", []):
        if not isinstance(model, dict) or not model.get("name"):
            continue
        model_id = model["name"].split("/", 1)[-1]
        models.append(
            {
                "id": model_id,
                "name": model_id,
                "context_length": model.get("inputTokenLimit") or model.get("outputTokenLimit"),
                "owned_by": model.get("displayName") or "Google",
                "active": True,
            }
        )
    return models


class AnthropicLLM(BaseLLM):
    def __init__(self, api_key: str, base_url: str, model: str):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model

    async def generate(self, prompt: str, system_prompt: str | None = None, model: str | None = None) -> str:
        model_name = model or self.model
        payload: dict[str, Any] = {
            "model": model_name,
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_prompt:
            payload["system"] = system_prompt

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        url = f"{self.base_url.rstrip('/')}/messages"
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        content = data.get("content", [])
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
        return "".join(parts).strip()


class GeminiLLM(BaseLLM):
    def __init__(self, api_key: str, base_url: str, model: str):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model

    async def generate(self, prompt: str, system_prompt: str | None = None, model: str | None = None) -> str:
        model_name = (model or self.model).replace("models/", "")
        url = f"{self.base_url.rstrip('/')}/models/{model_name}:generateContent"
        payload: dict[str, Any] = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}],
                }
            ],
        }
        if system_prompt:
            payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}

        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(url, params={"key": self.api_key}, json=payload)
            response.raise_for_status()
            data = response.json()

        candidates = data.get("candidates", [])
        if not candidates:
            return ""
        content = candidates[0].get("content", {})
        parts = content.get("parts", [])
        return "".join(part.get("text", "") for part in parts if isinstance(part, dict)).strip()
