# Cortex Workspace — Project Context

Last updated: 2026-06-18

## Executive Summary

A local-first workspace with secure authentication, a central memory system, and a clean foundation for future AI features. All endpoints verified working.

## Technology Stack

- **Backend**: FastAPI, SQLAlchemy, Alembic, Pydantic v2, Uvicorn
- **Database**: SQLite (file-based), Alembic migrations
- **Cache**: Redis (optional, graceful fallback)
- **Frontend**: Next.js 15, React 19, Tailwind CSS
- **Packaging**: pyproject (uv), Docker & docker-compose
- **Auth**: JWT (access + refresh tokens), Argon2 password hashing, Redis-backed rate limiting
- **Encryption**: Fernet (cryptography) for GitHub token storage

## Repository Structure

### Backend

```
backend/app/
├── main.py                  # App entry point, lifespan, CORS, middleware
├── core/                    # Infrastructure
│   ├── config.py            # Pydantic settings
│   ├── security.py          # Password hashing, JWT
│   ├── tokens.py            # Token creation/verification
│   ├── db.py                # DB session dependency
│   ├── redis.py             # Redis client (async, graceful)
│   ├── middleware.py         # Request logging middleware
│   ├── logging.py           # Buffered log handler
│   ├── paths.py             # Project root
│   ├── system_paths.py      # System directory management
│   ├── storage_abstraction.py # Path validation
│   └── storage_manager.py   # Storage path wrapper
├── auth/                    # Authentication system
│   ├── router.py            # Auth endpoints (register, login, refresh, logout, me, check-username)
│   ├── service.py           # Auth business logic
│   ├── tokens.py            # Refresh token management (Redis + JWT fallback)
│   ├── rate_limit.py        # Login rate limiting (Redis, fail-open)
│   ├── audit.py             # Auth event logging
│   ├── dependencies.py      # require_admin, require_role
│   └── __init__.py
├── db/                      # Database layer
│   ├── bootstrap.py         # Engine init, migrations, session factory
│   ├── base.py              # DeclarativeBase
│   └── session.py           # DynamicSessionLocal
├── models/                  # SQLAlchemy models
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
    └── models.py            # KnowledgeEntry (memory data model)
```

### Frontend

```
frontend/
├── app/
│   ├── layout.js            # Root layout (fonts, AuthProvider)
│   ├── page.js              # Landing page (/)
│   ├── globals.css          # Tailwind base styles
│   ├── auth/page.js         # Multi-step registration wizard + login (/auth)
│   ├── app/page.js          # Dashboard (/app)
│   ├── admin/page.js        # Admin dashboard — user management (/admin)
│   ├── profile/page.js      # Profile page — avatar, GitHub, settings (/profile)
│   └── api/[...path]/       # Catch-all proxy to backend (binary-safe)
├── src/shared/
│   ├── auth/                # AuthProvider, session.js, cortexApi.js
│   ├── ui/                  # Button, Input, Card, Steps, PasswordStrength
│   ├── layout/              # DashboardShell
│   └── design/              # Design tokens
└── package.json
```

## Application Lifecycle

1. **Startup**: Ensures system dirs → runs Alembic migrations → pings Redis → yields
2. **Request**: Middleware logs method/path/status/duration → DB session via dependency → JWT user resolution
3. **Shutdown**: Closes Redis connection

## Core Functional Areas

### 1. Authentication

- Endpoints: `/api/auth/*` (register, login, refresh, logout, me, check-username)
- JWT access tokens with configurable expiry (default 30 min)
- Refresh tokens: JWT-based (7-day default), server-revocable via Redis when available
- Rate limiting on login (Redis-backed, fails open)
- First user auto-promoted to admin
- Sync endpoints (register/login) run in FastAPI threadpool to avoid event loop blocking
- Real-time username availability checking via `/api/auth/check-username`

### 2. Central Memory System

- Endpoints: `GET/POST /api/memory`
- Data model: `KnowledgeEntry` in `knowledge_entries` table
- Fields: user_id, category, title, content, source_path, source_key
- User-scoped: authenticated users see their entries + global entries
- Category counts returned with listings

### 3. Profile

- Endpoints: `GET/PUT /api/v1/me/profile`
- Editable fields: full_name, nickname, bio, description
- Profile photo: upload (JPEG/PNG/WebP, max 2MB), auto-resized to 256×256 + 64×64 thumbnail
- Photo served as public endpoint for `<img>` tags

### 4. Admin User Management

- Endpoints: `/api/v1/users/*` (list, get, update, delete, promote, demote)
- Requires admin role
- Self-protection: admins cannot demote themselves
- Role changes via direct update are blocked (must use promote/demote)

### 5. GitHub Integration

- Endpoints: `GET/POST/DELETE /api/v1/me/github`
- Connect GitHub account with username + personal access token
- Token encrypted with Fernet (derived from SECRET_KEY) before storage
- Username uniqueness enforced across accounts
- Connection status visible in profile page

## Data Model

### users
- id, username (unique), full_name, hashed_password, role
- nickname, bio, description, profile_photo
- handles_json (→ handles property), vault_password_hash, preferences_json (→ preferences property)
- github_username (unique), github_token_encrypted

### auth_events
- id, user_id, ip_address, timestamp, event_type, metadata_json

### knowledge_entries
- id, user_id, category, title, content, source_path, source_key
- created_at, updated_at

### user_storage_registry
- id, user_id, storage_root, created_at, updated_at

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

Settings loaded from environment / `.env` via Pydantic BaseSettings:

- `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`
- `DATABASE_URL`, `REDIS_URL`
- `APP_NAME`, `DEBUG`, `API_V1_PREFIX`
- `CORTEX_ROOT`, `MEMORY_PATH`, `VAULT_PATH`
- `WORKSPACE_ROOT`
- `NEXT_PUBLIC_API_BASE_URL` (frontend proxy backend URL)

## Testing

```bash
uv run pytest
```

18 tests covering:
- Auth flows (register, login, me, vault password update, duplicate user, refresh, logout)
- Smoke tests (root, health, memory, register, login, me, profile, unauthenticated access)
