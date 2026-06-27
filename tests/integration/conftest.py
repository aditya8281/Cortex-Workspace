"""Integration test configuration."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.db.base import Base


@pytest.fixture(scope="module")
def test_db():
    """Module-scoped test database for integration tests."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    yield SessionLocal
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def db_session(test_db):
    """Per-test database session with rollback."""
    session = test_db()
    yield session
    session.rollback()
    session.close()
