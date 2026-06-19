import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.api.deps import get_db
from backend.app.db.base import Base
from backend.app.intelligence.models import KnowledgeEntry  # noqa: F401
from backend.app.main import app
from backend.app.models.auth_event import AuthEvent  # noqa: F401
from backend.app.models.storage_registry import StorageRegistry  # noqa: F401
from backend.app.models.user import User  # noqa: F401


@pytest.fixture(scope="session")
def _engine():
    """Create a single in-memory SQLite engine for the entire test session.

    Tables are created once and reused.  Each test gets its own nested
    transaction that is rolled back after the test completes.
    """
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
    """Provide an isolated DB session per test using nested transactions.

    Each test begins a SAVEPOINT.  After the test, the SAVEPOINT is rolled
    back so no data leaks between tests.  FastAPI's ``get_db`` dependency
    is overridden to yield this session.
    """
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


@pytest.fixture(name="client")
def fixture_client():
    """Function-scoped TestClient — each test gets a fresh client."""
    with TestClient(app) as c:
        yield c
