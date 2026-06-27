"""Interaction domain API router — Conversations, Notifications, Profile, Users, WS Models."""

from fastapi import APIRouter

from .conversations import router as conversations_router
from .notifications import router as notifications_router
from .profile import router as profile_router
from .users import router as users_router
from .ws_models import router as ws_models_router

router = APIRouter()
router.include_router(conversations_router)
router.include_router(notifications_router, prefix="/notifications")
router.include_router(profile_router, prefix="/me/profile")
router.include_router(users_router)
router.include_router(ws_models_router)
