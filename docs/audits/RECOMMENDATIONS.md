# Recommendations — Priority Order

## P0: Fix Now

### R1. Remove Ghost Memory Routes

**Problem:** Double-registered memory routes at `/api/v1/memory/...` and `/api/v1/api/v1/memory/...`

**Action:**
```python
# api/router.py — remove legacy include
api_router.include_router(memory_router, tags=["Memory"])  # ← DELETE
api_router.include_router(metrics_router, tags=["Metrics"])  # ← DELETE if metrics have hardcoded paths too
```

Then verify metrics_router doesn't have the same issue. If `api/metrics.py` routes have hardcoded `/api/v1/metrics` paths, the same double-registration exists.

**Risk:** Low. Routes work at correct path via direct inclusion in `main.py`.

### R2. Centralize `_extract_ws_token`

**Problem:** Same 10-line function duplicated in 6 files.

**Action:** Extract to `backend.app.core.websocket`:
```python
# In ConnectionManager or as standalone utility
@staticmethod
def extract_ws_token(ws: WebSocket, token: str | None = None) -> str | None:
    if token:
        return token
    protocols = ws.headers.get("sec-websocket-protocol", "")
    if protocols:
        return protocols.split(",")[0].strip() if "," in protocols else protocols.strip()
    return ws.cookies.get("cortex_access")
```

Replace all 6 copies with `from backend.app.core.websocket import manager; manager.extract_ws_token(ws, token)`.

### R3. Unify Demo WS Auth with `verify_ws_token`

```python
# api/ws.py — replace jwt.decode with verify_ws_token
from backend.app.core.db import verify_ws_token

try:
    user_id = await verify_ws_token(token)
except Exception:
    await ws.send_json({"type": "error", "message": "Invalid token"})
    await ws.close(code=4001)
    return
```

---

## P1: Fix This Week

### R4. Add WebSocket Integration Tests

**Problem:** Zero WS test coverage.

**Action:** Create `backend/tests/ws/` with tests using `httpx.AsyncClient` + `ws_connect`:

```python
@pytest.mark.asyncio
async def test_system_metrics_ws(test_client, mock_auth, db_session):
    """Verify system metrics WS accepts connection and sends data."""
    # Get WS token
    response = await test_client.get("/api/v1/auth/ws-token", ...)
    token = response.json()["token"]

    # Connect via WebSocket
    async with test_client.websocket_connect(
        f"/api/v1/ws/system?token={token}"
    ) as ws:
        data = ws.receive_json(timeout=2)
        assert data["type"] == "metrics"
        assert "cpu_percent" in data
```

Cover each endpoint:
- `ws_system.py` — metrics push every 500ms
- `ws_agents.py` — agent run status polling
- `ws_chat.py` — typing indicator relay
- `ws_models.py` — download progress
- `ws_notifications.py` — notification polling
- `ws.py` — demo endpoint (lower priority)

### R5. Implement Stale DB Session Refresh in WS Endpoints

**Problem:** `ws_agents.py` and `ws_notifications.py` hold one DB session for entire WS lifetime.

**Action:** Create a new session per poll iteration:

```python
# Before (ws_agents.py):
await manager.register(ws, channel=f"agents:{user_id}", user_id=int(user_id))
try:
    while True:
        data = _fetch_agent_runs(user_id)  # uses single session
        ...

# After:
await manager.register(ws, channel=f"agents:{user_id}", user_id=int(user_id))
try:
    while True:
        data = _fetch_agent_runs(user_id)  # creates/fresh session each call
        ...
```

Or pass a session factory to `_fetch_agent_runs`.

### R6. Add Runtime Validation for WS Data on Frontend

**Problem:** `MetricsProvider` casts `data as unknown as LiveMetrics` — no type safety.

**Action:** Add a validation function:

```typescript
function isLiveMetrics(data: Record<string, unknown>): data is LiveMetrics {
  return (
    typeof data.cpu_percent === "number" &&
    typeof data.ram_percent === "number" &&
    typeof data.ram_used_gb === "number" &&
    typeof data.ram_total_gb === "number"
  );
}

// In handleMessage:
if (data.type === "metrics" && isLiveMetrics(data)) {
  setMetrics(data);
}
```

---

## P2: This Sprint

### R7. Configure Frontend Testing Infrastructure

**Problem:** Zero frontend tests. Variable shadowing bug was only caught by TS check during WS rebuild.

**Action:**
```json
// vitest.config.ts
import { defineConfig } from "vitest/config";
export default defineConfig({
  test: {
    environment: "jsdom",
    setupFiles: ["./tests/setup.ts"],
  },
});
```

Tests to start with:
- `AuthProvider` smoke test (renders, fetches /me)
- `useWebSocket` unit test (connect, reconnect, disconnect)
- `Button` variant rendering
- MetricsProvider integration (mock WS, verify context updates)

### R8. Clean Up Auth Re-export Indirection

**Problem:** `api/auth.py` is a one-line re-export.

**Action:** Update `main.py`:
```python
# Before:
from backend.app.api.auth import router as auth_router
# After:
from backend.app.auth.router import router as auth_router
```

### R9. Remove Empty `__init__.py` Files or Add Docstrings

**Problem:** ~10 empty init files are just module markers.

**Action:** Either remove (Python 3.3+ namespace packages don't need them) or add docstrings explaining module purpose.

---

## P3: When Time Allows

### R10. Resolve Configuration Alias Deprecation

**Action:** Pick one canonical name per setting. Log a deprecation warning when the non-canonical alias is used.

### R11. Add `/api/v1/ws` to CSRF Exempt Prefixes

**Action:** Update `EXEMPT_PREFIXES` in `csrf.py` to include `/api/v1/ws` for documentation consistency.

### R12. Create Pages or Remove Unused Protected Routes

**Action:** For `/developer`, `/docs`, `/apps`, `/knowledge`, `/compare`, `/intelligence`, `/execution` — either:
a) Create proper `ComingSoon` page components, or
b) Remove from middleware `PROTECTED_PATHS` (they'll 404 anyway, just without auth redirect)

---

## Summary — What to Fix First

| Order | Action | Effort | Risk Reduction |
|-------|--------|--------|----------------|
| 1 | Fix ghost memory routes | 30 min | Eliminates double-prefix path |
| 2 | Centralize _extract_ws_token | 15 min | DRY, maintenance velocity |
| 3 | Fix demo WS auth | 30 min | Eliminates auth bypass |
| 4 | Add WS integration tests | 4-8 hrs | **Highest ROI** — catches next WS bug |
| 5 | Refresh DB sessions in WS | 2 hrs | Prevents stale query failures |
| 6 | Add WS data validation on FE | 1 hr | Type safety for metrics pipeline |
| 7 | Configure FE testing infra | 4 hrs | Prevents frontend regression bugs |
| 8 | Clean up auth re-export | 30 min | Remove indirection |
| 9 | Clean up config aliases | 15 min | Configuration consistency |
