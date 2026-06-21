"""Root conftest — shared fixtures for all test directories."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker

from backend.app.api.deps import get_current_user, get_db
from backend.app.db.base import Base
from backend.app.intelligence.models import KnowledgeEntry  # noqa: F401
from backend.app.main import app
from backend.app.models.auth_event import AuthEvent  # noqa: F401
from backend.app.models.document import Document, DocumentChunk  # noqa: F401
from backend.app.models.embedding_cache import EmbeddingCache  # noqa: F401
from backend.app.models.model_catalog import ModelCatalog, ModelVariant  # noqa: F401
from backend.app.models.repo_index import CodeChunk, RepoIndex  # noqa: F401
from backend.app.models.storage_registry import StorageRegistry  # noqa: F401
from backend.app.models.user import User  # noqa: F401
from backend.app.models.user_settings import UserModelSettings  # noqa: F401


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
        patch("backend.app.services.model_downloader.download_manager", mock_dm),
        patch("backend.app.services.file_watcher_v2.get_file_watcher_v2", return_value=mock_fw),
        patch("backend.app.services.memory_manager.get_vector_db", return_value=mock_vdb),
        patch("backend.app.services.memory_manager.get_embedding_service", return_value=mock_embedder),
    ]
    for p in patches:
        p.start()

    with TestClient(app) as c:
        yield c

    for p in patches:
        p.stop()


@pytest.fixture()
def db_session(_db_session):
    """Alias for _db_session for clarity in new tests."""
    return _db_session
