# Architecture Drift Report

## Drift 1: Legacy Route Hardcoding

**Severity:** Medium
**Location:** `backend/app/api/memory.py`
**Principle violated:** Router prefix should define the base path, not the endpoint decorator.

Every route in `api/memory.py` starts with `@router.get("/api/v1/memory/...")` — hardcoding the
API prefix. This was the pre-v1.02 pattern. All new v1 routers (in `api/v1/`) use relative paths
like `@router.get("/agents")` and rely on the container router's prefix.

**Evidence:**
```python
# Legacy (api/memory.py):
@router.get("/api/v1/memory", response_model=dict[str, Any])

# v1.02+ (api/v1/cognition/agents.py):
@router.get("/agents", response_model=AgentListResponse)
```

**Impact:**
- When `memory_router` is included in `api_router` (which is mounted at `/api/v1`),
  the effective path is `/api/v1/api/v1/memory` — a ghost route.
- The route is also directly included in app at the correct path `/api/v1/memory`.

## Drift 2: Demo WS Endpoint Auth Bypass

**Severity:** High
**Location:** `backend/app/api/ws.py`
**Principle violated:** All WS endpoints should use the centralized auth utilities.

The demo WS endpoint uses raw `jose.jwt.decode()` with `settings.SECRET_KEY` instead of
the shared `verify_ws_token()` function from `core/db.py`. This bypasses:
1. Token revocation check (`is_access_token_revoked`)
2. Multi-key rotation support (`settings.all_secret_keys`)
3. User `deleted_at` verification

**Evidence:**
```python
# api/ws.py (deviant):
payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

# v1 endpoints (standard):
user_id = await verify_ws_token(token)
```

## Drift 3: Duplicate WS Router Registration

**Severity:** Low
**Location:** `backend/app/main.py` and `backend/app/api/router.py`
**Principle violated:** Each router should be included exactly once.

`api/router.py` includes `memory_router` as a legacy backward-compatibility shim.
`main.py` also includes `memory_router` directly. The result is double registration.

## Drift 4: CSRF Documentation/Code Mismatch

**Severity:** Low
**Location:** `backend/app/core/csrf.py`
**Principle violated:** Implementation should match documentation.

The CSRF middleware exempts these path prefixes:
```python
EXEMPT_PREFIXES = ("/api/v1/auth/", "/api/v1/health/", "/metrics", "/ws")
```

The `/ws` prefix covers the `/ws/demo` endpoint. However, the v1 WS endpoints are at
`/api/v1/ws/*`, which does NOT start with `/ws`. These endpoints are only covered because
CSRFMiddleware early-returns on WS scope type (line: `if request.scope.get("type") == "websocket"`).

The prefix-based exemption is misleading — it implies `/ws` is the exemption mechanism,
when really the ASGI scope check is what protects them.

## Drift 5: Configuration Alias Accumulation

**Severity:** Low
**Location:** `backend/app/core/config.py`
**Principle violated:** One setting = one name.

```python
CORTEX_ROOT: str | None = Field(
    default=None,
    validation_alias=AliasChoices("CORTEX_ROOT", "CORTEX_STORAGE_ROOT"),
)
CORTEX_NEW_AGENT_LOOP: bool = Field(
    default=False,
    validation_alias=AliasChoices("CORTEX_NEW_AGENT_LOOP", "CORTEX_NEW_AGENT"),
)
```

Two settings that each accept two env var names. The aliases were added during migrations
but never removed. This creates an unbounded surface for configuration drift across deployments.
