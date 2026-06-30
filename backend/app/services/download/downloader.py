from __future__ import annotations

import asyncio
import enum
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from backend.app.core.config import settings

logger = logging.getLogger(__name__)

MODELS_DIR = Path(getattr(settings, "CORTEX_ROOT", None) or "./CortexMemory") / "models"
STATE_FILE = MODELS_DIR / "download_state.json"


class DownloadStatus(str, enum.Enum):
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class DownloadRecord:
    download_id: str
    model_name: str
    provider: str
    status: DownloadStatus = DownloadStatus.QUEUED
    progress: float = 0.0
    bytes_downloaded: int = 0
    total_bytes: int = 0
    speed_bytes_sec: float = 0.0
    eta_seconds: float | None = None
    retry_count: int = 0
    max_retries: int = 3
    error_message: str | None = None
    started_at: float | None = None
    completed_at: float | None = None
    created_at: float = field(default_factory=time.time)
    db_record_id: int | None = None


class _DownloadCancelled(Exception):
    pass


class _DownloadPaused(Exception):
    pass


class DownloadManager:
    def __init__(
        self,
        max_concurrent: int = 3,
        max_retries: int = 3,
    ):
        self.max_concurrent = max_concurrent
        self.max_retries = max_retries

        self._queue: asyncio.Queue[str] = asyncio.Queue()
        self._semaphore = asyncio.Semaphore(max_concurrent)

        self._records: dict[str, DownloadRecord] = {}
        self._tasks: dict[str, asyncio.Task] = {}

        self._speed_samples: dict[str, list[tuple[float, int]]] = {}
        self._last_progress_save: dict[str, float] = {}

        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        self._load_state()
        self._started = False
        self._worker_task: asyncio.Task | None = None

    def _load_state(self) -> None:
        if not STATE_FILE.exists():
            return
        try:
            with open(STATE_FILE) as f:
                data = json.load(f)
            for rec_data in data.get("records", []):
                rec = DownloadRecord(**rec_data)
                rec.status = DownloadStatus.QUEUED
                rec.retry_count = 0
                self._records[rec.download_id] = rec
                self._queue.put_nowait(rec.download_id)
            logger.info("Restored %d queued downloads from state file", len(data.get("records", [])))
        except (OSError, json.JSONDecodeError, TypeError) as e:
            logger.warning("Failed to load download state: %s", e)

    def _save_state(self) -> None:
        records_to_persist = [
            {
                "download_id": r.download_id,
                "model_name": r.model_name,
                "provider": r.provider,
                "progress": r.progress,
                "bytes_downloaded": r.bytes_downloaded,
                "total_bytes": r.total_bytes,
                "speed_bytes_sec": r.speed_bytes_sec,
                "retry_count": r.retry_count,
                "max_retries": r.max_retries,
                "error_message": r.error_message,
                "started_at": r.started_at,
                "completed_at": r.completed_at,
                "created_at": r.created_at,
                "db_record_id": r.db_record_id,
            }
            for r in self._records.values()
            if r.status in (DownloadStatus.QUEUED, DownloadStatus.DOWNLOADING, DownloadStatus.PAUSED)
        ]
        try:
            STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(STATE_FILE, "w") as f:
                json.dump({"records": records_to_persist}, f, indent=2)
        except OSError as e:
            logger.warning("Failed to save download state: %s", e)

    async def start(self) -> None:
        if self._started:
            return
        self._started = True
        self._worker_task = asyncio.create_task(self._worker())
        logger.info("Download manager worker started (max_concurrent=%d)", self.max_concurrent)

    async def stop(self) -> None:
        if not self._started:
            return
        self._started = False
        if hasattr(self, "_worker_task") and self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        logger.info("Download manager worker stopped")

    async def _worker(self) -> None:
        while True:
            download_id = await self._queue.get()
            record = self._records.get(download_id)
            if not record or record.status not in (DownloadStatus.QUEUED, DownloadStatus.PAUSED):
                self._queue.task_done()
                continue

            async with self._semaphore:
                await self._execute_download(record)
            self._queue.task_done()

    async def enqueue(
        self,
        model_name: str,
        provider: str = "ollama",
        max_retries: int | None = None,
        db_record_id: int | None = None,
    ) -> DownloadRecord:
        for rec in self._records.values():
            if rec.model_name == model_name and rec.status in (
                DownloadStatus.QUEUED,
                DownloadStatus.DOWNLOADING,
                DownloadStatus.PAUSED,
            ):
                raise ValueError(f"Model {model_name} already in download queue (id={rec.download_id})")

        download_id = str(uuid.uuid4())[:12]
        record = DownloadRecord(
            download_id=download_id,
            model_name=model_name,
            provider=provider,
            max_retries=max_retries if max_retries is not None else self.max_retries,
            db_record_id=db_record_id,
        )
        self._records[download_id] = record
        self._queue.put_nowait(download_id)
        self._save_state()
        logger.info("Enqueued download: %s (id=%s)", model_name, download_id)
        return record

    async def _execute_download(self, record: DownloadRecord) -> None:
        record.status = DownloadStatus.DOWNLOADING
        if record.started_at is None:
            record.started_at = time.time()
        self._speed_samples[record.download_id] = []
        self._save_state()
        self._update_db(record)

        try:
            if record.provider == "ollama":
                await self._pull_ollama(record)
            else:
                raise ValueError(f"Unsupported provider: {record.provider}")

            record.status = DownloadStatus.COMPLETED
            record.progress = 1.0
            record.completed_at = time.time()
            self._save_state()
            self._update_db(record)
            logger.info("Download completed: %s", record.model_name)
        except _DownloadPaused:
            record.status = DownloadStatus.PAUSED
            self._save_state()
            self._update_db(record)
            logger.info("Download paused: %s", record.model_name)
        except (_DownloadCancelled, asyncio.CancelledError):
            record.status = DownloadStatus.CANCELLED
            record.completed_at = time.time()
            self._save_state()
            self._update_db(record)
            logger.info("Download cancelled: %s", record.model_name)
        except Exception as e:
            logger.error("Download failed for %s: %s", record.model_name, e)
            if record.retry_count < record.max_retries:
                record.retry_count += 1
                record.status = DownloadStatus.QUEUED
                record.error_message = str(e)
                record.progress = 0.0
                record.bytes_downloaded = 0
                record.speed_bytes_sec = 0.0
                record.eta_seconds = None
                self._save_state()
                self._update_db(record)
                self._queue.put_nowait(record.download_id)
                logger.info(
                    "Retrying download: %s (attempt %d/%d)",
                    record.model_name,
                    record.retry_count,
                    record.max_retries,
                )
            else:
                record.status = DownloadStatus.FAILED
                record.error_message = str(e)
                record.completed_at = time.time()
                self._save_state()
                self._update_db(record)
        finally:
            self._tasks.pop(record.download_id, None)
            self._speed_samples.pop(record.download_id, None)
            self._last_progress_save.pop(record.download_id, None)

    async def _pull_ollama(self, record: DownloadRecord) -> None:
        import httpx

        base_url = settings.OLLAMA_BASE_URL
        model_name = record.model_name
        last_completed = record.bytes_downloaded

        async with httpx.AsyncClient(base_url=base_url, timeout=3600.0) as client:
            payload: dict = {"name": model_name}
            if last_completed > 0:
                payload["from"] = model_name

            async with client.stream("POST", "/api/pull", json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line:
                        continue

                    if record.status == DownloadStatus.PAUSED:
                        raise _DownloadPaused

                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    status = data.get("status", "")

                    if "total" in data and "completed" in data:
                        total = data["total"]
                        completed = data["completed"]
                        if total > 0:
                            record.bytes_downloaded = completed
                            record.total_bytes = total
                            record.progress = min(completed / total, 0.99)
                            self._update_speed_eta(record)
                            now = time.time()
                            last_save = self._last_progress_save.get(record.download_id, 0)
                            if now - last_save >= 2.0:
                                self._save_state()
                                self._update_db(record)
                                self._last_progress_save[record.download_id] = now
                    elif status == "success":
                        record.progress = 1.0
                        self._save_state()

    def _update_speed_eta(self, record: DownloadRecord) -> None:
        now = time.time()
        samples = self._speed_samples.setdefault(record.download_id, [])
        samples.append((now, record.bytes_downloaded))

        cutoff = now - 5.0
        samples[:] = [(t, b) for t, b in samples if t >= cutoff]

        if len(samples) < 2:
            return

        t0, b0 = samples[0]
        t1, b1 = samples[-1]
        dt = t1 - t0
        if dt <= 0:
            return

        speed = (b1 - b0) / dt
        record.speed_bytes_sec = speed

        remaining = record.total_bytes - record.bytes_downloaded
        if speed > 0 and remaining > 0:
            record.eta_seconds = remaining / speed
        else:
            record.eta_seconds = None

    def _update_db(self, record: DownloadRecord) -> None:
        if record.db_record_id is None:
            return
        try:
            from datetime import datetime, timezone

            from backend.app.db.session import SessionLocal
            from backend.app.models.intelligence.model_catalog import ModelDownload

            db = SessionLocal()
            try:
                download = db.query(ModelDownload).filter(ModelDownload.id == record.db_record_id).first()
                if download:
                    download.status = record.status.value
                    download.progress = record.progress
                    download.download_speed_bytes_sec = record.speed_bytes_sec
                    download.error_message = record.error_message
                    if record.started_at and not download.started_at:
                        download.started_at = datetime.fromtimestamp(record.started_at, tz=timezone.utc)
                    if record.completed_at:
                        download.completed_at = datetime.fromtimestamp(record.completed_at, tz=timezone.utc)
                    db.commit()
            finally:
                db.close()
        except Exception as e:
            logger.warning("Failed to update DB for download %s: %s", record.download_id, e)

    async def pause(self, download_id: str) -> DownloadRecord:
        record = self._records.get(download_id)
        if not record:
            raise KeyError(f"Download {download_id} not found")
        if record.status != DownloadStatus.DOWNLOADING:
            raise ValueError(f"Cannot pause download in status '{record.status.value}'")
        record.status = DownloadStatus.PAUSED
        self._save_state()
        return record

    async def resume(self, download_id: str) -> DownloadRecord:
        record = self._records.get(download_id)
        if not record:
            raise KeyError(f"Download {download_id} not found")
        if record.status != DownloadStatus.PAUSED:
            raise ValueError(f"Cannot resume download in status '{record.status.value}'")
        record.status = DownloadStatus.QUEUED
        self._queue.put_nowait(download_id)
        self._save_state()
        logger.info("Resumed download: %s (id=%s)", record.model_name, download_id)
        return record

    async def cancel(self, download_id: str) -> DownloadRecord:
        record = self._records.get(download_id)
        if not record:
            raise KeyError(f"Download {download_id} not found")
        if record.status in (DownloadStatus.COMPLETED, DownloadStatus.CANCELLED):
            raise ValueError(f"Cannot cancel download in status '{record.status.value}'")

        task = self._tasks.get(download_id)
        if task and not task.done():
            task.cancel()
            try:
                await asyncio.wait_for(asyncio.shield(task), timeout=2.0)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass

        if record.status not in (DownloadStatus.COMPLETED, DownloadStatus.CANCELLED):
            record.status = DownloadStatus.CANCELLED
            record.completed_at = time.time()
            self._save_state()
            self._update_db(record)

        return record

    def get_status(self, download_id: str) -> dict:
        record = self._records.get(download_id)
        if not record:
            raise KeyError(f"Download {download_id} not found")
        return {
            "download_id": record.download_id,
            "model_name": record.model_name,
            "provider": record.provider,
            "status": record.status.value,
            "progress": record.progress,
            "bytes_downloaded": record.bytes_downloaded,
            "total_bytes": record.total_bytes,
            "speed_bytes_sec": record.speed_bytes_sec,
            "eta_seconds": record.eta_seconds,
            "retry_count": record.retry_count,
            "max_retries": record.max_retries,
            "error_message": record.error_message,
            "started_at": record.started_at,
            "completed_at": record.completed_at,
            "created_at": record.created_at,
        }

    def list_downloads(self, status: str | None = None, limit: int = 50) -> list[dict]:
        records = list(self._records.values())
        if status:
            try:
                filter_status = DownloadStatus(status)
                records = [r for r in records if r.status == filter_status]
            except ValueError:
                pass
        records.sort(key=lambda r: r.created_at, reverse=True)
        return [
            {
                "download_id": r.download_id,
                "model_name": r.model_name,
                "provider": r.provider,
                "status": r.status.value,
                "progress": r.progress,
                "speed_bytes_sec": r.speed_bytes_sec,
                "bytes_downloaded": r.bytes_downloaded,
                "total_bytes": r.total_bytes,
                "eta_seconds": r.eta_seconds,
                "retry_count": r.retry_count,
                "error_message": r.error_message,
            }
            for r in records[:limit]
        ]

    def reorder(self, new_order: list[str]) -> list[str]:
        """Reorder the internal queue by download_id order.

        Only existing QUEUED/PAUSED IDs are considered. IDs not in _records
        are silently ignored. Returns the new order of all remaining IDs.
        """
        # Collect IDs that are still in the queue (QUEUED or PAUSED)
        queued_ids = [
            r.download_id for r in self._records.values() if r.status in (DownloadStatus.QUEUED, DownloadStatus.PAUSED)
        ]
        queued_set = set(queued_ids)

        # Filter new_order to only valid queued IDs, preserving order
        reordered = [did for did in new_order if did in queued_set]

        # Append any queued IDs not in new_order (in original order)
        for did in queued_ids:
            if did not in reordered:
                reordered.append(did)

        return reordered

    def clear_terminal(self) -> int:
        """Remove all COMPLETED, FAILED, and CANCELLED records from state.

        Returns the number of records removed.
        """
        terminal_statuses = {
            DownloadStatus.COMPLETED,
            DownloadStatus.FAILED,
            DownloadStatus.CANCELLED,
        }
        to_remove = [did for did, rec in self._records.items() if rec.status in terminal_statuses]
        for did in to_remove:
            del self._records[did]
        if to_remove:
            self._save_state()
        return len(to_remove)

    def clear_queue(self) -> int:
        count = 0
        for record in self._records.values():
            if record.status == DownloadStatus.QUEUED:
                record.status = DownloadStatus.CANCELLED
                record.completed_at = time.time()
                count += 1
        self._save_state()
        return count

    def get_queue_status(self) -> dict:
        statuses: dict[str, int] = {}
        for record in self._records.values():
            statuses[record.status.value] = statuses.get(record.status.value, 0) + 1
        return {
            "total": len(self._records),
            "queued": statuses.get("queued", 0),
            "downloading": statuses.get("downloading", 0),
            "paused": statuses.get("paused", 0),
            "completed": statuses.get("completed", 0),
            "failed": statuses.get("failed", 0),
            "cancelled": statuses.get("cancelled", 0),
            "max_concurrent": self.max_concurrent,
        }


download_manager = DownloadManager()


class _LegacyModelDownloader:
    """Backward-compatible adapter over DownloadManager.

    Preserves the old download_model / get_progress / cancel_download /
    get_active_progress API used by existing routes and WebSocket handler.
    """

    def __init__(self):
        self._dm = download_manager

    async def download_model(self, model_name: str, catalog: list[dict], variant: str | None = None) -> dict:
        full_model_name = f"{model_name}:{variant}" if variant else model_name

        from backend.app.services.intelligence.llm.manager import llm_manager

        available = await llm_manager.list_all_models()
        if any(m.name == full_model_name for m in available):
            return {"status": "already_downloaded", "model": full_model_name}

        model_entry = next((m for m in catalog if m["name"] == model_name), None)
        provider = model_entry.get("provider", "ollama") if model_entry else "ollama"

        record = await self._dm.enqueue(
            model_name=full_model_name,
            provider=provider,
        )
        return {"status": "started", "model": full_model_name, "download_id": record.download_id}

    def get_progress(self, model_name: str) -> float:
        for rec in self._dm._records.values():
            if rec.model_name == model_name:
                return rec.progress
        return 0.0

    async def cancel_download(self, model_name: str) -> bool:
        for rec in self._dm._records.values():
            if rec.model_name == model_name and rec.status in (
                DownloadStatus.QUEUED,
                DownloadStatus.DOWNLOADING,
                DownloadStatus.PAUSED,
            ):
                await self._dm.cancel(rec.download_id)
                return True
        return False

    def get_active_progress(self) -> dict[str, float]:
        active: dict[str, float] = {}
        for rec in self._dm._records.values():
            if (
                rec.status in (DownloadStatus.DOWNLOADING, DownloadStatus.PAUSED, DownloadStatus.QUEUED)
                and 0.0 < rec.progress <= 1.0
            ):
                active[rec.model_name] = rec.progress
        return active


model_downloader = _LegacyModelDownloader()
