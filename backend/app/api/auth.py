"""Legacy API shim that re-exports the new auth router from backend.app.auth.

This file keeps existing import paths intact while centralizing auth logic
inside `backend.app.auth`.
"""

from backend.app.auth.router import router

__all__ = ["router"]
