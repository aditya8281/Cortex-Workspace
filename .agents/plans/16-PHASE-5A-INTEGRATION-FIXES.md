# Phase 5A: Integration Fixes & Audit Response

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix all critical and high-priority issues found in the deep integration audit. Ensure every visible feature has a working backend, real data flow, and correct frontend ↔ backend contracts.

**Architecture:** Fix each system in place. No major rewrites. Targeted fixes to connect disconnected wires, replace mocks with real implementations, start dead code, and correct contract mismatches.

**Tech Stack:** Python 3.12+, SQLAlchemy 2.0, Alembic, Next.js 15, React 19, psutil, nvidia-smi, ONNX Runtime, Qdrant

## Global Constraints

- Python 3.12+, ruff line-length 120
- TypeScript strict, Next.js 15, React 19
- SQLAlchemy 2.0 `Mapped`/`mapped_column` style
- `backend.app.core.db` for `get_current_user`, `get_db` (NOT `backend.app.api.deps`)
- All backend changes compile-check: `uv run python -m py_compile <file>`
- All frontend changes build-check: `cd frontend && npx next build`
- Git commit after each task

---

## Task 1: GPU Utilization Metrics — Collect Real GPU %

**Files:**
- Modify: `backend/app/services/system_info.py`
- Modify: `backend/app/api/v1/system.py`
- Modify: `backend/app/api/v1/ws_system.py`

**Problem:** Dashboard GPU % is always `None`. The `nvidia-smi` query in `system_info.py` only fetches `name,driver_version,memory.total` but omits `utilization.gpu`.

- [ ] **Step 1: Add `utilization.gpu` to the nvidia-smi query**

In `backend/app/services/system_info.py`, find the `_nvidia_smi()` function. The query list at ~line 96 includes `["name", "driver_version", "memory.total"]`. Add `"utilization.gpu"` to this list.

```python
cmd = [
    "nvidia-smi",
    "--query-gpu=name,driver_version,memory.total,memory.used,utilization.gpu",
    "--format=csv,noheader,nounits",
]
```

Also add the new field to the parsed result dict:

```python
return {
    "detected": True,
    "name": parts[0].strip(),
    "type": "NVIDIA",
    "driver_version": parts[1].strip(),
    "memory_total_mb": int(float(parts[2].strip())),
    "memory_used_mb": int(float(parts[3].strip())),
    "utilization_gpu": int(float(parts[4].strip())),
}
```

- [ ] **Step 2: Return `gpu_percent` from the new data**

In `get_system_metrics()`, change `gpu_percent: None` to read from the new field:

```python
gpu_info = get_gpu_info()
gpu_percent = gpu_info.get("utilization_gpu") if gpu_info.get("detected") else None
```

- [ ] **Step 3: Fix the WebSocket endpoint**

In `backend/app/api/v1/ws_system.py`, `collect_metrics()` also hardcodes `gpu_percent: None`. Apply the same fix.

- [ ] **Step 4: Compile check**

```bash
uv run python -m py_compile backend/app/services/system_info.py && uv run python -m py_compile backend/app/api/v1/system.py && uv run python -m py_compile backend/app/api/v1/ws_system.py && uv run ruff check backend/app/services/system_info.py backend/app/api/v1/system.py backend/app/api/v1/ws_system.py && echo "PASS"
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/system_info.py backend/app/api/v1/system.py backend/app/api/v1/ws_system.py
git commit -m "fix: collect real GPU utilization percentage via nvidia-smi"
```

---

## Task 2: Dashboard WebSocket/HTTP State Merge

**Files:**
- Modify: `frontend/app/app/page.tsx`

**Problem:** WebSocket (2s) and HTTP polling (10s) both set `metrics` state, causing the WS payload (which lacks `processes`) to overwrite the HTTP data and blank out the processes tab.

- [ ] **Step 1: Merge WS data into existing state instead of replacing**

Find the WebSocket `onmessage` handler. Change `setMetrics(data)` to:

```typescript
setMetrics((prev) => ({ ...prev, ...data }));
```

- [ ] **Step 2: Also merge HTTP polling data**

Find the HTTP fetch `.then()` handler. Change `setMetrics(data)` to:

```typescript
setMetrics((prev) => ({ ...prev, ...data }));
```

- [ ] **Step 3: Build check**

```bash
cd frontend && npx next build 2>&1 | tail -5
```

- [ ] **Step 4: Commit**

```bash
git add frontend/app/app/page.tsx
git commit -m "fix: merge WS and HTTP metrics data to prevent process list flicker"
```

---

## Task 3: Start File Watcher on Application Startup

**Files:**
- Modify: `backend/app/main.py`

**Problem:** `FileWatcher.start()` exists but is never called. The sync system is dead code.

- [ ] **Step 1: Read `backend/app/main.py` to understand the lifespan**

Find the `lifespan` context manager or startup event.

- [ ] **Step 2: Import and start the file watcher in lifespan**

```python
from backend.app.services.file_watcher import file_watcher

# In lifespan startup, after DB init:
await file_watcher.start()
logger.info("File watcher started")

# In lifespan shutdown:
await file_watcher.stop()
logger.info("File watcher stopped")
```

- [ ] **Step 3: Verify `file_watcher` singleton exists in `file_watcher.py`**

If no module-level instance exists, create one:

```python
file_watcher = FileWatcher()
```

- [ ] **Step 4: Compile check**

```bash
uv run python -m py_compile backend/app/main.py && uv run ruff check backend/app/main.py && echo "PASS"
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/main.py
git commit -m "fix: start file watcher on application startup"
```

---

## Task 4: Real Embeddings via Ollama with Fallback

**Files:**
- Modify: `backend/app/services/embedding_service.py`
- Modify: `backend/app/core/config.py`

**Problem:** Embeddings are MD5 hash mocks by default. No real semantic vectors.

- [ ] **Step 1: Add embedding config to settings**

In `backend/app/core/config.py`, add:

```python
EMBEDDING_MODEL_PATH: str = ""
EMBEDDING_MODEL_NAME: str = "nomic-embed-text"
EMBEDDING_DIMENSION: int = 768
```

- [ ] **Step 2: Add Ollama embedding fallback**

In `backend/app/services/embedding_service.py`, add Ollama fallback method:

```python
async def _embed_via_ollama(self, texts: list[str]) -> list[list[float]]:
    import httpx
    from backend.app.core.config import settings
    base_url = settings.OLLAMA_BASE_URL
    vectors = []
    async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
        for text in texts:
            resp = await client.post("/api/embeddings", json={
                "model": settings.EMBEDDING_MODEL_NAME,
                "prompt": text,
            })
            resp.raise_for_status()
            vectors.append(resp.json()["embedding"])
    return vectors
```

- [ ] **Step 3: Restructure `_load_model()` to try ONNX first, then Ollama, then mock**

- [ ] **Step 4: Compile check**

```bash
uv run python -m py_compile backend/app/services/embedding_service.py && uv run python -m py_compile backend/app/core/config.py && uv run ruff check backend/app/services/embedding_service.py backend/app/core/config.py && echo "PASS"
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/embedding_service.py backend/app/core/config.py
git commit -m "feat: real embeddings via Ollama with ONNX fallback"
```

---

## Task 5: Chat Model Selection

**Files:**
- Modify: `backend/app/api/v1/conversations.py`
- Modify: `frontend/app/chat/page.tsx`

**Problem:** Users cannot select which LLM model to use in chat. `model_used` field in Conversation is always NULL.

- [ ] **Step 1: Add `model` field to SendMessagePayload**

In `backend/app/api/v1/conversations.py`:

```python
class SendMessagePayload(BaseModel):
    content: str = Field(min_length=1, max_length=10000)
    model: str | None = None
```

- [ ] **Step 2: Pass model to `chat_stream()` and update `model_used`**

In `_stream_chat_response()`, add `model` parameter and `user_id`:

```python
async def _stream_chat_response(
    conversation_id: int,
    user_content: str,
    db: Session,
    model: str | None = None,
    user_id: int | None = None,
) -> AsyncGenerator[str, None]:
    svc = ConversationService(db)
    svc.add_message(conversation_id, "user", user_content)

    # Update model_used
    if model and user_id:
        conv = svc.get(conversation_id, user_id)
        if conv:
            conv.model_used = model
            db.commit()

    history = svc.get_context_messages(conversation_id)
    messages = [LLMMessage(role=m.role, content=m.content) for m in history]

    async for chunk in llm_manager.chat_stream(messages, model=model, max_tokens=2048, temperature=0.7):
        yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
```

Update the route handler to pass the new params:

```python
return StreamingResponse(
    _stream_chat_response(conversation_id, payload.content, db, model=payload.model, user_id=current_user.id),
    media_type="text/event-stream",
)
```

- [ ] **Step 3: Add model selector to chat UI**

In `frontend/app/chat/page.tsx`, add a model dropdown above the input. Fetch models from the models API.

```tsx
const [selectedModel, setSelectedModel] = useState<string>("");
const [availableModels, setAvailableModels] = useState<string[]>([]);

useEffect(() => {
  api.get<{ models: Array<{ id: string; name: string }> }>("/api/v1/models").then((data) => {
    setAvailableModels(data.models.map((m) => m.id));
  });
}, []);
```

In the send function, include the model:

```typescript
body: JSON.stringify({ content: userMsg.content, model: selectedModel || undefined }),
```

- [ ] **Step 4: Build check**

```bash
cd frontend && npx next build 2>&1 | tail -5
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/v1/conversations.py frontend/app/chat/page.tsx
git commit -m "feat: model selection in chat with model_used persistence"
```

---

## Task 6: Agent Model ID and Tools Usage at Execution

**Files:**
- Modify: `backend/app/agents/executor.py`
- Modify: `backend/app/agents/run_manager.py`

**Problem:** Agent `model_id` and `tools_json` are stored but never used at execution time.

- [ ] **Step 1: Pass agent's `model_id` to LLM calls**

In `backend/app/agents/executor.py`, find `_execute_direct()` (~line 90). It calls `llm_manager.chat(messages, max_tokens=2048, temperature=0.3)`. Add `model` param:

```python
model_id = getattr(self._agent, "model_id", None) if hasattr(self, "_agent") else None
response = await llm_manager.chat(messages, model=model_id, max_tokens=2048, temperature=0.3)
```

- [ ] **Step 2: Use agent's `tools_json` for tool filtering**

In `executor.py`, the tools are registered in `_execute_with_llm` (~line 47). Filter based on agent config:

```python
import json
allowed_tools = json.loads(self._agent.tools_json) if self._agent.tools_json else ["search", "read_file", "write_file", "list_files"]
```

Then filter the tool schemas passed to the LLM.

- [ ] **Step 3: Wire planner with LLM**

In `backend/app/agents/run_manager.py`, find where `PlannerAgent` is instantiated. Pass `llm_manager.chat`:

```python
from backend.app.services.llm.manager import llm_manager
planner = PlannerAgent(llm_chat=llm_manager.chat)
```

- [ ] **Step 4: Compile check + Lint**

```bash
uv run python -m py_compile backend/app/agents/executor.py && uv run python -m py_compile backend/app/agents/run_manager.py && uv run ruff check backend/app/agents/executor.py backend/app/agents/run_manager.py && echo "PASS"
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/agents/executor.py backend/app/agents/run_manager.py
git commit -m "fix: use agent model_id and tools_json at execution, wire planner with LLM"
```

---

## Task 7: Background Agent Execution with Status Polling

**Files:**
- Modify: `backend/app/api/v1/agents.py`
- Create: `backend/app/agents/background.py`
- Modify: `frontend/app/agents/page.tsx`

**Problem:** Agent runs are synchronous and block the HTTP request.

- [ ] **Step 1: Create background execution wrapper**

Create `backend/app/agents/background.py`:

```python
from __future__ import annotations
import asyncio
import logging

logger = logging.getLogger(__name__)
_active_runs: dict[int, asyncio.Task] = {}


async def run_agent_background(run_id: int, agent_id: int, user_id: int, input_text: str):
    from backend.app.core.db import SessionLocal
    from backend.app.agents.run_manager import AgentRunManager

    db = SessionLocal()
    try:
        manager = AgentRunManager(db)
        run = manager.create_run(agent_id, user_id, input_text)
        _active_runs[run.id] = asyncio.current_task()
        await manager.execute_run(run)
    except Exception as e:
        logger.error(f"Background agent run {run_id} failed: {e}")
    finally:
        _active_runs.pop(run_id, None)
        db.close()


def get_run_status(run_id: int) -> str:
    if run_id in _active_runs:
        task = _active_runs[run_id]
        return "completed" if task.done() else "running"
    return "unknown"
```

- [ ] **Step 2: Make agent run endpoint async**

In `agents.py`, change `POST /runs` to start background task:

```python
import asyncio

@router.post("/runs")
async def create_run(payload: CreateRunPayload, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from backend.app.agents.background import run_agent_background
    # Create run first to get run_id
    from backend.app.agents.run_manager import AgentRunManager
    manager = AgentRunManager(db)
    run = manager.create_run(payload.agent_id, current_user.id, payload.input)
    asyncio.create_task(run_agent_background(run.id, payload.agent_id, current_user.id, payload.input))
    return {"status": "started", "run_id": run.id}
```

- [ ] **Step 3: Add status polling endpoint**

```python
@router.get("/runs/{run_id}/status")
async def get_run_status(run_id: int, current_user: User = Depends(get_current_user)):
    from backend.app.agents.background import get_run_status
    return {"run_id": run_id, "status": get_run_status(run_id)}
```

- [ ] **Step 4: Add frontend polling for active runs**

In `frontend/app/agents/page.tsx`, poll status after starting a run.

- [ ] **Step 5: Compile check + Lint + Build check**

```bash
uv run python -m py_compile backend/app/agents/background.py && uv run python -m py_compile backend/app/api/v1/agents.py && uv run ruff check backend/app/agents/background.py backend/app/api/v1/agents.py && echo "Backend PASS"
cd frontend && npx next build 2>&1 | tail -5
```

- [ ] **Step 6: Commit**

```bash
git add backend/app/agents/background.py backend/app/api/v1/agents.py frontend/app/agents/page.tsx
git commit -m "feat: background agent execution with status polling"
```

---

## Task 8: Search Page — Use LLM-Powered Answer Endpoint

**Files:**
- Modify: `frontend/app/search/page.tsx`

**Problem:** Search page builds synthetic "AI Answer" instead of calling `/search/answer`.

- [ ] **Step 1: Read the existing search page**

Find the synthetic answer generation code.

- [ ] **Step 2: Replace with real API call**

```typescript
const getAiAnswer = async (query: string) => {
  try {
    const res = await fetch("/api/v1/search/answer", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, repo_id: selectedRepo }),
    });
    const data = await res.json();
    return data.answer;
  } catch {
    return synthesizeFallbackAnswer(query, results);
  }
};
```

- [ ] **Step 3: Build check**

```bash
cd frontend && npx next build 2>&1 | tail -5
```

- [ ] **Step 4: Commit**

```bash
git add frontend/app/search/page.tsx
git commit -m "fix: use LLM-powered /search/answer endpoint"
```

---

## Task 9: Dynamic Model Catalogue from Ollama

**Files:**
- Modify: `backend/app/services/llm/manager.py`
- Modify: `backend/app/api/v1/models.py`

**Problem:** Model catalog is hardcoded to 7 models.

- [ ] **Step 1: Add Ollama catalog fetching**

In `llm/manager.py`, add method to fetch available models from Ollama:

```python
async def fetch_ollama_catalog(self) -> list[LLMModelInfo]:
    import httpx
    from backend.app.core.config import settings
    try:
        async with httpx.AsyncClient(base_url=settings.OLLAMA_BASE_URL, timeout=10.0) as client:
            resp = await client.get("/api/tags")
            resp.raise_for_status()
            data = resp.json()
            models = []
            for m in data.get("models", []):
                models.append(LLMModelInfo(
                    name=m["name"],
                    size_bytes=m.get("size", 0),
                    context_length=4096,
                    capabilities=["chat"],
                    description=f"Ollama model: {m['name']}",
                ))
            return models
    except Exception:
        return []
```

- [ ] **Step 2: Merge static + dynamic catalogs in `/models` endpoint**

```python
@router.get("/models")
async def list_models(current_user: User = Depends(get_current_user)):
    static = MODEL_CATALOG
    dynamic = await llm_manager.fetch_ollama_catalog()
    seen = {m["name"] for m in dynamic}
    extras = [asdict(m) for m in dynamic if m.name not in seen]
    return {"models": static + extras}
```

- [ ] **Step 3: Add model delete endpoint**

```python
@router.delete("/models/{model_name}")
async def delete_model(model_name: str, current_user: User = Depends(get_current_user)):
    import httpx
    from backend.app.core.config import settings
    async with httpx.AsyncClient(base_url=settings.OLLAMA_BASE_URL) as client:
        resp = await client.delete("/api/delete", json={"name": model_name})
        resp.raise_for_status()
    return {"status": "deleted", "model": model_name}
```

- [ ] **Step 4: Compile check**

```bash
uv run python -m py_compile backend/app/services/llm/manager.py && uv run python -m py_compile backend/app/api/v1/models.py && uv run ruff check backend/app/services/llm/manager.py backend/app/api/v1/models.py && echo "PASS"
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/llm/manager.py backend/app/api/v1/models.py
git commit -m "feat: dynamic model catalogue from Ollama with delete support"
```

---

## Task 10: Agent Delete Safety Check & Error Feedback

**Files:**
- Modify: `backend/app/api/v1/agents.py`
- Modify: `frontend/app/agents/page.tsx`

**Problem:** Agent deletion silently fails. No check for in-progress runs.

- [ ] **Step 1: Add safety check in backend**

In `delete_agent()`, check for active runs before deleting:

```python
active_runs = db.query(AgentRun).filter(
    AgentRun.agent_id == agent_id, AgentRun.status == "running"
).all()
if active_runs:
    raise HTTPException(status_code=409, detail="Cannot delete agent with active runs")
```

- [ ] **Step 2: Add proper error display in frontend**

Replace silent catch with user feedback:

```typescript
} catch (err: any) {
  const message = err?.response?.detail || "Failed to delete agent";
  alert(message);
}
```

- [ ] **Step 3: Build check**

```bash
cd frontend && npx next build 2>&1 | tail -5
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/api/v1/agents.py frontend/app/agents/page.tsx
git commit -m "fix: agent delete safety check and error feedback"
```

---

## Task 11: Agent Editing UI

**Files:**
- Create: `frontend/app/agents/AgentEditor.tsx`
- Modify: `frontend/app/agents/page.tsx`

**Problem:** Agent update endpoint exists but there's no UI to edit agents.

- [ ] **Step 1: Create AgentEditor component**

A modal/inline form with: Name, Description, System prompt, Model selection dropdown, Tools checkboxes.

- [ ] **Step 2: Add edit button to agent detail view**

- [ ] **Step 3: Build check**

```bash
cd frontend && npx next build 2>&1 | tail -5
```

- [ ] **Step 4: Commit**

```bash
git add frontend/app/agents/AgentEditor.tsx frontend/app/agents/page.tsx
git commit -m "feat: agent editing UI with model and tools configuration"
```

---

## Task 12: Background Sync with Progress Visibility

**Files:**
- Modify: `backend/app/services/file_watcher.py`
- Modify: `backend/app/api/v1/sync.py`

**Problem:** Sync is manual-only. No automatic background sync or progress tracking.

Note: `frontend/app/sync/page.tsx` does not currently exist. The SyncStatus component is embedded in other pages. This task focuses on backend progress tracking.

- [ ] **Step 1: Add progress tracking to file watcher**

In `file_watcher.py`, the `FileWatcher` class already has `watched_count` and `pending_count` properties. Add more detailed state tracking:

```python
_sync_state = {
    "status": "idle",
    "watching": 0,
    "pending": 0,
    "indexed": 0,
    "errors": 0,
    "last_sync": None,
}
```

- [ ] **Step 2: Update sync status endpoint to return progress**

In `sync.py`, return detailed state:

```python
@router.get("/sync/status")
async def get_sync_status(current_user: User = Depends(get_current_user)):
    return {
        "watching": _sync_state["watching"],
        "pending_changes": _sync_state["pending"],
        "indexed_files": _sync_state["indexed"],
        "errors": _sync_state["errors"],
        "status": _sync_state["status"],
        "last_sync": _sync_state["last_sync"],
    }
```

- [ ] **Step 3: Enhance frontend SyncStatus component with progress details**

The SyncStatus component is used across pages. Update it to show the new detailed status fields.

- [ ] **Step 4: Build check**

```bash
cd frontend && npx next build 2>&1 | tail -5
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/file_watcher.py backend/app/api/v1/sync.py frontend/
git commit -m "feat: background sync with progress visibility"
```

---

## Exit Criteria

- [ ] GPU % shows real utilization from nvidia-smi (not None)
- [ ] Dashboard processes list doesn't flicker/blank on WS updates
- [ ] File watcher starts on application startup
- [ ] Embeddings use real Ollama model (not MD5 mocks)
- [ ] Chat has model selector and `model_used` is persisted
- [ ] Agent execution uses agent-specific `model_id` and `tools_json`
- [ ] Agent runs execute in background with status polling
- [ ] Search uses LLM-powered `/search/answer` endpoint
- [ ] Model catalogue includes Ollama models dynamically
- [ ] Agent deletion checks for active runs and shows errors
- [ ] Agent editing UI exists and works end-to-end
- [ ] Background sync shows progress, status, and history
