# Cortex Workspace — System Analysis

Last updated: 2026-06-18

## Overview

Cortex is a local-first workspace with authentication, a central memory system, and a clean foundation for future features.

```
Client (Next.js :3000) ──► FastAPI Backend (:8000) ──► SQLite + Redis
```

- **Frontend**: Next.js 15 App Router, React 19, Tailwind CSS
- **Backend**: FastAPI (Python 3.10+), SQLAlchemy ORM, Alembic migrations
- **Storage**: SQLite database, Redis cache (optional)

## Backend Structure

```
backend/app/
├── main.py                  # FastAPI app entry point, lifespan, CORS, middleware
├── core/                    # Infrastructure: config, security, storage, DB, Redis
│   ├── config.py            # Pydantic settings from env vars
│   ├── security.py          # Password hashing (Argon2/bcrypt), JWT creation
│   ├── tokens.py            # Async token creation/verification wrappers
│   ├── db.py                # DB session dependency
│   ├── redis.py             # Redis client (async, graceful fallback)
│   ├── middleware.py         # Request logging middleware
│   ├── logging.py           # Buffered log handler
│   ├── paths.py             # Project root path
│   ├── system_paths.py      # System directory management
│   ├── storage_abstraction.py # Path validation, user storage management
│   └── storage_manager.py   # Storage path wrapper
├── auth/                    # Authentication system
│   ├── router.py            # Auth endpoints (register, login, refresh, logout, me, check-username)
│   ├── service.py           # Auth business logic (register, login, refresh, logout)
│   ├── tokens.py            # Refresh token management (Redis-backed + JWT fallback)
│   ├── rate_limit.py        # Login rate limiting (Redis-backed, fail-open)
│   ├── audit.py             # Auth event logging
│   ├── dependencies.py      # require_admin, require_role
│   └── __init__.py
├── db/                      # Database layer
│   ├── bootstrap.py         # Engine init, migrations, session factory
│   ├── base.py              # DeclarativeBase
│   └── session.py           # DynamicSessionLocal
├── models/                  # SQLAlchemy ORM models
│   ├── user.py              # User (auth, profile, GitHub fields)
│   ├── auth_event.py        # AuthEvent (audit log)
│   └── storage_registry.py  # StorageRegistry (per-user paths)
├── schemas/
│   └── user.py              # Pydantic schemas (UserRegister, UserResponse, etc.)
├── services/
│   ├── user_service.py      # User CRUD, serialization
│   ├── storage_registry.py  # Storage path registration
│   ├── health_service.py    # DB readiness check
│   └── memory_manager.py    # Central memory system manager
├── api/
│   ├── router.py            # Aggregates v1 routers (health, users, profile, github)
│   ├── auth.py              # Legacy shim → auth.router
│   ├── memory.py            # Central memory endpoints (GET/POST /api/memory)
│   ├── deps.py              # get_current_user, get_current_user_optional, get_db
│   └── v1/
│       ├── health.py        # /health/live, /ready, /deep
│       ├── users.py         # Admin user management
│       ├── profile.py       # GET/PUT /me/profile + photo upload/delete
│       └── github.py        # GitHub account connection/disconnection
└── intelligence/
    └── models.py            # KnowledgeEntry (central memory data model)
```

## Frontend Structure

```
frontend/
├── app/
│   ├── layout.js            # Root layout (fonts, AuthProvider)
│   ├── page.js              # Landing page (/)
│   ├── globals.css          # Global styles (Tailwind)
│   ├── auth/page.js         # Auth page — multi-step registration wizard + login (/auth)
│   ├── app/page.js          # Dashboard — protected (/app)
│   ├── admin/page.js        # Admin dashboard — user management (/admin)
│   ├── profile/page.js      # Profile page — avatar, settings, GitHub (/profile)
│   └── api/[...path]/       # Catch-all proxy to backend (binary-safe)
├── src/shared/
│   ├── auth/                # AuthProvider, session.js, cortexApi.js
│   ├── ui/                  # Button, Input, Card, Steps, PasswordStrength
│   ├── layout/              # DashboardShell
│   └── design/              # Design tokens
└── package.json
```

## Auth Flow

1. User submits credentials on `/auth`
2. Registration uses a multi-step wizard: Account → Profile → GitHub → Vault
3. Frontend calls `apiLogin`/`apiRegister` → backend `/api/auth/login` or `/api/auth/register`
4. Backend validates, creates user, returns JWT access token + refresh token + user object
5. Frontend stores tokens in sessionStorage via `AuthProvider`
6. All subsequent API calls include `Authorization: Bearer <token>` header
7. Refresh tokens are JWT-based (7-day expiry), server-revocable via Redis when available
8. Username availability is checked in real-time via `/api/auth/check-username`

## Key Backend Modules

| Module | Purpose |
|--------|---------|
| `core/config.py` | Pydantic settings from env vars |
| `core/security.py` | Password hashing (Argon2/bcrypt), JWT creation |
| `core/tokens.py` | Async token creation/verification wrappers |
| `core/storage_abstraction.py` | Path validation, user storage management |
| `auth/router.py` | Auth endpoints (sync def for register/login, async for refresh/logout/me/check-username) |
| `auth/service.py` | Registration, login, token refresh, logout business logic |
| `auth/tokens.py` | Refresh token management (Redis-backed + JWT-only fallback) |
| `services/user_service.py` | User CRUD, serialization |
| `services/health_service.py` | Database readiness check |
| `services/memory_manager.py` | Central memory system manager |

## Database

- **Engine**: SQLite via SQLAlchemy
- **Migrations**: Alembic (`migrations/versions/`)
- **Active tables**: `users`, `auth_events`, `knowledge_entries`, `user_storage_registry`, `alembic_version`
- **User columns**: id, username, full_name, hashed_password, role, nickname, bio, description, profile_photo, handles_json, vault_password_hash, preferences_json, github_username, github_token_encrypted
- **Init**: `bootstrap_database()` runs on app startup (runs Alembic migrations)

## API Endpoints (All Verified Working)

| Category | Endpoints | Auth |
|----------|-----------|------|
| Root | `GET /` | None |
| Auth | `POST /api/auth/register`, `/login`, `/refresh`, `/logout` | None |
| Auth (me) | `GET /api/auth/me`, `PUT /api/auth/me` | Required |
| Auth (check) | `POST /api/auth/check-username` | None |
| Memory | `GET /api/memory`, `POST /api/memory` | Optional |
| Health | `GET /api/v1/health/live`, `/ready`, `/deep` | None |
| Profile | `GET/PUT /api/v1/me/profile`, `POST /photo`, `GET/DELETE /photo` | Required |
| Profile (public) | `GET /api/v1/me/profile/photo/{user_id}` | None |
| Users | `GET/PUT/DELETE /api/v1/users/{id}`, `POST /promote`, `/demote` | Admin |
| GitHub | `GET/POST/DELETE /api/v1/me/github` | Required |

## Configuration

All config via environment variables (or `.env` file):

| Variable | Default | Purpose |
|----------|---------|---------|
| `SECRET_KEY` | (empty) | JWT signing key |
| `ALGORITHM` | HS256 | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 30 | Access token expiry |
| `DATABASE_URL` | (computed) | SQLite path |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis for refresh tokens |
| `APP_NAME` | Cortex Workspace | Application name |
| `DEBUG` | False | Debug mode |
| `API_V1_PREFIX` | /api/v1 | Versioned API prefix |
| `NEXT_PUBLIC_API_BASE_URL` | (none) | Backend URL for frontend proxy |

## Running

```bash
# Backend
uv run uvicorn backend.app.main:app --reload --port 8000

# Frontend
cd frontend && npm install && npm run dev

# Docker
./scripts/docker-run.sh
```

## Application Lifecycle

- **Startup**: Ensures system dirs → runs Alembic migrations → pings Redis (graceful fallback) → initializes DB engine
- **Request Handling**: RequestLoggingMiddleware logs method/path/status/duration; DB sessions provided per-request via dependency
- **Shutdown**: Closes Redis connection

## Safety Model

- No root required for normal operation
- Docker containers run as a non-root user
- Path access is restricted by storage abstraction
- Rate limiting on login (Redis-backed, fail-open)
- Admin self-protection (cannot demote yourself)
- Profile photos validated server-side (type, size limits)
- GitHub tokens encrypted with Fernet (derived from SECRET_KEY)
- Real-time username availability checking

## Developer Onboarding

- **Backend**: `uv run uvicorn backend.app.main:app --reload --port 8000`
- **Frontend**: `cd frontend && npm install && npm run dev`
- **Tests**: `uv run pytest`
- **Deployment**: Use docker-compose; configure SECRET_KEY and related env vars
