"""Tests for the unified model catalog API."""
from unittest.mock import AsyncMock, MagicMock, patch

from backend.app.models.intelligence.model_catalog import ModelCatalog, ModelVariant


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


def test_get_families(db_session, client, mock_auth):
    """Test that GET /models/families returns grouped families."""
    import datetime

    entry = ModelCatalog(
        model_id="test-model-8b",
        family="test-family",
        display_name="Test Model 8B",
        provider="ollama",
        parameter_count=8.0,
        context_length_default=32768,
        capabilities=["chat", "code"],
        description="Test model",
        last_updated=datetime.datetime.now(datetime.timezone.utc),
    )
    db_session.add(entry)
    db_session.flush()

    variant = ModelVariant(
        model_catalog_id=entry.id,
        variant_id="test-model-8b:q4_k_m",
        quantization="Q4_K_M",
        parameter_count=8.0,
        size_bytes=5000000000,
        size_gb=4.66,
        downloaded=False,
    )
    db_session.add(variant)
    db_session.commit()

    with patch("backend.app.api.v1.developer.catalog.llm_manager") as mock_llm:
        mock_llm.list_all_models = AsyncMock(return_value=[])
        response = client.get("/api/v1/models/families")
        assert response.status_code == 200
        data = response.json()
        assert "families" in data
        assert "embedding_families" in data
        assert "total_families" in data
        assert "total_models" in data
        assert data["total_models"] == 1
        assert data["total_families"] == 1


def test_get_family_variants(db_session, client, mock_auth):
    """Test that GET /models/families/{family}/variants returns variants."""
    import datetime

    entry = ModelCatalog(
        model_id="test-model-8b",
        family="test-family",
        display_name="Test Model 8B",
        provider="ollama",
        parameter_count=8.0,
        context_length_default=32768,
        capabilities=["chat", "code"],
        description="Test model",
        last_updated=datetime.datetime.now(datetime.timezone.utc),
    )
    db_session.add(entry)
    db_session.flush()

    variant = ModelVariant(
        model_catalog_id=entry.id,
        variant_id="test-model-8b:q4_k_m",
        quantization="Q4_K_M",
        parameter_count=8.0,
        size_bytes=5000000000,
        size_gb=4.66,
        downloaded=False,
    )
    db_session.add(variant)
    db_session.commit()

    with patch("backend.app.api.v1.developer.catalog.llm_manager") as mock_llm:
        mock_llm.list_all_models = AsyncMock(return_value=[])
        response = client.get("/api/v1/models/families/test-family/variants")
        assert response.status_code == 200
        data = response.json()
        assert data["family"] == "test-family"
        assert "variants" in data
        assert len(data["variants"]) == 1
        assert data["variants"][0]["model_id"] == "test-model-8b:q4_k_m"
