# Execution Plan — From Audit to Production Ready

This plan covers **every** finding from the 2026-06-29 systems audit:
all 11 reports, all 9 root causes, all 5 architecture drifts, all 7 broken
assumptions, all 12 technical debt items, all 7 risks, all 12 recommendations.

**Goal:** After this plan is executed, a re-audit returns "clean production ready."

---

## Legend

| Tag | Source |
|-----|--------|
| [RCA#N] | Root Cause Analysis, issue N |
| [AD#N] | Architecture Drift, item N |
| [BA#N] | Broken Assumptions, item N |
| [TD#N] | Technical Debt (priority N) |
| [MS#N] | Mismatch Report, item N |
| [CS#N] | Consistency Report, item N |
| [ET#N] | Execution Trace, item N |
| [RS#N] | Risk Report, item N |
| ✅ | Already fixed during audit |
| 🔴 | Remaining — needs work |

---

## Phase 0: Already Fixed

These were resolved during the audit itself and require no further action.

| Item | File(s) | Evidence |
|------|---------|----------|
| WS accept-first pattern applied to all 6 endpoints | All `ws_*.py` files | [RCA#1] ✅ |
| `MetricsProvider` uses `useWebSocket` instead of duplicating | `MetricsProvider.tsx` | [RCA#2] ✅ |
| Register page variable shadowing (`loading` → `submitting`) | `register/page.tsx` | [RCA#9][TD#3] ✅ |
| Unused `WSStatus` import removed from agents page | `agents/page.tsx` | [MS#1] ✅ |
| Unused `WSStatus` import removed from MetricsProvider | `MetricsProvider.tsx` | [MS#1] ✅ |
| Heartbeat ping (30s) added to `useWebSocket` | `useWebSocket.ts` | [BA#7] ✅ |
| `intentionalClose` flag prevents reconnect loops | `useWebSocket.ts` | [RCA#1 ancillary] ✅ |
| `useWebSocket.ts` lint error removed | `useWebSocket.ts` | [MS#1] ✅ |
| `CORTEX_BACKEND_URL` exposed as `NEXT_PUBLIC_CORTEX_BACKEND_URL` | `next.config.ts`, `useWebSocket.ts` | [BA#5] ✅ |

---

## Phase 1: Critical Architecture Fixes (Do First)

These are bugs and security gaps that have real user impact.

### 1.1 Remove Ghost Memory Routes

**Source:** [RCA#3][AD#1][AD#3][BA#4][TD#1]

The `memory_router` has hardcoded `/api/v1/memory/...` paths AND is included
in `api_router` (which is mounted at `/api/v1`), creating a second shadow path
`/api/v1/api/v1/memory/...`.

**Files:**
- `backend/app/api/router.py:12` — remove `api_router.include_router(memory_router, tags=["Memory"])`
- `backend/app/api/memory.py` — verify ALL routes use hardcoded `/api/v1/memory` (yes, they do)

**Risk:** Low. Routes work correctly via `main.py` direct inclusion at `/api/v1/memory`.

**Validation:** `curl -v http://localhost:8001/api/v1/api/v1/memory` returns 404 after fix.

### 1.2 Centralize `_extract_ws_token`

**Source:** [RCA#5][TD#2]

Same 10-line function duplicated identically in 6 files.

**Action:** Add to `backend/app/core/websocket.py`:
```python
@staticmethod
def extract_ws_token(ws: WebSocket, token: str | None = None) -> str | None:
    if token:
        return token
    protocols = ws.headers.get("sec-websocket-protocol", "")
    if protocols:
        return protocols.split(",")[0].strip() if "," in protocols else protocols.strip()
    return ws.cookies.get("cortex_access")
```

**Replace in:** `ws_system.py`, `ws_agents.py`, `ws_chat.py`, `ws_models.py`, `ws_notifications.py`, `ws.py`.

**Validation:** Each WS endpoint still accepts valid tokens. `git diff --stat` shows -50 lines.

### 1.3 Fix Demo WS Auth

**Source:** [RCA#6][AD#2][TD#5][RS#5]

`/ws/demo` uses raw `jose.jwt.decode()` instead of `verify_ws_token()`, bypassing:
- Token revocation check
- User `deleted_at` check
- Multi-key rotation

**Action:** Replace direct `jwt.decode()` with `await verify_ws_token(token)` in `backend/app/api/ws.py`.

**Validation:** Deleted user's JWT cannot connect to `/ws/demo`.

### 1.4 Fix Stale DB Sessions in WS Endpoints

**Source:** [RCA#7][BA#3][TD#12][RS#2]

`ws_agents.py` and `ws_notifications.py` create one `SessionLocal()` per WS connection.
Long-lived connections serve stale data and risk connection timeouts.

**Action:** Create fresh session per poll iteration:

```python
# ws_agents.py _fetch_agent_runs:
def _fetch_agent_runs(user_id: str) -> dict:
    db = SessionLocal()
    try:
        # ... existing query logic ...
    finally:
        db.close()
```

Same pattern for `ws_notifications.py`.

**Note:** This means creating/closing a session every 2s (agents) or 10s (notifications).
The overhead is negligible for PostgreSQL's connection pooling.

**Validation:** WS stays connected for 1+ hour with no stale query errors.

### 1.5 Fix LiveMetrics Unsafe Type Cast

**Source:** [TD#4][MS#2]

```typescript
// Current — unsafe:
setMetrics(data as unknown as LiveMetrics);

// Fixed — validated:
function isLiveMetrics(data: Record<string, unknown>): data is LiveMetrics {
  return (
    typeof data.cpu_percent === "number" &&
    typeof data.ram_percent === "number" &&
    typeof data.ram_used_gb === "number" &&
    typeof data.ram_total_gb === "number" &&
    typeof data.gpu_name === "string"
  );
}
```

**Action:** Add validation to `MetricsProvider.tsx:handleMessage`.

**Risk:** Low. Catches schema mismatches at runtime.

### 1.6 Add `/api/v1/ws` to CSRF Exempt Prefixes

**Source:** [AD#4][RS#7]

WAS: `EXEMPT_PREFIXES = ("/api/v1/auth/", "/api/v1/health/", "/metrics", "/ws")`
The `/ws` prefix covers the demo endpoint but NOT `/api/v1/ws/*` (v1 WS endpoints).
They only work because CSRF early-returns on WS scope type.

**Action:** Add `/api/v1/ws` to `EXEMPT_PREFIXES` in `backend/app/core/csrf.py`:

```python
EXEMPT_PREFIXES = ("/api/v1/auth/", "/api/v1/health/", "/metrics", "/ws", "/api/v1/ws")
```

---

## Phase 2: Testing Infrastructure (Highest ROI)

### 2.1 Configure Frontend Testing

**Source:** [TD#7][RS#6]

Zero frontend tests. Variable shadowing survived because of this.

**Action:**
1. Create `frontend/vitest.config.ts`:
```typescript
import { defineConfig } from "vitest/config";
import path from "path";
export default defineConfig({
  test: { environment: "jsdom", setupFiles: ["./tests/setup.ts"] },
  resolve: { alias: { "@": path.resolve(__dirname, "./src") } },
});
```
2. Create `frontend/tests/setup.ts`
3. Add `test` script to `frontend/package.json`

**Smoke tests:**
- `Button` renders correctly for each variant
- `Input` renders with label and error state
- `StatusDot` renders with correct color for each status
- `AuthProvider` fetches `/api/v1/auth/me` on mount

### 2.2 Add WebSocket Integration Tests

**Source:** [RCA#4][TD#11][RS#1]

All 6 WS endpoints have zero tests. The accept-first bug survived because of this gap.

**Action:** Create `backend/tests/ws/` with `httpx` or standard `TestClient.websocket_connect`:

```python
@pytest.mark.asyncio
async def test_system_metrics_ws(client, mock_auth, db_session):
    """System WS pushes metrics within 2 seconds of connect."""
    async with client.websocket_connect(
        "/api/v1/ws/system",
        subprotocols=["test-token"]
    ) as ws:
        data = ws.receive_json(timeout=2)
        assert data["type"] == "metrics"
        assert isinstance(data["cpu_percent"], (int, float))
```

Coverage target:
| Endpoint | Test case | Priority |
|----------|-----------|----------|
| `/ws/system` | Connect → receives metrics in ≤2s | P0 |
| `/ws/agents` | Connect → receives run status | P1 |
| `/ws/chat` | Send typing → receives broadcast | P1 |
| `/ws/models` | Connect → receives download state | P2 |
| `/ws/notifications` | Connect → receives notification count | P2 |
| `/ws/demo` | Send echo → receives echo | P3 |
| All endpoints | Invalid token → receives error + close | P0 |

---

## Phase 3: Code Quality & Consistency

### 3.1 Fix Missing `response_model` on Endpoints

**Source:** [CS#2]

5 endpoints lack `response_model`, violating CLAUDE.md principle:

| File | Route | Fix |
|------|-------|-----|
| `cognition/planning.py:125` | `GET /plan/{plan_id}/next-steps` | Add `response_model=PlanNextStepsResponse` |
| `cognition/confidence.py:30` | `POST /combine` | Add `response_model=ConfidenceResponse` |
| `cognition/confidence.py:42` | `GET /calibration` | Add `response_model=CalibrationResponse` |
| `cognition/errors.py:36` | `GET /patterns` | Add `response_model=ErrorPatternListResponse` |
| `execution/tools.py:68` | `GET /list` | Add `response_model=ToolListResponse` |

### 3.2 Clean Up Auth Re-export Indirection

**Source:** [TD#8][MS#4]

`backend/app/api/auth.py` is a one-line re-export of `backend.app.auth.router`.

**Action:** Update `backend/app/main.py`:
```python
# BEFORE
from backend.app.api.auth import router as auth_router
# AFTER
from backend.app.auth.router import router as auth_router
```

Then `backend/app/api/auth.py` can be removed.

### 3.3 Resolve Configuration Alias Deprecation

**Source:** [RCA#8][TD#10][RS#4][AD#5]

Two settings accept two env var names each.

**Action in `backend/app/core/config.py`:**
```python
CORTEX_ROOT: str | None = Field(
    default=None,
    validation_alias=AliasChoices(
        "CORTEX_ROOT",
        # "CORTEX_STORAGE_ROOT" ← REMOVE alias
    ),
)
CORTEX_NEW_AGENT_LOOP: bool = Field(
    default=False,
    validation_alias=AliasChoices(
        "CORTEX_NEW_AGENT_LOOP",
        # "CORTEX_NEW_AGENT" ← REMOVE alias
    ),
)
```

Add deprecation logging when old alias is used.

### 3.4 Add Runtime Validation for All WS Data Types

**Source:** [TD#4][MS#2]

After fixing `LiveMetrics` (Phase 1.5), also validate:
- `ProcessInfo` arrays — check `pid`, `name`, `cpu_percent` are present
- `SystemLog` arrays — check `timestamp`, `level`, `message` are present
- Agent run messages — check `id`, `status` are present
- Download progress — check `model_id`, `progress`, `status` are present

### 3.5 Clean Up Empty `__init__.py` Files

**Source:** [TD#6]

~10 empty `__init__.py` files. Either add docstrings or remove (Python 3.3+ namespace packages).

---

## Phase 4: Technical Debt & Cleanup

### 4.1 Resolve Unused Protected Routes

**Source:** [TD#9][MS#3]

7 middleware-protected paths have no page: `/developer`, `/docs`, `/apps`,
`/knowledge`, `/compare`, `/intelligence`, `/execution`.

**Action:** Either:
- (A) Create `ComingSoon` components for each path with sidebar integration
- (B) Remove from `PROTECTED_PATHS` in `middleware.ts` (they'll 404 anyway)
- (C) Keep protected but add a proper "Coming Soon" page that matches the sidebar

**Recommendation:** Option C — create a `ComingSoon` component and use it as a catch-all
for these paths.

### 4.2 Add `htttpx` / `websockets` Dev Dependency

**Source:** [TD#11]

For WS integration tests, add `httpx` and `websockets` to test dependencies.

**Action in `backend/pyproject.toml` or `requirements*.txt`:**
```
# test dependencies
httpx>=0.27.0
websockets>=12.0
pytest-asyncio>=0.24.0
```

### 4.3 Fix Race Condition in Token Refresh

**Source:** [ET#3]

If two simultaneous API calls both have expired tokens, both trigger refresh.
The first refresh revokes the old refresh token. The second refresh uses the now-revoked
token → 401 → both calls redirect to /auth.

**Action:** Add a refresh lock in `frontend/src/shared/api/client.ts`:
```typescript
let refreshPromise: Promise<Response> | null = null;

async function doRefresh(): Promise<Response> {
  if (refreshPromise) return refreshPromise;
  refreshPromise = fetch(`${API_BASE}/auth/refresh`, {
    method: "POST", credentials: "include",
  }).finally(() => { refreshPromise = null; });
  return refreshPromise;
}
```

This ensures only ONE refresh call runs at a time. Concurrent 401s share the same promise.

### 4.4 Add `metrics_router` Check

**Source:** [CS#2]

Verified: `metrics_router` has ONLY relative path (`/metrics`), NOT hardcoded.
The metrics route exists once at `/api/v1/metrics`. ✅ No ghost route.

**Action:** Document this in a comment in `api/router.py` next to the metrics include:
```python
# Note: metrics_router uses relative paths (/metrics), NOT hardcoded /api/v1/metrics.
# Included here for Prometheus exposition at /api/v1/metrics.
api_router.include_router(metrics_router, tags=["Metrics"])
```

---

## Phase 5: Preventative & Documentation

### 5.1 Add Middleware Checklist Item

**Source:** [RS#3]

Every new `BaseHTTPMiddleware` subclass must include the WebSocket bypass check.

**Action:**
- Add to `.claude/hooks/planning/` or as a comment in `main.py`:
```python
# ⚠️ IMPORTANT: Any BaseHTTPMiddleware added above MUST include:
#   if request.scope.get("type") == "websocket":
#       return await call_next(request)
# Otherwise ALL WebSocket endpoints will silently break.
```
- Add to the architecture drift detection skill

### 5.2 Create `.env.example` File

**Source:** [CS#3]

No `.env.example` exists. Developers must infer required env vars.

**Action:** Create `backend/.env.example`:
```env
DATABASE_URL=postgresql://cortex:cortex@localhost:5432/cortex
SECRET_KEY=
CORTEX_ROOT=~/CortexStorage
REDIS_URL=redis://localhost:6379/0
OLLAMA_BASE_URL=http://localhost:11434
CORS_ORIGINS=http://localhost:3000
```

### 5.3 Add WS Security Test

**Source:** [RS#5]

After fixing demo WS auth (Phase 1.3), add a test that verifies:
- Deleted user JWT → WS close with error
- Revoked JWT → WS close with error
- Expired JWT → WS close with error
- Missing token → WS close with error

Cover all 6 WS endpoints.

### 5.4 Remove Unused `/ws/demo` endpoint

**Source:** [ET#5]

No frontend code references `/ws/demo`. It has outdated auth. It's registered outside
the API prefix at root level.

**Action:** Either:
- (A) Delete `api/ws.py` and its inclusion in `main.py` (if truly unused)
- (B) Keep but update auth (already in Phase 1.3), add a note it's for manual testing

**Recommendation:** Keep with fixed auth + add docstring noting it's for manual WS testing.

---

## Summary — Execution Order

| Phase | Tasks | Effort | Risk |
|-------|-------|--------|------|
| P0 (Done) | 9 items already fixed | — | — |
| P1 (Crit) | 6 items: ghost routes, token centralization, demo auth, stale DB sessions, type safety, CSRF exempt | ~4 hours | Low |
| P2 (Test) | 2 items: frontend test infra, WS integration tests | ~12 hours | Low |
| P3 (Quality) | 5 items: response_model, auth re-export, config aliases, WS validation, __init__.py | ~3 hours | Low |
| P4 (Debt) | 4 items: unused routes, dev deps, refresh race condition, metrics check | ~3 hours | Low |
| P5 (Prevent) | 4 items: middleware checklist, .env.example, WS security test, /ws/demo | ~2 hours | Low |

**Total estimated effort:** ~24 hours
**Total items:** 30 fix items (9 already done, 21 remaining)
**Target outcome:** Re-audit returns zero findings, "clean production ready"

---

## Verification Protocol (Post-Execution)

After all phases complete, run the following to verify "clean production ready":

```bash
# Backend
make test          # 1,429+ tests passing (including new WS tests)
make lint          # ruff clean
make format        # ruff format clean

# Frontend
cd frontend && npx vitest run    # frontend tests passing
cd frontend && npx tsc --noEmit  # zero type errors

# Architecture
make hooks-onchange  # run all development hooks

# Manual verification
curl -v http://localhost:8001/api/v1/api/v1/memory  # returns 404 (ghost route gone)
```

Then re-run the systems audit protocol. Expected result: **clean production ready**.
