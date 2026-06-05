from fastapi import Depends, HTTPException
from backend.app.api.deps import get_current_user
from backend.app.models.user import User
from typing import Callable


def is_admin(user: User) -> bool:
    return getattr(user, "role", "") == "admin"


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Forbidden: Admin access required")
    return current_user


def can_access_self(current_user: User, target_id: int) -> bool:
    return is_admin(current_user) or (hasattr(current_user, "id") and current_user.id == int(target_id))


def can_modify_self(current_user: User, target_id: int) -> bool:
    # same semantics: admin or self
    return can_access_self(current_user, target_id)
