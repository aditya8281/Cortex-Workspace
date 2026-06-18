import os
import tempfile

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


@pytest.fixture(autouse=True, scope="session")
def _clean_db():
    """Provide a single isolated file-backed database for the entire test session.

    Uses a temp file (not in-memory) so all connections see the same data.
    Tables are created from SQLAlchemy models so the fixture always matches
    the current ORM definitions — no Alembic needed.
    """
    db_fd, db_path = tempfile.mkstemp(suffix=".test.db")
    os.close(db_fd)
    db_url = f"sqlite:///{db_path}"

    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def _override():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    os.unlink(db_path)


@pytest.fixture(name="client", scope="session")
def fixture_client():
    """Session-scoped TestClient that uses the clean-DB override."""
    with TestClient(app) as c:
        yield c
