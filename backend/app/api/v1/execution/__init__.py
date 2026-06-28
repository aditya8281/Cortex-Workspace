"""Execution domain API — tools and workflows."""

from fastapi import APIRouter

from .tools import router as tools_router
from .workflows import router as workflows_router

router = APIRouter()
router.include_router(tools_router, prefix="/tools", tags=["Execution - Tools"])
router.include_router(workflows_router, prefix="/workflows", tags=["Execution - Workflows"])
