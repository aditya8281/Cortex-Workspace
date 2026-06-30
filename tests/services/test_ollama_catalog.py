import pytest
from backend.app.services.intelligence.ollama_catalog import OllamaCatalogService


class TestParseNumCtx:
    def test_parse_num_ctx_from_parameters(self):
        params = "num_ctx=8192\ntemperature=0.7\n"
        result = OllamaCatalogService._parse_num_ctx(params)
        assert result == 8192

    def test_parse_num_ctx_from_parameters_with_space(self):
        params = "PARAMETER num_ctx 131072\n"
        result = OllamaCatalogService._parse_num_ctx(params)
        assert result == 131072

    def test_parse_num_ctx_missing(self):
        params = "temperature=0.7\n"
        result = OllamaCatalogService._parse_num_ctx(params)
        assert result is None

    def test_parse_num_ctx_empty(self):
        result = OllamaCatalogService._parse_num_ctx("")
        assert result is None

    def test_parse_num_ctx_none(self):
        result = OllamaCatalogService._parse_num_ctx(None)
        assert result is None
