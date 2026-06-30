"""Tests for catalog model ingestion — enrichment field piping to DB."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from backend.app.models.intelligence.model_catalog import ModelCatalog
from backend.app.services.intelligence.model_catalog import CatalogueManager
from backend.app.services.sync.service import SyncService

_NOW = datetime.now(timezone.utc)


class TestCatalogIngestionUnit:
    """Test that enrichment fields are properly piped to DB during ingestion."""

    def _make_entry(self, db_session, **kwargs) -> ModelCatalog:
        defaults = dict(
            family="test",
            provider="ollama",
            last_updated=_NOW,
        )
        defaults.update(kwargs)
        entry = ModelCatalog(**defaults)
        db_session.add(entry)
        return entry

    def test_ingest_sets_license(self, db_session):
        """License from enrichment dict should be stored."""
        entry = self._make_entry(
            db_session, model_id="test-license-model",
            display_name="Test License Model",
        )
        db_session.flush()

        # Simulate enrichment dict
        entry.license = "Apache-2.0"
        entry.recommended_use_cases = ["general chat", "Q&A"]
        db_session.commit()

        loaded = (
            db_session.query(ModelCatalog)
            .filter_by(model_id="test-license-model")
            .first()
        )
        assert loaded.license == "Apache-2.0"

    def test_ingest_sets_context_length(self, db_session):
        """context_length from enrichment should populate context_length_default."""
        entry = self._make_entry(
            db_session, model_id="test-ctx-model",
            display_name="Test Ctx Model",
            context_length_default=4096,
        )
        db_session.flush()

        # Simulate enrichment providing real context_length
        entry.context_length_default = 8192
        db_session.commit()

        loaded = (
            db_session.query(ModelCatalog)
            .filter_by(model_id="test-ctx-model")
            .first()
        )
        assert loaded.context_length_default == 8192

    def test_ingest_sets_embedding_fields(self, db_session):
        """embedding_dim and pooling_type should be stored."""
        entry = self._make_entry(
            db_session, model_id="test-embed-model",
            display_name="Test Embed Model",
        )
        db_session.flush()

        entry.embedding_dim = 768
        entry.pooling_type = "mean"
        db_session.commit()

        loaded = (
            db_session.query(ModelCatalog)
            .filter_by(model_id="test-embed-model")
            .first()
        )
        assert loaded.embedding_dim == 768
        assert loaded.pooling_type == "mean"

    def test_ingest_embedding_use_cases(self, db_session):
        """Embedding models get embedding-specific use cases."""
        entry = self._make_entry(
            db_session, model_id="test-embed-caps",
            display_name="Test Embed Caps",
        )
        db_session.flush()

        entry.recommended_use_cases = ["semantic search", "RAG", "text embeddings"]
        db_session.commit()

        loaded = (
            db_session.query(ModelCatalog)
            .filter_by(model_id="test-embed-caps")
            .first()
        )
        assert "semantic search" in loaded.recommended_use_cases

    def test_ingest_sets_architecture(self, db_session):
        """Architecture from enrichment dict should be stored."""
        entry = self._make_entry(
            db_session, model_id="test-arch-model",
            display_name="Test Arch Model",
        )
        db_session.flush()

        entry.architecture = "llama"
        db_session.commit()

        loaded = (
            db_session.query(ModelCatalog)
            .filter_by(model_id="test-arch-model")
            .first()
        )
        assert loaded.architecture == "llama"


@pytest.mark.usefixtures("_db_session")
class TestComputeRecommendedUseCases:
    """Test the _compute_recommended_use_cases static helper."""

    def test_embedding_capabilities(self):
        """Embedding models get embedding-specific use cases."""
        result = CatalogueManager._compute_recommended_use_cases(["embedding"])
        assert result == ["semantic search", "RAG", "text embeddings"]

    def test_code_capabilities(self):
        """Code models get code-specific use cases."""
        result = CatalogueManager._compute_recommended_use_cases(["code"])
        assert result == ["code generation", "programming assistance"]

    def test_vision_capabilities(self):
        """Vision models get vision-specific use cases."""
        result = CatalogueManager._compute_recommended_use_cases(["vision"])
        assert result == ["image understanding", "visual Q&A"]

    def test_chat_capabilities(self):
        """Chat models get general use cases."""
        result = CatalogueManager._compute_recommended_use_cases(["chat"])
        assert result == ["general chat", "Q&A"]

    def test_mixed_capabilities_embedding_priority(self):
        """Embedding capability takes priority over others."""
        result = CatalogueManager._compute_recommended_use_cases(
            ["embedding", "chat"]
        )
        assert result == ["semantic search", "RAG", "text embeddings"]

    def test_empty_capabilities(self):
        """Empty capabilities get default general use cases."""
        result = CatalogueManager._compute_recommended_use_cases([])
        assert result == ["general chat", "Q&A"]

    def test_sync_service_matches_catalogue_manager(self):
        """Both services should produce identical use cases for same input."""
        cases = [
            (["embedding"], ["semantic search", "RAG", "text embeddings"]),
            (["code"], ["code generation", "programming assistance"]),
            (["vision"], ["image understanding", "visual Q&A"]),
            (["chat"], ["general chat", "Q&A"]),
            ([], ["general chat", "Q&A"]),
        ]
        for capabilities, expected in cases:
            cm_result = CatalogueManager._compute_recommended_use_cases(capabilities)
            sync_result = SyncService._compute_recommended_use_cases(capabilities)
            assert cm_result == expected
            assert sync_result == expected


class TestCatalogIngestionEndToEnd:
    """Test the actual CatalogueManager.ingest_from_catalog with mock catalog data."""

    @patch(
        "backend.app.services.intelligence.ollama_catalog.get_ollama_catalog_sync"
    )
    def test_ingest_pipes_all_enrichment_fields(
        self, mock_get_catalog, db_session
    ):
        """ingest_from_catalog should pipe license, architecture, context_length,
        embedding_dim, pooling_type, and recommended_use_cases to DB."""
        mock_get_catalog.return_value = (
            [
                {
                    "name": "llama3:8b",
                    "family": "llama",
                    "parameter_size": "8B",
                    "capabilities": ["chat"],
                    "description": "Meta Llama 3 8B",
                    "source": "registry",
                    "size": 4700000000,
                    "size_bytes": 4700000000,
                    "quantization": "Q4_K_M",
                    "license": "Llama 3 Community",
                    "architecture": "llama",
                    "context_length": 8192,
                    "embedding_dim": None,
                    "pooling_type": None,
                },
                {
                    "name": "nomic-embed-text:v1.5",
                    "family": "nomic",
                    "parameter_size": "137M",
                    "capabilities": ["embedding"],
                    "description": "Nomic Embed Text v1.5",
                    "source": "registry",
                    "size": 87000000,
                    "size_bytes": 87000000,
                    "quantization": "Q8_0",
                    "license": "Apache-2.0",
                    "architecture": "bert",
                    "context_length": 2048,
                    "embedding_dim": 768,
                    "pooling_type": "mean",
                },
                {
                    "name": "codellama:7b",
                    "family": "codellama",
                    "parameter_size": "7B",
                    "capabilities": ["code", "chat"],
                    "description": "CodeLlama 7B",
                    "source": "registry",
                    "size": 3600000000,
                    "size_bytes": 3600000000,
                    "quantization": "Q4_K_M",
                    "license": "Llama 2",
                    "architecture": "llama",
                    "context_length": 16384,
                    "embedding_dim": None,
                    "pooling_type": None,
                },
            ],
            MagicMock(),
        )

        mgr = CatalogueManager(db_session)
        count = mgr.ingest_from_catalog()

        assert count == 3

        # Verify llama3:8b was ingested with correct fields
        llama3 = (
            db_session.query(ModelCatalog)
            .filter_by(model_id="llama3")
            .first()
        )
        assert llama3 is not None
        assert llama3.license == "Llama 3 Community"
        assert llama3.architecture == "llama"
        assert llama3.context_length_default == 8192
        assert llama3.recommended_use_cases == ["general chat", "Q&A"]

        # Verify nomic-embed-text was ingested with all enrichment fields
        nomic = (
            db_session.query(ModelCatalog)
            .filter_by(model_id="nomic-embed-text")
            .first()
        )
        assert nomic is not None
        assert nomic.license == "Apache-2.0"
        assert nomic.architecture == "bert"
        assert nomic.context_length_default == 2048
        assert nomic.embedding_dim == 768
        assert nomic.pooling_type == "mean"
        assert nomic.recommended_use_cases == [
            "semantic search",
            "RAG",
            "text embeddings",
        ]

        # Verify codellama:7b use cases reflect code capability
        codellama = (
            db_session.query(ModelCatalog)
            .filter_by(model_id="codellama")
            .first()
        )
        assert codellama is not None
        assert codellama.license == "Llama 2"
        assert codellama.architecture == "llama"
        assert codellama.context_length_default == 16384
        assert codellama.recommended_use_cases == [
            "code generation",
            "programming assistance",
        ]

    @patch(
        "backend.app.services.intelligence.ollama_catalog.get_ollama_catalog_sync"
    )
    def test_ingest_updates_existing_entries(
        self, mock_get_catalog, db_session
    ):
        """Ingestion should update enrichment fields on existing records."""
        # Pre-seed an existing entry with default values
        existing = ModelCatalog(
            model_id="llama3",
            family="llama",
            display_name="Old Name",
            provider="ollama",
            context_length_default=4096,
            capabilities=["chat"],
            last_updated=_NOW,
        )
        db_session.add(existing)
        db_session.commit()

        mock_get_catalog.return_value = (
            [
                {
                    "name": "llama3:8b",
                    "family": "llama",
                    "parameter_size": "8B",
                    "capabilities": ["chat"],
                    "description": "Updated description",
                    "source": "registry",
                    "size": 4700000000,
                    "size_bytes": 4700000000,
                    "quantization": "Q4_K_M",
                    "license": "Llama 3 Community",
                    "architecture": "llama",
                    "context_length": 8192,
                    "embedding_dim": None,
                    "pooling_type": None,
                },
            ],
            MagicMock(),
        )

        mgr = CatalogueManager(db_session)
        count = mgr.ingest_from_catalog()

        # Should return 0 (no new entries, just update)
        assert count == 0

        # Refresh and verify fields were updated
        db_session.refresh(existing)
        assert existing.license == "Llama 3 Community"
        assert existing.architecture == "llama"
        assert existing.context_length_default == 8192
        assert existing.recommended_use_cases == ["general chat", "Q&A"]

    @patch(
        "backend.app.services.intelligence.ollama_catalog.get_ollama_catalog_sync"
    )
    def test_ingest_does_not_overwrite_existing_fields(
        self, mock_get_catalog, db_session
    ):
        """Ingestion should not overwrite existing fields with empty values."""
        existing = ModelCatalog(
            model_id="existing-model",
            family="test",
            display_name="Existing Model",
            provider="ollama",
            license="Custom License",
            architecture="custom-arch",
            context_length_default=8192,
            capabilities=["chat"],
            last_updated=_NOW,
        )
        db_session.add(existing)
        db_session.commit()

        # New catalog data has None for license and architecture,
        # and no context_length
        mock_get_catalog.return_value = (
            [
                {
                    "name": "existing-model:latest",
                    "family": "test",
                    "parameter_size": "7B",
                    "capabilities": ["chat"],
                    "description": "Existing model desc",
                    "source": "registry",
                    "size": 1000000000,
                    "size_bytes": 1000000000,
                    "quantization": "Q4_K_M",
                    "license": None,
                    "architecture": None,
                    "embedding_dim": None,
                    "pooling_type": None,
                    # No context_length key
                },
            ],
            MagicMock(),
        )

        mgr = CatalogueManager(db_session)
        mgr.ingest_from_catalog()

        db_session.refresh(existing)
        # Existing should retain its original values
        assert existing.license == "Custom License"
        assert existing.architecture == "custom-arch"
        assert existing.context_length_default == 8192
