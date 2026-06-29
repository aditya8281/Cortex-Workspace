# Broken Assumptions

## Assumption 1: "CORS headers propagate to WebSocket close responses"

**Status:** BROKEN
**Details:** `CORSMiddlewareWithWS` attaches `Access-Control-Allow-Origin` headers to
`websocket.accept` AND `websocket.close` ASGI messages. However, when `ws.close()` is
called WITHOUT `ws.accept()` first, uvicorn's wsproto handler generates its OWN 403
response internally, bypassing both the endpoint handler AND the ASGI send wrapper.
The `close` message that `send_with_cors` modifies never gets sent.

**Evidence:**
```python
# cors.py — send_with_cors checks for websocket.accept and websocket.close:
if message["type"] in ("websocket.accept", "websocket.close"):
    # adds CORS headers

# But when close is called before accept, uvicorn intercepts at the protocol layer
# and generates a 403 WITHOUT going through the ASGI app at all.
```

**Impact:** The `CORSMiddlewareWithWS` implementation correctly wraps both message types,
but this only works when the endpoint calls `ws.accept()` first. The assumption that
"headers attached to websocket.close messages always propagate" is wrong when uvicorn
short-circuits before the ASGI application runs.

## Assumption 2: "WebSocket endpoints can authenticate before accept"

**Status:** BROKEN
**Details:** All 6 WS endpoints originally called `_extract_ws_token()` and `verify_ws_token()`
BEFORE `ws.accept()`. The assumption was "deny unauthorized connections early by closing before
accepting." This is logical from a security perspective but violates WebSocket protocol semantics.

**Why it's broken:** The WebSocket handshake completes on `ws.accept()` — this sends the
HTTP 101 Switching Protocols response. Any attempt to close the connection before this point
generates an error response, not a WebSocket close frame. The error response lacks CORS headers
because uvicorn's internal error handler doesn't go through the ASGI middleware.

## Assumption 3: "Module-level `get_db()` dependency override catches all DB usage"

**Status:** BROKEN for WS endpoints
**Details:** `ws_agents.py` and `ws_notifications.py` create DB sessions via `SessionLocal()`
directly, not through FastAPI's `Depends(get_db)`. Test overrides using
`app.dependency_overrides[get_db]` have no effect on these endpoints.

**Impact:** WS endpoints cannot be integrated into the standard test fixture pattern.
They always use the production database configuration, even in tests.

## Assumption 4: "`api/router.py` backward-compatibility includes are safe"

**Status:** BROKEN
**Details:** `api/router.py` includes `memory_router` and `metrics_router` as "legacy
backward-compatibility" entries. The assumption was "including the legacy router alongside
new routes is harmless." However, because `memory_router` has hardcoded `/api/v1/memory`
paths, and `api_router` is mounted at `/api/v1`, the effective path is `/api/v1/api/v1/memory`.
This NOT harmless — it's a double registration.

**Why it wasn't caught:** FastAPI doesn't warn about overlapping routes. The ghost routes
silently coexist with the correct ones.

## Assumption 5: "`CORTEX_BACKEND_URL` is automatically available in browser JS"

**Status:** BROKEN (now fixed)
**Details:** Before the env var fix, the frontend's `getWsBaseUrl()` read `CORTEX_BACKEND_URL`
directly. In Next.js, only `NEXT_PUBLIC_*` env vars are inlined into browser bundles at
compile time. The `CORTEX_BACKEND_URL` (without `NEXT_PUBLIC_` prefix) is always `undefined`
in browser JS.

**Fix:** `next.config.ts` exposes `CORTEX_BACKEND_URL` as `NEXT_PUBLIC_CORTEX_BACKEND_URL`
via the `env` config option.

## Assumption 6: "FastAPI middleware handles WebSocket"

**Status:** PARTIALLY BROKEN
**Details:** `BaseHTTPMiddleware` subclasses (like `RequestSizeLimitMiddleware` and
`CSRFMiddleware`) break WebSocket connections. The codebase has explicit early-return checks
for `request.scope.get("type") == "websocket"` in both classes. This is correct but fragile —
any new middleware added to `main.py` that extends `BaseHTTPMiddleware` will silently
break all WebSocket endpoints if it doesn't include the same check.

## Assumption 7: "Heartbeat pings are unnecessary for local WebSocket connections"

**Status:** CORRECTED
**Details:** The assumption was that since frontend and backend run on localhost, the
WebSocket connection would never drop silently. Reality: browser resource management,
OS power saving, and proxy reboots can all drop idle connections. The 30s heartbeat
ping detects stale connections.
