from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, HTTPException

from backend.app.api.deps import get_current_user
from backend.app.models.user import User


def require_role(role: str) -> Callable:
    def _require(current_user: User = Depends(get_current_user)) -> User:
        if getattr(current_user, "role", "") != role:
            raise HTTPException(status_code=403, detail="Forbidden: insufficient role")
        return current_user
    return _require


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if getattr(current_user, "role", "") != "admin":
        raise HTTPException(status_code=403, detail="Forbidden: Admin access required")
    return current_user

__all__ = ["require_role", "require_admin"]
