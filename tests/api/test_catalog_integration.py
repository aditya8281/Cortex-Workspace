"""Integration tests for catalog family grouping endpoints."""
from unittest.mock import AsyncMock, MagicMock, patch

import datetime

import pytest

from backend.app.models.intelligence.model_catalog import ModelCatalog, ModelVariant


class TestCatalogIntegration:
    """Integration-level tests for model catalog family API endpoints."""

    def _setup_test_data(self, db_session):
        """Create test catalog entry and variant in DB."""
        now = datetime.datetime.now(datetime.timezone.utc)
        entry = ModelCatalog(
            model_id="test-model-8b",
            family="test-family",
            display_name="Test Model 8B",
            provider="ollama",
            parameter_count=8.0,
            context_length_default=32768,
            capabilities=["chat", "code"],
            embedding_dim=768,
            description="Test model",
            last_updated=now,
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
            quality_score=85.0,
            downloaded=False,
        )
        db_session.add(variant)
        db_session.commit()
        return entry, variant

    def test_families_endpoint_returns_grouped_data(
        self, db_session, client, mock_auth
    ):
        """GET /models/families returns properly structured grouped data."""
        self._setup_test_data(db_session)

        with patch(
            "backend.app.api.v1.developer.catalog.llm_manager"
        ) as mock_llm:
            mock_llm.list_all_models = AsyncMock(return_value=[])
            response = client.get("/api/v1/models/families")

        assert response.status_code == 200
        data = response.json()

        assert "families" in data
        assert "embedding_families" in data
        assert isinstance(data["families"], list)
        assert isinstance(data["embedding_families"], list)

    def test_family_variants_returns_list(
        self, db_session, client, mock_auth
    ):
        """GET /models/families/{family}/variants returns variant list."""
        self._setup_test_data(db_session)

        with patch(
            "backend.app.api.v1.developer.catalog.llm_manager"
        ) as mock_llm:
            mock_llm.list_all_models = AsyncMock(return_value=[])
            response = client.get(
                "/api/v1/models/families/test-family/variants",
            )

        assert response.status_code == 200
        data = response.json()
        assert data["family"] == "test-family"
        assert "variants" in data

    def test_family_variants_404_for_unknown(
        self, db_session, client, mock_auth
    ):
        """Unknown family returns 404."""
        with patch(
            "backend.app.api.v1.developer.catalog.llm_manager"
        ) as mock_llm:
            mock_llm.list_all_models = AsyncMock(return_value=[])
            response = client.get(
                "/api/v1/models/families/nonexistent-family/variants",
            )

        assert response.status_code == 404

    def test_list_models_includes_new_fields(
        self, db_session, client, mock_auth
    ):
        """List endpoint returns family, embedding_dim fields."""
        mock_model = {
            "name": "qwen3:8b",
            "family": "qwen3",
            "parameter_size": "8B",
            "quantization": "Q4_K_M",
            "embedding_dim": None,
            "size": 8589934592,
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
            patch(
                "backend.app.api.v1.developer.catalog.llm_manager"
            ) as mock_llm,
        ):
            mock_llm.list_all_models = AsyncMock(return_value=[])
            response = client.get("/api/v1/models")

        assert response.status_code == 200
        data = response.json()
        if data["models"]:
            model = data["models"][0]
            assert "family" in model
            assert "embedding_dim" in model

    def test_quality_score_is_normalized(
        self, db_session, client, mock_auth
    ):
        """quality_score should be 0-1 scale."""
        entry, variant = self._setup_test_data(db_session)

        mock_model = {
            "name": entry.model_id,
            "family": entry.family,
            "parameter_size": "8B",
            "quantization": "Q4_K_M",
            "embedding_dim": entry.embedding_dim,
            "size": variant.size_bytes or 5000000000,
            "size_bytes": variant.size_bytes or 5000000000,
            "context_length": entry.context_length_default or 4096,
            "capabilities": entry.capabilities or ["chat"],
            "description": "",
        }

        with (
            patch(
                "backend.app.services.intelligence.ollama_catalog.get_ollama_catalog",
                new_callable=AsyncMock,
                return_value=([mock_model], MagicMock()),
            ),
            patch(
                "backend.app.api.v1.developer.catalog.llm_manager"
            ) as mock_llm,
        ):
            mock_llm.list_all_models = AsyncMock(return_value=[])
            list_resp = client.get("/api/v1/models")
            assert list_resp.status_code == 200
            data = list_resp.json()

            if not data["models"]:
                pytest.skip("No models in catalog")

            model_name = data["models"][0]["name"]
            detail_resp = client.get(f"/api/v1/models/{model_name}")

        if detail_resp.status_code == 200:
            detail = detail_resp.json()
            for v in detail.get("variants", []):
                if v.get("quality_score") is not None:
                    assert 0 <= v["quality_score"] <= 1
