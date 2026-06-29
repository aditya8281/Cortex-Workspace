# Root Cause Analysis

## Issue 1: WebSocket Connection Failures (Frontend ↔ Backend)

### Symptom
Frontend WebSocket connections fail with `readyState: 3` after handshake. Browser shows CORS errors or
silent close. Frames never arrive.

### Causal Chain

```
Problem
  └── Browser receives WebSocket close before accept
        └── Uvicorn generates hardcoded 403 on `ws.close()` without `ws.accept()`
              └── uvicorn's wsproto implementation discards custom headers on close-without-accept
                    └── 403 response lacks Access-Control-Allow-Origin
                          └── Browser sees missing CORS header → blocks connection
                                └── Endpoint called `ws.close()` before `ws.accept()`
                                      └── All 6 WS endpoints verified token BEFORE accepting
                                            └── Original design assumed accept-first was insecure
                                                  └── Trades security for protocol correctness
```

### Root Cause
**Architectural assumption violated:** WebSocket protocol requires `ws.accept()` to fire the handshake
(101 Switching Protocols). All custom response headers (including CORS) are only attached to that
handshake message. Calling `ws.close()` before `ws.accept()` causes uvicorn to generate a bare 403
without CORS — even with CORSMiddleware in place.

### Fix Applied
Moved `ws.accept()` to the first line of every WS endpoint handler, BEFORE token extraction. Error
responses now use `ws.send_json()` followed by `ws.close()` instead of bare `ws.close()`.

### Impact
All 6 WS endpoints, the CORSMiddlewareWithWS class, the demo endpoint. Trusted relationship:
CORSMiddlewareWithWS only works correctly when endpoints call `ws.accept()` first.

---

## Issue 2: MetricsProvider Duplicates Core WS Logic

### Symptom
`MetricsProvider.tsx` has its own WebSocket connection management (retry logic, reconnect delays,
timer management) that duplicates `useWebSocket.ts`. This creates two independent WS patterns
in the codebase with different retry behaviors.

### Causal Chain

```
Problem
  └── MetricsProvider bypasses useWebSocket hook
        └── Created before useWebSocket was the shared pattern
              └── Historical: MetricsProvider was the first WS consumer
                    └── When useWebSocket was factored out, MetricsProvider was never migrated
                          └── Architectural debt: duplicated connection logic
```

### Root Cause
**Failed refactoring.** `useWebSocket` was introduced as a shared WS hook, but the original
`MetricsProvider` implementation was never migrated to use it. The codebase ended up with
two independent WS retry/reconnect implementations.

### Fix Applied
Rewrote `MetricsProvider` to delegate all connection management to `useWebSocket`.

---

## Issue 3: Double-Registration of Memory API Routes

### Symptom
Memory API routes are accessible at both correct (`/api/v1/memory/...`) and incorrect
(`/api/v1/api/v1/memory/...`) paths. Every memory endpoint is unintentionally shadow-copied.

### Causal Chain

```
Problem
  └── Both [app] and [api_router] include memory_router
        └── api_router is mounted at /api/v1 → creates double-path
              └── memory_router routes hardcode /api/v1/memory prefix in @router decorators
                    └── api/router.py includes memory_router (without prefix) for "backward compatibility"
                          └── main.py also includes memory_router directly (correct registration)
                                └── Architectural migration (v1.02) left legacy routes in place
                                      └── Post-refactor cleanup was incomplete
```

### Root Cause
**Incomplete architectural migration.** When the v1.02 domain reorganization moved routes into
`api/v1/`, the legacy `api/memory.py` routes were retained and included via TWO paths — once
directly (correct) and once through the aggregator Router (creates double-prefix). This was
never cleaned up.

### Impact
- Unused route shadow: `/api/v1/api/v1/memory/*` takes router table space
- Potential confusion for API consumers
- All memory operations have two paths that produce identical results

---

## Issue 4: Zero WebSocket Test Coverage

### Symptom
None of the 6 WebSocket endpoints have tests. No test file in `backend/tests/` references
`websocket` or `ws_`.

### Causal Chain

```
Problem
  └── WS endpoints cannot be tested via TestClient (no WS support in Starlette)
        └── No alternative test strategy was implemented
              └── No integration tests using httpx or websockets library
                    └── WS was never prioritized for testing
                          └── Accept-first bug persisted undetected
```

### Root Cause
**Testing gap for non-HTTP protocols.** Starlette's `TestClient` doesn't support WebSocket
connections. No alternative testing strategy (e.g., `httpx.AsyncClient` with `ws_connect` or
dedicated WS integration tests) was implemented. The entire WS layer is untested.

---

## Issue 5: `_extract_ws_token` Duplicated Across 6 Files

### Symptom
The same 10-line function `_extract_ws_token` is defined identically in all 6 WS endpoint files.

### Causal Chain

```
Problem
  └── No shared import for token extraction
        └── Each endpoint originally implemented its own token extraction
              └── Never refactored into a shared utility
                    └── Code-review gap — duplication was not flagged
```

### Root Cause
**Missed refactoring opportunity.** Unlike the `ConnectionManager` (which IS shared), the
token-extraction helper was never centralized. Every endpoint defines its own copy.

---

## Issue 6: Demo WS Endpoint Verifies Auth Inconsistently

### Symptom
`/ws/demo` uses raw `jose.jwt.decode()` instead of `verify_ws_token()`, bypassing:
- Token revocation checks
- User `deleted_at` check
- Multi-key rotation support

### Causal Chain

```
Problem
  └── Demo endpoint implements its own auth logic
        └── Created separately from the v1 WS endpoints (different dev cycle)
              └── Auth refactoring (centralized verify_ws_token) missed this file
```

### Root Cause
**Orphaned endpoint.** The demo endpoint at `api/ws.py` was created before auth was centralized
and was never updated to use the shared `verify_ws_token` function.

---

## Issue 7: Manual DB Session Creation in WS Endpoints

### Symptom
`ws_agents.py` and `ws_notifications.py` create DB sessions via `SessionLocal()` directly
instead of using `get_db()` dependency injection.

### Causal Chain

```
Problem
  └── WS endpoints are long-lived connections, not request-response
        └── FastAPI's Depends(get_db) creates/close per-request, not per-connection
              └── WS endpoints need to create sessions inside their run loop
                    └── SessionLocal() is the only option for long-lived connections
                          └── Test overrides to get_db do not cover these DB sessions
```

### Root Cause
**Architectural impedance mismatch.** FastAPI's dependency injection is request-scoped.
WebSocket connections are long-lived. WS endpoints must manually manage DB sessions,
which means they cannot participate in FastAPI's DI test overriding mechanism.

---

## Issue 8: Configuration Key Drift

### Symptom
Two settings have multiple valid env var names via `AliasChoices`:
- `CORTEX_ROOT` / `CORTEX_STORAGE_ROOT` — same setting, two names
- `CORTEX_NEW_AGENT_LOOP` / `CORTEX_NEW_AGENT` — same bool, two names

### Causal Chain

```
Problem
  └── Backward compatibility aliases added during migrations
        └── Old config keys renamed but old names kept as aliases
              └── Aliases were never removed after migration completed
                    └── No deprecation schedule enforced
```

### Root Cause
**Alias rot.** Configuration key renames added backward-compatibility aliases that were
never cleaned up. The codebase now accepts two spellings for the same setting,
creating potential for configuration drift across deployments.

---

## Issue 9: Register Page Variable Shadowing

### Symptom
`frontend/src/app/auth/register/page.tsx` declares `loading` twice:
```ts
const { user, loading } = useAuth();    // line 141
const [loading, setLoading] = useState(false);  // line 171 → RE-ASSIGNMENT ERROR
```

### Causal Chain

```
Problem
  └── Developer reused 'loading' name without noticing existing declaration
        └── TypeScript error was suppressed or not caught in CI
              └── Build pipeline does not enforce noUnusedLocals / noShadowedNames (strict checks)
```

### Root Cause
**TypeScript strict checking gap.** The project's `tsconfig.json` does not enforce
`noUnusedLocals` (or similar strict flag) aggressively enough to catch variable shadowing
in the build pipeline — or the build was never run on this file until the WS rebuild.

## Root Cause Summary

| # | Issue | Depth | Category |
|---|-------|-------|----------|
| 1 | WS accept-before-close | 6 levels | Protocol assumption violation |
| 2 | MetricsProvider duplicating WS | 4 levels | Failed refactoring |
| 3 | Double-registered memory routes | 6 levels | Incomplete migration cleanup |
| 4 | Zero WS test coverage | 5 levels | Testing gap for non-HTTP |
| 5 | _extract_ws_token duplication | 4 levels | Review gap |
| 6 | Demo WS auth inconsistency | 4 levels | Orphaned endpoint |
| 7 | Manual DB sessions in WS | 4 levels | Architecture mismatch |
| 8 | Config key aliases | 3 levels | Alias rot |
| 9 | Variable shadowing | 3 levels | Strict checking gap |

## Highest-Leverage Root Causes

1. **Incomplete architectural migrations** (issues 2, 3, 5, 6) — Legacy code from refactors
   that was never fully cleaned up. These produce the most observable symptoms.

2. **Protocol assumption violation** (issue 1) — A subtle protocol-level assumption
   that was logically "secure" but violated WebSocket specification requirements,
   cascading into the most user-visible bug.

3. **Testing gap for non-HTTP protocols** (issues 4, 7) — The WS layer has zero tests
   because the standard test framework doesn't support it and no alternative was built.
