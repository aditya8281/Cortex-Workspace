"""Ollama Library Scraper — scrapes model catalog from ollama.com/library.

Uses semantic HTML selectors with a robust fallback chain:
  data-attrs → semantic HTML → structural patterns → text matching
"""

from __future__ import annotations

import asyncio
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import httpx
import structlog
from bs4 import BeautifulSoup, Tag

logger = structlog.get_logger(__name__)

CACHE_DIR = Path("CortexMemory")
CACHE_FILE = CACHE_DIR / "ollama_library_catalog.json"
DEFAULT_CACHE_TTL_HOURS = 24

BASE_URL = "https://ollama.com/library"
TIMEOUT_SECONDS = 30.0

HARDCODED_MODELS: list[dict[str, Any]] = [
    {
        "name": "llama3.1",
        "description": "Meta Llama 3.1 instruction-tuned model.",
        "capabilities": ["chat"],
        "suggested_ram": "8GB+",
    },
    {
        "name": "llama3.2",
        "description": "Meta Llama 3.2 with improved reasoning.",
        "capabilities": ["chat"],
        "suggested_ram": "8GB+",
    },
    {"name": "llama3", "description": "Meta Llama 3 base model.", "capabilities": ["chat"], "suggested_ram": "8GB+"},
    {"name": "llama2", "description": "Meta Llama 2 base model.", "capabilities": ["chat"], "suggested_ram": "8GB+"},
    {
        "name": "codellama",
        "description": "Code-specialized Llama model.",
        "capabilities": ["chat", "code"],
        "suggested_ram": "8GB+",
    },
    {"name": "mistral", "description": "Mistral AI 7B model.", "capabilities": ["chat"], "suggested_ram": "6GB+"},
    {"name": "mistral-nemo", "description": "Mistral AI 12B model.", "capabilities": ["chat"], "suggested_ram": "8GB+"},
    {
        "name": "mixtral",
        "description": "Mistral AI Mixture of Experts.",
        "capabilities": ["chat"],
        "suggested_ram": "12GB+",
    },
    {
        "name": "phi",
        "description": "Microsoft Phi-3 mini model.",
        "capabilities": ["chat", "reasoning"],
        "suggested_ram": "2GB+",
    },
    {
        "name": "phi3",
        "description": "Microsoft Phi-3 small language model.",
        "capabilities": ["chat", "reasoning"],
        "suggested_ram": "4GB+",
    },
    {
        "name": "gemma",
        "description": "Google Gemma lightweight model.",
        "capabilities": ["chat"],
        "suggested_ram": "6GB+",
    },
    {
        "name": "gemma2",
        "description": "Google Gemma 2 improved model.",
        "capabilities": ["chat"],
        "suggested_ram": "6GB+",
    },
    {"name": "qwen", "description": "Alibaba Qwen model.", "capabilities": ["chat", "code"], "suggested_ram": "6GB+"},
    {
        "name": "qwen2",
        "description": "Alibaba Qwen 2 model.",
        "capabilities": ["chat", "code"],
        "suggested_ram": "6GB+",
    },
    {
        "name": "qwen2.5",
        "description": "Alibaba Qwen 2.5 model.",
        "capabilities": ["chat", "code"],
        "suggested_ram": "6GB+",
    },
    {
        "name": "deepseek-coder",
        "description": "DeepSeek code generation model.",
        "capabilities": ["chat", "code"],
        "suggested_ram": "6GB+",
    },
    {
        "name": "deepseek-v2",
        "description": "DeepSeek V2 MoE model.",
        "capabilities": ["chat", "code"],
        "suggested_ram": "12GB+",
    },
    {
        "name": "nomic-embed-text",
        "description": "Nomic text embedding model.",
        "capabilities": ["embedding"],
        "suggested_ram": "2GB+",
    },
    {
        "name": "mxbai-embed-large",
        "description": "MixedBread large embedding model.",
        "capabilities": ["embedding"],
        "suggested_ram": "2GB+",
    },
    {
        "name": "llava",
        "description": "Large Language and Vision Assistant.",
        "capabilities": ["chat", "vision"],
        "suggested_ram": "6GB+",
    },
    {
        "name": "llava-llama3",
        "description": "LLaVA with Llama 3.",
        "capabilities": ["chat", "vision"],
        "suggested_ram": "8GB+",
    },
    {"name": "bakllava", "description": "BakLLaVA model.", "capabilities": ["chat", "vision"], "suggested_ram": "6GB+"},
    {
        "name": "starcoder2",
        "description": "StarCoder 2 code model.",
        "capabilities": ["chat", "code"],
        "suggested_ram": "6GB+",
    },
    {
        "name": "starcoder",
        "description": "StarCoder code model.",
        "capabilities": ["chat", "code"],
        "suggested_ram": "8GB+",
    },
    {"name": "wizardlm2", "description": "WizardLM 2 model.", "capabilities": ["chat"], "suggested_ram": "6GB+"},
    {
        "name": "orca2",
        "description": "Microsoft Orca 2 model.",
        "capabilities": ["chat", "reasoning"],
        "suggested_ram": "8GB+",
    },
    {
        "name": "neural-chat",
        "description": "Intel Neural Chat model.",
        "capabilities": ["chat"],
        "suggested_ram": "6GB+",
    },
    {"name": "command-r", "description": "Cohere Command R model.", "capabilities": ["chat"], "suggested_ram": "8GB+"},
    {
        "name": "command-r-plus",
        "description": "Cohere Command R+ model.",
        "capabilities": ["chat"],
        "suggested_ram": "12GB+",
    },
    {"name": "aya", "description": "Cohere Aya multilingual model.", "capabilities": ["chat"], "suggested_ram": "6GB+"},
    {"name": "bert", "description": "BERT embeddings model.", "capabilities": ["embedding"], "suggested_ram": "2GB+"},
    {
        "name": "bge-large",
        "description": "BAAI BGE large embedding.",
        "capabilities": ["embedding"],
        "suggested_ram": "2GB+",
    },
    {
        "name": "bge-base",
        "description": "BAAI BGE base embedding.",
        "capabilities": ["embedding"],
        "suggested_ram": "2GB+",
    },
    {
        "name": "allminilm",
        "description": "All MiniLM embedding models.",
        "capabilities": ["embedding"],
        "suggested_ram": "1GB+",
    },
]


class OllamaLibraryScraper:
    """Scrapes the Ollama model library with robust, semantic selectors."""

    def __init__(self, cache_dir: Path | str | None = None, cache_ttl_hours: int = DEFAULT_CACHE_TTL_HOURS):
        self._cache_dir = Path(cache_dir) if cache_dir else CACHE_DIR
        self._cache_file = self._cache_dir / "ollama_library_catalog.json"
        self._cache_ttl_hours = cache_ttl_hours

    # ── Public API ────────────────────────────────────────────────

    async def fetch_models(self, force_refresh: bool = False) -> list[dict[str, Any]]:
        cache = self._load_cache()
        if cache and not force_refresh and self._is_cache_valid(cache):
            logger.info("ollama_cache_hit", count=len(cache.get("models", [])))
            return cache.get("models", [])

        try:
            models = await self._scrape_all_pages()
            if models:
                self._save_cache(models)
                return models
        except Exception as exc:
            logger.error("ollama_scrape_failed", error=str(exc))

        if cache and "models" in cache:
            logger.info("ollama_stale_cache_fallback", count=len(cache["models"]))
            return cache["models"]

        logger.info("ollama_hardcoded_fallback", count=len(HARDCODED_MODELS))
        self._save_cache(HARDCODED_MODELS)
        return list(HARDCODED_MODELS)

    def fetch_models_sync(self, force_refresh: bool = False) -> list[dict[str, Any]]:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self.fetch_models(force_refresh))
            finally:
                loop.close()
        else:
            raise RuntimeError(
                "fetch_models_sync() cannot be called from an async context. Use fetch_models() instead."
            )

    # ── Scraping ──────────────────────────────────────────────────

    async def _scrape_all_pages(self) -> list[dict[str, Any]]:
        all_models: list[dict[str, Any]] = []
        page = 1
        max_pages = 50

        while page <= max_pages:
            html = await self._fetch_page(page)
            if not html:
                break
            models = self._parse_page_models(html)
            if not models:
                break
            all_models.extend(models)
            if not self._has_next_page(html):
                break
            page += 1

        seen: set[str] = set()
        unique: list[dict[str, Any]] = []
        for m in all_models:
            if m["name"] not in seen:
                seen.add(m["name"])
                unique.append(m)
        return unique

    async def _fetch_page(self, page: int = 1) -> str | None:
        url = f"{BASE_URL}?page={page}" if page > 1 else BASE_URL
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS, follow_redirects=True) as client:
                resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
                resp.raise_for_status()
                return resp.text
        except Exception as exc:
            logger.error("ollama_fetch_page_failed", page=page, error=str(exc))
            return None

    # ── Parsing with semantic selectors ───────────────────────────

    def _parse_page_models(self, html: str) -> list[dict[str, Any]]:
        soup = BeautifulSoup(html, "html.parser")
        models: list[dict[str, Any]] = []

        for card in self._find_model_cards(soup):
            model = self._extract_model_from_card(card)
            if model:
                models.append(model)
        return models

    def _find_model_cards(self, soup: BeautifulSoup) -> list[Tag]:
        """Find model card elements using the fallback selector chain."""
        # Strategy 1: data attributes
        cards = soup.select("[data-model-name], [data-model], [data-slug]")
        if cards:
            logger.debug("selector_strategy", strategy="data_attrs", count=len(cards))
            return cards

        # Strategy 2: semantic HTML (article, section with links to /library/)
        cards = soup.select("article a[href^='/library/'], section a[href^='/library/']")
        if cards:
            logger.debug("selector_strategy", strategy="semantic_html", count=len(cards))
            return cards

        # Strategy 3: structural patterns — links that point to /library/{name}
        cards = soup.select("a[href^='/library/']")
        if cards:
            logger.debug("selector_strategy", strategy="structural_links", count=len(cards))
            return cards

        # Strategy 4: text-based fallback — find any h2/h3 with nearby description text
        logger.debug("selector_strategy", strategy="text_matching_fallback")
        return self._find_cards_by_text_pattern(soup)

    def _find_cards_by_text_pattern(self, soup: BeautifulSoup) -> list[Tag]:
        """Last-resort: walk the DOM and collect link elements near headings."""
        cards: list[Tag] = []
        for link in soup.find_all("a", href=True):
            href = link.get("href")
            href_str = ""
            if isinstance(href, str):
                href_str = href
            elif href is not None:
                href_str = str(href[0]) if href else ""
            if not href_str.startswith("/library/"):
                continue
            name = href_str.split("/library/")[-1].strip("/")
            if name and not name.startswith("?"):
                cards.append(link)
        return cards

    def _extract_model_from_card(self, card: Tag) -> dict[str, Any] | None:
        """Extract model metadata from a single card element using the selector chain."""
        name = self._extract_name(card)
        if not name:
            return None

        display_name = self._extract_display_name(card) or name
        description = self._extract_description(card) or ""
        capabilities = self._infer_capabilities(name)
        suggested_ram = self._estimate_ram(name, capabilities)

        return {
            "name": name,
            "display_name": display_name,
            "description": description,
            "capabilities": capabilities,
            "suggested_ram": suggested_ram,
            "parameter_variants": _extract_parameter_variants(name),
        }

    # ── Field extractors with fallback chain ──────────────────────

    def _extract_name(self, card: Tag) -> str | None:
        # data attribute
        for attr in ("data-model-name", "data-model", "data-slug"):
            val = card.get(attr)
            if val:
                return str(val).strip()

        # href-based extraction
        href = card.get("href")
        if isinstance(href, str):
            match = re.search(r"/library/([^/?]+)", href)
            if match:
                return match.group(1).strip()
        elif href is not None:
            # AttributeValueList — take first
            href_str = str(href[0]) if href else ""
            if href_str:
                match = re.search(r"/library/([^/?]+)", href_str)
                if match:
                    return match.group(1).strip()

        # heading text as last resort
        heading = card.find(["h1", "h2", "h3", "h4"])
        if heading:
            return heading.get_text(strip=True).lower().replace(" ", "-")

        return None

    def _extract_display_name(self, card: Tag) -> str | None:
        # Heading inside the card
        heading = card.find(["h1", "h2", "h3", "h4"])
        if heading:
            return heading.get_text(strip=True)

        # aria-label
        aria = card.get("aria-label")
        if aria:
            return str(aria)

        # title attribute
        title = card.get("title")
        if title:
            return str(title)

        return None

    def _extract_description(self, card: Tag) -> str | None:
        # <p> or <span> with description
        for tag_name in ("p", "span", "div"):
            for el in card.find_all(tag_name):
                text = el.get_text(strip=True)
                if text and len(text) > 10:
                    return text

        # aria-describedby or aria-description
        desc_id = card.get("aria-describedby")
        if desc_id:
            desc_el = card.find(id=desc_id)
            if desc_el:
                return desc_el.get_text(strip=True)

        aria_desc = card.get("aria-description")
        if aria_desc:
            return str(aria_desc)

        # Last resort: any long-ish text node
        text = card.get_text(strip=True)
        if text and len(text) > 20:
            lines = [line.strip() for line in text.split("\n") if line.strip()]
            for line in lines[1:]:
                if len(line) > 10:
                    return line
        return None

    # ── Capability / RAM inference ────────────────────────────────

    @staticmethod
    def _infer_capabilities(model_name: str) -> list[str]:
        name_lower = model_name.lower()
        caps = ["chat"]
        if any(x in name_lower for x in ("code", "coder", "starcoder", "deepseek", "codellama")):
            caps.append("code")
        if any(x in name_lower for x in ("vision", "llava", "bakllava")):
            caps.append("vision")
        if any(x in name_lower for x in ("embed", "nomic", "bge", "mxbai", "bert", "allminilm")):
            caps.append("embedding")
        if any(x in name_lower for x in ("reason", "phi", "orca", "qwen")):
            caps.append("reasoning")
        return list(set(caps))

    @staticmethod
    def _estimate_ram(model_name: str, capabilities: list[str]) -> str:
        name_lower = model_name.lower()
        if "embedding" in capabilities:
            return "1-2GB"
        if any(x in name_lower for x in ("phi", ":0.5b", ":1b", ":2b", ":2.7b", ":3b")):
            return "2-4GB"
        if any(x in name_lower for x in (":3b", ":4b", ":7b", ":8b")):
            return "6-8GB"
        if any(x in name_lower for x in (":14b", ":13b", ":12b")):
            return "12-16GB"
        if any(x in name_lower for x in (":34b", ":32b", ":30b")):
            return "24-32GB"
        if any(x in name_lower for x in (":70b", ":72b", ":65b")):
            return "48-64GB"
        if any(x in name_lower for x in (":405b", ":236b", ":180b")):
            return "128GB+"
        return "6-8GB"

    # ── Pagination ────────────────────────────────────────────────

    def _has_next_page(self, html: str) -> bool:
        soup = BeautifulSoup(html, "html.parser")
        # Look for "Next" link
        next_link = soup.find("a", string=re.compile(r"next", re.IGNORECASE))
        if next_link:
            return True
        # Regex fallback
        return bool(re.search(r'<a[^>]+href="/library\?page=\d+"[^>]*>\s*Next', html, re.IGNORECASE))

    # ── Cache ─────────────────────────────────────────────────────

    def _load_cache(self) -> dict[str, Any] | None:
        try:
            if not self._cache_file.exists():
                return None
            return json.loads(self._cache_file.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.warning("ollama_cache_load_failed", error=str(exc))
            return None

    def _save_cache(self, models: list[dict[str, Any]]) -> None:
        try:
            self._cache_dir.mkdir(parents=True, exist_ok=True)
            data = {"fetched_at": datetime.now(timezone.utc).isoformat(), "models": models}
            self._cache_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception as exc:
            logger.warning("ollama_cache_save_failed", error=str(exc))

    def _is_cache_valid(self, cache: dict[str, Any]) -> bool:
        if not cache or "fetched_at" not in cache:
            return False
        try:
            fetched_at = datetime.fromisoformat(cache["fetched_at"])
            age = datetime.now(timezone.utc) - fetched_at
            return age < timedelta(hours=self._cache_ttl_hours)
        except Exception:
            return False


# ── Standalone helpers (kept for backward compatibility) ──────────


def _extract_parameter_variants(name: str) -> list[dict[str, Any]]:
    variants: list[dict[str, Any]] = []
    base_name = name
    size_match = re.search(r":(\d+(\.\d+)?b)", name.lower())
    if size_match:
        base_name = name[: size_match.start()]
    pattern = re.compile(r"(\d+(\.\d+)?b)", re.IGNORECASE)
    if pattern.search(name):
        for match in pattern.finditer(name):
            variant_name = f"{base_name}:{match.group(1)}"
            size_bytes = _estimate_model_size(match.group(1))
            variants.append({"name": variant_name, "parameters": match.group(1).upper(), "size_bytes": size_bytes})
    if not variants:
        variants.append({"name": name, "parameters": "Unknown", "size_bytes": 0})
    return variants


def _estimate_model_size(size_str: str) -> int:
    try:
        size_str = size_str.lower().rstrip("b")
        if "x" in size_str:
            parts = size_str.split("x")
            num = float(parts[0]) * float(parts[1])
        else:
            num = float(size_str)
        if num >= 100:
            return int(num * 1_000_000_000)
        return int(num * 1_000_000_000_000)
    except Exception:
        return 0


# ── Module-level convenience functions (backward compat) ──────────

_default_scraper = OllamaLibraryScraper()


async def get_ollama_library_models_async(force_refresh: bool = False) -> list[dict[str, Any]]:
    return await _default_scraper.fetch_models(force_refresh)


def get_ollama_library_models(force_refresh: bool = False) -> list[dict[str, Any]]:
    return _default_scraper.fetch_models_sync(force_refresh)


if __name__ == "__main__":
    import asyncio

    models = asyncio.run(get_ollama_library_models_async())
    print(f"Found {len(models)} models")
    for m in models[:5]:
        print(f"  - {m['name']}: {m.get('description', '')[:50]}...")
