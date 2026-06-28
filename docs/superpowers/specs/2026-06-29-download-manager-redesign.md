# Download Manager Redesign — Full Docked Panel

> **For agentic workers:** This spec defines a complete redesign of the model download manager UI. The current system has capable backend logic (pause/resume/cancel exist in DownloadManager) but no API endpoints expose them, and the frontend shows almost no feedback during downloads.

**Goal:** Replace the invisible download experience with a Free Download Manager-style docked panel — persistent bottom bar with per-download progress, speed, ETA, pause/resume/cancel controls, queue management, and history.

**Architecture:** Backend gets 6 new endpoints exposing existing DownloadManager methods. Frontend gets a new DownloadProvider (unified WebSocket + REST) and a DockedDownloadPanel component pinned to the bottom of the Models page.

**Tech Stack:** FastAPI, SQLAlchemy, Next.js 15, React 19, Tailwind CSS, existing WebSocket infrastructure

---

## 1. Problem Statement

Current download UX has these issues:

1. **No visible progress during browse** — ModelCard shows a tiny progress bar, but you must switch to the Downloads tab to see speed/ETA
2. **No pause/resume** — DownloadManager has `pause()` and `resume()` methods but no API endpoints expose them
3. **No delete from local** — Cancel only stops the download; partial files remain in Ollama storage
4. **ModelDetailModal bypasses tracking** — Downloads from the modal don't update the page-level progress map
5. **No queue management** — Can't reorder, bulk cancel, or clear the queue from UI
6. **Dual tracking** — DownloadsView polls REST every 2s while WebSocket also pushes, causing redundant requests
7. **No history visibility** — Completed/failed downloads are buried in a collapsible section

---

## 2. Backend Changes

### 2.1 New Endpoints

Add to `backend/app/api/v1/integration/downloads.py`:

| Method | Path | Request Body | Response | Notes |
|--------|------|-------------|----------|-------|
| POST | `/models/{name}/pause` | — | `PauseDownloadResponse` | Sets status to PAUSED. 404 if not found/not active. |
| POST | `/models/{name}/resume` | — | `ResumeDownloadResponse` | Resumes paused/queued download. 404 if not found. |
| DELETE | `/models/{name}/local` | — | `DeleteModelResponse` | Cancels if active, then calls Ollama DELETE /api/delete to remove files. |
| POST | `/models/downloads/reorder` | `{job_ids: string[]}` | `ReorderQueueResponse` | Reorders the internal asyncio.Queue. Only QUEUED items can be reordered. |
| POST | `/models/downloads/bulk-cancel` | `{job_ids: string[]}` | `BulkCancelResponse` | Cancels multiple downloads at once. Returns count cancelled. |
| POST | `/models/downloads/clear-completed` | — | `ClearCompletedResponse` | Clears all COMPLETED/FAILED/CANCELLED from state. |

### 2.2 New Schemas

Add to `backend/app/schemas/intelligence/model.py`:

```python
class PauseDownloadResponse(BaseModel):
    paused: bool
    model: str

class ResumeDownloadResponse(BaseModel):
    resumed: bool
    model: str

class ReorderQueueResponse(BaseModel):
    reordered: bool
    new_order: list[str]  # job_ids in new order

class BulkCancelResponse(BaseModel):
    cancelled: int
    job_ids: list[str]

class ClearCompletedResponse(BaseModel):
    cleared: int
```

### 2.3 Enhanced WebSocket Payload

Update `backend/app/api/v1/interaction/ws_models.py` to push richer data:

```python
# Current (every 1s):
{"type": "model_progress", "models": [{"name": "llama3.2:3b", "progress": 0.45}]}

# New (every 1s):
{
    "type": "model_progress",
    "models": [
        {
            "name": "llama3.2:3b",
            "progress": 0.45,
            "status": "downloading",       # NEW: downloading|queued|paused|completed|failed|cancelled
            "speed_bytes_sec": 12900000,    # NEW
            "eta_seconds": 120,             # NEW
            "bytes_downloaded": 3200000000,  # NEW
            "total_bytes": 7100000000,       # NEW
            "queue_position": null           # NEW: only for queued items
        }
    ]
}
```

### 2.4 DownloadManager Reorder Method

Add `reorder(new_order: list[str])` method to `DownloadManager` in `backend/app/services/download/downloader.py`:

```python
def reorder(self, new_order: list[str]) -> list[str]:
    """Reorder the internal queue by job_id order.
    
    Only QUEUED items can be reordered. DOWNLOADING items are unaffected.
    Returns the new order of all job_ids.
    """
```

---

## 3. Frontend Changes

### 3.1 DownloadProvider (new shared context)

Create `frontend/src/shared/downloads/DownloadProvider.tsx`:

**Single source of truth** for all download state across the Models page.

```typescript
interface DownloadState {
    active: DownloadJob[];      // Currently downloading
    queued: DownloadJob[];      // Waiting in queue
    history: DownloadJob[];     // Completed/failed/cancelled
    connected: boolean;         // WebSocket connection status
}

interface DownloadActions {
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
```

**Data sources:**
- WebSocket `/ws/models` — pushes active/queued state every 1s (real-time progress)
- REST `GET /models/downloads/queue` — initial load + fallback for history
- REST `GET /models/downloads/history` — for the history drawer

**Provider wraps the Models page content** (not the whole app — downloads are scoped to Models page).

### 3.2 DockedDownloadPanel (new component)

Create `frontend/src/features/models/components/DockedDownloadPanel.tsx`:

**Layout:**
```
┌─────────────────────────────────────────────────────┐
│  ⬇ Downloads (2 active, 1 queued)         [─] [×]  │
│  ┌───────────────────────────────────────────────┐  │
│  │ ▣ llama3.1:8b-q4   ████████░░░ 72%  12.3MB/s │  │
│  │   [⏸] [■]                                2m   │  │
│  │ ▣ mistral:7b        ███░░░░░░░░ 28%   8.1MB/s │  │
│  │   [⏸] [■]                                5m   │  │
│  │ ── Queued ──                                  │  │
│  │    codellama:13b           position #1    3m   │  │
│  │    [■]                                        │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

**States:**
- **Collapsed (default):** Thin bar: `⬇ Downloads (2 active) — 72% 12.3MB/s ▸`. Click to expand.
- **Expanded:** Full panel with download rows, queued section, history link.
- **Empty + hidden:** No downloads = panel completely hidden. Badge on Downloads tab shows count.

**Per-download row:**
- Model name + variant tag
- Progress bar (animated, width transition 300ms, color: green/yellow/red based on speed)
- Speed (MB/s) + ETA (human-readable)
- Controls: Pause/Resume toggle button, Cancel (X) button
- For queued items: queue position number + estimated wait

**History drawer:**
- Accessible from panel header "History" link
- Slides up from panel (transform transition 200ms)
- Shows completed/failed/cancelled downloads
- Each row: model name, final size, status icon (check/x/stop), error message if failed, timestamp
- Retry button on failed items
- "Clear all" button

### 3.3 ModelCard Updates

Modify `frontend/src/features/models/components/ModelCard.tsx`:

- When downloading: Show inline progress bar with speed (from DownloadProvider), not just percentage
- Add pause/resume small toggle button next to cancel
- When installed: Add "Delete" button (red, with confirmation) that calls `deleteLocal()`
- Remove the model from `downloadingModels` map prop — DownloadProvider handles this

### 3.4 ModelDetailModal Fix

Modify `frontend/src/features/models/components/ModelDetailModal.tsx`:

- Download button calls `DownloadActions.download()` from provider instead of `downloads.download()` directly
- This ensures the download appears in the provider's state immediately
- Modal shows inline progress after download starts (not just spinner)

### 3.5 Models Page Wiring

Modify `frontend/src/features/models/page.tsx`:

- Remove `downloadingModels` state and WebSocket connection (moved to DownloadProvider)
- Remove `handleDownload`, `handleCancelDownload` (moved to DownloadProvider)
- Wrap content in `<DownloadProvider>`
- Render `<DockedDownloadPanel />` at bottom
- Pass `downloadActions` down to BrowseView, ModelCard, etc.

### 3.6 BrowseView Updates

Modify `frontend/src/features/models/components/BrowseView.tsx`:

- Remove `downloadingModels` prop requirement from ModelCard
- ModelCard reads download state from DownloadProvider context directly

### 3.7 DownloadsTab Enhancement

Modify `frontend/src/features/models/components/DownloadsView.tsx`:

- Read from DownloadProvider instead of polling REST directly
- Remove dual tracking (REST polling + WebSocket)
- Add queue reordering (drag handle or up/down arrows)
- Add bulk select checkbox per row + bulk cancel toolbar
- Add "Clear completed" button

### 3.8 InstalledView Enhancement

Modify `frontend/src/features/models/components/InstalledView.tsx`:

- Delete button uses `DownloadActions.deleteLocal()` (cancels if downloading + removes from Ollama)
- Add model size display (from installed data)
- Add disk usage indicator

---

## 4. Data Flow

```
User clicks Download
    |
    v
DownloadActions.download(modelId, variant)
    |-- POST /models/{name}/download
    |-- Optimistically add to active[] with progress=0
    |
    v
WebSocket /ws/models pushes every 1s:
    |-- DownloadProvider updates active/queued/history arrays
    |-- DockedDownloadPanel re-renders with new progress
    |-- ModelCard re-renders with new progress (via context)
    |
    v
Download completes:
    |-- WS pushes status=completed
    |-- DownloadProvider moves from active[] to history[]
    |-- Panel shows completion animation
    |-- If panel collapsed: badge count updates
```

---

## 5. File Changes Summary

### Backend (3 files)
| File | Change |
|------|--------|
| `backend/app/api/v1/integration/downloads.py` | Add 6 endpoints: pause, resume, delete-local, reorder, bulk-cancel, clear-completed |
| `backend/app/schemas/intelligence/model.py` | Add 5 response schemas |
| `backend/app/api/v1/interaction/ws_models.py` | Enhance WS payload with status, speed, eta, bytes, queue_position |
| `backend/app/services/download/downloader.py` | Add `reorder()` method to DownloadManager |

### Frontend (10 files)
| File | Change |
|------|--------|
| `frontend/src/shared/downloads/DownloadProvider.tsx` | **NEW** — Unified download state + actions context |
| `frontend/src/features/models/components/DockedDownloadPanel.tsx` | **NEW** — Persistent bottom download panel |
| `frontend/src/features/models/page.tsx` | Wrap in DownloadProvider, render DockedDownloadPanel, remove local WS/polling |
| `frontend/src/features/models/components/ModelCard.tsx` | Read from provider, add pause/resume/delete buttons |
| `frontend/src/features/models/components/ModelDetailModal.tsx` | Use provider download action, show inline progress |
| `frontend/src/features/models/components/BrowseView.tsx` | Remove downloadingModels prop, cards use provider |
| `frontend/src/features/models/components/DownloadsView.tsx` | Read from provider, add queue reorder + bulk cancel |
| `frontend/src/features/models/components/InstalledView.tsx` | Use provider deleteLocal, add disk usage |
| `frontend/src/features/models/api.ts` | Add new download API methods (pause, resume, deleteLocal, reorder, bulkCancel, clearCompleted) |
| `frontend/src/features/integration/api.ts` | Add new download endpoint calls |

---

## 6. Error Handling

- **Pause when not active:** Backend returns 404 with "Download not found or not active"
- **Resume when not paused:** Backend returns 400 with "Download is not in a pausable state"
- **Delete while downloading:** Frontend auto-cancels first, then deletes from Ollama
- **WebSocket disconnect:** Provider falls back to REST polling every 2s. Reconnects automatically.
- **Queue reorder invalid:** Backend validates all job_ids exist and are QUEUED, returns 400 if not

---

## 7. Testing

### Backend Tests
- Test each new endpoint (pause, resume, delete-local, reorder, bulk-cancel, clear-completed)
- Test edge cases: pause already-paused, resume not-paused, delete non-existent
- Test reorder with mixed statuses (some queued, some downloading)
- Test bulk-cancel with invalid job_ids

### Frontend Tests
- Test DownloadProvider state transitions
- Test DockedDownloadPanel render with various states (empty, collapsed, expanded, single download, multiple downloads)
- Test ModelCard shows correct controls based on download status
- Test history drawer opens/closes and shows correct items

---

## 8. Migration Notes

- No database migration needed — all new endpoints use existing DownloadManager in-memory state
- WebSocket endpoint is backwards compatible — new fields are additive
- Existing DownloadsView can coexist with DockedDownloadPanel during development
