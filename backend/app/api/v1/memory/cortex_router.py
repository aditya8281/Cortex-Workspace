"""Cortex memory domain router — aggregates all v1.03 memory endpoints."""

from fastapi import APIRouter

from .cortex_episodic import router as episodic_router
from .cortex_graph import router as graph_router
from .cortex_search import forget_router
from .cortex_search import router as search_router
from .cortex_semantic import router as semantic_router
from .cortex_working import router as working_router

cortex_memory_router = APIRouter()
cortex_memory_router.include_router(episodic_router)
cortex_memory_router.include_router(semantic_router)
cortex_memory_router.include_router(working_router)
cortex_memory_router.include_router(graph_router)
cortex_memory_router.include_router(search_router)
cortex_memory_router.include_router(forget_router)
