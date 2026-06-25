"""Tests for model detail scraper."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.app.services.model_detail_scraper import (
    ModelDetail,
    ModelDetailScraper,
    ModelVariant,
    _guess_quantization,
    _parse_size_from_text,
)

# ── Fixtures ─────────────────────────────────────────────────────


@pytest.fixture
def scraper() -> ModelDetailScraper:
    return ModelDetailScraper()


@pytest.fixture
def sample_ollama_html() -> str:
    return """
    <html>
    <head><meta name="description" content="Meta Llama 3.1 8B parameter model."></head>
    <body>
        <h1>Llama 3.1</h1>
        <p>Meta Llama 3.1 is a powerful open-source large language model with 8B parameters.</p>
        <div class="tags">
            <code>llama3.1:8b</code>
            <code>llama3.1:70b</code>
            <code>llama3.1:8b-q4_0</code>
        </div>
        <div class="models">
            <tr><td>llama3.1:8b Q4_0</td><td>4.7 GB</td></tr>
            <tr><td>llama3.1:70b Q4_0</td><td>40 GB</td></tr>
        </div>
        <p>Context length: 128000 tokens</p>
        <p>Architecture: Transformer decoder-only</p>
        <p>License: llama3.1 community license</p>
    </body>
    </html>
    """


@pytest.fixture
def sample_hf_response() -> dict:
    return {
        "id": "TheBloke/Llama-2-7B-GGUF",
        "description": "Llama 2 7B in GGUF format.",
        "tags": ["llama", "gguf", "text-generation"],
        "license": "llama2",
        "siblings": [
            {"rfilename": "llama-2-7b.Q4_K_M.gguf"},
            {"rfilename": "llama-2-7b.Q8_0.gguf"},
        ],
    }


# ── Dataclass tests ──────────────────────────────────────────────


class TestModelDetail:
    def test_model_detail_defaults(self) -> None:
        detail = ModelDetail(model_id="test", display_name="Test")
        assert detail.model_id == "test"
        assert detail.display_name == "Test"
        assert detail.family == ""
        assert detail.parameter_count is None
        assert detail.architecture is None
        assert detail.context_length is None
        assert detail.capabilities == []
        assert detail.license is None
        assert detail.description == ""
        assert detail.tags == []
        assert detail.variants == []
        assert detail.source_url == ""

    def test_model_variant_defaults(self) -> None:
        variant = ModelVariant(name="model:7b")
        assert variant.name == "model:7b"
        assert variant.quantization == ""
        assert variant.size_bytes == 0
        assert variant.parameter_count == ""


# ── Initialization tests ─────────────────────────────────────────


class TestScraperInit:
    def test_scraper_initializes(self, scraper: ModelDetailScraper) -> None:
        assert scraper is not None

    def test_scraper_has_client(self, scraper: ModelDetailScraper) -> None:
        assert hasattr(scraper, "_client")

    def test_scraper_client_configured(self, scraper: ModelDetailScraper) -> None:
        assert scraper._client.timeout.read == 30.0


# ── Quantization guessing tests ──────────────────────────────────


class TestQuantizationGuessing:
    def test_q4_0(self) -> None:
        assert _guess_quantization("model:7b-q4_0") == "Q4_0"

    def test_q4_k_m(self) -> None:
        assert _guess_quantization("model:7b-Q4_K_M") == "Q4_K_M"

    def test_q5_0(self) -> None:
        assert _guess_quantization("model:7b-q5_0") == "Q5_0"

    def test_q5_k_m(self) -> None:
        assert _guess_quantization("model:7b-Q5_K_M") == "Q5_K_M"

    def test_q6_k(self) -> None:
        assert _guess_quantization("model:7b-q6_k") == "Q6_K"

    def test_q8_0(self) -> None:
        assert _guess_quantization("model:7b-q8_0") == "Q8_0"

    def test_f16(self) -> None:
        assert _guess_quantization("model:f16") == "F16"

    def test_no_quantization(self) -> None:
        assert _guess_quantization("model:7b") == ""


# ── Size parsing tests ───────────────────────────────────────────


class TestSizeParsing:
    def test_parse_gb(self) -> None:
        assert _parse_size_from_text("4.7 GB") == int(4.7 * 1024**3)

    def test_parse_mb(self) -> None:
        assert _parse_size_from_text("500 MB") == int(500 * 1024**2)

    def test_parse_kb(self) -> None:
        assert _parse_size_from_text("100 KB") == int(100 * 1024)

    def test_parse_no_match(self) -> None:
        assert _parse_size_from_text("no size info") == 0


# ── Ollama parsing tests ─────────────────────────────────────────


class TestOllamaParsing:
    def test_parse_ollama_page_basic(self, scraper: ModelDetailScraper, sample_ollama_html: str) -> None:
        detail = scraper._parse_ollama_page("llama3.1", sample_ollama_html, "https://ollama.com/library/llama3.1")
        assert detail.model_id == "llama3.1"
        assert detail.display_name == "Llama 3.1"
        assert "8B" in detail.description
        assert detail.source_url == "https://ollama.com/library/llama3.1"

    def test_parse_ollama_context_length(self, scraper: ModelDetailScraper, sample_ollama_html: str) -> None:
        detail = scraper._parse_ollama_page("llama3.1", sample_ollama_html, "https://ollama.com/library/llama3.1")
        assert detail.context_length == 128000

    def test_parse_ollama_architecture(self, scraper: ModelDetailScraper, sample_ollama_html: str) -> None:
        detail = scraper._parse_ollama_page("llama3.1", sample_ollama_html, "https://ollama.com/library/llama3.1")
        assert detail.architecture == "Transformer"

    def test_parse_ollama_license(self, scraper: ModelDetailScraper, sample_ollama_html: str) -> None:
        detail = scraper._parse_ollama_page("llama3.1", sample_ollama_html, "https://ollama.com/library/llama3.1")
        assert detail.license is not None
        assert "llama" in detail.license.lower()

    def test_parse_ollama_tags(self, scraper: ModelDetailScraper, sample_ollama_html: str) -> None:
        detail = scraper._parse_ollama_page("llama3.1", sample_ollama_html, "https://ollama.com/library/llama3.1")
        assert len(detail.tags) > 0

    def test_parse_ollama_variants(self, scraper: ModelDetailScraper, sample_ollama_html: str) -> None:
        detail = scraper._parse_ollama_page("llama3.1", sample_ollama_html, "https://ollama.com/library/llama3.1")
        assert len(detail.variants) > 0

    def test_parse_ollama_capabilities(self, scraper: ModelDetailScraper, sample_ollama_html: str) -> None:
        detail = scraper._parse_ollama_page("llama3.1", sample_ollama_html, "https://ollama.com/library/llama3.1")
        assert "chat" in detail.capabilities


# ── Capability inference tests ───────────────────────────────────


class TestCapabilityInference:
    def test_chat_model(self, scraper: ModelDetailScraper) -> None:
        caps = ModelDetailScraper._infer_capabilities("llama3.1", [])
        assert "chat" in caps

    def test_code_model(self, scraper: ModelDetailScraper) -> None:
        caps = ModelDetailScraper._infer_capabilities("codellama", [])
        assert "code" in caps

    def test_vision_model(self, scraper: ModelDetailScraper) -> None:
        caps = ModelDetailScraper._infer_capabilities("llava", [])
        assert "vision" in caps

    def test_embedding_model(self, scraper: ModelDetailScraper) -> None:
        caps = ModelDetailScraper._infer_capabilities("nomic-embed-text", [])
        assert "embedding" in caps

    def test_reasoning_model(self, scraper: ModelDetailScraper) -> None:
        caps = ModelDetailScraper._infer_capabilities("phi3", [])
        assert "reasoning" in caps


# ── Async scraping tests (mocked HTTP) ───────────────────────────


class TestScrapeOllama:
    @pytest.mark.asyncio
    async def test_scrape_ollama_success(self, scraper: ModelDetailScraper, sample_ollama_html: str) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = sample_ollama_html

        with patch.object(scraper._client, "get", new_callable=AsyncMock, return_value=mock_response):
            detail = await scraper.scrape_ollama_detail("llama3.1")
            assert detail is not None
            assert detail.model_id == "llama3.1"
            assert detail.display_name == "Llama 3.1"

    @pytest.mark.asyncio
    async def test_scrape_ollama_not_found(self, scraper: ModelDetailScraper) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch.object(scraper._client, "get", new_callable=AsyncMock, return_value=mock_response):
            detail = await scraper.scrape_ollama_detail("nonexistent-model")
            assert detail is None

    @pytest.mark.asyncio
    async def test_scrape_ollama_network_error(self, scraper: ModelDetailScraper) -> None:
        with patch.object(scraper._client, "get", new_callable=AsyncMock, side_effect=Exception("network error")):
            detail = await scraper.scrape_ollama_detail("llama3.1")
            assert detail is None


class TestScrapeHF:
    @pytest.mark.asyncio
    async def test_scrape_hf_success(self, scraper: ModelDetailScraper, sample_hf_response: dict) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_hf_response

        with patch.object(scraper._client, "get", new_callable=AsyncMock, return_value=mock_response):
            detail = await scraper.scrape_hf_detail("TheBloke/Llama-2-7B-GGUF")
            assert detail is not None
            assert detail.model_id == "TheBloke/Llama-2-7B-GGUF"
            assert detail.family == "TheBloke"
            assert detail.display_name == "Llama-2-7B-GGUF"
            assert detail.license == "llama2"
            assert "llama" in detail.tags
            assert len(detail.variants) == 2
            assert detail.variants[0].quantization == "Q4_K_M"
            assert detail.variants[1].quantization == "Q8_0"

    @pytest.mark.asyncio
    async def test_scrape_hf_not_found(self, scraper: ModelDetailScraper) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch.object(scraper._client, "get", new_callable=AsyncMock, return_value=mock_response):
            detail = await scraper.scrape_hf_detail("nonexistent/repo")
            assert detail is None

    @pytest.mark.asyncio
    async def test_scrape_hf_network_error(self, scraper: ModelDetailScraper) -> None:
        with patch.object(scraper._client, "get", new_callable=AsyncMock, side_effect=Exception("timeout")):
            detail = await scraper.scrape_hf_detail("TheBloke/Llama-2-7B-GGUF")
            assert detail is None


# ── Close tests ──────────────────────────────────────────────────


class TestCleanup:
    @pytest.mark.asyncio
    async def test_close(self, scraper: ModelDetailScraper) -> None:
        await scraper.close()
        assert scraper._client.is_closed
