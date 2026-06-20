"""Tests for Ollama library scraper with semantic selectors."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from backend.app.services.ollama_library_scraper import (
    OllamaLibraryScraper,
    _estimate_model_size,
    _extract_parameter_variants,
)

# ── Fixtures ─────────────────────────────────────────────────────


@pytest.fixture
def scraper(tmp_path: Path) -> OllamaLibraryScraper:
    return OllamaLibraryScraper(cache_dir=tmp_path, cache_ttl_hours=24)


@pytest.fixture
def sample_html() -> str:
    """HTML that mimics the ollama.com/library structure with model cards."""
    return """
    <html>
    <body>
      <div class="models">
        <a href="/library/llama3.1" class="model-card">
          <h2>Llama 3.1</h2>
          <p>Meta Llama 3.1 instruction-tuned model.</p>
        </a>
        <a href="/library/codellama" class="model-card">
          <h2>Code Llama</h2>
          <p>Code-specialized Llama model for code generation.</p>
        </a>
        <a href="/library/mistral" class="model-card">
          <h2>Mistral</h2>
          <p>Mistral AI 7B model.</p>
        </a>
        <a href="/library/nomic-embed-text" class="model-card">
          <h2>Nomic Embed Text</h2>
          <p>Nomic text embedding model.</p>
        </a>
      </div>
      <a href="/library?page=2">Next</a>
    </body>
    </html>
    """


@pytest.fixture
def html_with_data_attrs() -> str:
    """HTML with data-* attributes on model cards."""
    return """
    <html>
    <body>
      <div data-model-name="llama3.1">
        <h2>Llama 3.1</h2>
        <p>Meta Llama 3.1 instruction-tuned model.</p>
      </div>
      <div data-model-name="codellama">
        <h2>Code Llama</h2>
        <p>Code-specialized Llama model.</p>
      </div>
    </body>
    </html>
    """


@pytest.fixture
def html_no_next_page() -> str:
    """HTML without a Next link."""
    return """
    <html>
    <body>
      <a href="/library/llama3.1"><h2>Llama 3.1</h2><p>Meta model.</p></a>
    </body>
    </html>
    """


@pytest.fixture
def empty_html() -> str:
    return "<html><body></body></html>"


# ── Initialization tests ─────────────────────────────────────────


class TestScraperInit:
    def test_scraper_initializes(self) -> None:
        scraper = OllamaLibraryScraper()
        assert scraper is not None

    def test_scraper_has_cache_dir(self, tmp_path: Path) -> None:
        scraper = OllamaLibraryScraper(cache_dir=tmp_path)
        assert hasattr(scraper, "_cache_dir")
        assert scraper._cache_dir == tmp_path

    def test_scraper_has_cache_file(self, tmp_path: Path) -> None:
        scraper = OllamaLibraryScraper(cache_dir=tmp_path)
        assert scraper._cache_file.name == "ollama_library_catalog.json"

    def test_default_cache_ttl(self) -> None:
        scraper = OllamaLibraryScraper()
        assert scraper._cache_ttl_hours == 24

    def test_custom_cache_ttl(self, tmp_path: Path) -> None:
        scraper = OllamaLibraryScraper(cache_dir=tmp_path, cache_ttl_hours=48)
        assert scraper._cache_ttl_hours == 48


# ── Cache tests ──────────────────────────────────────────────────


class TestCache:
    def test_load_cache_empty(self, scraper: OllamaLibraryScraper) -> None:
        assert scraper._load_cache() is None

    def test_save_and_load_cache(self, scraper: OllamaLibraryScraper) -> None:
        models = [{"name": "llama3.1", "description": "Test"}]
        scraper._save_cache(models)
        cache = scraper._load_cache()
        assert cache is not None
        assert cache["models"] == models
        assert "fetched_at" in cache

    def test_cache_validity(self, scraper: OllamaLibraryScraper) -> None:
        # No cache
        assert not scraper._is_cache_valid({})

        # Valid cache
        cache = {"fetched_at": datetime.now(timezone.utc).isoformat(), "models": []}
        assert scraper._is_cache_valid(cache)

        # Expired cache
        old = {"fetched_at": (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat(), "models": []}
        assert not scraper._is_cache_valid(old)

    def test_cache_respects_ttl(self, tmp_path: Path) -> None:
        scraper = OllamaLibraryScraper(cache_dir=tmp_path, cache_ttl_hours=1)
        models = [{"name": "test"}]
        scraper._save_cache(models)

        # Cache should be valid
        cache = scraper._load_cache()
        assert scraper._is_cache_valid(cache)

    def test_load_cache_corrupt_file(self, scraper: OllamaLibraryScraper) -> None:
        scraper._cache_dir.mkdir(parents=True, exist_ok=True)
        scraper._cache_file.write_text("not json")
        assert scraper._load_cache() is None


# ── Parsing tests ────────────────────────────────────────────────


class TestParsing:
    def test_parse_page_models(self, scraper: OllamaLibraryScraper, sample_html: str) -> None:
        models = scraper._parse_page_models(sample_html)
        assert len(models) == 4
        names = {m["name"] for m in models}
        assert "llama3.1" in names
        assert "codellama" in names

    def test_parse_empty_html(self, scraper: OllamaLibraryScraper, empty_html: str) -> None:
        models = scraper._parse_page_models(empty_html)
        assert len(models) == 0

    def test_model_has_required_fields(self, scraper: OllamaLibraryScraper, sample_html: str) -> None:
        models = scraper._parse_page_models(sample_html)
        for model in models:
            assert "name" in model
            assert "display_name" in model
            assert "description" in model
            assert "capabilities" in model
            assert "suggested_ram" in model
            assert "parameter_variants" in model

    def test_model_name_from_href(self, scraper: OllamaLibraryScraper, sample_html: str) -> None:
        models = scraper._parse_page_models(sample_html)
        llama = next(m for m in models if m["name"] == "llama3.1")
        assert llama["name"] == "llama3.1"

    def test_data_attrs_priority(self, scraper: OllamaLibraryScraper, html_with_data_attrs: str) -> None:
        models = scraper._parse_page_models(html_with_data_attrs)
        assert len(models) == 2
        names = {m["name"] for m in models}
        assert "llama3.1" in names
        assert "codellama" in names


# ── Selector strategy tests ──────────────────────────────────────


class TestSelectorStrategies:
    def test_find_cards_data_attrs(self, scraper: OllamaLibraryScraper, html_with_data_attrs: str) -> None:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html_with_data_attrs, "html.parser")
        cards = scraper._find_model_cards(soup)
        assert len(cards) == 2

    def test_find_cards_semantic_html(self, scraper: OllamaLibraryScraper, sample_html: str) -> None:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(sample_html, "html.parser")
        cards = scraper._find_model_cards(soup)
        assert len(cards) >= 4

    def test_find_cards_structural_links(self, scraper: OllamaLibraryScraper, sample_html: str) -> None:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(sample_html, "html.parser")
        cards = scraper._find_model_cards(soup)
        assert len(cards) >= 4


# ── Field extraction tests ───────────────────────────────────────


class TestFieldExtraction:
    def test_extract_name_from_href(self, scraper: OllamaLibraryScraper) -> None:
        from bs4 import BeautifulSoup

        html = '<a href="/library/llama3.1"><h2>Llama</h2></a>'
        soup = BeautifulSoup(html, "html.parser")
        card = soup.find("a")
        assert scraper._extract_name(card) == "llama3.1"

    def test_extract_name_from_data_attr(self, scraper: OllamaLibraryScraper) -> None:
        from bs4 import BeautifulSoup

        html = '<div data-model-name="gemma2"><h2>Gemma 2</h2></div>'
        soup = BeautifulSoup(html, "html.parser")
        card = soup.find("div")
        assert scraper._extract_name(card) == "gemma2"

    def test_extract_display_name_from_heading(self, scraper: OllamaLibraryScraper) -> None:
        from bs4 import BeautifulSoup

        html = '<a href="/library/llama"><h2>Llama 3.1</h2></a>'
        soup = BeautifulSoup(html, "html.parser")
        card = soup.find("a")
        assert scraper._extract_display_name(card) == "Llama 3.1"

    def test_extract_description_from_p(self, scraper: OllamaLibraryScraper) -> None:
        from bs4 import BeautifulSoup

        html = '<a href="/library/llama"><h2>Llama</h2><p>Meta Llama model for chat.</p></a>'
        soup = BeautifulSoup(html, "html.parser")
        card = soup.find("a")
        desc = scraper._extract_description(card)
        assert desc is not None
        assert "Meta Llama" in desc


# ── Capability inference tests ───────────────────────────────────


class TestCapabilityInference:
    def test_chat_model(self) -> None:
        caps = OllamaLibraryScraper._infer_capabilities("llama3.1")
        assert "chat" in caps

    def test_code_model(self) -> None:
        caps = OllamaLibraryScraper._infer_capabilities("codellama")
        assert "code" in caps
        assert "chat" in caps

    def test_vision_model(self) -> None:
        caps = OllamaLibraryScraper._infer_capabilities("llava")
        assert "vision" in caps

    def test_embedding_model(self) -> None:
        caps = OllamaLibraryScraper._infer_capabilities("nomic-embed-text")
        assert "embedding" in caps

    def test_reasoning_model(self) -> None:
        caps = OllamaLibraryScraper._infer_capabilities("phi3")
        assert "reasoning" in caps


# ── RAM estimation tests ─────────────────────────────────────────


class TestRamEstimation:
    def test_embedding_low_ram(self) -> None:
        ram = OllamaLibraryScraper._estimate_ram("nomic-embed-text", ["embedding"])
        assert "2GB" in ram or "1GB" in ram

    def test_small_model(self) -> None:
        ram = OllamaLibraryScraper._estimate_ram("phi3:3.8b", ["chat"])
        assert "2GB" in ram or "4GB" in ram

    def test_large_model(self) -> None:
        ram = OllamaLibraryScraper._estimate_ram("llama3.1:70b", ["chat"])
        assert "48GB" in ram or "64GB" in ram


# ── Parameter variant tests ──────────────────────────────────────


class TestParameterVariants:
    def test_single_variant(self) -> None:
        variants = _extract_parameter_variants("llama3:8b")
        assert len(variants) == 1
        assert variants[0]["parameters"] == "8B"

    def test_multiple_variants(self) -> None:
        variants = _extract_parameter_variants("llama2")
        assert len(variants) >= 1

    def test_no_variant(self) -> None:
        variants = _extract_parameter_variants("unknown-model")
        assert len(variants) == 1
        assert variants[0]["parameters"] == "Unknown"


class TestModelSizeEstimation:
    def test_seven_billion(self) -> None:
        assert _estimate_model_size("7b") == 7_000_000_000_000

    def test_seventy_billion(self) -> None:
        assert _estimate_model_size("70b") == 70_000_000_000_000

    def test_moe_mix(self) -> None:
        size = _estimate_model_size("8x7b")
        assert size == 56_000_000_000_000

    def test_invalid_returns_zero(self) -> None:
        assert _estimate_model_size("abc") == 0


# ── Pagination tests ─────────────────────────────────────────────


class TestPagination:
    def test_has_next_page_true(self, scraper: OllamaLibraryScraper, sample_html: str) -> None:
        assert scraper._has_next_page(sample_html)

    def test_has_next_page_false(self, scraper: OllamaLibraryScraper, html_no_next_page: str) -> None:
        assert not scraper._has_next_page(html_no_next_page)


# ── Integration tests (mocked HTTP) ──────────────────────────────


class TestFetchModels:
    @pytest.mark.asyncio
    async def test_fetch_models_from_cache(self, scraper: OllamaLibraryScraper) -> None:
        cached = [{"name": "llama3.1"}]
        scraper._save_cache(cached)
        result = await scraper.fetch_models()
        assert result == cached

    @pytest.mark.asyncio
    async def test_fetch_models_stale_cache(self, scraper: OllamaLibraryScraper) -> None:
        """When scraping fails, stale cache should be returned."""
        old = [{"name": "stale"}]
        scraper._save_cache(old)
        # Manually age the cache
        cache_data = json.loads(scraper._cache_file.read_text())
        old_time = (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat()
        cache_data["fetched_at"] = old_time
        scraper._cache_file.write_text(json.dumps(cache_data))

        # Mock fetch to fail
        with patch.object(scraper, "_scrape_all_pages", side_effect=Exception("network error")):
            result = await scraper.fetch_models()
        assert result == old

    @pytest.mark.asyncio
    async def test_fetch_models_hardcoded_fallback(self, scraper: OllamaLibraryScraper) -> None:
        """When scraping fails and no cache, hardcoded list should be used."""
        with patch.object(scraper, "_scrape_all_pages", side_effect=Exception("network error")):
            result = await scraper.fetch_models()
        assert len(result) > 0
        assert result[0]["name"] == "llama3.1"


# ── Backward compatibility tests ─────────────────────────────────


class TestBackwardCompat:
    def test_get_ollama_library_models_returns_list(self) -> None:
        from backend.app.services.ollama_library_scraper import get_ollama_library_models

        result = get_ollama_library_models(force_refresh=False)
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_ollama_library_models_async_returns_list(self) -> None:
        from backend.app.services.ollama_library_scraper import get_ollama_library_models_async

        result = await get_ollama_library_models_async(force_refresh=False)
        assert isinstance(result, list)
