"""Background library.json scraper.

Scrapes ollama.com/library to update backend/app/data/library.json
with the latest model families and tags. Runs once at startup and
on manual trigger (not periodic).
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_LIBRARY_URL = "https://ollama.com/library"
_OUTPUT = Path(__file__).resolve().parent.parent / "data" / "library.json"


def _parse_model_names(html: str) -> list[str]:
    """Extract model family names from the library listing page."""
    pattern = r'href="/library/([a-zA-Z0-9][a-zA-Z0-9._-]*)"'
    matches = re.findall(pattern, html)
    seen: set[str] = set()
    names: list[str] = []
    for m in matches:
        if ":" not in m and m not in seen:
            seen.add(m)
            names.append(m)
    return names


def _parse_model_tags(html: str, model_name: str) -> list[str]:
    """Extract tag names from a model page."""
    escaped = re.escape(model_name)
    pattern = rf'href="/library/{escaped}:([^"]+)"'
    matches = re.findall(pattern, html)
    seen: set[str] = set()
    tags: list[str] = []
    for t in matches:
        if t not in seen:
            seen.add(t)
            tags.append(t)
    return tags


async def scrape_library_background() -> None:
    """Scrape ollama.com/library and update backend/app/data/library.json.

    Runs in background — does not block startup. Silently fails on errors.
    """
    try:
        async with httpx.AsyncClient(
            follow_redirects=True,
            headers={"User-Agent": "cortex/1.0"},
            timeout=30,
        ) as client:
            resp = await client.get(_LIBRARY_URL)
            resp.raise_for_status()
            model_names = _parse_model_names(resp.text)
            logger.info("Library scrape: found %d model families", len(model_names))

            semaphore = asyncio.Semaphore(10)
            total_tags = 0
            models: list[dict[str, Any]] = []

            async def _scrape_one(name: str) -> dict[str, Any]:
                async with semaphore:
                    try:
                        r = await client.get(f"{_LIBRARY_URL}/{name}", timeout=20)
                        if r.status_code == 200:
                            tags = _parse_model_tags(r.text, name)
                            return {"name": name, "tags": tags}
                    except Exception:
                        pass
                    return {"name": name, "tags": []}

            results = await asyncio.gather(*[_scrape_one(n) for n in model_names])
            for r in results:
                total_tags += len(r["tags"])
                models.append(r)

            library = {
                "scraped_at": datetime.now(timezone.utc).isoformat(),
                "source": _LIBRARY_URL,
                "total_models": len(models),
                "total_tags": total_tags,
                "models": sorted(models, key=lambda m: m["name"]),
            }
            _OUTPUT.parent.mkdir(parents=True, exist_ok=True)
            _OUTPUT.write_text(json.dumps(library, indent=2))
            logger.info(
                "Library scrape complete: %d models, %d tags saved to %s",
                len(models),
                total_tags,
                _OUTPUT,
            )
    except Exception as e:
        logger.warning("Library scrape failed (non-blocking): %s", e)
