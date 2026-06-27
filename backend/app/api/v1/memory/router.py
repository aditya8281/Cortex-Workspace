"""Memory domain API router — Knowledge, Long-Term Memory, Search, Cortex Memory."""

from fastapi import APIRouter

from .cortex_router import cortex_memory_router
from .knowledge import router as knowledge_router
from .long_term_memory import router as ltm_router
from .search import router as search_router

router = APIRouter()
router.include_router(knowledge_router)
router.include_router(ltm_router)
router.include_router(search_router)
router.include_router(cortex_memory_router)
