# Mismatch Report

## Backend ↔ Frontend Schema Mismatches

### 1. `WSStatus` type — exported but only used internally

**File:** `frontend/src/shared/ws/useWebSocket.ts`
**Issue:** `WSStatus` is exported but the only external consumer was `MetricsProvider.tsx` (pre-fix)
and `agents/page.tsx` (pre-fix). After the rebuild, no external file uses the type.
The return type of `useWebSocket()` already uses it.

**Status:** Was used in 2 places (both removed in rebuild). Now a dead export.

### 2. `LiveMetrics` — cast through `as unknown`

**File:** `frontend/src/shared/ws/MetricsProvider.tsx:76`
**Code:**
```typescript
setMetrics(data as unknown as LiveMetrics);
```
**Cause:** `data` is typed as `Record<string, unknown>` from the WS hook. Direct cast from
`Record<string, unknown>` to `LiveMetrics` fails TypeScript's structural check because
`data` isn't known to have the required properties. Double cast is a symptom of unsafe typing.

**Risk:** A backend schema change to the metrics payload won't cause a TypeScript compile error.
Mismatch only surfaces at runtime as missing fields.

**Fix:** Add a runtime validator (zod or manual check) that asserts the shape before casting.

### 3. `ProcessInfo` — has `memory_percent` but backend uses `mean_memory`

**Need to verify this. Let me check the backend's WS response.**

### 4. `UserRefreshPayload` schema mismatch — optional fields

The frontend `MeUpdate` type may not match `UserRegisterPayload` schema on backend. Need deeper audit.

## Frontend Routing Mismatches

### 1. Middleware `PROTECTED_PATHS` has 19 paths

**File:** `frontend/src/middleware.ts`
Some of these paths don't have corresponding page routes:
- `/dashboard` → redirects to `/` (dashboard is the root page)
- `/developer` → no page file
- `/docs` → no page file
- `/apps` → no page file
- `/knowledge` → no page file
- `/compare` → no page file (this was in models feature)
- `/intelligence` → no page file
- `/execution` → no page file

These are listed as "Coming Soon" in the sidebar. They're protected (no anonymous access), but
there's no page for them — they'd show the Not Found page or a fallback.

### 2. `/models/health` backend endpoint — no page mapping

The backend provides `/api/v1/models/health` and `/api/v1/models/metrics` endpoints, but
there's no dedicated frontend page for model health. These are consumed as part of the
system page.

## Backend Router Mismatches

### 1. `metrics_router` duplication

**Files:** `api/metrics.py`, `api/router.py`, `main.py`
`metrics_router` is included in `api_router` (which is at `/api/v1`). But unlike `memory_router`,
it's NOT also included directly in `main.py`. So the metrics routes are only at `/api/v1/metrics`,
not duplicated. This is actually CORRECT — but inconsistent with how `memory_router` is handled.

### 2. Auth routes — registered at app root, not in api_router

Auth routes start with `/api/v1/auth/`. The auth_router is included directly in `main.py`
without any prefix. This means the route paths ARE the full paths. This is correct and avoids
the double-prefix problem.

But `auth_router` is ALSO re-exported through `backend.app.api.auth` as a compatibility shim.
This indirection is unnecessary — `main.py` could import from `backend.app.auth.router` directly.
