"""Tests for DownloadManager reorder and clear_terminal methods."""

import pytest

from backend.app.services.download.downloader import (
    STATE_FILE,
    DownloadManager,
    DownloadStatus,
)


@pytest.fixture
def dm():
    dm = DownloadManager(max_concurrent=1, max_retries=0)
    dm._records.clear()
    yield dm
    dm._records.clear()
    if STATE_FILE.exists():
        STATE_FILE.unlink()


@pytest.mark.asyncio
async def test_reorder_changes_queue_order(dm):
    """Reordering changes the dequeue order."""
    r1 = await dm.enqueue("model-a", "ollama")
    r2 = await dm.enqueue("model-b", "ollama")
    r3 = await dm.enqueue("model-c", "ollama")

    new_order = dm.reorder([r3.download_id, r1.download_id, r2.download_id])
    assert r3.download_id == new_order[0]
    assert r1.download_id == new_order[1]
    assert r2.download_id == new_order[2]


@pytest.mark.asyncio
async def test_reorder_ignores_nonexistent_ids(dm):
    """Non-existent IDs are ignored."""
    r1 = await dm.enqueue("model-a", "ollama")
    r2 = await dm.enqueue("model-b", "ollama")

    new_order = dm.reorder(["nonexistent", r2.download_id, r1.download_id])
    assert len(new_order) == 2


def test_reorder_empty(dm):
    """Reorder with empty list returns empty."""
    new_order = dm.reorder([])
    assert new_order == []


@pytest.mark.asyncio
async def test_clear_terminal(dm):
    """clear_terminal removes COMPLETED, FAILED, CANCELLED records."""
    r1 = await dm.enqueue("model-a", "ollama")
    r2 = await dm.enqueue("model-b", "ollama")

    # Simulate terminal states
    dm._records[r1.download_id].status = DownloadStatus.COMPLETED
    dm._records[r2.download_id].status = DownloadStatus.FAILED

    cleared = dm.clear_terminal()
    assert cleared == 2
    assert len(dm._records) == 0


@pytest.mark.asyncio
async def test_clear_terminal_keeps_active(dm):
    """clear_terminal does not remove DOWNLOADING or QUEUED records."""
    r1 = await dm.enqueue("model-a", "ollama")
    r2 = await dm.enqueue("model-b", "ollama")

    # Set one record to terminal so clear_terminal has something to remove
    dm._records[r2.download_id].status = DownloadStatus.COMPLETED
    # r1 stays QUEUED (non-terminal)

    cleared = dm.clear_terminal()
    assert cleared == 1
    assert len(dm._records) == 1
    assert r1.download_id in dm._records
