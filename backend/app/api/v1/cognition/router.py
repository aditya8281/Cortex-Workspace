"""Cognition domain API router — Agents."""

from fastapi import APIRouter

from .agents import router as agents_router

router = APIRouter()
router.include_router(agents_router)
