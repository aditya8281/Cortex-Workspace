"""Factory functions for interaction domain models."""

from backend.app.models.interaction.user import User


def create_user(
    user_id: str = "test_user_0001",
    **kwargs,
) -> User:
    """Create a User model instance for testing."""
    from faker import Faker
    fake = Faker()
    return User(
        id=kwargs.get("id", user_id),
        username=kwargs.get("username", fake.user_name()),
        full_name=kwargs.get("full_name", fake.name()),
        hashed_password=kwargs.get("hashed_password", "hashed_test_password"),
        role=kwargs.get("role", "user"),
    )
