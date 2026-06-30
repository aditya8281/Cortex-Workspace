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


class TestEmbeddingDetection:
    def test_detect_embedding_by_name(self):
        caps = OllamaCatalogService._detect_capabilities(template="", model_name="nomic-embed-text")
        assert "embedding" in caps

    def test_detect_embedding_bge(self):
        caps = OllamaCatalogService._detect_capabilities(template="", model_name="bge-m3")
        assert "embedding" in caps

    def test_detect_embedding_qwen(self):
        caps = OllamaCatalogService._detect_capabilities(template="", model_name="qwen3-embedding")
        assert "embedding" in caps

    def test_chat_model_not_embedding(self):
        caps = OllamaCatalogService._detect_capabilities(template="", model_name="qwen3:8b")
        assert "embedding" not in caps

    def test_parse_embedding_dim_from_parameters(self):
        params = "num_ctx=8192\nembedding_dim=768\n"
        dim = OllamaCatalogService._parse_embedding_dim(params)
        assert dim == 768

    def test_parse_embedding_dim_hidden_size(self):
        params = "hidden_size=1024\n"
        dim = OllamaCatalogService._parse_embedding_dim(params)
        assert dim == 1024

    def test_embedding_dim_fallback_known_model(self):
        dim = OllamaCatalogService._get_embedding_dim_fallback("nomic-embed-text")
        assert dim == 768

    def test_embedding_dim_fallback_unknown(self):
        dim = OllamaCatalogService._get_embedding_dim_fallback("some-random-model")
        assert dim is None

    def test_normalize_embedding_model(self):
        model = {
            "name": "nomic-embed-text:latest",
            "capabilities": ["completion"],
            "parameters": "num_ctx=8192\nembedding_dim=768\n"
        }
        OllamaCatalogService._normalize_model(model)
        assert "embedding" in model["capabilities"]
        assert "chat" not in model["capabilities"]
        assert model["embedding_dim"] == 768
