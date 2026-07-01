"""WS test fixtures — patch SessionLocal for WS auth tests."""
from unittest.mock import patch

import pytest

from backend.app.core.db import get_db
from backend.app.models.interaction.user import User


@pytest.fixture(autouse=True)
def _patch_ws_db(_engine):
    """Redirect SessionLocal (used by verify_ws_token) to the test DB and seed user 1."""
    from backend.app.main import app

    # Find the test session from the get_db override
    test_session = None
    for dep, func in app.dependency_overrides.items():
        if dep is get_db:
            gen = func()
            test_session = next(gen)
            try:
                next(gen)
            except StopIteration:
                pass
            break

    if test_session is None:
        yield
        return

    # Seed user 1
    existing = test_session.query(User).filter(User.id == 1).first()
    if not existing:
        user = User(
            id=1,
            username="ws_test_user",
            full_name="WS Test User",
            hashed_password="unused",
        )
        test_session.add(user)
        test_session.commit()

    # Redirect SessionLocal to return the test session
    def _fake_session_local(**kwargs):
        return test_session

    with patch("backend.app.core.db.SessionLocal", _fake_session_local):
        yield
