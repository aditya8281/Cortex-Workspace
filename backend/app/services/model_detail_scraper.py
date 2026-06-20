"""Model Detail Scraper — scrapes detailed model info from Ollama and HuggingFace."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import httpx
import structlog
from bs4 import BeautifulSoup

logger = structlog.get_logger(__name__)

OLLAMA_BASE_URL = "https://ollama.com/library"
HF_API_URL = "https://huggingface.co/api/models"
TIMEOUT_SECONDS = 30.0


@dataclass
class ModelVariant:
    """A single quantization/tag variant of a model."""

    name: str
    quantization: str = ""
    size_bytes: int = 0
    parameter_count: str = ""


@dataclass
class ModelDetail:
    """Structured detail for a single model from a provider."""

    model_id: str
    display_name: str
    family: str = ""
    parameter_count: float | None = None
    architecture: str | None = None
    context_length: int | None = None
    capabilities: list[str] = field(default_factory=list)
    license: str | None = None
    description: str = ""
    tags: list[str] = field(default_factory=list)
    variants: list[ModelVariant] = field(default_factory=list)
    source_url: str = ""


class ModelDetailScraper:
    """Scrapes detailed model info from Ollama and HuggingFace."""

    def __init__(self) -> None:
        self._client = httpx.AsyncClient(timeout=TIMEOUT_SECONDS, follow_redirects=True)

    async def scrape_ollama_detail(self, model_name: str) -> ModelDetail | None:
        """Scrape model detail from ollama.com/library/{model_name}."""
        try:
            url = f"{OLLAMA_BASE_URL}/{model_name}"
            resp = await self._client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code != 200:
                logger.warning("ollama_detail_not_found", model=model_name, status=resp.status_code)
                return None

            return self._parse_ollama_page(model_name, resp.text, url)

        except Exception as exc:
            logger.error("scrape_ollama_detail_failed", model=model_name, error=str(exc))
            return None

    async def scrape_hf_detail(self, repo_id: str) -> ModelDetail | None:
        """Scrape model detail from HuggingFace API."""
        try:
            resp = await self._client.get(f"{HF_API_URL}/{repo_id}")
            if resp.status_code != 200:
                logger.warning("hf_detail_not_found", repo=repo_id, status=resp.status_code)
                return None

            data = resp.json()
            parts = repo_id.split("/", 1)
            family = parts[0] if len(parts) > 1 else ""
            name = parts[-1] if parts else repo_id

            tags = data.get("tags", []) or []
            siblings = data.get("siblings", []) or []
            gguf_files = [s for s in siblings if isinstance(s, dict) and s.get("rfilename", "").endswith(".gguf")]

            return ModelDetail(
                model_id=repo_id,
                display_name=name,
                family=family,
                description=data.get("description", "") or "",
                tags=tags,
                license=data.get("license"),
                source_url=f"https://huggingface.co/{repo_id}",
                variants=[
                    ModelVariant(name=gguf["rfilename"], quantization=_guess_quantization(gguf["rfilename"]))
                    for gguf in gguf_files
                ],
            )

        except Exception as exc:
            logger.error("scrape_hf_detail_failed", repo=repo_id, error=str(exc))
            return None

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()

    # ── Ollama HTML parsing ────────────────────────────────────────

    def _parse_ollama_page(self, model_name: str, html: str, url: str) -> ModelDetail:
        """Parse an Ollama model page into a ModelDetail."""
        soup = BeautifulSoup(html, "html.parser")

        display_name = self._extract_heading(soup) or model_name
        description = self._extract_ollama_description(soup) or ""
        tags = self._extract_ollama_tags(soup)
        variants = self._extract_ollama_variants(soup)
        context_length = self._extract_context_length(soup)
        architecture = self._extract_architecture(soup)
        license_str = self._extract_license(soup)
        capabilities = self._infer_capabilities(model_name, tags)

        param_count = None
        param_match = re.search(r"(\d+(?:\.\d+)?)\s*[Bb]", description)
        if param_match:
            try:
                param_count = float(param_match.group(1))
            except ValueError:
                pass

        return ModelDetail(
            model_id=model_name,
            display_name=display_name,
            description=description,
            tags=tags,
            variants=variants,
            context_length=context_length,
            architecture=architecture,
            license=license_str,
            parameter_count=param_count,
            capabilities=capabilities,
            source_url=url,
        )

    def _extract_heading(self, soup: BeautifulSoup) -> str | None:
        for tag in ("h1", "h2"):
            heading = soup.find(tag)
            if heading:
                return heading.get_text(strip=True)
        return None

    def _extract_ollama_description(self, soup: BeautifulSoup) -> str | None:
        meta = soup.find("meta", attrs={"name": "description"})
        if meta and meta.get("content"):
            content = meta["content"]
            if isinstance(content, str):
                return content.strip()

        for tag in ("p", "span"):
            for el in soup.find_all(tag):
                text = el.get_text(strip=True)
                if text and len(text) > 20:
                    return text
        return None

    def _extract_ollama_tags(self, soup: BeautifulSoup) -> list[str]:
        tags: list[str] = []
        for el in soup.find_all(["code", "span", "a"]):
            text = el.get_text(strip=True)
            if text and re.match(r"^[\w.-]+:\d", text):
                tags.append(text)
        return list(dict.fromkeys(tags))

    def _extract_ollama_variants(self, soup: BeautifulSoup) -> list[ModelVariant]:
        variants: list[ModelVariant] = []
        for el in soup.find_all(["tr", "li", "div"]):
            text = el.get_text(strip=True)
            match = re.search(r"([\w.-]+:\d+(?:\.\d+)?[bBkKmMgG]?)", text)
            if match:
                tag_str = match.group(1)
                variants.append(
                    ModelVariant(
                        name=tag_str,
                        quantization=_guess_quantization(tag_str),
                        size_bytes=_parse_size_from_text(text),
                    )
                )
        return variants

    def _extract_context_length(self, soup: BeautifulSoup) -> int | None:
        text = soup.get_text()
        match = re.search(r"(?:context|ctx)\s*(?:length|window|size)?\s*[:=]?\s*([\d,]+)\s*(?:tokens?)?", text, re.IGNORECASE)
        if match:
            try:
                return int(match.group(1).replace(",", ""))
            except ValueError:
                pass
        return None

    def _extract_architecture(self, soup: BeautifulSoup) -> str | None:
        text = soup.get_text()
        match = re.search(r"architecture\s*[:=]?\s*(\S+)", text, re.IGNORECASE)
        if match:
            return match.group(1)
        return None

    def _extract_license(self, soup: BeautifulSoup) -> str | None:
        text = soup.get_text()
        for pattern in [r"license\s*[:=]?\s*(\S+)", r"licensed?\s+under\s+(\S+)"]:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None

    @staticmethod
    def _infer_capabilities(model_name: str, tags: list[str]) -> list[str]:
        name_lower = model_name.lower()
        tag_text = " ".join(tags).lower()
        combined = f"{name_lower} {tag_text}"
        caps = ["chat"]
        if any(x in combined for x in ("code", "coder", "starcoder", "codellama")):
            caps.append("code")
        if any(x in combined for x in ("vision", "llava")):
            caps.append("vision")
        if any(x in combined for x in ("embed", "nomic", "bge", "mxbai", "bert")):
            caps.append("embedding")
        if any(x in combined for x in ("reason", "phi", "orca")):
            caps.append("reasoning")
        return list(set(caps))


# ── Helpers ──────────────────────────────────────────────────────


def _guess_quantization(tag_str: str) -> str:
    tag_lower = tag_str.lower()
    if "q4_0" in tag_lower or "q40" in tag_lower:
        return "Q4_0"
    if "q4_k" in tag_lower or "q4km" in tag_lower:
        return "Q4_K_M"
    if "q5_0" in tag_lower or "q50" in tag_lower:
        return "Q5_0"
    if "q5_k" in tag_lower or "q5km" in tag_lower:
        return "Q5_K_M"
    if "q6_k" in tag_lower or "q6km" in tag_lower:
        return "Q6_K"
    if "q8_0" in tag_lower or "q80" in tag_lower:
        return "Q8_0"
    if "f16" in tag_lower:
        return "F16"
    if "fp16" in tag_lower:
        return "FP16"
    return ""


def _parse_size_from_text(text: str) -> int:
    match = re.search(r"([\d.]+)\s*(GB|MB|KB|B)", text, re.IGNORECASE)
    if not match:
        return 0
    value = float(match.group(1))
    unit = match.group(2).upper()
    multipliers = {"B": 1, "KB": 1024, "MB": 1024**2, "GB": 1024**3}
    return int(value * multipliers.get(unit, 1))
