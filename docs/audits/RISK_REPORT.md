# Risk Report

## Risk 1: Untested WebSocket Layer

**Severity:** Critical
**Likelihood:** High
**Current impact:** All 6 WS endpoints are completely untested. The accept-first bug
survived undetected because of this gap. Future changes to any WS endpoint will also
be untested unless a test strategy is implemented.

**Mitigation:** Implement WS integration tests using `websockets` library + test server fixture.
Highest priority: `ws_system.py` (most active connection), `ws_agents.py` (uses direct SessionLocal).

**Risk window:** Every WS deployment until tests exist.

## Risk 2: Long-lived DB Sessions in WS Endpoints

**Severity:** High
**Likelihood:** Medium
**Current impact:** `ws_agents.py` and `ws_notifications.py` create a single DB session
per WebSocket connection. If a WS connection stays open for hours (designed behavior),
the session may operate on stale data or encounter connection timeouts.

**Worst case:** A user leaves an agents tab open overnight. The WS keeps polling. The
DB session goes stale → query fails → endpoint crashes → WS closes → user sees
"disconnected" status in morning.

**Mitigation:** Create fresh `SessionLocal()` per poll iteration instead of one per WS connection.

## Risk 3: BaseHTTPMiddleware + WebSocket Fragility

**Severity:** Medium
**Likelihood:** Low (next time a middleware is added)
**Current impact:** `RequestSizeLimitMiddleware` and `CSRFMiddleware` both have explicit
early returns for WebSocket scope. Any future middleware added to `main.py` that extends
`BaseHTTPMiddleware` will break ALL WebSocket endpoints unless the WS check is included.

**Known issue:** The `RequestSizeLimitMiddleware` comment says:
```python
# BaseHTTPMiddleware breaks WebSocket upgrades — bypass early
if request.scope.get("type") == "websocket":
    return await call_next(request)
```

This pattern must be replicated in every `BaseHTTPMiddleware` subclass.

**Mitigation:** Replace `BaseHTTPMiddleware` subclasses with low-level ASGI middleware
that doesn't break WS. Or add a code-review checklist item for new middleware.

## Risk 4: Configuration Key Alias Drift

**Severity:** Low
**Likelihood:** Medium
**Current impact:** Two settings accept two env var names each. If a deployment sets
`CORTEX_STORAGE_ROOT` and another sets `CORTEX_ROOT`, they'll behave identically now but
could diverge if one alias is deprecated. Production deployments may have inconsistent config.

**Mitigation:** Pick one canonical name per setting, document it, schedule alias removal.

## Risk 5: Demo WS Endpoint Auth Gap

**Severity:** Low
**Likelihood:** Low
**Current impact:** `/ws/demo` doesn't check `deleted_at` or token revocation.
If a deleted account's JWT is used to connect, it would succeed where it should fail.

**Mitigation:** Switch to `verify_ws_token()`. Low priority — demo endpoint has no
production-critical functionality.

## Risk 6: No Frontend Tests

**Severity:** Medium
**Likelihood:** High
**Current impact:** Zero frontend tests. The variable shadowing bug (`loading` declared twice)
was only caught by the WS rebuild type-check, not by CI. Any frontend refactoring risks
silent breakage.

**Mitigation:** Configure Vitest + jsdom. At minimum, smoke-test the AuthProvider
and WS hooks.

## Risk 7: CSRF Documentation Drift

**Severity:** Low
**Likelihood:** Low
**Current impact:** The CSRF middleware's `EXEMPT_PREFIXES` includes `/ws` as a prefix-based
exemption, but WS endpoints are actually protected by the ASGI scope check. Future changes
to the WS scope check could leave `/api/v1/ws/*` endpoints exposed if a developer relies on
the prefix-based exemption (which doesn't cover them).

**Mitigation:** Add `/api/v1/ws` to `EXEMPT_PREFIXES` for documentation consistency,
keeping the WS scope check as defense-in-depth.

## Risk Summary

| # | Risk | Severity | Likelihood | Priority |
|---|------|----------|------------|----------|
| R1 | Untested WS layer | Critical | High | P0 |
| R2 | Stale DB sessions in WS | High | Medium | P1 |
| R3 | Middleware + WS fragility | Medium | Low | P2 |
| R4 | Config alias drift | Low | Medium | P3 |
| R5 | Demo WS auth gap | Low | Low | P3 |
| R6 | No frontend tests | Medium | High | P1 |
| R7 | CSRF doc drift | Low | Low | P4 |
