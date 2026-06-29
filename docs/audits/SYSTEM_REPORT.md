# CORTEX — Systems Forensics Investigation

## Repository Structure

```
Cortex-Workspace/                    # ~18K files across 6 subsystems
├── backend/                         # FastAPI — 415 Python files, 45K LoC
│   ├── backend/app/
│   │   ├── agents/                  # Agent execution engine (34 files)
│   │   ├── api/                     # API layer
│   │   │   ├── auth.py              # → re-exports backend.app.auth.router
│   │   │   ├── memory.py            # Legacy memory routes (HARDCODED /api/v1/memory)
│   │   │   ├── metrics.py           # Prometheus-style metrics
│   │   │   ├── router.py            # Master api_router aggregator
│   │   │   ├── ws.py                # Demo WS endpoint (/ws/demo)
│   │   │   └── v1/                  # 10 domain routers
│   │   ├── auth/                    # Auth service & rate limiting
│   │   ├── core/                    # Config, middleware, security, DB, CORS
│   │   ├── daemon/                  # CLI daemon (cortexd)
│   │   ├── db/                      # Bootstrap, session, migrations
│   │   ├── mcp/                     # Model Context Protocol bridge
│   │   ├── models/                  # 64 SQLAlchemy models
│   │   ├── schemas/                 # 179 Pydantic schemas
│   │   ├── services/                # 80+ service files across 10 domains
│   │   └── tasks/                   # Background workers
│   ├── tests/                       # 169 test files, 18K LoC
│   └── backend/app/data/            # library.json (model catalog)
├── frontend/                        # Next.js 15 — 107 TSX/TS files, 10K LoC
│   ├── src/
│   │   ├── app/                     # 20 page routes
│   │   ├── features/                # 12 feature modules
│   │   └── shared/                  # Auth, WS, UI, API client
│   └── middleware.ts                # Server-side auth guard
├── crates/                          # Rust crates (code-intel, file-watcher)
├── docs/                            # Architecture, decisions, audits
├── cli/                             # TypeScript CLI
├── migrations/                      # 37 Alembic migrations
└── .claude/                         # 70+ skills, hooks, commands
```

## Subsystem Inventory

| Subsystem | Files | LoC | Tests |
|-----------|-------|-----|-------|
| Backend API | ~130 | ~18K | 1,429 passing |
| Backend Auth | 6 | ~25K | (covered by API tests) |
| Backend Agents | 34 | ~5K | Minimal |
| Backend Core | 18 | ~3K | N/A |
| Backend Models | 40+ | ~3K | N/A |
| Backend Services | 80+ | ~10K | (covered by API tests) |
| Frontend Pages | 20 | ~4K | 0 (not scaffolded) |
| Frontend Features | 50 | ~5K | 0 |
| Frontend Shared | 17 | ~2K | 0 |
| Rust Crates | 2 | ~2K | N/A |
| Docs | 58 files | unknown | N/A |

## Config (backend.app.core.config)

```python
SECRET_KEY: str = ""                 # Auto-generated in dev; required in prod
DATABASE_URL: str = ""               # Postgres; must be set
REDIS_URL: str = "redis://localhost:6379/0"  # Optional, fails open
API_V1_PREFIX: str = "/api/v1"
ALLOWED_ORIGINS: str = ""            # Comma-separated for production
CORTEX_ROOT: str | None              # Aliases: CORTEX_ROOT, CORTEX_STORAGE_ROOT
CORTEX_NEW_AGENT_LOOP: bool = False  # Aliases: CORTEX_NEW_AGENT_LOOP, CORTEX_NEW_AGENT
```

## Middleware Chain (registration order → execution reverse order)

```
CORSMiddlewareWithWS          → handles WS CORS, inherits Starlette CORSMiddleware
RequestLoggingMiddleware      → request_id + timing
GZipMiddleware                → compress responses ≥500B
RequestSizeLimitMiddleware    → 10MB default, 2MB upload
RateLimitMiddleware           → configurable per-route
CSRFMiddleware                → double-submit cookie (exempts /ws, /auth, /health)
HTTPSRedirectMiddleware       → optional production redirect
FastAPI router                → serves endpoints
```

## Router Inclusion (main.py)

```
app
├── api_router @ /api/v1          ← ALL v1 routes + legacy memory/metrics
├── auth_router                    ← Auth endpoints (no prefix; routes hardcode /api/v1/auth)
├── memory_router                  ← DUPLICATE: also in api_router
└── ws_router                      ← /ws/demo (no /api/v1 prefix)
```

## Frontend Config (next.config.ts)

```
Dynamic rewrite: /api/:path* → http://localhost:$CORTEX_BACKEND_PORT/api/:path*
Env: NEXT_PUBLIC_CORTEX_BACKEND_URL = CORTEX_BACKEND_URL (from .env.local)
WS: direct connection to backend at getWsBaseUrl() + path
```
