"""Tests for the unified model catalog API."""

from unittest.mock import AsyncMock, MagicMock, patch


def test_list_models_includes_new_fields(client, mock_auth):
    """Verify that list models response includes family, parameter_size,
    quantization, and embedding_dim fields."""
    mock_model = {
        "name": "qwen3:8b",
        "family": "qwen3",
        "parameter_size": "8B",
        "quantization": "Q4_K_M",
        "embedding_dim": None,
        "size": 8589934592,  # 8 GB
        "size_bytes": 8589934592,
        "context_length": 32768,
        "capabilities": ["chat"],
        "description": "",
    }

    with (
        patch(
            "backend.app.services.intelligence.ollama_catalog.get_ollama_catalog",
            new_callable=AsyncMock,
            return_value=([mock_model], MagicMock()),
        ),
        patch("backend.app.api.v1.developer.catalog.llm_manager") as mock_llm,
    ):
        mock_llm.list_all_models = AsyncMock(return_value=[])
        response = client.get("/api/v1/models")
        assert response.status_code == 200
        data = response.json()
        assert "models" in data
        if data["models"]:
            model = data["models"][0]
            assert "family" in model, "Missing 'family' in list response"
            assert "parameter_size" in model, "Missing 'parameter_size' in list response"
            assert "quantization" in model, "Missing 'quantization' in list response"
            assert "embedding_dim" in model, "Missing 'embedding_dim' in list response"
