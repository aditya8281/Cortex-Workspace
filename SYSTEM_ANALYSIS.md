# Cortex Workspace — System Architecture

> Last updated: 2026-06-07

## Overview

Cortex is a local-first AI assistant platform with a FastAPI backend, Next.js frontend, and SQLite database. It provides multi-agent orchestration, intelligent memory, workspace synchronization, and a secure user vault system.

## Architecture

```
Client (Next.js :3000) ──► FastAPI Backend (:8000) ──► SQLite + Redis
```

- **Frontend**: Next.js 15 App Router, React 19, Tailwind CSS
- **Backend**: FastAPI (Python 3.12+), SQLAlchemy ORM, Alembic migrations
- **Storage**: SQLite database, Redis cache, on-disk user vaults

## Backend Structure

```
backend/app/
├── main.py                  # FastAPI app entry point, lifespan, CORS, middleware
├── core/                    # Infrastructure: config, security, storage, DB, Redis
├── auth/                    # Authentication: JWT, refresh tokens, rate limiting
├── db/                      # Database engine, session, bootstrap, base model
├── models/                  # SQLAlchemy ORM models
├── schemas/                 # Pydantic request/response schemas
├── services/                # Business logic layer
├── api/                     # API routes (v1 prefix)
│   ├── router.py            # Aggregates all v1 sub-routers
│   └── v1/                  # Individual endpoint modules
├── ai/                      # LLM gateway, model registry, providers
├── executor/                # Task execution: graph, workflow engine, tools
├── agent/                   # Multi-agent orchestration
├── intelligence/            # File sync, memory, observer services
├── tools/                   # Built-in tool definitions
└── state/                   # Runtime state management
```

## Frontend Structure

```
frontend/
├── app/
│   ├── layout.js            # Root layout (fonts, AuthProvider)
│   ├── page.js              # Landing page (/)
│   ├── globals.css          # Global styles
│   ├── auth/page.js         # Auth page — login + register tabs (/auth)
│   ├── app/page.js          # Dashboard — protected (/app)
│   └── api/auth/            # Next.js proxy routes to backend
├── src/shared/
│   ├── auth/                # AuthProvider, session, cortexApi
│   ├── ui/                  # Button, Input, Card
│   ├── layout/              # DashboardShell
│   └── design/              # Design tokens
```

## Auth Flow

1. User submits credentials on `/auth`
2. Frontend calls `apiLogin`/`apiRegister` → backend `/api/auth/login` or `/api/auth/register`
3. Backend validates, creates user, returns JWT + user object
4. Frontend stores token in sessionStorage via `AuthProvider`
5. All subsequent API calls include `Authorization: Bearer <token>` header

## Key Backend Modules

| Module | Purpose |
|--------|---------|
| `core/config.py` | Pydantic settings from env vars |
| `core/security.py` | Password hashing (Argon2/bcrypt), JWT creation |
| `core/tokens.py` | Async token creation/verification wrappers |
| `core/storage_abstraction.py` | Path validation, user storage management |
| `auth/service.py` | Registration, login, token refresh, logout |
| `auth/tokens.py` | Refresh token management (Redis-backed) |
| `services/user_service.py` | User CRUD, serialization |
| `services/storage_registry.py` | Per-user storage path registry |
| `ai/gateway.py` | LLM request routing |
| `executor/executor.py` | Task execution engine |

## Database

- **Engine**: SQLite via SQLAlchemy
- **Migrations**: Alembic (`migrations/versions/`)
- **Key tables**: `users`, `user_storage_registry`, `user_settings`, `user_profiles`, `context_items`, `memories`
- **Init**: `bootstrap_database()` runs on app startup

## Configuration

All config via environment variables (or `.env` file):

| Variable | Default | Purpose |
|----------|---------|---------|
| `SECRET_KEY` | (empty) | JWT signing key |
| `DATABASE_URL` | (computed) | SQLite path |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis for refresh tokens |
| `AI_MODE` | `local` | AI backend mode |
| `OLLAMA_URL` | `http://localhost:11434` | Local Ollama endpoint |

## Running

```bash
# Backend
cd backend && uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend && npm run dev

# Docker
docker-compose up
```
