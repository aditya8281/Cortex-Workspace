from __future__ import annotations
import asyncio
import logging
from pathlib import Path

from backend.app.core.config import settings

logger = logging.getLogger(__name__)

MODELS_DIR = Path(getattr(settings, "CORTEX_ROOT", None) or "./CortexMemory") / "models"


class ModelDownloader:
    def __init__(self):
        self._active_downloads: dict[str, asyncio.Task] = {}
        self._progress: dict[str, float] = {}

    async def download_model(self, model_name: str, catalog: list[dict]) -> dict:
        """Start downloading a model. Returns immediately."""
        if model_name in self._active_downloads:
            return {"status": "already_downloading", "model": model_name}

        # Check catalog
        model_entry = next((m for m in catalog if m["name"] == model_name), None)
        if not model_entry:
            raise ValueError(f"Model {model_name} not found in catalog")

        # Check if already available via providers
        from backend.app.services.llm.manager import llm_manager
        available = await llm_manager.list_all_models()
        if any(m.name == model_name for m in available):
            return {"status": "already_downloaded", "model": model_name}

        task = asyncio.create_task(self._do_download(model_name, model_entry))
        self._active_downloads[model_name] = task
        return {"status": "started", "model": model_name}

    async def _do_download(self, model_name: str, model_entry: dict):
        """Execute the download via Ollama pull."""
        try:
            self._progress[model_name] = 0.01

            if model_entry.get("provider") == "ollama":
                await self._pull_ollama(model_name)
            else:
                raise ValueError(f"No download method for {model_name} (provider: {model_entry.get('provider')})")

            self._progress[model_name] = 1.0
        except asyncio.CancelledError:
            logger.info("Download cancelled: %s", model_name)
            self._progress.pop(model_name, None)
        except Exception as e:
            logger.error("Download failed for %s: %s", model_name, e)
            self._progress[model_name] = 0.0
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
                        elif status == "success":
                            self._progress[model_name] = 1.0

    def get_progress(self, model_name: str) -> float:
        """Get current download progress for a model."""
        return self._progress.get(model_name, 0.0)

    async def cancel_download(self, model_name: str) -> bool:
        """Cancel an active download."""
        task = self._active_downloads.get(model_name)
        if task and not task.done():
            task.cancel()
            self._active_downloads.pop(model_name, None)
            return True
        return False


model_downloader = ModelDownloader()
