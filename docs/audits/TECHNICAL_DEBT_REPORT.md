# Technical Debt Report

## Priority 1 (Fix Immediately)

### TD-1: Ghost Routes from Double Router Inclusion

**Type:** DRY violation / Route pollution
**Files:** `backend/app/main.py:51`, `backend/app/api/router.py:12`
**Fix:** Remove `memory_router` from `api_router` and only include directly in `main.py`.
Or refactor `memory_router` routes to NOT hardcode `/api/v1/memory` prefix.

**Effort:** 30 minutes
**Risk:** Low — routes already work at correct path. Only ghost path breaks.

### TD-2: `_extract_ws_token` Duplicated Across 6 Files

**Type:** Code duplication
**Files:** `ws_system.py`, `ws_agents.py`, `ws_chat.py`, `ws_models.py`, `ws_notifications.py`, `ws.py`
**Fix:** Extract to `backend.app.core.websocket` as `manager.extract_ws_token(ws, token)`

**Effort:** 15 minutes
**Risk:** Trivial

### TD-3: Variable Shadowing in Register Page

**Type:** Code quality
**File:** `frontend/src/app/auth/register/page.tsx:171`
**Fix:** Already applied (`loading` → `submitting`)

**Effort:** Already fixed
**Risk:** N/A

---

## Priority 2 (This Week)

### TD-4: LiveMetrics Unsafe Type Cast

**Type:** Type safety
**File:** `frontend/src/shared/ws/MetricsProvider.tsx:76`
**Fix:** Add runtime validation (zod or manual field check) for incoming WS metrics data.

```typescript
const { status } = useWebSocket({
  path: "/api/v1/ws/system",
  enabled: !!user,
  onMessage: validateAndSetMetrics, // validate before setState
});
```

**Effort:** 1 hour
**Risk:** Low

### TD-5: Demo WS Auth Bypass

**Type:** Security inconsistency
**File:** `backend/app/api/ws.py:35-44`
**Fix:** Replace direct `jwt.decode()` with `verify_ws_token()` and add `deleted_at` check.

**Effort:** 30 minutes
**Risk:** Low (demo endpoint, not production-critical)

### TD-6: Empty `__init__.py` Files

**Type:** Repository clutter
**Files:** All `__init__.py` files that are empty or minimal
**Count:** ~10 empty init files (module markers with no docstring)
**Effort:** 1 minute each
**Risk:** Trivial

---

## Priority 3 (This Sprint)

### TD-7: Frontend Testing Gap

**Type:** Coverage
**Files:** All frontend `.tsx`/`.ts` files
**Status:** Zero frontend tests. Not even Vitest configured.
**Fix:** Configure Vitest + jsdom + React Testing Library. Start with smoke tests:
- `AuthProvider` renders without error
- `MetricsProvider` connects WS on mount
- `Button` renders with correct variants

**Effort:** 4 hours (initial) + ongoing
**Risk:** Low-medium

### TD-8: Auth Re-export Indirection

**Type:** Unnecessary layer
**File:** `backend/app/api/auth.py`
**Status:** `api/auth.py` is a one-liner re-export of `backend.app.auth.router`.
**Fix:** Update `main.py` imports to point directly to `backend.app.auth.router`.

**Effort:** 30 minutes
**Risk:** Low

### TD-9: Empty Pages Listed in Middleware

**Type:** Dead code / UX gap
**Files:** `frontend/src/middleware.ts` + missing page files
**Status:** 7 middleware-protected paths have no corresponding page:
- `/developer`, `/docs`, `/apps`, `/knowledge`, `/compare`, `/intelligence`, `/execution`
**Fix:** Create `ComingSoon` components or remove from PROTECTED_PATHS.

**Effort:** 30 minutes
**Risk:** Low

---

## Priority 4 (When Time Allows)

### TD-10: Config Alias Cleanup

**Type:** Configuration drift
**File:** `backend/app/core/config.py`
**Fix:** Remove `AliasChoices` — choose one canonical name per setting.
- `CORTEX_ROOT` wins over `CORTEX_STORAGE_ROOT`
- `CORTEX_NEW_AGENT_LOOP` wins over `CORTEX_NEW_AGENT`

**Effort:** 15 minutes
**Risk:** Medium (deployments may use old names)

### TD-11: WS Endpoint Test Strategy

**Type:** Coverage gap
**Files:** All 6 WS endpoint files
**Status:** Zero WS tests. Cannot use standard TestClient.
**Fix:** Implement integration tests using `httpx.AsyncClient` with `ws_connect` or Python
`websockets` library against a test instance.

**Effort:** 4-8 hours
**Risk:** Low

### TD-12: Long-lived DB Sessions in WS Endpoints

**Type:** Architectural debt
**Files:** `ws_agents.py:30`, `ws_notifications.py:30`
**Status:** Manual `SessionLocal()` usage creates stale session problem during long WS lifetimes.
**Fix:** Implement session refresh pattern — create fresh sessions for each poll iteration,
not one session for the entire WS connection.

**Effort:** 2 hours
**Risk:** Low-medium
