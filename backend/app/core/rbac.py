from backend.app.auth.dependencies import require_admin
from backend.app.models.user import User


def is_admin(user: User) -> bool:
    return getattr(user, "role", "") == "admin"


def can_access_self(current_user: User, target_id: int) -> bool:
    return is_admin(current_user) or (hasattr(current_user, "id") and current_user.id == int(target_id))


def can_modify_self(current_user: User, target_id: int) -> bool:
    # same semantics: admin or self
    return can_access_self(current_user, target_id)

