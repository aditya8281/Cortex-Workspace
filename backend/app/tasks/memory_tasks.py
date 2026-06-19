"""Background tasks for memory operations."""
from __future__ import annotations

import logging
from typing import Any

from backend.app.core.db import SessionLocal
from backend.app.services.memory_manager import MemoryManager
from backend.app.services.repo_scanner import RepoScanner

logger = logging.getLogger(__name__)


async def embed_memory_task(ctx: dict, entry_id: int) -> dict[str, Any]:
    """Background task to embed a single memory entry."""
    db = SessionLocal()
    try:
        manager = MemoryManager(db)
        entry = manager.get(entry_id)
        if not entry:
            return {"status": "error", "message": f"Entry {entry_id} not found"}
        manager.update(entry_id)
        return {"status": "success", "entry_id": entry_id}
    except Exception as e:
        logger.error("Failed to embed memory %d: %s", entry_id, e)
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


async def scan_repo_task(ctx: dict, repo_path: str, user_id: int | None = None) -> dict[str, Any]:
    """Background task to scan and index a repository."""
    db = SessionLocal()
    try:
        scanner = RepoScanner(db)
        result = scanner.scan_repo(repo_path, user_id)
        return {
            "status": "success",
            "repo_id": result.repo_id,
            "files_scanned": result.files_scanned,
            "chunks_created": result.chunks_created,
        }
    except Exception as e:
        logger.error("Failed to scan repo %s: %s", repo_path, e)
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


async def bulk_embed_task(ctx: dict, entry_ids: list[int]) -> dict[str, Any]:
    """Background task to embed multiple memory entries."""
    db = SessionLocal()
    try:
        manager = MemoryManager(db)
        success_count = 0
        error_count = 0

        for entry_id in entry_ids:
            try:
                manager.update(entry_id)
                success_count += 1
            except Exception as e:
                logger.error("Failed to embed %d: %s", entry_id, e)
                error_count += 1

        return {
            "status": "success",
            "total": len(entry_ids),
            "success": success_count,
            "errors": error_count,
        }
    finally:
        db.close()
