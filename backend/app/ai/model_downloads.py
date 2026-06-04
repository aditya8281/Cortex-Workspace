from __future__ import annotations

import json
import logging
import threading
import uuid
from datetime import datetime, timezone
from typing import Any

import httpx

from backend.app.core.config import settings
from backend.app.core.paths import PROJECT_ROOT

logger = logging.getLogger(__name__)

DOWNLOAD_STATE_FILE = PROJECT_ROOT / ".cortex" / "model_download_jobs.json"


class ModelDownloadManager:
    def __init__(self):
        self._lock = threading.RLock()
        self._jobs: dict[str, dict[str, Any]] = {}
        self._threads: dict[str, threading.Thread] = {}
        self._load_state()
        self._restore_incomplete_jobs()

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _load_state(self) -> None:
        from backend.app.services.memory_manager import memory_manager
        state_file = memory_manager.get_path("cache", "model_download_jobs.json")
        if not state_file.exists():
            self._jobs = {}
            return
        try:
            data = json.loads(state_file.read_text(encoding="utf-8"))
            jobs = data.get("jobs", {})
            if isinstance(jobs, dict):
                self._jobs = jobs
            else:
                self._jobs = {}
        except Exception:
            self._jobs = {}

    def _save_state(self) -> None:
        from backend.app.services.memory_manager import memory_manager
        state_file = memory_manager.get_path("cache", "model_download_jobs.json")
        state_file.parent.mkdir(parents=True, exist_ok=True)
        payload = {"jobs": self._jobs, "updated_at": self._now()}
        state_file.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    def _restore_incomplete_jobs(self) -> None:
        for job_id, job in list(self._jobs.items()):
            if job.get("status") in {"running", "queued"}:
                job["status"] = "queued"
                job["updated_at"] = self._now()
                self._spawn_worker(job_id)
        self._save_state()

    def list_jobs(self) -> list[dict[str, Any]]:
        with self._lock:
            return [self._jobs[job_id].copy() for job_id in sorted(self._jobs.keys())]

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        with self._lock:
            job = self._jobs.get(job_id)
            return job.copy() if job else None

    def find_active_job_for_model(self, model_name: str) -> dict[str, Any] | None:
        with self._lock:
            for job in self._jobs.values():
                if job.get("model") == model_name and job.get("status") in {"queued", "running", "paused"}:
                    return job.copy()
        return None

    def start_download(self, model_name: str) -> dict[str, Any]:
        existing = self.find_active_job_for_model(model_name)
        if existing:
            return existing

        with self._lock:
            job_id = str(uuid.uuid4())
            job = {
                "id": job_id,
                "model": model_name,
                "status": "queued",
                "percent": 0,
                "completed": 0,
                "total": 0,
                "message": "Queued for download",
                "error": None,
                "created_at": self._now(),
                "updated_at": self._now(),
            }
            self._jobs[job_id] = job
            self._save_state()
        self._spawn_worker(job_id)
        return job.copy()

    def resume_download(self, job_id: str) -> dict[str, Any]:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                raise KeyError(job_id)
            if job.get("status") == "completed":
                return job.copy()
            job["status"] = "queued"
            job["message"] = "Resuming download"
            job["error"] = None
            job["updated_at"] = self._now()
            self._save_state()
            self._spawn_worker(job_id)
            return job.copy()

    def cancel_download(self, job_id: str) -> dict[str, Any]:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                raise KeyError(job_id)
            if job.get("status") in {"completed", "failed"}:
                return job.copy()
            job["status"] = "cancelled"
            job["message"] = "Cancelled by user"
            job["updated_at"] = self._now()
            self._save_state()
            return job.copy()

    def _spawn_worker(self, job_id: str) -> None:
        thread = self._threads.get(job_id)
        if thread and thread.is_alive():
            return
        thread = threading.Thread(target=self._run_job, args=(job_id,), name=f"cortex-download-{job_id}", daemon=True)
        self._threads[job_id] = thread
        thread.start()

    def _update_job(self, job_id: str, **updates: Any) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return
            job.update(updates)
            job["updated_at"] = self._now()
            self._save_state()

    def _run_job(self, job_id: str) -> None:
        job = self.get_job(job_id)
        if not job:
            return

        model_name = job["model"]
        url = f"{settings.OLLAMA_URL.rstrip('/')}/api/pull"
        self._update_job(job_id, status="running", message="Downloading model", error=None)

        try:
            with httpx.Client(timeout=3600) as client:
                with client.stream("POST", url, json={"name": model_name}) as response:
                    if response.status_code != 200:
                        self._update_job(
                            job_id,
                            status="failed",
                            message=f"Failed to start download: {response.status_code}",
                            error=f"HTTP {response.status_code}",
                        )
                        return

                    for raw_line in response.iter_lines():
                        if not raw_line:
                            continue

                        current = self.get_job(job_id)
                        if not current or current.get("status") == "cancelled":
                            self._update_job(job_id, message="Download cancelled")
                            return

                        try:
                            line = raw_line.decode("utf-8") if isinstance(raw_line, bytes) else str(raw_line)
                            payload = json.loads(line)
                        except Exception:
                            continue

                        status = str(payload.get("status") or "downloading")
                        completed = int(payload.get("completed") or 0)
                        total = int(payload.get("total") or 0)
                        percent = int((completed / total) * 100) if total > 0 else current.get("percent", 0)

                        self._update_job(
                            job_id,
                            status="running",
                            message=status,
                            completed=completed,
                            total=total,
                            percent=min(max(percent, 0), 100),
                            error=None,
                        )

                        if status.lower() in {"success", "pull complete", "downloaded", "verifying sha256 digest", "writing manifest"} and total > 0 and completed >= total:
                            self._update_job(
                                job_id,
                                status="completed",
                                message="Download completed",
                                completed=total,
                                total=total,
                                percent=100,
                                error=None,
                            )
                            return

            final = self.get_job(job_id)
            if final and final.get("status") != "cancelled":
                self._update_job(
                    job_id,
                    status="completed",
                    message="Download completed",
                    percent=100,
                    error=None,
                )
        except Exception as exc:
            logger.warning("Model download failed for %s: %s", model_name, exc)
            self._update_job(
                job_id,
                status="failed",
                message="Download failed",
                error=str(exc),
            )


model_download_manager = ModelDownloadManager()
