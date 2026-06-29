# Consistency Report

## Frontend ↔ Backend API Contract

| Frontend Call | Expected Backend Path | Actual Backend | Match |
|---------------|----------------------|----------------|-------|
| `apiFetch("/agents")` | `/api/v1/agents` | `@router.get("/agents")` via api_router@`/api/v1` | ✅ |
| `apiFetch("/agents/runs")` | `/api/v1/agents/runs` | `@router.get("/agents/runs")` | ✅ |
| `apiFetch("/conversations")` | `/api/v1/conversations` | `@router.get("/conversations")` | ✅ |
| `apiFetch("/awareness/repos")` | `/api/v1/awareness/repos` | `@router.get("/repos")` via awareness_router@`/api/v1/awareness` | ✅ |
| `apiFetch("/models")` | `/api/v1/models` | `@router.get("/models")` via developer_router | ✅ |
| `/api/v1/auth/ws-token` | `/api/v1/auth/ws-token` | `@router.get("/api/v1/auth/ws-token")` directly | ✅ |
| `WS /api/v1/ws/system` | `/api/v1/ws/system` | `@router.websocket("/ws/system")` via api_router@`/api/v1` | ✅ |
| `WS /api/v1/ws/agents` | `/api/v1/ws/agents` | `@router.websocket("/ws/agents")` via api_router@`/api/v1` | ✅ |
| `WS /api/v1/ws/chat` | `/api/v1/ws/chat` | `@router.websocket("/ws/chat")` via api_router@`/api/v1` | ✅ |

**Conclusion:** Frontend ↔ backend API contract is consistent.

## Middleware ↔ Implementation Consistency

| Rule | Reality | Match |
|------|---------|-------|
| CSRF exempts `/ws`, `/auth`, `/health` | CORSMiddlewareWithWS exempts WS scope via early return ✅ | ✅ |
| CSRF exempts paths starting with `/ws` | `/ws/demo` covered. `/api/v1/ws/*` NOT covered by prefix check | ❌ PARTIAL |
| | BUT CSRFMiddleware early-returns on WS scope anyway | ✅ (runtime) |
| | Documentation says `/ws` prefix — code actually handles WS scope type | ⚠️ Doc drift |
| `response_model=` on all decorators | ~15 endpoints use `response_model=dict` or omit entirely | ❌ VIOLATED |
| "Specific routes before parameterized" | `/models/installed` before `/models/{model_id}` — registered in correct order | ✅ |

## Config ↔ Documentation Consistency

| Setting Documented | In Config | In .env.example | Match |
|--------------------|-----------|-----------------|-------|
| `SECRET_KEY` | ✅ | ❌ (auto-gen in dev) | ⚠️ |
| `DATABASE_URL` | ✅ | ❌ (must be set) | ⚠️ |
| `CORTEX_ROOT` | ✅ (alt: `CORTEX_STORAGE_ROOT`) | ❌ | ⚠️ |
| `CORTEX_NEW_AGENT_LOOP` | ✅ (alt: `CORTEX_NEW_AGENT`) | ❌ | ⚠️ |

## Architecture Principles ↔ Code

| Principle | Code State | Match |
|-----------|-----------|-------|
| "Router prefix (no hardcoded paths)" | `memory_router` uses hardcoded `/api/v1/memory/...` | ❌ |
| "response_model on ALL decorators" | Missing on ~15 endpoints | ❌ |
| "Ownership: resource.user_id == current_user.id" | Verified in all checked endpoints | ✅ |
| "get_db() generator" | Used in all HTTP endpoints. NOT in WS endpoints | ✅ (by design) |
| "Auth: JWT access + refresh httpOnly" | ✅ | ✅ |
| "CSRF double-submit" | Implemented | ✅ |

## Route Registration Consistency

| Route Pattern | Registration | Duplicates |
|---------------|-------------|------------|
| `/api/v1/agents/*` | via cognition_router → api_router → app | ✅ unique |
| `/api/v1/memory/*` | via memory_router → app (direct) | ✅ correct path |
| `/api/v1/api/v1/memory/*` | via memory_router → api_router → app | ❌ GHOST COPY |
| `/api/v1/ws/system` | via ws_system_router → system_router → api_router | ✅ unique |
| `/ws/demo` | via ws_router → app (direct, no prefix) | ✅ unique |
| `/api/v1/auth/*` | via auth_router → app (direct) | ✅ unique |

**Verdict:** 1 duplicate route pattern, 6 unique.

## Naming Consistency

| Pattern | Count | Issue |
|---------|-------|-------|
| `WsXYZ`, `ws_xyz` (endpoints) | 6 files | Consistent snake_case in filenames ✅ |
| Router-level mix: `ws_chat_router` vs `ws_system_router` | — | Consistent naming ✅ |
| `_extract_ws_token` duplicated | 6 copies | ❌ Not DRY |
| `user_id` in auth vs `user_id` in WS | — | Consistent parameter naming ✅ |
