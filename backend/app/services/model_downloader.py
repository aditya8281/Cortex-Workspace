from __future__ import annotations
import asyncio
import json
import logging
import time
from pathlib import Path

from backend.app.core.config import settings

logger = logging.getLogger(__name__)

MODELS_DIR = Path(getattr(settings, "CORTEX_ROOT", None) or "./CortexMemory") / "models"
PROGRESS_FILE = MODELS_DIR / "download_progress.json"


class ModelDownloader:
    def __init__(self):
        self._active_downloads: dict[str, asyncio.Task] = {}
        self._progress: dict[str, float] = {}
        self._persisted_status: dict[str, dict] = {}
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        self._load_progress()

    def _load_progress(self) -> None:
        """Load progress from JSON file."""
        if not PROGRESS_FILE.exists():
            return
        try:
            with open(PROGRESS_FILE, "r") as f:
                data = json.load(f)
            for model_name, info in data.items():
                self._progress[model_name] = info.get("progress", 0.0)
                self._persisted_status[model_name] = info
        except (json.JSONDecodeError, IOError) as e:
            logger.warning("Failed to load progress file: %s", e)

    def _save_progress(self) -> None:
        """Save progress to JSON file."""
        data = {}
        for model_name, progress in self._progress.items():
            status = "downloading"
            if model_name in self._persisted_status:
                status = self._persisted_status[model_name].get("status", status)
            data[model_name] = {
                "progress": progress,
                "status": status,
                "started_at": self._persisted_status.get(model_name, {}).get("started_at", time.time())
            }
        try:
            with open(PROGRESS_FILE, "w") as f:
                json.dump(data, f, indent=2)
        except IOError as e:
            logger.warning("Failed to save progress file: %s", e)

    async def download_model(self, model_name: str, catalog: list[dict], variant: str | None = None) -> dict:
        """Start downloading a model. Returns immediately."""
        full_model_name = model_name
        if variant:
            full_model_name = f"{model_name}:{variant}"

        if full_model_name in self._active_downloads:
            return {"status": "already_downloading", "model": full_model_name}

        model_entry = next((m for m in catalog if m["name"] == model_name), None)
        if not model_entry:
            raise ValueError(f"Model {model_name} not found in catalog")

        from backend.app.services.llm.manager import llm_manager
        available = await llm_manager.list_all_models()
        if any(m.name == full_model_name for m in available):
            return {"status": "already_downloaded", "model": full_model_name}

        task = asyncio.create_task(self._do_download(full_model_name, model_entry))
        self._active_downloads[full_model_name] = task
        return {"status": "started", "model": full_model_name}

    async def _do_download(self, model_name: str, model_entry: dict):
        """Execute the download via Ollama pull."""
        try:
            self._progress[model_name] = 0.01
            self._persisted_status[model_name] = {"status": "downloading", "progress": 0.01, "started_at": time.time()}
            self._save_progress()

            if model_entry.get("provider") == "ollama":
                await self._pull_ollama(model_name)
            else:
                raise ValueError(f"No download method for {model_name} (provider: {model_entry.get('provider')})")

            self._progress[model_name] = 1.0
            self._persisted_status[model_name] = {"status": "completed", "progress": 1.0, "started_at": self._persisted_status.get(model_name, {}).get("started_at", time.time())}
            self._save_progress()
        except asyncio.CancelledError:
            logger.info("Download cancelled: %s", model_name)
            self._progress.pop(model_name, None)
            self._persisted_status[model_name] = {"status": "failed", "progress": 0.0, "started_at": self._persisted_status.get(model_name, {}).get("started_at", time.time())}
            self._save_progress()
        except Exception as e:
            logger.error("Download failed for %s: %s", model_name, e)
            self._progress[model_name] = 0.0
            self._persisted_status[model_name] = {"status": "failed", "progress": 0.0, "started_at": self._persisted_status.get(model_name, {}).get("started_at", time.time())}
            self._save_progress()
        finally:
            self._active_downloads.pop(model_name, None)

    async def _pull_ollama(self, model_name: str):
        """Pull model via Ollama API with progress tracking."""
        import httpx
        from backend.app.core.config import settings
        base_url = settings.OLLAMA_BASE_URL

        async with httpx.AsyncClient(base_url=base_url, timeout=3600.0) as client:
            async with client.stream("POST", "/api/pull", json={"name": model_name}) as resp:
                resp.raise_for_status()
                import json
                async for line in resp.aiter_lines():
                    if line:
                        data = json.loads(line)
                        status = data.get("status", "")
                        if "total" in data and "completed" in data:
                            total = data["total"]
                            completed = data["completed"]
                            if total > 0:
                                self._progress[model_name] = min(completed / total, 0.99)
                                self._save_progress()
                        elif status == "success":
                            self._progress[model_name] = 1.0
                            self._save_progress()

    def get_progress(self, model_name: str) -> float:
        """Get current download progress for a model."""
        if model_name in self._progress:
            return self._progress[model_name]
        if model_name in self._persisted_status:
            info = self._persisted_status[model_name]
            if info.get("status") == "completed":
                return 1.0
            return info.get("progress", 0.0)
        return 0.0

    async def cancel_download(self, model_name: str) -> bool:
        """Cancel an active download."""
        task = self._active_downloads.get(model_name)
        if task and not task.done():
            task.cancel()
            self._active_downloads.pop(model_name, None)
            return True
        return False


model_downloader = ModelDownloader()
