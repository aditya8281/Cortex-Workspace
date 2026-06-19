from __future__ import annotations

import logging

from arq import create_pool
from arq.connections import RedisSettings
from arq.cron import cron

from backend.app.core.config import settings
from backend.app.tasks.memory_tasks import (
    build_graph_task,
    bulk_embed_task,
    embed_memory_task,
    index_repo_task,
    scan_repo_task,
)

logger = logging.getLogger(__name__)

REDIS_SETTINGS = RedisSettings.from_dsn(settings.REDIS_URL)


async def sample_task(ctx: dict, name: str = "world") -> str:
    """Sample task to verify the worker is running.

    Usage:
        result = await enqueue_task("sample_task", "Alice")
    """
    logger.info("Hello, %s!", name)
    return f"Hello, {name}!"


async def health_check_task(ctx: dict) -> str:
    """Periodic health check — demonstrates recurring cron tasks."""
    logger.debug("Worker health check OK")
    return "OK"


class WorkerSettings:
    functions = [sample_task, health_check_task, embed_memory_task, scan_repo_task, bulk_embed_task, index_repo_task, build_graph_task]
    redis_settings = REDIS_SETTINGS
    keep_result = 3600
    keep_result_forever = False
    on_startup = None
    on_shutdown = None
    cron_jobs = [
        cron(health_check_task, minute={0, 30}, run_at_startup=True),
    ]


async def enqueue_task(task_name: str, *args, **kwargs) -> str | None:
    """Enqueue a background task and return its job ID.

    Example:
        >>> import asyncio
        >>> job_id = await enqueue_task("sample_task", "Alice")
        >>> print(f"Job enqueued: {job_id}")
    """
    pool = await create_pool(REDIS_SETTINGS)
    try:
        job = await pool.enqueue_job(task_name, *args, **kwargs)
        return job.job_id if job else None
    finally:
        await pool.close()


if __name__ == "__main__":
    """Run worker directly: python -m backend.app.tasks.worker"""
    import asyncio

    async def _demo():
        logger.info("Enqueuing sample task...")
        jid = await enqueue_task("sample_task", "Cortex")
        logger.info("Task enqueued: jid=%s", jid)

    asyncio.run(_demo())
