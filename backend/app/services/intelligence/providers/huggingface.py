"""HuggingFace provider adapter."""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any

import httpx
import structlog

from backend.app.services.providers.base import (
    ProviderAdapter,
    ProviderDownloadResult,
    ProviderModelInfo,
    ProviderVariantInfo,
)

logger = structlog.get_logger()

HF_API_BASE = "https://huggingface.co/api"
GGUF_PATTERN = re.compile(
    r"(?P<name>[A-Za-z0-9._-]+)"
    r"(?:\+(?P<adapter>[A-Za-z0-9._-]+))?"
    r"-(?P<size>[0-9]+[BbMm])"
    r"(?:-(?P<ctx>[0-9]+))?"
    r"-(?P<quant>[A-Za-z0-9_]+)"
    r"\.gguf$"
)

PARAM_PATTERNS: list[tuple[re.Pattern[str], float]] = [
    (re.compile(r"\b(\d+(?:\.\d+)?)\s*[Bb]\b"), 1.0),
    (re.compile(r"\b(\d+(?:\.\d+)?)\s*[Mm]\b"), 1e-3),
]

PIPELINE_CAPABILITIES: dict[str, list[str]] = {
    "text-generation": ["chat"],
    "text2text-generation": ["chat"],
    "text-classification": ["classification"],
    "token-classification": ["ner"],
    "question-answering": ["qa"],
    "fill-mask": ["fill-mask"],
    "summarization": ["summarization"],
    "translation": ["translation"],
    "feature-extraction": ["embedding"],
    "image-classification": ["vision"],
    "image-to-text": ["vision"],
    "object-detection": ["vision"],
    "visual-question-answering": ["vision"],
    "automatic-speech-recognition": ["audio"],
    "text-to-speech": ["audio"],
    "conversational": ["chat"],
    "table-question-answering": ["table-qa"],
}


class HuggingFaceProvider(ProviderAdapter):
    """HuggingFace Hub model provider."""

    def __init__(self, token: str | None = None, base_url: str = HF_API_BASE):
        self._base_url = base_url.rstrip("/")
        self._token = token
        headers: dict[str, str] = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            headers=headers,
            timeout=30.0,
        )

    @property
    def name(self) -> str:
        return "huggingface"

    @property
    def display_name(self) -> str:
        return "HuggingFace"

    async def health_check(self) -> bool:
        try:
            resp = await self._client.get("/models?limit=1")
            return resp.status_code == 200
        except Exception:
            return False

    async def list_models(self) -> list[ProviderModelInfo]:
        models: list[ProviderModelInfo] = []
        try:
            url: str | None = "/models?search=gguf&sort=downloads&direction=-1&limit=100"
            while url:
                resp = await self._client.get(url)
                resp.raise_for_status()
                data = resp.json()
                if not data:
                    break
                for item in data:
                    model = self._parse_model_summary(item)
                    if model:
                        models.append(model)
                url = self._next_link(resp)
        except Exception as e:
            logger.error("huggingface_list_models_failed", error=str(e))
        return models

    async def get_model_variants(self, model_id: str) -> list[ProviderVariantInfo]:
        variants: list[ProviderVariantInfo] = []
        try:
            resp = await self._client.get(f"/models/{model_id}/tree/main")
            resp.raise_for_status()
            files = resp.json()
            for f in files:
                filename = f.get("path", "")
                if not filename.endswith(".gguf"):
                    continue
                parsed = self._parse_gguf_filename(filename)
                if parsed is None:
                    continue
                quant = parsed.get("quant", "unknown")
                variants.append(
                    ProviderVariantInfo(
                        variant_id=f"{model_id}/{filename}",
                        quantization=quant,
                        size_bytes=f.get("size"),
                        size_gb=round(f.get("size", 0) / (1024**3), 2) if f.get("size") else None,
                        download_url=f"https://huggingface.co/{model_id}/resolve/main/{filename}",
                        extra_metadata={"filename": filename},
                    )
                )
        except Exception as e:
            logger.error("huggingface_get_variants_failed", model_id=model_id, error=str(e))
        return variants

    async def get_model_detail(self, model_id: str) -> ProviderModelInfo | None:
        try:
            resp = await self._client.get(f"/models/{model_id}")
            resp.raise_for_status()
            item = resp.json()
            return self._parse_model_detail(item)
        except Exception as e:
            logger.error("huggingface_get_detail_failed", model_id=model_id, error=str(e))
            return None

    async def download_model(
        self,
        model_id: str,
        variant_id: str | None = None,
        on_progress: Callable[[float], None] | None = None,
    ) -> ProviderDownloadResult:
        try:
            if variant_id:
                filename = variant_id.split("/", 1)[1] if "/" in variant_id else variant_id
            else:
                files_resp = await self._client.get(f"/models/{model_id}/tree/main")
                files_resp.raise_for_status()
                files = files_resp.json()
                gguf_files = [f for f in files if f.get("path", "").endswith(".gguf")]
                if not gguf_files:
                    return ProviderDownloadResult(success=False, error_message="No GGUF files found")
                gguf_files.sort(key=lambda x: x.get("size", 0))
                filename = gguf_files[0]["path"]

            download_url = f"https://huggingface.co/{model_id}/resolve/main/{filename}"

            async with self._client.stream("GET", download_url) as resp:
                if resp.status_code != 200:
                    return ProviderDownloadResult(success=False, error_message=f"HTTP {resp.status_code}")

                total = int(resp.headers.get("content-length", 0))
                downloaded = 0
                async for chunk in resp.aiter_bytes():
                    downloaded += len(chunk)
                    if on_progress and total > 0:
                        on_progress(downloaded / total)

            return ProviderDownloadResult(
                success=True,
                model_name=model_id,
                file_size_bytes=downloaded if downloaded > 0 else None,
            )
        except Exception as e:
            logger.error("huggingface_download_failed", model_id=model_id, error=str(e))
            return ProviderDownloadResult(success=False, error_message=str(e))

    async def cancel_download(self, model_id: str) -> bool:
        return False

    async def delete_model(self, model_id: str) -> bool:
        return False

    async def list_installed(self) -> list[ProviderModelInfo]:
        return []

    def _next_link(self, resp: httpx.Response) -> str | None:
        link = resp.headers.get("link", "")
        if not link:
            return None
        match = re.search(r'<[^>]+>;\s*rel="next"', link)
        if not match:
            return None
        url_match = re.search(r"<([^>]+)>", match.group(0))
        if not url_match:
            return None
        next_url = url_match.group(1)
        if next_url.startswith("http"):
            parsed = httpx.URL(next_url)
            path = str(parsed.raw_path)
            if parsed.query:
                path += f"?{parsed.query.decode()}"
            return path
        return next_url

    def _parse_gguf_filename(self, filename: str) -> dict[str, Any] | None:
        match = GGUF_PATTERN.match(filename)
        if match:
            return match.groupdict()
        name = filename.rsplit(".gguf", 1)[0]
        quant_match = re.search(r"(Q[0-9A-Z]+[_A-Z0-9]*|[A-Z]{1,2}\d+[A-Z0-9]*)", name)
        quant = quant_match.group(1) if quant_match else "unknown"
        return {"name": name, "quant": quant}

    def _parse_model_summary(self, item: dict[str, Any]) -> ProviderModelInfo | None:
        model_id = item.get("modelId") or item.get("id", "")
        if not model_id:
            return None
        tags = item.get("tags") or []
        pipeline_tag = item.get("pipeline_tag", "")
        capabilities = self._infer_capabilities(tags, pipeline_tag)
        param_count = self._extract_parameter_count(tags)
        return ProviderModelInfo(
            provider_model_id=model_id,
            display_name=model_id.split("/")[-1] if "/" in model_id else model_id,
            family=self._extract_family(model_id, tags),
            parameter_count=param_count,
            architecture=self._extract_architecture(tags),
            context_length=self._extract_context_length(tags),
            capabilities=capabilities,
            license=item.get("license") or self._extract_license(tags),
            description=item.get("description", ""),
            tags=tags,
            source_url=f"https://huggingface.co/{model_id}",
            extra_metadata={
                "downloads": item.get("downloads", 0),
                "likes": item.get("likes", 0),
                "pipeline_tag": pipeline_tag,
            },
        )

    def _parse_model_detail(self, item: dict[str, Any]) -> ProviderModelInfo | None:
        model_id = item.get("modelId") or item.get("id", "")
        if not model_id:
            return None
        tags = item.get("tags") or []
        pipeline_tag = item.get("pipeline_tag", "")
        capabilities = self._infer_capabilities(tags, pipeline_tag)
        param_count = self._extract_parameter_count(tags)
        safetensors = item.get("safetensors", {})
        total_params = safetensors.get("total")
        if total_params and param_count is None:
            param_count = round(total_params / 1e9, 1)
        return ProviderModelInfo(
            provider_model_id=model_id,
            display_name=model_id.split("/")[-1] if "/" in model_id else model_id,
            family=self._extract_family(model_id, tags),
            parameter_count=param_count,
            architecture=self._extract_architecture(tags),
            context_length=self._extract_context_length(tags),
            capabilities=capabilities,
            license=item.get("license") or self._extract_license(tags),
            description=item.get("description", ""),
            tags=tags,
            source_url=f"https://huggingface.co/{model_id}",
            extra_metadata={
                "downloads": item.get("downloads", 0),
                "likes": item.get("likes", 0),
                "pipeline_tag": pipeline_tag,
                "card_data": item.get("card_data", {}),
            },
        )

    def _infer_capabilities(self, tags: list[str], pipeline_tag: str = "") -> list[str]:
        caps: list[str] = []
        if pipeline_tag in PIPELINE_CAPABILITIES:
            caps.extend(PIPELINE_CAPABILITIES[pipeline_tag])
        lower_tags = [t.lower() for t in tags]
        if any(t in ("gguf", "ggml") for t in lower_tags):
            caps.append("gguf")
        if any(("vision" in t) and ("vision" not in caps) for t in lower_tags):
            caps.append("vision")
        if any(("code" in t) and ("code" not in caps) for t in lower_tags):
            caps.append("code")
        if any(("embed" in t) and ("embedding" not in caps) for t in lower_tags):
            caps.append("embedding")
        if any(("chat" in t) and ("chat" not in caps) for t in lower_tags):
            caps.append("chat")
        return caps if caps else ["chat"]

    def _extract_parameter_count(self, tags: list[str]) -> float | None:
        for tag in tags:
            for pattern, scale in PARAM_PATTERNS:
                m = pattern.search(tag)
                if m:
                    return round(float(m.group(1)) * scale, 2) if scale != 1.0 else float(m.group(1))
        return None

    def _extract_architecture(self, tags: list[str]) -> str | None:
        arch_keywords = [
            "llama",
            "mistral",
            "mixtral",
            "phi",
            "qwen",
            "gemma",
            "gpt",
            "bloom",
            "falcon",
            "mpt",
            "dolly",
            "starcoder",
            "codellama",
            "deepseek",
            "yi",
            "internlm",
            "baichuan",
            "command-r",
            "jamba",
        ]
        lower_tags = [t.lower() for t in tags]
        for arch in arch_keywords:
            if any(arch in t for t in lower_tags):
                return arch
        return None

    def _extract_context_length(self, tags: list[str]) -> int | None:
        for tag in tags:
            m = re.search(r"(\d+)k?\s*(?:context|ctx|tokens?)", tag.lower())
            if m:
                return int(m.group(1)) * (1000 if "k" in tag.lower() else 1)
        return None

    def _extract_family(self, model_id: str, tags: list[str]) -> str:
        parts = model_id.split("/")
        name = parts[-1] if parts else model_id
        # Split on common separators, take first token, join if it was split on underscore
        base = name.split("-")[0]
        tokens = base.split("_")
        base = "".join(tokens[:2]) if len(tokens) > 1 else tokens[0]
        # Remove trailing version-like suffixes
        base = re.sub(r"\d+$", "", base)
        return base.lower()

    def _extract_license(self, tags: list[str]) -> str | None:
        known_licenses = {
            "apache-2.0",
            "mit",
            "lgpl-2.1",
            "lgpl-3.0",
            "gpl-2.0",
            "gpl-3.0",
            "bsd-2-clause",
            "bsd-3-clause",
            "cc-by-4.0",
            "cc-by-sa-4.0",
            "cc0-1.0",
            "artistic-2.0",
            "unlicense",
            "wtfpl",
            "isc",
        }
        for tag in tags:
            if tag.startswith("license:"):
                return tag.split(":", 1)[1]
            lower = tag.lower()
            if lower in known_licenses:
                return lower
            if "license" in lower and len(tag) < 50:
                return tag
        return None
