# Download Manager Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the invisible download experience with a Free Download Manager-style docked panel — persistent bottom bar with per-download progress, speed, ETA, pause/resume/cancel controls, queue management, and history.

**Architecture:** Backend gets new endpoints (pause, resume, delete-local, reorder, bulk-cancel, clear-completed) and enhanced WebSocket payload. Frontend gets a new DownloadProvider (unified WebSocket state) and a DockedDownloadPanel pinned to bottom of Models page. Existing components (ModelCard, DownloadsView, InstalledView) updated to consume from provider.

**Tech Stack:** FastAPI, SQLAlchemy, Next.js 15, React 19, Tailwind CSS, existing WebSocket infrastructure

## Global Constraints

- Backend: FastAPI + sync SQLAlchemy 2.0. `response_model=` on all decorators. Specific routes before parameterized.
- Frontend: Next.js 15 App Router + React 19 + TypeScript + Tailwind CSS. Dark-only. Geist font.
- Auth: JWT in httpOnly cookie `cortex_access`. WS reads via `/api/v1/auth/ws-token`.
- WebSocket: Connects directly to port 8000 (not via Next.js proxy). Uses `useWebSocket` hook.
- File placement: Backend routers in `backend/app/api/v1/integration/`. Schemas in `backend/app/schemas/intelligence/`. Frontend features in `frontend/src/features/models/`. Shared UI in `frontend/src/shared/ui/`. Shared downloads in `frontend/src/shared/downloads/`.
- API prefix: All backend routes mounted under `/api/v1/`. Frontend `apiFetch` prepends this automatically.
- Tests: `tests/` at project root. SQLite in-memory. `make test` runs backend pytest.
- No database migration needed — all new endpoints use existing DownloadManager in-memory state.

---

## File Structure

### Backend
| File | Action | Responsibility |
|------|--------|---------------|
| `backend/app/schemas/intelligence/model.py` | Modify | Add 5 new response schemas |
| `backend/app/api/v1/integration/downloads.py` | Modify | Add 6 new endpoints |
| `backend/app/services/download/downloader.py` | Modify | Add `reorder()` and `clear_terminal()` methods |
| `backend/app/api/v1/interaction/ws_models.py` | Modify | Enhance WS payload with full download state |

### Frontend
| File | Action | Responsibility |
|------|--------|---------------|
| `frontend/src/shared/downloads/DownloadProvider.tsx` | Create | Unified download state + actions context |
| `frontend/src/shared/downloads/useDownloadContext.ts` | Create | Type-safe hook for consuming DownloadProvider |
| `frontend/src/features/models/components/DockedDownloadPanel.tsx` | Create | Persistent bottom download panel |
| `frontend/src/features/models/page.tsx` | Modify | Wrap in DownloadProvider, render panel, remove local WS |
| `frontend/src/features/models/components/ModelCard.tsx` | Modify | Read from provider, add pause/resume/delete |
| `frontend/src/features/models/components/ModelDetailModal.tsx` | Modify | Use provider download action |
| `frontend/src/features/models/components/BrowseView.tsx` | Modify | Remove downloadingModels prop |
| `frontend/src/features/models/components/DownloadsView.tsx` | Modify | Read from provider, add queue reorder + bulk cancel |
| `frontend/src/features/models/components/InstalledView.tsx` | Modify | Use provider deleteLocal |
| `frontend/src/features/integration/api.ts` | Modify | Add new download endpoint calls |

### Tests
| File | Action | Responsibility |
|------|--------|---------------|
| `tests/api/integration/test_download_endpoints.py` | Create | Test all new endpoints |
| `tests/services/test_download_manager.py` | Create | Test reorder() and clear_terminal() |
| `tests/frontend/downloads/DownloadProvider.test.tsx` | Create | Test provider state transitions |
| `tests/frontend/downloads/DockedDownloadPanel.test.tsx` | Create | Test panel rendering |

---

## Task 1: Backend — Response Schemas

**Files:**
- Modify: `backend/app/schemas/intelligence/model.py`
- Test: `tests/api/integration/test_schemas.py`

**Interfaces:**
- Consumes: existing `BaseModel` from pydantic (already imported)
- Produces: `PauseDownloadResponse`, `ResumeDownloadResponse`, `ReorderQueueResponse`, `BulkCancelResponse`, `ClearCompletedResponse` — used by Task 2 (endpoints)

- [ ] **Step 1: Add new response schemas**

Open `backend/app/schemas/intelligence/model.py`. Find the existing download-related schemas (after `InstalledModelsResponse`). Add:

```python
class PauseDownloadResponse(BaseModel):
    paused: bool
    model: str

class ResumeDownloadResponse(BaseModel):
    resumed: bool
    model: str

class ReorderQueueResponse(BaseModel):
    reordered: bool
    new_order: list[str]

class BulkCancelResponse(BaseModel):
    cancelled: int
    job_ids: list[str]

class ClearCompletedResponse(BaseModel):
    cleared: int
```

- [ ] **Step 2: Verify import works**

Run: `.venv/bin/python -c "from backend.app.schemas.intelligence.model import PauseDownloadResponse, ResumeDownloadResponse, ReorderQueueResponse, BulkCancelResponse, ClearCompletedResponse; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add backend/app/schemas/intelligence/model.py
git commit -m "feat: add download manager response schemas"
```

---

## Task 2: Backend — DownloadManager Methods

**Files:**
- Modify: `backend/app/services/download/downloader.py`
- Test: `tests/services/test_download_manager.py`

**Interfaces:**
- Consumes: existing `DownloadManager` class, `DownloadStatus` enum
- Produces: `DownloadManager.reorder(new_order: list[str]) -> list[str]`, `DownloadManager.clear_terminal() -> int` — used by Task 3 (endpoints)

- [ ] **Step 1: Write test for reorder()**

Create `tests/services/test_download_manager.py`:

```python
"""Tests for DownloadManager reorder and clear_terminal methods."""
import asyncio
import pytest
from backend.app.services.download.downloader import DownloadManager, DownloadStatus


@pytest.fixture
def dm():
    return DownloadManager(max_concurrent=1, max_retries=0)


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

    dm._records[r1.download_id].status = DownloadStatus.DOWNLOADING

    cleared = dm.clear_terminal()
    assert cleared == 1
    assert len(dm._records) == 1
    assert r1.download_id in dm._records
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/services/test_download_manager.py -v`
Expected: FAIL — `AttributeError: 'DownloadManager' object has no attribute 'reorder'`

- [ ] **Step 3: Implement reorder() and clear_terminal()**

Open `backend/app/services/download/downloader.py`. Add after the `clear_queue()` method (around line 445):

```python
    def reorder(self, new_order: list[str]) -> list[str]:
        """Reorder the internal queue by download_id order.

        Only existing QUEUED/PAUSED IDs are considered. IDs not in _records
        are silently ignored. Returns the new order of all remaining IDs.
        """
        # Collect IDs that are still in the queue (QUEUED or PAUSED)
        queued_ids = [
            r.download_id for r in self._records.values()
            if r.status in (DownloadStatus.QUEUED, DownloadStatus.PAUSED)
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
        to_remove = [
            did for did, rec in self._records.items()
            if rec.status in terminal_statuses
        ]
        for did in to_remove:
            del self._records[did]
        if to_remove:
            self._save_state()
        return len(to_remove)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/services/test_download_manager.py -v`
Expected: 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/download/downloader.py tests/services/test_download_manager.py
git commit -m "feat: add reorder and clear_terminal methods to DownloadManager"
```

---

## Task 3: Backend — Download Endpoints

**Files:**
- Modify: `backend/app/api/v1/integration/downloads.py`
- Test: `tests/api/integration/test_download_endpoints.py`

**Interfaces:**
- Consumes: `PauseDownloadResponse`, `ResumeDownloadResponse`, `ReorderQueueResponse`, `BulkCancelResponse`, `ClearCompletedResponse` (from Task 1). `download_manager.reorder()`, `download_manager.clear_terminal()` (from Task 2). `download_manager`, `model_downloader`, `DownloadStatus` (existing).
- Produces: 6 new API endpoints — consumed by frontend API client (Task 7)

**Important routing note:** Specific routes MUST be registered BEFORE parameterized routes. The new `/models/downloads/reorder`, `/models/downloads/bulk-cancel`, `/models/downloads/clear-completed` must appear before `@router.post("/models/{model_name}/download")` and other `/{model_name}` routes.

- [ ] **Step 1: Write test for pause endpoint**

Create `tests/api/integration/test_download_endpoints.py`:

```python
"""Tests for new download manager endpoints."""
import pytest
from unittest.mock import AsyncMock, patch
from backend.app.api.v1.integration.downloads import router
from backend.app.services.download.downloader import download_manager, DownloadStatus


@pytest.mark.asyncio
async def test_pause_download(async_client, auth_headers):
    """POST /models/{name}/pause pauses an active download."""
    # Enqueue a download
    record = await download_manager.enqueue("test-model:latest", "ollama")
    download_manager._records[record.download_id].status = DownloadStatus.DOWNLOADING

    resp = await async_client.post(
        "/api/v1/models/test-model:latest/pause",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["paused"] is True
    assert data["model"] == "test-model:latest"

    # Cleanup
    await download_manager.cancel(record.download_id)


@pytest.mark.asyncio
async def test_pause_download_not_found(async_client, auth_headers):
    """POST /models/{name}/pause returns 404 for non-existent download."""
    resp = await async_client.post(
        "/api/v1/models/nonexistent-model/pause",
        headers=auth_headers,
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_resume_download(async_client, auth_headers):
    """POST /models/{name}/resume resumes a paused download."""
    record = await download_manager.enqueue("resume-model:latest", "ollama")
    download_manager._records[record.download_id].status = DownloadStatus.PAUSED

    resp = await async_client.post(
        "/api/v1/models/resume-model:latest/resume",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["resumed"] is True
    assert data["model"] == "resume-model:latest"

    # Cleanup
    await download_manager.cancel(record.download_id)


@pytest.mark.asyncio
async def test_resume_download_not_paused(async_client, auth_headers):
    """POST /models/{name}/resume returns 400 for non-paused download."""
    record = await download_manager.enqueue("active-model:latest", "ollama")
    # Status is QUEUED, not PAUSED

    resp = await async_client.post(
        "/api/v1/models/active-model:latest/resume",
        headers=auth_headers,
    )
    assert resp.status_code == 400

    # Cleanup
    await download_manager.cancel(record.download_id)


@pytest.mark.asyncio
async def test_bulk_cancel(async_client, auth_headers):
    """POST /models/downloads/bulk-cancel cancels multiple downloads."""
    r1 = await download_manager.enqueue("bulk-a:latest", "ollama")
    r2 = await download_manager.enqueue("bulk-b:latest", "ollama")

    resp = await async_client.post(
        "/api/v1/models/downloads/bulk-cancel",
        json={"job_ids": [r1.download_id, r2.download_id]},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["cancelled"] == 2


@pytest.mark.asyncio
async def test_clear_completed(async_client, auth_headers):
    """POST /models/downloads/clear-completed clears terminal records."""
    r1 = await download_manager.enqueue("done-model:latest", "ollama")
    download_manager._records[r1.download_id].status = DownloadStatus.COMPLETED

    resp = await async_client.post(
        "/api/v1/models/downloads/clear-completed",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["cleared"] >= 1


@pytest.mark.asyncio
async def test_delete_local(async_client, auth_headers):
    """DELETE /models/{name}/local cancels download and removes from Ollama."""
    record = await download_manager.enqueue("delete-me:latest", "ollama")
    download_manager._records[record.download_id].status = DownloadStatus.QUEUED

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_client.delete.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        resp = await async_client.delete(
            "/api/v1/models/delete-me:latest/local",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "deleted"
        assert data["model"] == "delete-me:latest"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/api/integration/test_download_endpoints.py -v`
Expected: FAIL — 404 or 405 on the new endpoints (not yet registered)

- [ ] **Step 3: Implement the 6 new endpoints**

Open `backend/app/api/v1/integration/downloads.py`. Add the new imports at the top:

```python
from backend.app.schemas.intelligence.model import (
    CancelDownloadResponse,
    DeleteModelResponse,
    DownloadHistoryResponse,
    DownloadModelResponse,
    DownloadProgressResponse,
    DownloadQueueResponse,
    InstalledModelsResponse,
    SyncInstalledResponse,
    PauseDownloadResponse,          # NEW
    ResumeDownloadResponse,         # NEW
    ReorderQueueResponse,           # NEW
    BulkCancelResponse,             # NEW
    ClearCompletedResponse,         # NEW
)
```

Add `from pydantic import BaseModel` for the request body:

```python
from pydantic import BaseModel
```

Add request body model:

```python
class _ReorderRequest(BaseModel):
    job_ids: list[str]

class _BulkCancelRequest(BaseModel):
    job_ids: list[str]
```

**IMPORTANT:** Add the new endpoints BEFORE the parameterized routes. Insert them after the `list_installed_models` and `sync_installed_models` endpoints, but BEFORE `@router.get("/models/downloads/queue")`.

```python
@router.post("/models/{model_name}/pause", response_model=PauseDownloadResponse)
async def pause_download(
    model_name: str,
    current_user: User = Depends(get_current_user),
):
    """Pause an active download."""
    from backend.app.services.download.downloader import download_manager as dm, DownloadStatus

    for rec in dm._records.values():
        if rec.model_name == model_name and rec.status == DownloadStatus.DOWNLOADING:
            await dm.pause(rec.download_id)
            return {"paused": True, "model": model_name}
    raise HTTPException(status_code=404, detail=f"Download for {model_name} not found or not active")


@router.post("/models/{model_name}/resume", response_model=ResumeDownloadResponse)
async def resume_download(
    model_name: str,
    current_user: User = Depends(get_current_user),
):
    """Resume a paused download."""
    from backend.app.services.download.downloader import download_manager as dm, DownloadStatus

    for rec in dm._records.values():
        if rec.model_name == model_name and rec.status == DownloadStatus.PAUSED:
            await dm.resume(rec.download_id)
            return {"resumed": True, "model": model_name}
    raise HTTPException(status_code=400, detail=f"Download for {model_name} is not paused")


@router.delete("/models/{model_name}/local", response_model=DeleteModelResponse)
async def delete_model_local(
    model_name: str,
    current_user: User = Depends(get_current_user),
):
    """Cancel download if active, then remove model from Ollama."""
    from backend.app.services.download.downloader import download_manager as dm, DownloadStatus

    # Cancel if currently downloading/queued
    for rec in dm._records.values():
        if rec.model_name == model_name and rec.status in (
            DownloadStatus.QUEUED, DownloadStatus.DOWNLOADING, DownloadStatus.PAUSED
        ):
            await dm.cancel(rec.download_id)

    # Delete from Ollama
    import httpx
    from backend.app.core.config import settings

    async with httpx.AsyncClient(base_url=settings.OLLAMA_BASE_URL, timeout=30.0) as client:
        resp = await client.request("DELETE", "/api/delete", json={"name": model_name})
        resp.raise_for_status()
    return {"status": "deleted", "model": model_name}
```

Add these AFTER the existing `list_installed_models` and `sync_installed_models` but BEFORE `get_download_queue`:

```python
@router.post("/models/downloads/reorder", response_model=ReorderQueueResponse)
async def reorder_download_queue(
    request: _ReorderRequest,
    current_user: User = Depends(get_current_user),
):
    """Reorder the download queue by job_id order."""
    from backend.app.services.download.downloader import download_manager as dm

    new_order = dm.reorder(request.job_ids)
    return {"reordered": True, "new_order": new_order}


@router.post("/models/downloads/bulk-cancel", response_model=BulkCancelResponse)
async def bulk_cancel_downloads(
    request: _BulkCancelRequest,
    current_user: User = Depends(get_current_user),
):
    """Cancel multiple downloads at once."""
    from backend.app.services.download.downloader import download_manager as dm

    cancelled_ids = []
    for job_id in request.job_ids:
        try:
            await dm.cancel(job_id)
            cancelled_ids.append(job_id)
        except (KeyError, ValueError):
            pass
    return {"cancelled": len(cancelled_ids), "job_ids": cancelled_ids}


@router.post("/models/downloads/clear-completed", response_model=ClearCompletedResponse)
async def clear_completed_downloads(
    current_user: User = Depends(get_current_user),
):
    """Clear all completed/failed/cancelled downloads from state."""
    from backend.app.services.download.downloader import download_manager as dm

    cleared = dm.clear_terminal()
    return {"cleared": cleared}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/api/integration/test_download_endpoints.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/v1/integration/downloads.py tests/api/integration/test_download_endpoints.py
git commit -m "feat: add pause, resume, delete-local, reorder, bulk-cancel, clear-completed endpoints"
```

---

## Task 4: Backend — Enhanced WebSocket Payload

**Files:**
- Modify: `backend/app/api/v1/interaction/ws_models.py`
- Test: (manual — run backend, connect WS, verify payload shape)

**Interfaces:**
- Consumes: `download_manager._records` (existing DownloadRecord fields)
- Produces: Enhanced `model_progress` message with status, speed, eta, bytes, queue_position — consumed by DownloadProvider (Task 8)

- [ ] **Step 1: Enhance the WebSocket handler**

Open `backend/app/api/v1/interaction/ws_models.py`. Replace the `while True` loop body:

```python
"""WebSocket endpoint for real-time model download progress."""

from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from backend.app.core.security import verify_access_token
from backend.app.services.download.downloader import download_manager, DownloadStatus

router = APIRouter()


def _extract_ws_token(ws: WebSocket, token: str | None = None) -> str | None:
    """Extract JWT from query param, sec-websocket-protocol header, or cookie."""
    if token:
        return token
    protocols = ws.headers.get("sec-websocket-protocol", "")
    if protocols:
        return protocols.split(",")[0].strip() if "," in protocols else protocols.strip()
    return ws.cookies.get("cortex_access")


def _build_download_payload() -> dict:
    """Build the full model_progress payload from DownloadManager records."""
    models = []
    queued_positions: dict[str, int] = {}
    position_counter = 1
    for rec in download_manager._records.values():
        if rec.status == DownloadStatus.QUEUED:
            queued_positions[rec.download_id] = position_counter
            position_counter += 1

    for rec in download_manager._records.values():
        if rec.status in (
            DownloadStatus.DOWNLOADING,
            DownloadStatus.QUEUED,
            DownloadStatus.PAUSED,
        ):
            models.append({
                "name": rec.model_name,
                "progress": rec.progress,
                "status": rec.status.value,
                "speed_bytes_sec": rec.speed_bytes_sec,
                "eta_seconds": rec.eta_seconds,
                "bytes_downloaded": rec.bytes_downloaded,
                "total_bytes": rec.total_bytes,
                "queue_position": queued_positions.get(rec.download_id),
                "download_id": rec.download_id,
            })
        elif rec.status in (DownloadStatus.COMPLETED, DownloadStatus.FAILED, DownloadStatus.CANCELLED):
            # Send terminal events once (client can remove from active)
            models.append({
                "name": rec.model_name,
                "progress": rec.progress,
                "status": rec.status.value,
                "speed_bytes_sec": 0,
                "eta_seconds": None,
                "bytes_downloaded": rec.bytes_downloaded,
                "total_bytes": rec.total_bytes,
                "queue_position": None,
                "download_id": rec.download_id,
                "error": rec.error_message,
            })

    return {"type": "model_progress", "models": models}


@router.websocket("/ws/models")
async def model_download_progress_ws(ws: WebSocket, token: str = Query(None)):
    """Push download progress for all active model downloads every second."""
    token = _extract_ws_token(ws, token)
    if not token:
        await ws.close(code=4001, reason="Authentication required")
        return
    try:
        _user_id = verify_access_token(token)
    except Exception:
        await ws.close(code=4001, reason="Invalid token")
        return
    await ws.accept()
    try:
        while True:
            payload = _build_download_payload()

            if payload["models"]:
                await ws.send_text(json.dumps(payload))

            await asyncio.sleep(1)
    except WebSocketDisconnect:
        pass
    except Exception:
        try:
            await ws.close()
        except Exception:
            pass
```

- [ ] **Step 2: Verify import works**

Run: `.venv/bin/python -c "from backend.app.api.v1.interaction.ws_models import router; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add backend/app/api/v1/interaction/ws_models.py
git commit -m "feat: enhance WS payload with download status, speed, ETA, queue position"
```

---

## Task 5: Frontend — Download API Client Updates

**Files:**
- Modify: `frontend/src/features/integration/api.ts`
- Test: (TypeScript compile check)

**Interfaces:**
- Consumes: existing `apiFetch`, `DownloadJob`, `DownloadHistoryItem`
- Produces: `downloads.pause()`, `downloads.resume()`, `downloads.deleteLocal()`, `downloads.reorder()`, `downloads.bulkCancel()`, `downloads.clearCompleted()` — used by DownloadProvider (Task 8)

- [ ] **Step 1: Add new download API methods**

Open `frontend/src/features/integration/api.ts`. Add to the `downloads` object (after the existing `remove` method):

```typescript
  pause: (modelName: string) =>
    apiFetch<{ paused: boolean; model: string }>(
      `/models/${modelName}/pause`,
      { method: "POST" }
    ),

  resume: (modelName: string) =>
    apiFetch<{ resumed: boolean; model: string }>(
      `/models/${modelName}/resume`,
      { method: "POST" }
    ),

  deleteLocal: (modelName: string) =>
    apiFetch<{ status: string; model: string }>(
      `/models/${modelName}/local`,
      { method: "DELETE" }
    ),

  reorder: (jobIds: string[]) =>
    apiFetch<{ reordered: boolean; new_order: string[] }>(
      "/models/downloads/reorder",
      { method: "POST", body: { job_ids: jobIds } }
    ),

  bulkCancel: (jobIds: string[]) =>
    apiFetch<{ cancelled: number; job_ids: string[] }>(
      "/models/downloads/bulk-cancel",
      { method: "POST", body: { job_ids: jobIds } }
    ),

  clearCompleted: () =>
    apiFetch<{ cleared: number }>(
      "/models/downloads/clear-completed",
      { method: "POST" }
    ),
```

- [ ] **Step 2: TypeScript compile check**

Run: `cd frontend && npx tsc --noEmit`
Expected: No errors

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/integration/api.ts
git commit -m "feat: add pause, resume, deleteLocal, reorder, bulkCancel, clearCompleted API methods"
```

---

## Task 6: Frontend — DownloadProvider

**Files:**
- Create: `frontend/src/shared/downloads/DownloadProvider.tsx`
- Create: `frontend/src/shared/downloads/useDownloadContext.ts`
- Test: `tests/frontend/downloads/DownloadProvider.test.tsx`

**Interfaces:**
- Consumes: `useWebSocket` hook (from `@/shared/ws/useWebSocket`), `downloads` API client (from `@/features/integration/api`), `DownloadJob` type (from `@/features/integration/api`)
- Produces: `DownloadProvider` component, `useDownloadContext()` hook returning `DownloadState + DownloadActions` — consumed by all download UI components (Tasks 9-12)

- [ ] **Step 1: Create DownloadProvider**

Create `frontend/src/shared/downloads/DownloadProvider.tsx`:

```tsx
"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { useWebSocket } from "@/shared/ws/useWebSocket";
import { downloads } from "@/features/integration/api";
import type { DownloadJob, DownloadHistoryItem } from "@/features/integration/api";

// ── Types ──────────────────────────────────────────────────────────────────

export interface DownloadState {
  active: DownloadJob[];
  queued: DownloadJob[];
  history: DownloadHistoryItem[];
  connected: boolean;
}

export interface DownloadActions {
  download: (modelId: string, variant?: string) => Promise<void>;
  pause: (modelId: string) => Promise<void>;
  resume: (modelId: string) => Promise<void>;
  cancel: (modelId: string) => Promise<void>;
  deleteLocal: (modelId: string) => Promise<void>;
  retry: (modelId: string) => Promise<void>;
  bulkCancel: (jobIds: string[]) => Promise<void>;
  clearCompleted: () => Promise<void>;
  refresh: () => Promise<void>;
}

interface DownloadContextType {
  state: DownloadState;
  actions: DownloadActions;
}

// ── Context ────────────────────────────────────────────────────────────────

const DownloadContext = createContext<DownloadContextType | null>(null);

export function useDownloadContext(): DownloadContextType {
  const ctx = useContext(DownloadContext);
  if (!ctx) throw new Error("useDownloadContext must be used within DownloadProvider");
  return ctx;
}

// ── Provider ───────────────────────────────────────────────────────────────

export function DownloadProvider({ children }: { children: ReactNode }) {
  const [active, setActive] = useState<DownloadJob[]>([]);
  const [queued, setQueued] = useState<DownloadJob[]>([]);
  const [history, setHistory] = useState<DownloadHistoryItem[]>([]);

  // Refs for stable access in callbacks
  const activeRef = useRef(active);
  activeRef.current = active;

  // ── Load queue from REST (initial + fallback) ────────────────────────

  const loadQueue = useCallback(async () => {
    try {
      const res = await downloads.queue();
      setActive(res.active);
      setQueued(res.queued);
    } catch {
      // ignore
    }
  }, []);

  const loadHistory = useCallback(async () => {
    try {
      const res = await downloads.history(30);
      setHistory(res.history);
    } catch {
      // ignore
    }
  }, []);

  // Initial load
  useEffect(() => {
    loadQueue();
    loadHistory();
  }, [loadQueue, loadHistory]);

  // ── WebSocket for real-time progress ─────────────────────────────────

  const handleWSMessage = useCallback((data: Record<string, unknown>) => {
    if (data.type !== "model_progress" || !Array.isArray(data.models)) return;

    const models = data.models as Array<{
      name: string;
      progress: number;
      status: string;
      speed_bytes_sec: number;
      eta_seconds: number | null;
      bytes_downloaded: number;
      total_bytes: number;
      queue_position: number | null;
      download_id: string;
      error?: string;
    }>;

    const newActive: DownloadJob[] = [];
    const newQueued: DownloadJob[] = [];
    const terminalStatuses = new Set(["completed", "failed", "cancelled"]);

    for (const m of models) {
      const job: DownloadJob = {
        job_id: m.download_id,
        model_id: m.name,
        status: m.status,
        progress: m.progress,
        speed_bytes_sec: m.speed_bytes_sec,
        downloaded_bytes: m.bytes_downloaded,
        total_bytes: m.total_bytes,
        eta_seconds: m.eta_seconds,
        queue_position: m.queue_position,
        error: m.error ?? null,
      };

      if (m.status === "downloading" || m.status === "paused") {
        newActive.push(job);
      } else if (m.status === "queued") {
        newQueued.push(job);
      }
      // Terminal statuses are handled by loadHistory below
    }

    setActive(newActive);
    setQueued(newQueued);

    // If any terminal events, refresh history
    if (models.some(m => terminalStatuses.has(m.status))) {
      loadHistory();
    }
  }, [loadHistory]);

  const { status: wsStatus } = useWebSocket({
    path: "/api/v1/ws/models",
    enabled: true,
    onMessage: handleWSMessage,
  });

  // ── Actions ──────────────────────────────────────────────────────────

  const download = useCallback(async (modelId: string, variant?: string) => {
    // Optimistically add to active
    setActive(prev => {
      if (prev.some(j => j.model_id === modelId)) return prev;
      return [...prev, {
        job_id: `optimistic-${Date.now()}`,
        model_id: modelId,
        status: "downloading",
        progress: 0,
        speed_bytes_sec: null,
        downloaded_bytes: 0,
        total_bytes: 0,
        eta_seconds: null,
        queue_position: null,
        error: null,
      }];
    });

    try {
      await downloads.download(modelId, variant);
    } catch {
      // Remove optimistic entry on failure
      setActive(prev => prev.filter(j => j.model_id !== modelId));
    }
  }, []);

  const pause = useCallback(async (modelId: string) => {
    try {
      await downloads.pause(modelId);
      // Optimistic: mark as paused locally (WS will confirm)
      setActive(prev => prev.map(j =>
        j.model_id === modelId ? { ...j, status: "paused" } : j
      ));
    } catch {
      // ignore
    }
  }, []);

  const resume = useCallback(async (modelId: string) => {
    try {
      await downloads.resume(modelId);
      // Optimistic: move from active to queued
      setActive(prev => prev.filter(j => j.model_id !== modelId));
      setQueued(prev => [...prev, {
        job_id: `resumed-${Date.now()}`,
        model_id: modelId,
        status: "queued",
        progress: 0,
        speed_bytes_sec: null,
        downloaded_bytes: 0,
        total_bytes: 0,
        eta_seconds: null,
        queue_position: null,
        error: null,
      }]);
    } catch {
      // ignore
    }
  }, []);

  const cancel = useCallback(async (modelId: string) => {
    try {
      await downloads.cancel(modelId);
    } catch {
      // ignore
    }
    // Remove from active and queued
    setActive(prev => prev.filter(j => j.model_id !== modelId));
    setQueued(prev => prev.filter(j => j.model_id !== modelId));
    // Refresh history to show cancelled entry
    loadHistory();
  }, [loadHistory]);

  const deleteLocal = useCallback(async (modelId: string) => {
    // Cancel if downloading/queued
    setActive(prev => prev.filter(j => j.model_id !== modelId));
    setQueued(prev => prev.filter(j => j.model_id !== modelId));

    try {
      await downloads.deleteLocal(modelId);
    } catch {
      // ignore
    }
    loadHistory();
  }, [loadHistory]);

  const retry = useCallback(async (modelId: string) => {
    try {
      await downloads.download(modelId);
      loadQueue();
    } catch {
      // ignore
    }
  }, [loadQueue]);

  const bulkCancel = useCallback(async (jobIds: string[]) => {
    try {
      await downloads.bulkCancel(jobIds);
    } catch {
      // ignore
    }
    setActive(prev => prev.filter(j => !jobIds.includes(j.job_id)));
    setQueued(prev => prev.filter(j => !jobIds.includes(j.job_id)));
    loadHistory();
  }, [loadHistory]);

  const clearCompleted = useCallback(async () => {
    try {
      await downloads.clearCompleted();
    } catch {
      // ignore
    }
    setHistory([]);
  }, []);

  const refresh = useCallback(async () => {
    await Promise.all([loadQueue(), loadHistory()]);
  }, [loadQueue, loadHistory]);

  // ── Value ────────────────────────────────────────────────────────────

  const state: DownloadState = useMemo(() => ({
    active,
    queued,
    history,
    connected: wsStatus === "connected",
  }), [active, queued, history, wsStatus]);

  const actions: DownloadActions = useMemo(() => ({
    download,
    pause,
    resume,
    cancel,
    deleteLocal,
    retry,
    bulkCancel,
    clearCompleted,
    refresh,
  }), [download, pause, resume, cancel, deleteLocal, retry, bulkCancel, clearCompleted, refresh]);

  const value: DownloadContextType = useMemo(() => ({
    state,
    actions,
  }), [state, actions]);

  return (
    <DownloadContext.Provider value={value}>
      {children}
    </DownloadContext.Provider>
  );
}
```

- [ ] **Step 2: Create useDownloadContext hook file**

Create `frontend/src/shared/downloads/useDownloadContext.ts`:

```tsx
export { useDownloadContext } from "./DownloadProvider";
export type { DownloadState, DownloadActions } from "./DownloadProvider";
```

- [ ] **Step 3: TypeScript compile check**

Run: `cd frontend && npx tsc --noEmit`
Expected: No errors

- [ ] **Step 4: Commit**

```bash
git add frontend/src/shared/downloads/
git commit -m "feat: add DownloadProvider — unified download state + actions context"
```

---

## Task 7: Frontend — DockedDownloadPanel

**Files:**
- Create: `frontend/src/features/models/components/DockedDownloadPanel.tsx`
- Test: `tests/frontend/downloads/DockedDownloadPanel.test.tsx`

**Interfaces:**
- Consumes: `useDownloadContext()` (from Task 6), `formatBytes`, `formatSpeed`, `formatEta` (from `../api`)
- Produces: `<DockedDownloadPanel />` component — rendered by Models page (Task 9)

- [ ] **Step 1: Create DockedDownloadPanel**

Create `frontend/src/features/models/components/DockedDownloadPanel.tsx`:

```tsx
"use client";

import { useState } from "react";
import { useDownloadContext } from "@/shared/downloads/DownloadProvider";
import { formatBytes, formatSpeed, formatEta } from "../api";
import { Button } from "@/shared/ui/Button";
import { StatusDot } from "@/shared/ui/StatusDot";

export function DockedDownloadPanel() {
  const { state, actions } = useDownloadContext();
  const { active, queued, history, connected } = state;
  const [expanded, setExpanded] = useState(true);
  const [showHistory, setShowHistory] = useState(false);

  // Hide completely when no downloads at all
  const totalItems = active.length + queued.length;
  if (totalItems === 0 && !showHistory) {
    return null;
  }

  const totalActive = active.length;
  const totalQueued = queued.length;
  const overallProgress = active.length > 0
    ? Math.round(active.reduce((sum, j) => sum + j.progress, 0) / active.length * 100)
    : 0;
  const topSpeed = active.reduce((max, j) => Math.max(max, j.speed_bytes_sec ?? 0), 0);

  return (
    <div className="fixed bottom-0 left-0 right-0 z-40 border-t border-border-subtle bg-bg-base/95 backdrop-blur-sm">
      {/* Collapsed bar */}
      {!expanded && (
        <button
          onClick={() => setExpanded(true)}
          className="w-full flex items-center gap-3 px-4 py-2.5 text-sm hover:bg-bg-surface/50 transition-colors"
          aria-label="Expand download panel"
        >
          <div className="h-2 w-2 rounded-full bg-accent animate-pulse" />
          <span className="text-text-primary font-medium">
            Downloads
          </span>
          {totalActive > 0 && (
            <span className="text-text-muted">
              ({totalActive} active{totalQueued > 0 ? `, ${totalQueued} queued` : ""})
            </span>
          )}
          <span className="ml-auto text-text-muted font-mono text-xs">
            {overallProgress}%{topSpeed > 0 && ` · ${formatSpeed(topSpeed)}`}
          </span>
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-text-muted">
            <path d="M2 8l4-4 4 4" />
          </svg>
        </button>
      )}

      {/* Expanded panel */}
      {expanded && (
        <div className="max-h-[40vh] overflow-hidden flex flex-col">
          {/* Header */}
          <div className="flex items-center gap-3 px-4 py-2.5 border-b border-border-subtle">
            <button
              onClick={() => setExpanded(false)}
              className="text-text-muted hover:text-text-primary transition-colors"
              aria-label="Collapse download panel"
            >
              <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M2 4l4 4 4-4" />
              </svg>
            </button>
            <span className="text-sm font-medium text-text-primary">
              Downloads
            </span>
            {totalActive > 0 && (
              <span className="text-xs text-text-muted">
                {totalActive} active{totalQueued > 0 ? `, ${totalQueued} queued` : ""}
              </span>
            )}
            <div className="ml-auto flex items-center gap-2">
              {!connected && (
                <StatusDot color="danger" />
              )}
              <button
                onClick={() => setShowHistory(!showHistory)}
                className="text-xs text-text-muted hover:text-text-primary transition-colors"
              >
                History
              </button>
            </div>
          </div>

          {/* Download rows */}
          <div className="overflow-y-auto flex-1">
            {/* Active downloads */}
            {active.map(job => (
              <div key={job.job_id} className="px-4 py-3 border-b border-border-subtle last:border-0">
                <div className="flex items-center gap-3 mb-1.5">
                  <StatusDot color={job.status === "paused" ? "warning" : "accent"} pulse={job.status === "downloading"} />
                  <span className="text-sm text-text-primary font-mono flex-1 truncate">
                    {job.model_id}
                  </span>
                  <span className="text-xs text-text-muted font-mono">
                    {Math.round(job.progress * 100)}%
                  </span>
                  <span className="text-xs text-text-muted">
                    {formatSpeed(job.speed_bytes_sec ?? 0)}
                  </span>
                  <span className="text-xs text-text-muted w-16 text-right">
                    {formatEta(job.eta_seconds)}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="flex-1 h-1.5 rounded-full bg-bg-surface overflow-hidden">
                    <div
                      className="h-full rounded-full bg-accent transition-[width] duration-300"
                      style={{ width: `${Math.round(job.progress * 100)}%` }}
                    />
                  </div>
                  <div className="flex items-center gap-1">
                    {job.status === "downloading" ? (
                      <button
                        onClick={() => actions.pause(job.model_id)}
                        className="p-1 rounded text-text-muted hover:text-text-primary hover:bg-bg-surface transition-colors"
                        aria-label={`Pause download of ${job.model_id}`}
                        title="Pause"
                      >
                        <svg width="14" height="14" viewBox="0 0 14 14" fill="currentColor">
                          <rect x="3" y="2" width="3" height="10" rx="0.5" />
                          <rect x="8" y="2" width="3" height="10" rx="0.5" />
                        </svg>
                      </button>
                    ) : job.status === "paused" ? (
                      <button
                        onClick={() => actions.resume(job.model_id)}
                        className="p-1 rounded text-text-muted hover:text-accent hover:bg-bg-surface transition-colors"
                        aria-label={`Resume download of ${job.model_id}`}
                        title="Resume"
                      >
                        <svg width="14" height="14" viewBox="0 0 14 14" fill="currentColor">
                          <path d="M3 1.5v11l9-5.5z" />
                        </svg>
                      </button>
                    ) : null}
                    <button
                      onClick={() => actions.cancel(job.model_id)}
                      className="p-1 rounded text-text-muted hover:text-danger hover:bg-bg-surface transition-colors"
                      aria-label={`Cancel download of ${job.model_id}`}
                      title="Cancel"
                    >
                      <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5">
                        <path d="M3 3l8 8M11 3l-8 8" />
                      </svg>
                    </button>
                  </div>
                </div>
                {/* Show bytes downloaded */}
                <div className="mt-1 text-[0.625rem] text-text-muted font-mono">
                  {formatBytes(job.downloaded_bytes)} / {formatBytes(job.total_bytes)}
                </div>
              </div>
            ))}

            {/* Queued */}
            {queued.length > 0 && (
              <div className="px-4 py-2 border-b border-border-subtle">
                <span className="text-xs text-text-muted font-medium">Queued</span>
              </div>
            )}
            {queued.map(job => (
              <div key={job.job_id} className="px-4 py-2.5 flex items-center gap-3 border-b border-border-subtle last:border-0">
                <span className="text-xs text-text-muted font-mono w-6 text-center">
                  #{job.queue_position ?? "?"}
                </span>
                <span className="text-sm text-text-primary font-mono flex-1 truncate">
                  {job.model_id}
                </span>
                <button
                  onClick={() => actions.cancel(job.model_id)}
                  className="p-1 rounded text-text-muted hover:text-danger hover:bg-bg-surface transition-colors"
                  aria-label={`Cancel queued download of ${job.model_id}`}
                  title="Cancel"
                >
                  <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5">
                    <path d="M3 3l8 8M11 3l-8 8" />
                  </svg>
                </button>
              </div>
            ))}

            {/* History drawer */}
            {showHistory && history.length > 0 && (
              <div className="border-t border-border-subtle">
                <div className="px-4 py-2 flex items-center justify-between">
                  <span className="text-xs text-text-muted font-medium">History</span>
                  <button
                    onClick={() => actions.clearCompleted()}
                    className="text-xs text-text-muted hover:text-danger transition-colors"
                  >
                    Clear all
                  </button>
                </div>
                {history.map(item => (
                  <div key={item.job_id} className="px-4 py-2 flex items-center gap-3 text-sm border-b border-border-subtle last:border-0">
                    <StatusDot
                      color={item.status === "completed" ? "success" : item.status === "failed" ? "danger" : "default"}
                    />
                    <span className="text-text-primary font-mono flex-1 truncate">
                      {item.model_id}
                    </span>
                    <span className="text-xs text-text-muted">
                      {formatBytes(item.total_bytes)}
                    </span>
                    {item.status === "failed" && item.error && (
                      <span className="text-xs text-danger max-w-[150px] truncate">
                        {item.error}
                      </span>
                    )}
                    {item.status === "failed" && (
                      <button
                        onClick={() => actions.retry(item.model_id)}
                        className="text-xs text-accent hover:text-accent/80 transition-colors"
                      >
                        Retry
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: TypeScript compile check**

Run: `cd frontend && npx tsc --noEmit`
Expected: No errors

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/models/components/DockedDownloadPanel.tsx
git commit -m "feat: add DockedDownloadPanel — persistent bottom download panel"
```

---

## Task 8: Frontend — Wire Models Page to DownloadProvider

**Files:**
- Modify: `frontend/src/features/models/page.tsx`
- Modify: `frontend/src/features/models/components/ModelCard.tsx`
- Modify: `frontend/src/features/models/components/BrowseView.tsx`

**Interfaces:**
- Consumes: `DownloadProvider`, `useDownloadContext` (from Task 6), `DockedDownloadPanel` (from Task 7)
- Produces: Models page wired to provider, ModelCard reading from context, BrowseView without downloadingModels prop

- [ ] **Step 1: Update Models page**

Open `frontend/src/features/models/page.tsx`. Make these changes:

1. Remove `import { useWebSocket } from "@/shared/ws/useWebSocket";`
2. Add imports:
```typescript
import { DownloadProvider } from "@/shared/downloads/DownloadProvider";
import { DockedDownloadPanel } from "./components/DockedDownloadPanel";
```

3. Remove the `downloadingModels` state and `handleDownloadProgress` callback and `useWebSocket` call (lines 43, 71-92)

4. Remove `handleDownload` and `handleCancelDownload` functions (lines 96-126)

5. Remove `downloadingModels` and `onCancelDownload` props from `<BrowseView>`:

```tsx
{activeTab === "browse" && (
  <BrowseView
    hardware={hardware}
    onDownload={handleDownloadFromBrowse}
    onViewDetail={handleViewDetail}
    compareSelectedIds={compareSelectedIds}
    onToggleCompare={handleToggleCompare}
    compareDisabled={compareDisabled}
  />
)}
```

6. Wrap the tab content and panel in `<DownloadProvider>`:

```tsx
<DownloadProvider>
  {/* Tab content */}
  <div role="tabpanel" aria-label={`${activeTab} tab`}>
    {/* ... existing tab content ... */}
  </div>

  {/* Docked download panel */}
  <DockedDownloadPanel />
</DownloadProvider>
```

7. Update `handleDownloadFromCompare` to use download context:

```typescript
// Remove handleDownloadFromCompare since CompareView gets download action from provider
```

- [ ] **Step 2: Update ModelCard to read from context**

Open `frontend/src/features/models/components/ModelCard.tsx`. Changes:

1. Add import:
```typescript
import { useDownloadContext } from "@/shared/downloads/DownloadProvider";
```

2. Remove `downloading`, `downloadProgress`, `onCancelDownload` from props

3. Inside the component, add:
```typescript
const { state, actions } = useDownloadContext();
const downloadJob = state.active.find(j => j.model_id === model.model_id)
  ?? state.queued.find(j => j.model_id === model.model_id);
const isDownloading = !!downloadJob;
const isPaused = downloadJob?.status === "paused";
```

4. Replace the downloading state section (lines 108-126) to show speed + pause/resume:

```tsx
{isDownloading && downloadJob && (
  <div className="space-y-1.5">
    <div className="h-2 rounded-full bg-bg-surface overflow-hidden">
      <div
        className={`h-full rounded-full transition-[width] duration-300 ${
          isPaused ? "bg-warning" : "bg-accent"
        }`}
        style={{ width: `${Math.round(downloadJob.progress * 100)}%` }}
        role="progressbar"
        aria-valuenow={Math.round(downloadJob.progress * 100)}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`Downloading ${model.display_name}: ${Math.round(downloadJob.progress * 100)}%`}
      />
    </div>
    <div className="flex items-center gap-2 text-xs text-text-muted">
      <span>{Math.round(downloadJob.progress * 100)}%</span>
      {(downloadJob.speed_bytes_sec ?? 0) > 0 && (
        <>
          <span>·</span>
          <span>{formatSpeed(downloadJob.speed_bytes_sec ?? 0)}</span>
        </>
      )}
      {downloadJob.eta_seconds != null && downloadJob.eta_seconds > 0 && (
        <>
          <span>·</span>
          <span>{formatEta(downloadJob.eta_seconds)}</span>
        </>
      )}
    </div>
  </div>
)}
```

5. Replace the actions section (lines 128-155):

```tsx
<div className="flex items-center gap-2 mt-auto pt-1">
  {isDownloading ? (
    <>
      {downloadJob?.status === "downloading" ? (
        <Button
          size="sm"
          variant="ghost"
          onClick={() => actions.pause(model.model_id)}
          aria-label={`Pause download of ${model.display_name}`}
        >
          Pause
        </Button>
      ) : downloadJob?.status === "paused" ? (
        <Button
          size="sm"
          variant="ghost"
          onClick={() => actions.resume(model.model_id)}
          aria-label={`Resume download of ${model.display_name}`}
        >
          Resume
        </Button>
      ) : null}
      <Button
        size="sm"
        variant="ghost"
        onClick={() => actions.cancel(model.model_id)}
        aria-label={`Cancel download of ${model.display_name}`}
      >
        Cancel
      </Button>
    </>
  ) : model.downloaded ? (
    <>
      <Button
        size="sm"
        variant="ghost"
        onClick={() => onViewDetail(model.model_id)}
      >
        View Details
      </Button>
      <Button
        size="sm"
        variant="ghost"
        className="text-danger hover:text-danger"
        onClick={() => {
          if (window.confirm(`Delete ${model.display_name}? This will remove it from Ollama.`)) {
            actions.deleteLocal(model.model_id);
          }
        }}
        aria-label={`Delete ${model.display_name}`}
      >
        Delete
      </Button>
    </>
  ) : (
    <Button
      size="sm"
      onClick={() => onDownload(model.model_id)}
      aria-label={`Download ${model.display_name}`}
    >
      Download
    </Button>
  )}

  <label className="flex items-center gap-1.5 ml-auto cursor-pointer">
    <input
      type="checkbox"
      checked={compareSelected}
      onChange={() => onToggleCompare(model.model_id)}
      disabled={!compareSelected && compareDisabled}
      className="h-3.5 w-3.5 rounded border-border-default bg-bg-surface text-accent accent-accent"
      aria-label={`Add ${model.display_name} to comparison`}
    />
    <span className="text-xs text-text-muted">Compare</span>
  </label>
</div>
```

- [ ] **Step 3: Update BrowseView to remove downloadingModels prop**

Open `frontend/src/features/models/components/BrowseView.tsx`. Changes:

1. Remove `downloadingModels` and `onCancelDownload` from `BrowseViewProps` interface
2. Remove those props from the destructured parameters
3. Remove passing `downloading` and `downloadProgress` to `<ModelCard>` — ModelCard now reads from context:

```tsx
<ModelCard
  key={model.model_id}
  model={model}
  onDownload={onDownload}
  onViewDetail={onViewDetail}
  compareSelected={compareSelectedIds.includes(model.model_id)}
  onToggleCompare={onToggleCompare}
  compareDisabled={compareDisabled}
/>
```

- [ ] **Step 4: TypeScript compile check**

Run: `cd frontend && npx tsc --noEmit`
Expected: No errors

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/models/page.tsx frontend/src/features/models/components/ModelCard.tsx frontend/src/features/models/components/BrowseView.tsx
git commit -m "feat: wire Models page to DownloadProvider, update ModelCard with pause/resume/delete"
```

---

## Task 9: Frontend — Update ModelDetailModal

**Files:**
- Modify: `frontend/src/features/models/components/ModelDetailModal.tsx`

**Interfaces:**
- Consumes: `useDownloadContext()` (from Task 6)
- Produces: Modal uses provider download action instead of direct API call

- [ ] **Step 1: Read current ModelDetailModal**

Read `frontend/src/features/models/components/ModelDetailModal.tsx` to find the download button handler.

- [ ] **Step 2: Update download handler**

Add import:
```typescript
import { useDownloadContext } from "@/shared/downloads/DownloadProvider";
```

Inside the component, add:
```typescript
const { actions } = useDownloadContext();
```

Find the download button's onClick handler (it currently calls `downloads.download()` directly). Replace with:
```typescript
async function handleDownload() {
  setDownloading(true);
  try {
    await actions.download(detail.name, selectedVariantId);
    onDownload(detail.name);
  } catch {
    // ignore
  } finally {
    setDownloading(false);
  }
}
```

Remove the direct `downloads` import if it's no longer used elsewhere in the file.

- [ ] **Step 3: TypeScript compile check**

Run: `cd frontend && npx tsc --noEmit`
Expected: No errors

- [ ] **Step 4: Commit**

```bash
git add frontend/src/features/models/components/ModelDetailModal.tsx
git commit -m "feat: ModelDetailModal uses DownloadProvider instead of direct API call"
```

---

## Task 10: Frontend — Update DownloadsView

**Files:**
- Modify: `frontend/src/features/models/components/DownloadsView.tsx`

**Interfaces:**
- Consumes: `useDownloadContext()` (from Task 6)
- Produces: DownloadsView reads from provider instead of polling REST

- [ ] **Step 1: Rewrite DownloadsView**

Open `frontend/src/features/models/components/DownloadsView.tsx`. Rewrite to use provider:

```tsx
"use client";

import { useState } from "react";
import { useDownloadContext } from "@/shared/downloads/DownloadProvider";
import { downloads } from "../api";
import { formatBytes, formatSpeed, formatEta } from "../api";
import { Card } from "@/shared/ui/Card";
import { Button } from "@/shared/ui/Button";
import { EmptyState } from "@/shared/ui/EmptyState";
import { StatusDot } from "@/shared/ui/StatusDot";

export function DownloadsView() {
  const { state, actions } = useDownloadContext();
  const { active, queued, history } = state;
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  const toggleSelect = (jobId: string) => {
    setSelectedIds(prev => {
      const next = new Set(prev);
      if (next.has(jobId)) next.delete(jobId);
      else next.add(jobId);
      return next;
    });
  };

  const handleBulkCancel = () => {
    actions.bulkCancel(Array.from(selectedIds));
    setSelectedIds(new Set());
  };

  const totalItems = active.length + queued.length + history.length;

  if (totalItems === 0) {
    return (
      <EmptyState
        title="No downloads yet"
        description="Browse models to find one to download"
      />
    );
  }

  return (
    <div className="space-y-4">
      {/* Active downloads */}
      {active.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-text-primary">
              Active ({active.length})
            </h3>
            {selectedIds.size > 0 && (
              <Button size="sm" variant="ghost" onClick={handleBulkCancel} className="text-danger">
                Cancel {selectedIds.size} selected
              </Button>
            )}
          </div>
          <div className="space-y-2">
            {active.map(job => {
              const percent = Math.round(job.progress * 100);
              return (
                <Card key={job.job_id} className="p-3">
                  <div className="flex items-center gap-3 mb-2">
                    <input
                      type="checkbox"
                      checked={selectedIds.has(job.job_id)}
                      onChange={() => toggleSelect(job.job_id)}
                      className="h-3.5 w-3.5 rounded border-border-default bg-bg-surface accent-accent"
                    />
                    <StatusDot color={job.status === "paused" ? "warning" : "accent"} pulse={job.status === "downloading"} />
                    <span className="text-sm text-text-primary font-mono flex-1 truncate">
                      {job.model_id}
                    </span>
                    <span className="text-xs text-text-muted font-mono">{percent}%</span>
                  </div>
                  <div className="h-2 rounded-full bg-bg-surface overflow-hidden mb-2">
                    <div
                      className={`h-full rounded-full transition-[width] duration-300 ${
                        job.status === "paused" ? "bg-warning" : "bg-accent"
                      }`}
                      style={{ width: `${percent}%` }}
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-text-muted">
                      {formatSpeed(job.speed_bytes_sec ?? 0)} · {formatEta(job.eta_seconds)}
                    </span>
                    <div className="flex items-center gap-1">
                      {job.status === "downloading" ? (
                        <Button size="sm" variant="ghost" onClick={() => actions.pause(job.model_id)}>
                          Pause
                        </Button>
                      ) : job.status === "paused" ? (
                        <Button size="sm" variant="ghost" onClick={() => actions.resume(job.model_id)}>
                          Resume
                        </Button>
                      ) : null}
                      <Button size="sm" variant="ghost" onClick={() => actions.cancel(job.model_id)}>
                        Cancel
                      </Button>
                    </div>
                  </div>
                </Card>
              );
            })}
          </div>
        </div>
      )}

      {/* Queued */}
      {queued.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-text-primary mb-3">
            Queued ({queued.length})
          </h3>
          <div className="space-y-1">
            {queued.map(job => (
              <Card key={job.job_id} className="p-3 flex items-center gap-3">
                <input
                  type="checkbox"
                  checked={selectedIds.has(job.job_id)}
                  onChange={() => toggleSelect(job.job_id)}
                  className="h-3.5 w-3.5 rounded border-border-default bg-bg-surface accent-accent"
                />
                <StatusDot color="warning" />
                <span className="text-sm text-text-primary font-mono flex-1 truncate">
                  {job.model_id}
                </span>
                <span className="text-xs text-text-muted">
                  Position: #{job.queue_position ?? "?"}
                </span>
                <Button size="sm" variant="ghost" onClick={() => actions.cancel(job.model_id)}>
                  Cancel
                </Button>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* History */}
      {history.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-text-primary">
              History ({history.length})
            </h3>
            <Button size="sm" variant="ghost" onClick={actions.clearCompleted}>
              Clear all
            </Button>
          </div>
          <div className="space-y-1">
            {history.map(item => (
              <div key={item.job_id} className="flex items-center gap-3 px-3 py-2 text-sm rounded-md hover:bg-bg-surface/50">
                <StatusDot
                  color={item.status === "completed" ? "success" : item.status === "failed" ? "danger" : "default"}
                />
                <span className="text-text-primary font-mono flex-1 truncate">
                  {item.model_id}
                </span>
                <span className="text-xs text-text-muted">
                  {formatBytes(item.total_bytes)}
                </span>
                {item.status === "failed" && item.error && (
                  <span className="text-xs text-danger max-w-[200px] truncate">
                    {item.error}
                  </span>
                )}
                {item.status === "failed" && (
                  <Button size="sm" variant="ghost" onClick={() => actions.retry(item.model_id)}>
                    Retry
                  </Button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: TypeScript compile check**

Run: `cd frontend && npx tsc --noEmit`
Expected: No errors

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/models/components/DownloadsView.tsx
git commit -m "feat: DownloadsView reads from DownloadProvider, add bulk cancel + clear completed"
```

---

## Task 11: Frontend — Update InstalledView

**Files:**
- Modify: `frontend/src/features/models/components/InstalledView.tsx`

**Interfaces:**
- Consumes: `useDownloadContext()` (from Task 6)
- Produces: InstalledView uses provider deleteLocal

- [ ] **Step 1: Update InstalledView delete handler**

Open `frontend/src/features/models/components/InstalledView.tsx`. Changes:

1. Add import:
```typescript
import { useDownloadContext } from "@/shared/downloads/DownloadProvider";
```

2. Inside the component, add:
```typescript
const { actions } = useDownloadContext();
```

3. Update `handleDelete` to use provider:
```typescript
const handleDelete = async () => {
  if (!deleteTarget) return;
  setDeleting(true);
  try {
    await actions.deleteLocal(deleteTarget.model_id);
    setModels(prev => prev.filter(m => m.model_id !== deleteTarget.model_id));
    if (defaultModelId === deleteTarget.model_id) {
      setDefaultModelId(null);
      localStorage.removeItem("cortex_default_model");
    }
    setDeleteTarget(null);
  } catch {
    // ignore
  } finally {
    setDeleting(false);
  }
};
```

- [ ] **Step 2: TypeScript compile check**

Run: `cd frontend && npx tsc --noEmit`
Expected: No errors

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/models/components/InstalledView.tsx
git commit -m "feat: InstalledView uses DownloadProvider for delete"
```

---

## Task 12: Final Verification

**Files:**
- All modified files

**Interfaces:**
- Consumes: All previous tasks
- Produces: Clean build, all tests passing

- [ ] **Step 1: Run backend tests**

Run: `.venv/bin/python -m pytest tests/ -x -q`
Expected: All tests pass

- [ ] **Step 2: Run frontend TypeScript check**

Run: `cd frontend && npx tsc --noEmit`
Expected: No errors

- [ ] **Step 3: Run frontend build**

Run: `cd frontend && npm run build`
Expected: Build succeeds

- [ ] **Step 4: Run lint**

Run: `make lint`
Expected: Clean

- [ ] **Step 5: Final commit**

```bash
git add -A
git commit -m "chore: final verification — download manager redesign complete"
```
