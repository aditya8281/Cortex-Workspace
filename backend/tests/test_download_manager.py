"""Tests for queue-based download manager."""

from __future__ import annotations

import asyncio
import json
import time
from unittest.mock import patch

import pytest

from backend.app.services.model_downloader import (
    DownloadManager,
    DownloadRecord,
    DownloadStatus,
)


@pytest.fixture
def tmp_models_dir(tmp_path):
    """Create a temporary models directory for testing."""
    d = tmp_path / "models"
    d.mkdir()
    return d


@pytest.fixture
def manager(tmp_models_dir):
    """Create a fresh DownloadManager with tmp state file."""
    with patch("backend.app.services.model_downloader.MODELS_DIR", tmp_models_dir), patch(
        "backend.app.services.model_downloader.STATE_FILE", tmp_models_dir / "state.json"
    ):
        mgr = DownloadManager(max_concurrent=2, max_retries=2)
        yield mgr


@pytest.fixture
def manager_with_state(tmp_models_dir):
    """Create a DownloadManager that has pre-existing queued downloads."""
    state_file = tmp_models_dir / "state.json"
    state_file.write_text(
        json.dumps(
            {
                "records": [
                    {
                        "download_id": "abc123",
                        "model_name": "llama3.2:3b",
                        "provider": "ollama",
                        "progress": 0.0,
                        "bytes_downloaded": 0,
                        "total_bytes": 0,
                        "speed_bytes_sec": 0.0,
                        "retry_count": 0,
                        "max_retries": 3,
                        "error_message": None,
                        "started_at": None,
                        "completed_at": None,
                        "created_at": 1000.0,
                        "db_record_id": None,
                    }
                ]
            }
        )
    )
    with patch("backend.app.services.model_downloader.MODELS_DIR", tmp_models_dir), patch(
        "backend.app.services.model_downloader.STATE_FILE", state_file
    ):
        yield DownloadManager(max_concurrent=2, max_retries=3)


# --- Enqueue Tests ---


@pytest.mark.asyncio
async def test_enqueue_creates_record(manager: DownloadManager):
    record = await manager.enqueue("llama3.2:3b", provider="ollama")
    assert record.model_name == "llama3.2:3b"
    assert record.status == DownloadStatus.QUEUED
    assert record.download_id in manager._records


@pytest.mark.asyncio
async def test_enqueue_duplicate_raises(manager: DownloadManager):
    await manager.enqueue("model-a", provider="ollama")
    with pytest.raises(ValueError, match="already in download queue"):
        await manager.enqueue("model-a", provider="ollama")


@pytest.mark.asyncio
async def test_enqueue_persists_state(manager: DownloadManager, tmp_models_dir):
    await manager.enqueue("model-x", provider="ollama")
    state_file = tmp_models_dir / "state.json"
    assert state_file.exists()
    data = json.loads(state_file.read_text())
    assert len(data["records"]) == 1
    assert data["records"][0]["model_name"] == "model-x"


# --- State Persistence Tests ---


def test_load_state_restores_queued(manager_with_state: DownloadManager):
    assert "abc123" in manager_with_state._records
    rec = manager_with_state._records["abc123"]
    assert rec.model_name == "llama3.2:3b"
    assert rec.status == DownloadStatus.QUEUED


def test_load_state_handles_missing_file(tmp_models_dir):
    with patch("backend.app.services.model_downloader.MODELS_DIR", tmp_models_dir), patch(
        "backend.app.services.model_downloader.STATE_FILE", tmp_models_dir / "nonexistent.json"
    ):
        mgr = DownloadManager()
        assert len(mgr._records) == 0


def test_load_state_handles_corrupt_file(tmp_models_dir):
    bad_file = tmp_models_dir / "state.json"
    bad_file.write_text("not valid json {{{")
    with patch("backend.app.services.model_downloader.MODELS_DIR", tmp_models_dir), patch(
        "backend.app.services.model_downloader.STATE_FILE", bad_file
    ):
        mgr = DownloadManager()
        assert len(mgr._records) == 0


# --- Pause / Resume Tests ---


@pytest.mark.asyncio
async def test_pause_downloading_record(manager: DownloadManager):
    record = await manager.enqueue("model-p", provider="ollama")
    record.status = DownloadStatus.DOWNLOADING
    paused = await manager.pause(record.download_id)
    assert paused.status == DownloadStatus.PAUSED


@pytest.mark.asyncio
async def test_pause_nonexistent_raises(manager: DownloadManager):
    with pytest.raises(KeyError):
        await manager.pause("nonexistent-id")


@pytest.mark.asyncio
async def test_pause_not_downloading_raises(manager: DownloadManager):
    record = await manager.enqueue("model-q", provider="ollama")
    with pytest.raises(ValueError, match="Cannot pause"):
        await manager.pause(record.download_id)


@pytest.mark.asyncio
async def test_resume_paused_record(manager: DownloadManager):
    record = await manager.enqueue("model-r", provider="ollama")
    record.status = DownloadStatus.PAUSED
    resumed = await manager.resume(record.download_id)
    assert resumed.status == DownloadStatus.QUEUED


@pytest.mark.asyncio
async def test_resume_nonexistent_raises(manager: DownloadManager):
    with pytest.raises(KeyError):
        await manager.resume("nonexistent-id")


@pytest.mark.asyncio
async def test_resume_not_paused_raises(manager: DownloadManager):
    record = await manager.enqueue("model-s", provider="ollama")
    with pytest.raises(ValueError, match="Cannot resume"):
        await manager.resume(record.download_id)


# --- Cancel Tests ---


@pytest.mark.asyncio
async def test_cancel_queued_record(manager: DownloadManager):
    record = await manager.enqueue("model-c", provider="ollama")
    cancelled = await manager.cancel(record.download_id)
    assert cancelled.status == DownloadStatus.CANCELLED


@pytest.mark.asyncio
async def test_cancel_nonexistent_raises(manager: DownloadManager):
    with pytest.raises(KeyError):
        await manager.cancel("nonexistent-id")


@pytest.mark.asyncio
async def test_cancel_completed_raises(manager: DownloadManager):
    record = await manager.enqueue("model-d", provider="ollama")
    record.status = DownloadStatus.COMPLETED
    with pytest.raises(ValueError, match="Cannot cancel"):
        await manager.cancel(record.download_id)


@pytest.mark.asyncio
async def test_cancel_running_task(manager: DownloadManager):
    record = await manager.enqueue("model-t", provider="ollama")
    record.status = DownloadStatus.DOWNLOADING

    async def fake_execute(rec):
        try:
            await asyncio.sleep(100)
        except asyncio.CancelledError:
            rec.status = DownloadStatus.CANCELLED
            raise

    task = asyncio.create_task(fake_execute(record))
    manager._tasks[record.download_id] = task

    cancelled = await manager.cancel(record.download_id)
    assert cancelled.status == DownloadStatus.CANCELLED


# --- Status / List Tests ---


@pytest.mark.asyncio
async def test_get_status(manager: DownloadManager):
    record = await manager.enqueue("model-s", provider="ollama")
    status = manager.get_status(record.download_id)
    assert status["model_name"] == "model-s"
    assert status["status"] == "queued"


@pytest.mark.asyncio
async def test_get_status_nonexistent_raises(manager: DownloadManager):
    with pytest.raises(KeyError):
        manager.get_status("nonexistent-id")


@pytest.mark.asyncio
async def test_list_downloads(manager: DownloadManager):
    await manager.enqueue("m1", provider="ollama")
    await manager.enqueue("m2", provider="ollama")
    await manager.enqueue("m3", provider="ollama")
    downloads = manager.list_downloads()
    assert len(downloads) == 3


@pytest.mark.asyncio
async def test_list_downloads_filter_status(manager: DownloadManager):
    r1 = await manager.enqueue("m1", provider="ollama")
    r2 = await manager.enqueue("m2", provider="ollama")
    r1.status = DownloadStatus.COMPLETED
    r2.status = DownloadStatus.QUEUED
    queued = manager.list_downloads(status="queued")
    assert len(queued) == 1
    assert queued[0]["model_name"] == "m2"


@pytest.mark.asyncio
async def test_list_downloads_limit(manager: DownloadManager):
    for i in range(5):
        await manager.enqueue(f"m{i}", provider="ollama")
    limited = manager.list_downloads(limit=2)
    assert len(limited) == 2


# --- Queue Status Tests ---


@pytest.mark.asyncio
async def test_queue_status(manager: DownloadManager):
    await manager.enqueue("m1", provider="ollama")
    await manager.enqueue("m2", provider="ollama")
    status = manager.get_queue_status()
    assert status["total"] == 2
    assert status["queued"] == 2
    assert status["max_concurrent"] == 2


# --- Clear Queue Tests ---


@pytest.mark.asyncio
async def test_clear_queue(manager: DownloadManager):
    await manager.enqueue("m1", provider="ollama")
    await manager.enqueue("m2", provider="ollama")
    count = manager.clear_queue()
    assert count == 2
    for rec in manager._records.values():
        assert rec.status == DownloadStatus.CANCELLED


# --- Download Execution Tests ---


@pytest.mark.asyncio
async def test_execute_download_ollama_success(manager: DownloadManager):
    async def fake_pull(record):
        record.progress = 1.0
        record.bytes_downloaded = 1000
        record.total_bytes = 1000

    with patch.object(manager, "_pull_ollama", fake_pull), patch.object(manager, "_update_db"):
        record = await manager.enqueue("model-ok", provider="ollama")
        await manager._execute_download(record)
        assert record.status == DownloadStatus.COMPLETED
        assert record.progress == 1.0


@pytest.mark.asyncio
async def test_execute_download_unsupported_provider(manager: DownloadManager):
    record = await manager.enqueue("model-bad", provider="unknown", max_retries=0)
    with patch.object(manager, "_update_db"):
        await manager._execute_download(record)
        assert record.status == DownloadStatus.FAILED
        assert "Unsupported provider" in record.error_message


@pytest.mark.asyncio
async def test_execute_download_retries_on_failure(manager: DownloadManager):
    call_count = 0

    async def failing_pull(record):
        nonlocal call_count
        call_count += 1
        raise ConnectionError("connection lost")

    with patch.object(manager, "_pull_ollama", failing_pull), patch.object(manager, "_update_db"):
        record = await manager.enqueue("model-retry", provider="ollama", max_retries=2)
        await manager._execute_download(record)
        assert record.retry_count == 1
        assert record.status == DownloadStatus.QUEUED


@pytest.mark.asyncio
async def test_execute_download_fails_after_max_retries(manager: DownloadManager):
    async def failing_pull(record):
        raise ConnectionError("connection lost")

    with patch.object(manager, "_pull_ollama", failing_pull), patch.object(manager, "_update_db"):
        record = await manager.enqueue("model-exhaust", provider="ollama", max_retries=0)
        await manager._execute_download(record)
        assert record.status == DownloadStatus.FAILED
        assert record.retry_count == 0


@pytest.mark.asyncio
async def test_execute_download_paused_during_pull(manager: DownloadManager):
    from backend.app.services.model_downloader import _DownloadPaused

    async def pull_then_pause(record):
        record.status = DownloadStatus.PAUSED
        raise _DownloadPaused()

    with patch.object(manager, "_pull_ollama", pull_then_pause), patch.object(manager, "_update_db"):
        record = await manager.enqueue("model-pause-pull", provider="ollama", max_retries=0)
        await manager._execute_download(record)
        assert record.status == DownloadStatus.PAUSED


# --- Speed / ETA Tests ---


def test_update_speed_eta_basic(manager: DownloadManager):
    record = DownloadRecord(
        download_id="speed1",
        model_name="test",
        provider="ollama",
        total_bytes=1000,
    )
    manager._speed_samples["speed1"] = []

    record.bytes_downloaded = 0
    record._update_speed_eta = lambda: None  # bypass for manual test
    manager._update_speed_eta(record)

    # With only 0 or 1 sample, no speed calculated
    assert record.speed_bytes_sec == 0.0


def test_update_speed_eta_with_samples(manager: DownloadManager):
    record = DownloadRecord(
        download_id="speed2",
        model_name="test",
        provider="ollama",
        total_bytes=10000,
    )
    now = time.time()
    manager._speed_samples["speed2"] = [
        (now - 3.0, 1000),
        (now, 4000),
    ]
    record.bytes_downloaded = 4000
    record.total_bytes = 10000

    manager._update_speed_eta(record)

    assert record.speed_bytes_sec > 0
    assert record.eta_seconds is not None
    assert record.eta_seconds > 0


def test_update_speed_eta_no_remaining(manager: DownloadManager):
    record = DownloadRecord(
        download_id="speed3",
        model_name="test",
        provider="ollama",
        total_bytes=1000,
        bytes_downloaded=1000,
    )
    now = time.time()
    manager._speed_samples["speed3"] = [
        (now - 2.0, 500),
        (now, 1000),
    ]
    manager._update_speed_eta(record)
    assert record.eta_seconds is None


# --- Worker Integration Test ---


@pytest.mark.asyncio
async def test_worker_processes_queue(manager: DownloadManager):
    completed = []

    async def fake_pull(record):
        record.progress = 1.0
        completed.append(record.model_name)

    with patch.object(manager, "_pull_ollama", fake_pull), patch.object(manager, "_update_db"):
        await manager.enqueue("w1", provider="ollama")
        await manager.enqueue("w2", provider="ollama")

        await manager.start()
        # Give the worker time to process items
        for _ in range(20):
            await asyncio.sleep(0.05)
            if len(completed) >= 2:
                break

        await manager.stop()

        assert len(completed) == 2
        for rec in manager._records.values():
            assert rec.status == DownloadStatus.COMPLETED


@pytest.mark.asyncio
async def test_worker_respects_concurrency_limit(manager: DownloadManager):
    max_running = 0
    current_running = 0
    lock = asyncio.Lock()

    async def slow_pull(record):
        nonlocal max_running, current_running
        async with lock:
            current_running += 1
            if current_running > max_running:
                max_running = current_running
        await asyncio.sleep(0.3)
        async with lock:
            current_running -= 1
        record.progress = 1.0

    with patch.object(manager, "_pull_ollama", slow_pull), patch.object(manager, "_update_db"):
        for i in range(5):
            await manager.enqueue(f"conc-{i}", provider="ollama")

        await manager.start()
        await asyncio.sleep(2.0)
        await manager.stop()

        assert max_running <= manager.max_concurrent


# --- Record Dataclass Tests ---


def test_download_record_defaults():
    rec = DownloadRecord(download_id="x", model_name="m", provider="ollama")
    assert rec.status == DownloadStatus.QUEUED
    assert rec.progress == 0.0
    assert rec.retry_count == 0
    assert rec.max_retries == 3
    assert rec.error_message is None


def test_download_status_values():
    assert DownloadStatus.QUEUED.value == "queued"
    assert DownloadStatus.DOWNLOADING.value == "downloading"
    assert DownloadStatus.PAUSED.value == "paused"
    assert DownloadStatus.COMPLETED.value == "completed"
    assert DownloadStatus.FAILED.value == "failed"
    assert DownloadStatus.CANCELLED.value == "cancelled"


# --- Edge Case Tests ---


@pytest.mark.asyncio
async def test_enqueue_after_cancel_reuses_slot(manager: DownloadManager):
    r1 = await manager.enqueue("edge-m", provider="ollama")
    await manager.cancel(r1.download_id)
    assert r1.status == DownloadStatus.CANCELLED
    r2 = await manager.enqueue("edge-m", provider="ollama")
    assert r2.status == DownloadStatus.QUEUED
    assert r2.download_id != r1.download_id


@pytest.mark.asyncio
async def test_multiple_providers_different_models(manager: DownloadManager):
    r1 = await manager.enqueue("model-a", provider="ollama")
    r2 = await manager.enqueue("model-b", provider="huggingface")
    assert r1.provider == "ollama"
    assert r2.provider == "huggingface"
    assert len(manager._records) == 2


@pytest.mark.asyncio
async def test_custom_max_retries_per_download(manager: DownloadManager):
    record = await manager.enqueue("retry-custom", provider="ollama", max_retries=5)
    assert record.max_retries == 5


@pytest.mark.asyncio
async def test_db_record_id_propagated(manager: DownloadManager):
    record = await manager.enqueue("db-model", provider="ollama", db_record_id=42)
    assert record.db_record_id == 42
