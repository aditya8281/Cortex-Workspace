# Ollama Auto-Detect + Full Registry Integration Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Auto-detect Ollama models pulled outside Cortex, integrate full registry.ollama.ai (214 models), add fallback JSON, and report catalog health to users.

**Architecture:** Two services: (1) `OllamaSyncService` syncs installed models to DB, (2) Enhanced `OllamaCatalogService` loads from `library.json` (214 models), probes full OCI registry, saves fallback JSON, reports source health. Frontend shows catalog status banner.

**Tech Stack:** Python (httpx, SQLAlchemy, asyncio), Next.js (React), pytest

## Global Constraints

- Python 3.11+, async/await throughout
- SQLAlchemy ORM with Alembic migrations (no Drizzle)
- `settings.OLLAMA_BASE_URL` from `backend/app/core/config.py`
- Frontend: Next.js App Router, TypeScript, Tailwind
- All tests must pass before commit
- Commit after each task with one-line message

---

## File Structure

| File | Action | Purpose |
|------|--------|---------|
| `backend/app/data/library.json` | CREATE | Full model index (214 models, 773 tags) from ref scripts |
| `backend/app/services/ollama_sync.py` | CREATE | OllamaSyncService for installed model detection |
| `backend/app/services/ollama_catalog.py` | EDIT | Load from library.json, add fallback, track source health |
| `backend/app/main.py` | EDIT | Startup sync + periodic background task |
| `backend/app/api/v1/models.py` | EDIT | POST /models/installed/sync + catalog_status in /models |
| `backend/app/schemas/models.py` | EDIT | Add SyncInstalledResponse + CatalogStatus |
| `frontend/app/models/ModelsPage.tsx` | EDIT | Add Scan button + catalog status banner |
| `frontend/src/shared/api/models.ts` | EDIT | Add syncInstalled() API |
| `tests/services/test_ollama_sync.py` | CREATE | Unit tests for OllamaSyncService |
| `tests/api/test_models_sync.py` | CREATE | Integration tests for sync endpoint |

---

### Task 1: Copy library.json to backend

**Files:**
- Create: `backend/app/data/library.json`
- Source: `.agents/ref/models/library.json`

**Interfaces:**
- Consumes: `.agents/ref/models/library.json` (214 models, 773 tags)
- Produces: `backend/app/data/library.json` (canonical model index)

- [ ] **Step 1: Copy the file**

```bash
mkdir -p backend/app/data
cp .agents/ref/models/library.json backend/app/data/library.json
```

- [ ] **Step 2: Verify contents**

```bash
python3 -c "import json; d=json.load(open('backend/app/data/library.json')); print(f'{d[\"total_models\"]} models, {d[\"total_tags\"]} tags')"
```

Expected: `214 models, 773 tags`

- [ ] **Step 3: Commit**

```bash
git add backend/app/data/library.json
git commit -m "feat: add library.json with 214 Ollama model families"
```

---

### Task 2: Create OllamaSyncService

**Files:**
- Create: `backend/app/services/ollama_sync.py`
- Test: `tests/services/test_ollama_sync.py`

**Interfaces:**
- Consumes: `settings.OLLAMA_BASE_URL`, `ModelVariant` model, `ModelCatalog` model
- Produces: `OllamaSyncService.sync_installed_models(db) -> SyncResult`

- [ ] **Step 1: Write the failing test**

```python
# tests/services/test_ollama_sync.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone

from backend.app.services.ollama_sync import OllamaSyncService, SyncResult


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.execute.return_value = MagicMock()
    db.commit = MagicMock()
    return db


@pytest.mark.asyncio
async def test_sync_marks_downloaded_variant(mock_db):
    """Existing variant with matching ollama_tag gets marked downloaded."""
    mock_variant = MagicMock()
    mock_variant.downloaded = False
    mock_variant.ollama_tag = "llama3.1:8b"

    mock_db.execute.return_value.scalar_one_or_none.return_value = mock_variant

    mock_installed = [{"name": "llama3.1:8b", "size": 4700000000}]

    with patch("backend.app.services.ollama_sync.settings") as mock_settings:
        mock_settings.OLLAMA_BASE_URL = "http://localhost:11434"
        with patch("backend.app.services.ollama_sync.httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = {"models": mock_installed}
            mock_response.raise_for_status = MagicMock()
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(return_value=mock_response)

            service = OllamaSyncService()
            result = await service.sync_installed_models(mock_db)

    assert result.matched == 1
    assert mock_variant.downloaded is True
    assert mock_variant.last_downloaded_at is not None


@pytest.mark.asyncio
async def test_sync_graceful_on_offline(mock_db):
    """Returns empty result when Ollama is offline."""
    import httpx

    with patch("backend.app.services.ollama_sync.settings") as mock_settings:
        mock_settings.OLLAMA_BASE_URL = "http://localhost:11434"
        with patch("backend.app.services.ollama_sync.httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))

            service = OllamaSyncService()
            result = await service.sync_installed_models(mock_db)

    assert result.matched == 0
    assert result.created == 0
    assert len(result.errors) > 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/services/test_ollama_sync.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'backend.app.services.ollama_sync'`

- [ ] **Step 3: Write the implementation**

```python
# backend/app/services/ollama_sync.py
"""Ollama auto-detect sync service.

Queries Ollama's /api/tags to detect locally installed models
and syncs their download status to the database.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.models.model_catalog import ModelCatalog, ModelVariant

logger = logging.getLogger(__name__)


@dataclass
class SyncResult:
    matched: int = 0
    created: int = 0
    deleted: int = 0
    errors: list[str] = field(default_factory=list)


def _guess_quant_from_tag(tag: str) -> str:
    """Guess quantization level from Ollama tag."""
    tag_lower = tag.lower()
    if "q4_k_m" in tag_lower:
        return "Q4_K_M"
    if "q4_k_s" in tag_lower:
        return "Q4_K_S"
    if "q5_k_m" in tag_lower:
        return "Q5_K_M"
    if "q8_0" in tag_lower:
        return "Q8_0"
    if "q3_k" in tag_lower:
        return "Q3_K"
    if "fp16" in tag_lower or "f16" in tag_lower:
        return "FP16"
    if "q6_k" in tag_lower:
        return "Q6_K"
    return "default"


def _extract_param_count(model_name: str) -> float:
    """Extract parameter count from model name (e.g., 'llama3.1:8b' -> 8.0)."""
    import re
    match = re.search(r"(\d+\.?\d*)[bB]", model_name)
    if match:
        return float(match.group(1))
    return 7.0


class OllamaSyncService:
    """Syncs Ollama's locally installed models to the Cortex database."""

    async def sync_installed_models(self, db: Session) -> SyncResult:
        result = SyncResult()

        # 1. Query Ollama for installed models
        installed_models = await self._fetch_installed(result)
        if installed_models is None:
            return result

        installed_tags = {m["name"] for m in installed_models}
        installed_by_tag = {m["name"]: m for m in installed_models}

        # 2. Match existing variants by ollama_tag
        existing_variants = db.execute(
            select(ModelVariant).where(
                ModelVariant.ollama_tag.isnot(None),
                ModelVariant.ollama_tag.in_(list(installed_tags)),
            )
        ).scalars().all()

        matched_tags = set()
        for variant in existing_variants:
            if not variant.downloaded:
                variant.downloaded = True
                variant.last_downloaded_at = datetime.now(timezone.utc)
                result.matched += 1
            matched_tags.add(variant.ollama_tag)

        # 3. Create unknown models
        unmatched_tags = installed_tags - matched_tags
        for tag in unmatched_tags:
            model_info = installed_by_tag[tag]
            base_name = tag.split(":")[0]

            # Find or create ModelCatalog entry
            catalog = db.execute(
                select(ModelCatalog).where(ModelCatalog.model_id == base_name)
            ).scalar_one_or_none()

            if catalog is None:
                catalog = ModelCatalog(
                    model_id=base_name,
                    display_name=base_name.replace("-", " ").title(),
                    family="unknown",
                    provider="ollama",
                    parameter_count=_extract_param_count(base_name),
                )
                db.add(catalog)
                db.flush()
                result.created += 1

            # Create variant
            variant = ModelVariant(
                model_catalog_id=catalog.id,
                variant_id=tag,
                ollama_tag=tag,
                quantization=_guess_quant_from_tag(tag),
                size_bytes=model_info.get("size", 0),
                downloaded=True,
                last_downloaded_at=datetime.now(timezone.utc),
            )
            db.add(variant)
            result.created += 1

        # 4. Detect deletions
        downloaded_variants = db.execute(
            select(ModelVariant).where(
                ModelVariant.downloaded == True,
                ModelVariant.ollama_tag.isnot(None),
            )
        ).scalars().all()

        for variant in downloaded_variants:
            if variant.ollama_tag not in installed_tags:
                variant.downloaded = False
                result.deleted += 1

        db.commit()
        return result

    async def _fetch_installed(self, result: SyncResult) -> list[dict] | None:
        """Fetch installed models from Ollama. Returns None on failure."""
        try:
            async with httpx.AsyncClient(
                base_url=settings.OLLAMA_BASE_URL, timeout=5.0
            ) as client:
                resp = await client.get("/api/tags")
                resp.raise_for_status()
                return resp.json().get("models", [])
        except Exception as e:
            logger.warning("Failed to fetch Ollama models: %s", e)
            result.errors.append(str(e))
            return None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/services/test_ollama_sync.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/ollama_sync.py tests/services/test_ollama_sync.py
git commit -m "feat: add OllamaSyncService for auto-detecting installed models"
```

---

### Task 3: Add sync endpoint + schema

**Files:**
- Modify: `backend/app/api/v1/models.py:199` (add endpoint after `list_installed_models`)
- Modify: `backend/app/schemas/models.py` (add `SyncInstalledResponse`)
- Test: `tests/api/test_models_sync.py`

**Interfaces:**
- Consumes: `OllamaSyncService.sync_installed_models(db)` from Task 2
- Produces: `POST /api/v1/models/installed/sync` endpoint

- [ ] **Step 1: Write the failing test**

```python
# tests/api/test_models_sync.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from backend.app.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_current_user():
    user = MagicMock()
    user.id = 1
    return user


@pytest.mark.asyncio
async def test_sync_endpoint_returns_result(client, mock_current_user):
    """POST /models/installed/sync returns SyncInstalledResponse."""
    mock_result = MagicMock()
    mock_result.matched = 2
    mock_result.created = 1
    mock_result.deleted = 0
    mock_result.errors = []

    with patch("backend.app.api.v1.models.get_current_user", return_value=mock_current_user):
        with patch("backend.app.api.v1.models.OllamaSyncService") as MockService:
            MockService.return_value.sync_installed_models = AsyncMock(return_value=mock_result)
            response = client.post("/api/v1/models/installed/sync")

    assert response.status_code == 200
    data = response.json()
    assert data["matched"] == 2
    assert data["created"] == 1
    assert data["deleted"] == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/api/test_models_sync.py -v`
Expected: FAIL with 405 Method Not Allowed (endpoint doesn't exist)

- [ ] **Step 3: Add SyncInstalledResponse schema**

```python
# In backend/app/schemas/models.py, add after InstalledModelsResponse:

class SyncInstalledResponse(BaseModel):
    """Response for Ollama model sync."""
    matched: int = 0
    created: int = 0
    deleted: int = 0
    errors: list[str] = []
```

- [ ] **Step 4: Add sync endpoint**

```python
# In backend/app/api/v1/models.py, after list_installed_models endpoint:

@router.post("/models/installed/sync", response_model=SyncInstalledResponse)
async def sync_installed_models(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Sync locally installed Ollama models to the database."""
    from backend.app.services.ollama_sync import OllamaSyncService

    service = OllamaSyncService()
    result = await service.sync_installed_models(db)
    return result
```

Also add `SyncInstalledResponse` to the imports at top of models.py.

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/api/test_models_sync.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/api/v1/models.py backend/app/schemas/models.py tests/api/test_models_sync.py
git commit -m "feat: add POST /models/installed/sync endpoint"
```

---

### Task 4: Wire startup + periodic background sync + library scrape

**Files:**
- Modify: `backend/app/main.py:97-115` (after DB init section)
- Create: `backend/app/services/library_scraper.py` (wraps scrape_library.py logic)

**Interfaces:**
- Consumes: `OllamaSyncService.sync_installed_models(db)` from Task 2
- Consumes: `scrape_library.py` logic from ref scripts
- Produces: Startup sync, 60s periodic background task, background library scrape

- [ ] **Step 1: Create library_scraper.py service**

Create `backend/app/services/library_scraper.py` that wraps the scraping logic from `.agents/ref/scripts/scrape_library.py` into an async function:

```python
"""Background library.json scraper.

Scrapes ollama.com/library to update backend/app/data/library.json
with the latest model families and tags. Runs once at startup and
on manual trigger (not periodic).
"""
from __future__ import annotations

import asyncio
import json
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
            # Step 1: Fetch library listing page
            resp = await client.get(_LIBRARY_URL)
            resp.raise_for_status()
            model_names = _parse_model_names(resp.text)
            logger.info("Library scrape: found %d model families", len(model_names))

            # Step 2: Scrape each model page for tags
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

            # Step 3: Save
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
```

- [ ] **Step 2: Edit main.py startup section**

After the DB init block (around line 104), add:

```python
    # Background library scrape (non-blocking — updates library.json once)
    try:
        import asyncio as _asyncio
        _asyncio.create_task(scrape_library_background())
        logger.info("Library scrape started in background")
    except Exception as e:
        logger.warning("Failed to start library scrape: %s", e)

    # Auto-detect Ollama models on startup
    try:
        from backend.app.services.ollama_sync import OllamaSyncService
        from backend.app.db.session import SessionLocal as _SyncSessionLocal

        _sync_db = _SyncSessionLocal()
        try:
            _sync_result = await OllamaSyncService().sync_installed_models(_sync_db)
            logger.info(
                "Ollama model sync: matched=%d created=%d deleted=%d",
                _sync_result.matched,
                _sync_result.created,
                _sync_result.deleted,
            )
        finally:
            _sync_db.close()
    except Exception as e:
        logger.warning("Ollama model sync failed on startup: %s", e)
```

After the sync state recovery block (around line 134), add the periodic task:

```python
    # Periodic Ollama model sync (every 60 seconds)
    async def _periodic_ollama_sync():
        while True:
            await asyncio.sleep(60)
            try:
                from backend.app.services.ollama_sync import OllamaSyncService
                from backend.app.db.session import SessionLocal as _PeriodicSession

                _pdb = _PeriodicSession()
                try:
                    await OllamaSyncService().sync_installed_models(_pdb)
                finally:
                    _pdb.close()
            except Exception:
                pass

    asyncio.create_task(_periodic_ollama_sync())
    logger.info("Periodic Ollama model sync started (60s interval)")
```

- [ ] **Step 3: Run existing tests to verify no breakage**

Run: `pytest tests/ -v --timeout=30`
Expected: All existing tests still pass

- [ ] **Step 4: Commit**

```bash
git add backend/app/services/library_scraper.py backend/app/main.py
git commit -m "feat: wire startup sync + background library scrape"
```

---

### Task 5: Upgrade catalog to full registry (library.json)

**Files:**
- Modify: `backend/app/services/ollama_catalog.py` — major refactor

**Interfaces:**
- Consumes: `backend/app/data/library.json` (214 models from Task 1)
- Produces: `fetch_registry_models()` uses all 214 models, `CatalogSourceStatus` tracking

- [ ] **Step 1: Replace POPULAR_MODELS with library.json loader**

In `backend/app/services/ollama_catalog.py`, replace the `POPULAR_MODELS` constant (lines 49-84) with:

```python
import re
from pathlib import Path

_LIBRARY_JSON = Path(__file__).resolve().parent.parent / "data" / "library.json"


def _load_library_json() -> list[dict[str, Any]]:
    """Load full model list from backend/app/data/library.json.

    Returns list of dicts with 'name' and 'tags' keys.
    Falls back to empty list if file not found.
    """
    if not _LIBRARY_JSON.exists():
        logger.warning("library.json not found at %s", _LIBRARY_JSON)
        return []
    try:
        data = json.loads(_LIBRARY_JSON.read_text())
        models = data.get("models", [])
        total_tags = sum(len(m.get("tags", ["latest"])) for m in models)
        logger.info(
            "Loaded %d models (%d tags) from library.json",
            len(models),
            total_tags,
        )
        return models
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Failed to load library.json: %s", e)
        return []
```

- [ ] **Step 2: Update fetch_registry_models to use library.json**

Replace `fetch_registry_models()` (lines 207-227) with:

```python
    async def fetch_registry_models(self) -> list[dict[str, Any]]:
        """Probe the OCI registry for ALL models from library.json.

        Iterates over all 214 model families and their tags,
        probing each model:tag combination via OCI manifest + blob.
        No model weights are downloaded.

        Returns:
            List of model dicts from the registry source.
        """
        await self.get_client()
        models: list[dict[str, Any]] = []

        library_models = _load_library_json()
        if not library_models:
            logger.warning("No library.json models available for registry probe")
            return []

        # Build full probe list: (model_name, tag, all_tags)
        probe_list: list[tuple[str, str, list[str]]] = []
        for m in library_models:
            name = m["name"]
            tags = m.get("tags", ["latest"])
            for tag in tags:
                probe_list.append((name, tag, tags))

        logger.info(
            "Probing %d model:tag pairs from registry (concurrency=%d)",
            len(probe_list),
            CONCURRENCY_LIMIT,
        )

        async def _probe_one(
            model_name: str, tag: str, all_tags: list[str]
        ) -> None:
            async with self._semaphore:
                result = await self._probe_registry_model(model_name, tag)
            if result is not None:
                result["available_tags"] = all_tags
                models.append(result)

        await asyncio.gather(
            *[_probe_one(name, tag, tags) for name, tag, tags in probe_list]
        )

        logger.info("Registry probe complete: %d models found", len(models))
        return models
```

- [ ] **Step 3: Add source status tracking**

Add a dataclass near the top of the file (after imports):

```python
@dataclass
class CatalogSourceStatus:
    """Track health status of each catalog source."""
    cloud: str = "pending"      # "ok", "unavailable", "timeout", "pending"
    local: str = "pending"
    registry: str = "pending"
    last_updated: str = ""
    from_fallback: bool = False
    errors: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "cloud": self.cloud,
            "local": self.local,
            "registry": self.registry,
            "last_updated": self.last_updated,
            "from_fallback": self.from_fallback,
            "errors": self.errors,
        }
```

Add `from dataclasses import dataclass, field` to imports if not already present.

- [ ] **Step 4: Add fallback JSON mechanism**

Add these methods to `OllamaCatalogService`:

```python
FALLBACK_FILE = CACHE_DIR / "ollama_catalog_fallback.json"


def _save_fallback(self, models: list[dict[str, Any]]) -> None:
    """Save catalog to fallback file after successful fetch."""
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        data = {
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "models": models,
        }
        with open(FALLBACK_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.debug("Saved fallback catalog (%d models)", len(models))
    except OSError as e:
        logger.warning("Failed to save fallback catalog: %s", e)


def _load_fallback(self) -> list[dict[str, Any]] | None:
    """Load catalog from fallback file."""
    try:
        if FALLBACK_FILE.exists():
            with open(FALLBACK_FILE, encoding="utf-8") as f:
                data = json.load(f)
            models = data.get("models", [])
            logger.info("Loaded fallback catalog (%d models)", len(models))
            return models
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Failed to load fallback catalog: %s", e)
    return None
```

- [ ] **Step 5: Update fetch_catalog to use fallback + status tracking**

Replace `fetch_catalog()` (lines 111-175) with:

```python
    async def fetch_catalog(
        self,
        force_refresh: bool = False,
        include_cloud: bool = True,
        include_local: bool = True,
        include_registry: bool = True,
    ) -> tuple[list[dict[str, Any]], CatalogSourceStatus]:
        """Fetch the unified model catalog from all enabled sources.

        Returns:
            Tuple of (models list, source status).
        """
        status = CatalogSourceStatus()

        if not force_refresh:
            cached = self._load_cache()
            if cached is not None and self._is_cache_valid(cached):
                models = cached.get("models", [])
                logger.debug("Returning %d cached catalog models", len(models))
                status.from_fallback = False
                status.last_updated = cached.get("fetched_at", "")
                return models, status

        tasks: list[asyncio.Task] = []
        source_priority: dict[str, int] = {}

        if include_cloud:
            tasks.append(asyncio.create_task(self.fetch_cloud_models()))
            source_priority["cloud"] = 3
        if include_local:
            tasks.append(asyncio.create_task(self.fetch_local_models()))
            source_priority["local"] = 2
        if include_registry:
            tasks.append(asyncio.create_task(self.fetch_registry_models()))
            source_priority["registry"] = 1

        results = await asyncio.gather(*tasks, return_exceptions=True)

        merged: dict[str, dict[str, Any]] = {}
        source_names = []
        if include_cloud:
            source_names.append("cloud")
        if include_local:
            source_names.append("local")
        if include_registry:
            source_names.append("registry")

        for result, source_name in zip(results, source_names, strict=False):
            if isinstance(result, Exception):
                status.cloud = "error" if source_name == "cloud" else status.cloud
                status.local = "error" if source_name == "local" else status.local
                status.registry = "error" if source_name == "registry" else status.registry
                status.errors[source_name] = str(result)
                logger.warning("Source %s failed: %s", source_name, result)
                continue

            if not result:
                # Source returned empty — might be unavailable
                if source_name == "cloud":
                    status.cloud = "unavailable"
                elif source_name == "local":
                    status.local = "unavailable"
                elif source_name == "registry":
                    status.registry = "unavailable"
                continue

            # Mark source as OK
            if source_name == "cloud":
                status.cloud = "ok"
            elif source_name == "local":
                status.local = "ok"
            elif source_name == "registry":
                status.registry = "ok"

            for model in result:
                key = model.get("name", "")
                existing = merged.get(key)
                if existing is None:
                    merged[key] = model
                else:
                    existing_priority = source_priority.get(existing.get("source", ""), 0)
                    new_priority = source_priority.get(model.get("source", ""), 0)
                    if new_priority > existing_priority:
                        merged[key] = model

        models = list(merged.values())
        models.sort(key=lambda m: m.get("name", ""))

        # All sources failed — try fallback
        if not models:
            logger.warning("All catalog sources failed, attempting fallback")
            fallback = self._load_fallback()
            if fallback:
                models = fallback
                status.from_fallback = True
                status.errors["_fallback"] = "All sources failed, using cached fallback"

        if models:
            self._save_cache(models)
            self._save_fallback(models)
            status.last_updated = datetime.now(timezone.utc).isoformat()

        logger.info(
            "Fetched %d unique models (cloud=%s, local=%s, registry=%s, fallback=%s)",
            len(models),
            status.cloud,
            status.local,
            status.registry,
            status.from_fallback,
        )
        return models, status
```

- [ ] **Step 6: Update get_ollama_catalog and get_ollama_catalog_sync**

```python
async def get_ollama_catalog(
    force_refresh: bool = False,
) -> tuple[list[dict[str, Any]], CatalogSourceStatus]:
    """Async convenience function to get the Ollama catalog."""
    return await get_catalog_service().fetch_catalog(force_refresh=force_refresh)


def get_ollama_catalog_sync(
    force_refresh: bool = False,
) -> tuple[list[dict[str, Any]], CatalogSourceStatus]:
    """Sync convenience function to get the Ollama catalog."""
    return get_catalog_service().fetch_catalog_sync(force_refresh=force_refresh)
```

- [ ] **Step 7: Run tests to verify no breakage**

Run: `pytest tests/ -v --timeout=30`
Expected: All tests pass (note: callers of `get_ollama_catalog` may need updating for tuple return)

- [ ] **Step 8: Commit**

```bash
git add backend/app/services/ollama_catalog.py
git commit -m "feat: upgrade catalog to full registry (214 models) with fallback JSON"
```

---

### Task 6: Update /models endpoint with catalog_status

**Files:**
- Modify: `backend/app/api/v1/models.py:56-122` (`list_models` endpoint)
- Modify: `backend/app/schemas/models.py` (add `CatalogStatus` schema)

**Interfaces:**
- Consumes: `get_ollama_catalog()` now returns `(models, status)` tuple from Task 5
- Produces: `/models` response includes `catalog_status` field

- [ ] **Step 1: Add CatalogStatus schema**

```python
# In backend/app/schemas/models.py:

class CatalogSourceStatusResponse(BaseModel):
    cloud: str = "pending"
    local: str = "pending"
    registry: str = "pending"
    last_updated: str = ""
    from_fallback: bool = False
    errors: dict[str, str] = {}
```

- [ ] **Step 2: Update list_models endpoint**

```python
# In backend/app/api/v1/models.py, update list_models:

@router.get("/models", response_model=ModelListResponse)
async def list_models(
    model_type: str | None = None,
    downloaded_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from backend.app.services.ollama_catalog import get_ollama_catalog

    catalog_models, source_status = await get_ollama_catalog()

    # ... rest of existing logic unchanged ...

    return {
        "models": catalog,
        "total_count": len(catalog),
        "downloaded_count": sum(1 for m in catalog if m.get("downloaded")),
        "available_from_providers": [...],
        "type_counts": _compute_type_counts(catalog),
        "size_counts": _compute_size_counts(catalog),
        "catalog_status": source_status.to_dict(),
    }
```

- [ ] **Step 3: Update frontend ModelListResponse type**

```typescript
// In frontend/src/shared/types.ts (or wherever ModelListResponse is defined):

interface CatalogStatus {
  cloud: string;
  local: string;
  registry: string;
  last_updated: string;
  from_fallback: boolean;
  errors: Record<string, string>;
}

interface ModelListResponse {
  models: ModelInfo[];
  total_count: number;
  downloaded_count: number;
  available_from_providers: unknown[];
  type_counts: Record<string, number>;
  size_counts: Record<string, number>;
  catalog_status?: CatalogStatus;
}
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/ -v --timeout=30`
Expected: All tests pass

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/v1/models.py backend/app/schemas/models.py
git commit -m "feat: add catalog_status to /models response"
```

---

### Task 7: Add catalog status banner to frontend

**Files:**
- Modify: `frontend/app/models/ModelsPage.tsx`

**Interfaces:**
- Consumes: `catalog_status` from `/models` API response
- Produces: Status banner when catalog is degraded or from fallback

- [ ] **Step 1: Add CatalogStatusBanner component**

In `frontend/app/models/ModelsPage.tsx`, add a small banner component:

```tsx
function CatalogStatusBanner({ status }: { status?: CatalogStatus }) {
  if (!status) return null;

  const isDegraded =
    status.from_fallback ||
    status.cloud !== "ok" ||
    status.registry !== "ok";

  if (!isDegraded) return null;

  const issues: string[] = [];
  if (status.from_fallback) issues.push("Using cached catalog (all sources unavailable)");
  if (status.cloud !== "ok") issues.push(`Cloud: ${status.cloud}`);
  if (status.registry !== "ok") issues.push(`Registry: ${status.registry}`);

  return (
    <div className="glass-panel rounded-xl px-4 py-2 mb-4 border border-warning/20 bg-warning/5">
      <div className="flex items-center gap-2 text-[11px] text-warning">
        <AlertTriangle size={14} />
        <span>Catalog degraded — {issues.join("; ")}</span>
      </div>
    </div>
  );
}
```

Add `AlertTriangle` to lucide-react imports if not already present.

- [ ] **Step 2: Wire status into page**

In the page component, store the status from the API response:

```tsx
const [catalogStatus, setCatalogStatus] = useState<CatalogStatus | undefined>();

// In the useEffect that fetches data:
const catalogData = await modelsApi.list();
setCatalogStatus(catalogData.catalog_status);
```

Render the banner above the main content:
```tsx
<CatalogStatusBanner status={catalogStatus} />
```

- [ ] **Step 3: Run type check**

Run: `npx tsc --noEmit`
Expected: No type errors

- [ ] **Step 4: Commit**

```bash
git add frontend/app/models/ModelsPage.tsx
git commit -m "feat: add catalog status banner for degraded sources"
```

---

### Task 8: Fix hardcoded LOCAL_URL in ollama_catalog.py

**Files:**
- Modify: `backend/app/services/ollama_catalog.py:28`

**Interfaces:**
- Consumes: `settings.OLLAMA_BASE_URL`
- Produces: Fixed LOCAL_URL constant

- [ ] **Step 1: Edit the file**

```python
# In backend/app/services/ollama_catalog.py, line 28:

# BEFORE:
LOCAL_URL = "http://localhost:11434"

# AFTER:
from backend.app.core.config import settings
LOCAL_URL = settings.OLLAMA_BASE_URL
```

Note: Check if `settings` is already imported in this file. If so, just change the `LOCAL_URL` line.

- [ ] **Step 2: Run tests to verify no breakage**

Run: `pytest tests/ -v --timeout=30`
Expected: All tests pass

- [ ] **Step 3: Commit**

```bash
git add backend/app/services/ollama_catalog.py
git commit -m "fix: use settings.OLLAMA_BASE_URL instead of hardcoded localhost"
```

---

### Task 9: Add Scan button + catalog refresh to frontend

**Files:**
- Modify: `frontend/app/models/ModelsPage.tsx` (add Scan button + handler)
- Modify: `frontend/src/shared/api/models.ts` (add syncInstalled + refreshCatalog APIs)
- Modify: `backend/app/api/v1/models.py` (add POST /models/catalogue/refresh endpoint)
- Modify: `backend/app/services/ollama_catalog.py` (add refresh_catalog method)

**Interfaces:**
- Consumes: `POST /api/v1/models/installed/sync` from Task 3
- Consumes: `scrape_library_background()` from Task 4
- Produces: Scan button triggers library re-scrape + catalog refresh + installed sync

- [ ] **Step 1: Add refreshCatalog backend endpoint**

In `backend/app/api/v1/models.py`, add a new endpoint that triggers library re-scrape + catalog refresh:

```python
@router.post("/models/catalogue/refresh")
async def refresh_catalogue(
    current_user: User = Depends(get_current_user),
):
    """Refresh the Ollama catalog: re-scrape library, re-probe registry, update cache."""
    from backend.app.services.library_scraper import scrape_library_background
    from backend.app.services.ollama_catalog import get_catalog_service

    # Re-scrape library.json in background
    asyncio.create_task(scrape_library_background())

    # Force-refresh the catalog
    service = get_catalog_service()
    models, status = await service.fetch_catalog(force_refresh=True)

    return {
        "status": "ok",
        "models_added": len(models),
        "catalog_status": status.to_dict(),
    }
```

Make sure `asyncio` is imported at top of models.py.

- [ ] **Step 2: Add frontend API calls**

```typescript
// In frontend/src/shared/api/models.ts, add after installed():

syncInstalled: (): Promise<{ matched: number; created: number; deleted: number; errors: string[] }> =>
  api.post("/api/v1/models/installed/sync"),

refreshCatalog: (): Promise<{ status: string; models_added: number; catalog_status: Record<string, unknown> }> =>
  api.post("/api/v1/models/catalogue/refresh"),
```

- [ ] **Step 3: Add Scan button to ModelsPage**

In `frontend/app/models/ModelsPage.tsx`, find the installed bar header section. Add a Scan button next to it:

```tsx
import { RefreshCw } from "lucide-react";
```

In the installed bar header, add:
```tsx
<div className="flex items-center justify-between mb-3">
  <div className="flex items-center gap-3">
    <h2 className="text-lg font-semibold text-text">Installed Models</h2>
    {installedModels.length > 0 && (
      <span className="font-mono text-[10px] px-2 py-0.5 rounded-full bg-accent/10 text-accent border border-accent/20">
        {installedModels.length}
      </span>
    )}
  </div>
  <Button
    onClick={handleSyncInstalled}
    variant="ghost"
    size="sm"
    disabled={syncing}
  >
    <RefreshCw size={14} className={syncing ? "animate-spin" : ""} />
    Scan
  </Button>
</div>
```

Add state and handler — Scan triggers BOTH installed sync AND catalog refresh:
```tsx
const [syncing, setSyncing] = useState(false);

const handleSyncInstalled = async () => {
  setSyncing(true);
  try {
    // Re-scrape library + refresh catalog + sync installed models
    await Promise.all([
      modelsApi.refreshCatalog(),
      modelsApi.syncInstalled(),
    ]);
    setRefreshKey((k) => k + 1);
  } catch (err) {
    console.error("Sync failed:", err);
  } finally {
    setSyncing(false);
  }
};
```

- [ ] **Step 4: Run frontend tests**

Run: `npm test -- --passWithNoTests`
Expected: All tests pass

- [ ] **Step 5: Run type check**

Run: `npx tsc --noEmit`
Expected: No type errors

- [ ] **Step 6: Commit**

```bash
git add frontend/app/models/ModelsPage.tsx frontend/src/shared/api/models.ts backend/app/api/v1/models.py
git commit -m "feat: add Scan button with catalog refresh + library re-scrape"
```

---

### Task 10: End-to-end verification

- [ ] **Step 1: Run all backend tests**

Run: `pytest tests/ -v --timeout=60`
Expected: All tests pass

- [ ] **Step 2: Run frontend build**

Run: `npm run build`
Expected: Build succeeds

- [ ] **Step 3: Manual smoke test**

1. Start Cortex: `make dev`
2. Verify startup logs show "Library scrape started in background"
3. Verify startup logs show "Ollama model sync: matched=X created=Y deleted=Z"
4. Verify startup logs show "Loaded 214 models (773 tags) from library.json"
5. Go to Models page → verify installed models are listed
6. Click Scan button → verify it triggers catalog refresh + installed sync
7. From terminal: `ollama pull tinyllama` → click Scan → verify new model appears
8. From terminal: `ollama rm tinyllama` → click Scan → verify model removed from installed
9. Verify catalog shows 200+ models (from registry probe)
10. If Ollama is offline → verify status banner shows "Catalog degraded"
11. Delete `CortexMemory/ollama_catalog.json` → restart → verify fallback loads

---

### Task 11: Delete ref scripts after integration

**Files:**
- Delete: `.agents/ref/` directory (all reference scripts integrated)

**Interfaces:**
- Consumes: All valuable code from `.agents/ref/` has been integrated
- Produces: Clean workspace without stale reference files

- [ ] **Step 1: Verify all valuable code is integrated**

Confirm these are in the codebase:
- `scrape_library.py` logic → `backend/app/services/library_scraper.py`
- `build_catalog.py` registry probing → `backend/app/services/ollama_catalog.py`
- `library.json` → `backend/app/data/library.json`

- [ ] **Step 2: Delete the ref directory**

```bash
git rm -rf .agents/ref/
```

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "chore: remove .agents/ref after integrating all valuable code"
```
