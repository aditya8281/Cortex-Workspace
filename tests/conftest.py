"""Conftest for tests/ — shared fixtures and external service mocks."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker

from backend.app.api.deps import get_current_user, get_db
from backend.app.db.base import Base

# Ensure all models are imported so Base.metadata knows about them.
from backend.app.intelligence.models import KnowledgeEntry  # noqa: F401
from backend.app.main import app
from backend.app.models.awareness.repo_index import CodeChunk, RepoIndex  # noqa: F401
from backend.app.models.intelligence.embedding_cache import EmbeddingCache  # noqa: F401
from backend.app.models.intelligence.model_catalog import ModelCatalog, ModelVariant  # noqa: F401
from backend.app.models.interaction.user import User  # noqa: F401
from backend.app.models.memory.document import Document, DocumentChunk  # noqa: F401
from backend.app.models.memory.episodic import EpisodicMemory  # noqa: F401
from backend.app.models.memory.memory_graph import MemoryEdge, MemoryNode  # noqa: F401
from backend.app.models.memory.semantic import SemanticMemory  # noqa: F401
from backend.app.models.memory.storage_registry import StorageRegistry  # noqa: F401
from backend.app.models.memory.working import WorkingMemory  # noqa: F401
from backend.app.models.privacy.access_policy import AccessPolicy  # noqa: F401
from backend.app.models.privacy.audit_log import AuditLog  # noqa: F401
from backend.app.models.privacy.auth_event import AuthEvent  # noqa: F401
from backend.app.models.privacy.consent import ConsentRecord  # noqa: F401
from backend.app.models.privacy.data_deletion import DataDeletionRequest  # noqa: F401
from backend.app.models.privacy.data_export import DataExport  # noqa: F401
from backend.app.models.privacy.role import Permission, Role  # noqa: F401
from backend.app.models.privacy.user_settings import UserModelSettings  # noqa: F401
from backend.app.models.cognition.task_plan import TaskPlan  # noqa: F401
from backend.app.models.cognition.error_analysis import ErrorAnalysis  # noqa: F401
from backend.app.models.cognition.hypothesis import Hypothesis  # noqa: F401
from backend.app.models.cognition.confidence_score import ConfidenceScore  # noqa: F401
from backend.app.models.execution.tool_execution import ToolExecution  # noqa: F401
from backend.app.models.execution.workflow import Workflow  # noqa: F401


@compiles(JSONB, "sqlite")
def _compile_jsonb_sqlite(type_, compiler, **kw):
    return "JSON"


@pytest.fixture(scope="session")
def _engine():
    """Create a single in-memory SQLite engine for the entire test session."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(autouse=True)
def _db_session(_engine):
    """Provide an isolated DB session per test using nested transactions."""
    connection = _engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection, autocommit=False, autoflush=False)()

    def _override():
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = _override
    yield session
    app.dependency_overrides.clear()
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def mock_auth():
    """Provide a mock authenticated user for tests that need it."""
    mock_user = MagicMock(spec=User)
    mock_user.id = 1
    mock_user.username = "test_user"
    mock_user.full_name = "Test User"
    mock_user.role = "user"
    mock_user.nickname = "testnick"
    mock_user.bio = None
    mock_user.description = None
    mock_user.profile_photo = None
    mock_user.handles_json = {}
    mock_user.preferences_json = {}
    mock_user.vault_locked = True
    mock_user.github_username = None
    mock_user.created_at = None
    mock_user.updated_at = None
    mock_user.deleted_at = None

    def _override_current_user():
        return mock_user

    app.dependency_overrides[get_current_user] = _override_current_user
    yield mock_user
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture(name="client")
def fixture_client():
    """Function-scoped TestClient — each test gets a fresh client."""
    mock_dm = MagicMock()
    mock_dm.start = AsyncMock()
    mock_dm.stop = AsyncMock()
    mock_vdb = MagicMock()
    mock_vdb.upsert = MagicMock()
    mock_vdb.search = MagicMock(return_value=[])
    mock_vdb.delete = MagicMock()
    mock_embedder = MagicMock()
    mock_embedder.embed_single = MagicMock(return_value=[0.1] * 128)
    mock_embedder.embed_batch = MagicMock(return_value=[[0.1] * 128])
    mock_embedder.compute_embedding_id = MagicMock(return_value="test_id")

    mock_fw = MagicMock()

    patches = [
        patch("backend.app.services.download.downloader.download_manager", mock_dm),
        patch("backend.app.services.awareness.file_watcher.get_file_watcher_v2", return_value=mock_fw),
        patch("backend.app.services.memory.manager.get_vector_db", return_value=mock_vdb),
        patch("backend.app.services.memory.manager.get_embedding_service", return_value=mock_embedder),
    ]
    for p in patches:
        p.start()

    with TestClient(app) as c:
        yield c

    for p in patches:
        p.stop()


@pytest.fixture(autouse=True)
def _mock_external_services():
    """Mock vector DB, embedding service, cache, and RAG pipeline."""
    mock_vector_db = MagicMock()
    mock_vector_db.collection_exists.return_value = True
    mock_vector_db.upsert.return_value = None
    mock_vector_db.search.return_value = []
    mock_vector_db.delete.return_value = None
    mock_vector_db.list_collections.return_value = []

    mock_embedder = MagicMock()
    mock_embedder.embed_single.return_value = [0.1] * 768
    mock_embedder.embed_batch.side_effect = lambda texts: [[0.1] * 768 for _ in texts]
    mock_embedder.compute_embedding_id.return_value = "test-embedding-id"

    mock_cache = MagicMock()
    mock_cache.get.return_value = None
    mock_cache.put.return_value = None
    mock_cache.invalidate.return_value = 0

    mock_file_watcher = MagicMock()
    mock_file_watcher.watch.return_value = True
    mock_file_watcher.unwatch.return_value = True
    mock_file_watcher.start.return_value = None
    mock_file_watcher.stop.return_value = None

    mock_rag_pipeline = MagicMock()
    mock_rag_pipeline.retrieve_context.return_value = MagicMock(
        results=[], formatted_context="", total_tokens=0, source_count=0
    )
    mock_rag_pipeline.build_messages.return_value = [
        {"role": "system", "content": "You are Cortex, a helpful AI assistant."},
    ]
    mock_rag_pipeline.consolidate.return_value = []

    mock_fulltext = MagicMock()
    mock_fulltext.search_code.return_value = []
    mock_fulltext.search_documents.return_value = []

    with (
        patch("backend.app.services.memory.manager.get_vector_db", return_value=mock_vector_db),
        patch("backend.app.services.memory.manager.get_embedding_service", return_value=mock_embedder),
        patch("backend.app.services.awareness.repository.get_embedding_service", return_value=mock_embedder),
        patch("backend.app.services.awareness.repository.get_vector_db", return_value=mock_vector_db),
        patch("backend.app.services.intelligence.embedding_cache.get_embedding_cache", return_value=mock_cache),
        patch("backend.app.services.memory.deletion.get_vector_db", return_value=mock_vector_db),
        patch("backend.app.services.memory.deletion.get_embedding_cache", return_value=mock_cache),
        patch("backend.app.services.memory.document_indexer.get_vector_db", return_value=mock_vector_db),
        patch("backend.app.services.memory.document_indexer.get_embedding_service", return_value=mock_embedder),
        patch("backend.app.services.memory.document_indexer.get_embedding_cache", return_value=mock_cache),
        patch("backend.app.services.memory.indexing_orchestrator.get_file_watcher_v2", return_value=mock_file_watcher),
        patch("backend.app.services.intelligence.hybrid_retrieval.get_vector_db", return_value=mock_vector_db),
        patch("backend.app.services.intelligence.hybrid_retrieval.get_embedding_service", return_value=mock_embedder),
        patch("backend.app.services.intelligence.hybrid_retrieval.get_fulltext_search", return_value=mock_fulltext),
        patch("backend.app.services.intelligence.rag_pipeline.get_rag_pipeline", return_value=mock_rag_pipeline),
    ):
        yield


@pytest.fixture()
def db_session(_db_session):
    """Alias for _db_session for clarity in new tests."""
    return _db_session
