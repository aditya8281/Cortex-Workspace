# Cortex

**A machine intelligence layer that gives a computer its own brain.**

Cortex is not a chatbot. Cortex is not primarily a RAG platform. Cortex is not primarily a repository assistant.

Cortex is intended to become a system where users ask questions **without knowing exact filenames or locations**, because **Cortex continuously understands the machine**.

---

## The Vision

A user should eventually be able to ask Cortex:

> Find a file that explains attention mechanisms.
>
> Find the repository handling authentication.
>
> Tell me where this project is located.
>
> Explain this codebase.
>
> Summarize what changed on this machine.
>
> Open a document related to this topic.
>
> Execute a development task.

**Without knowing exact filenames or locations.**
**Cortex should know because it continuously understands the machine.**

### Mental Model: Cortex as a Friend

Think of Cortex as a person — a friend to its users.

- **Cortex has its own brain** (`CortexMemory/`) — shared understanding of the system
- **Users have private storage** — their vault, settings, chat history
- **Vaults are secrets** — never automatically indexed, embedded, or added to shared memory
- **All users benefit from shared knowledge** — without exposing private data

---

## Current Status

**Phase 1 (Identity + Secure Storage + Neural Dark UI)** — Complete

- Multi-user authentication with JWT and refresh tokens
- Encrypted private vault per user (separate password)
- Profile management and GitHub account linking
- Admin user management
- Shared memory layer scaffolding (PostgreSQL + filesystem ready)
- Spring-physics animations, 3D effects, command palette, glass morphism UI
- Cookie-based authentication with automatic refresh

**Prerequisites (Repository Alignment)** — Complete

- Vector database (Qdrant), Embedding service (ONNX/BGE-M3), Task queue (arq)
- WebSocket endpoint, Global rate limiting, Soft delete + restore
- JWT in httpOnly cookies, CSP headers, TLS configuration
- Structured logging + correlation IDs, Metrics endpoint, Backup strategy
- Frontend test framework (Vitest)

**Security Audit** — P0/P1 fixes applied

- Memory API requires authentication
- Vault path traversal blocked
- Token expiry reduced to 30 minutes
- CSRF, CORS, WebSocket security tightened
- Foreign key constraints added to repo models

**Phase 2 (Memory & Indexing)** — Ready to start

AI memory, embeddings, repository indexing, knowledge graphs, and agent orchestration are **next in line**.

| Area | State |
|------|-------|
| Tests | 156 (backend 147, frontend 9) |
| Frontend build | Passes |
| Linting | ruff + ESLint + mypy — all clean |
| Auth + vault backend | Production-quality foundation |
| Vault UI | Full file browser with table/list/grid views |
| Neural Dark redesign | Complete |
| CLI | Scaffolded (command stubs) |
| CortexMemory AI dirs | Empty scaffolding |

---

## Features

### Phase 1: Identity + Secure Storage (Implemented)

| Feature | Status |
|---------|--------|
| Multi-user authentication (register, login, logout) | ✅ |
| JWT with automatic refresh token rotation | ✅ |
| Cookie-based auth (httpOnly, automatic refresh) | ✅ |
| Encrypted vault with separate password | ✅ |
| User profile + avatar upload | ✅ |
| GitHub account linking | ✅ |
| Rate limiting on auth endpoints | ✅ |
| Audit logging (auth events) | ✅ |
| Admin user management | ✅ |
| Health checks + CI tests | ✅ |

### Neural Dark Redesign (Implemented)

| Feature | Status |
|---------|--------|
| Spring-physics animations (framer-motion) | ✅ |
| 3D effects (Three.js / React Three Fiber) | ✅ |
| Command palette (⌘K via cmdk) | ✅ |
| Glass morphism UI | ✅ |
| Adaptive layout (DashboardShell) | ✅ |
| Toast notifications (sonner) | ✅ |
| Radix UI primitives (dialog, dropdown, tooltip) | ✅ |
| Page transitions + stagger animations | ✅ |

### Security (Implemented)

| Feature | Status |
|---------|--------|
| Memory API requires authentication | ✅ |
| Vault path traversal protection | ✅ |
| Access token 30-minute expiry (auto-refreshed while logged in) | ✅ |
| CSRF double-submit protection | ✅ |
| CORS restricted to explicit origins | ✅ |
| WebSocket authentication | ✅ |
| Foreign key constraints on all relations | ✅ |
| Request ID correlation (contextvars) | ✅ |
| Health check returns 503 when degraded | ✅ |

### CLI (Scaffolded)

| Feature | Status |
|---------|--------|
| Command stubs (15 commands) | ✅ |
| Command implementations | ⏳ |

### Phase 2 Foundations (Implemented)

| Feature | Status |
|---------|--------|
| Vector database (Qdrant) | ✅ |
| Embedding service (ONNX/BGE-M3) | ✅ |
| Task queue (arq) | ✅ |
| WebSocket endpoint | ✅ |
| Global rate limiting | ✅ |
| Soft delete + restore | ✅ |
| JWT in httpOnly cookies | ✅ |
| CSP headers | ✅ |
| TLS configuration | ✅ |
| Structured logging + correlation IDs | ✅ |
| Metrics endpoint | ✅ |
| Backup strategy | ✅ |
| Frontend test framework (Vitest) | ✅ |

### Phase 2+: Machine Understanding (Planned)

| Feature | Status |
|---------|--------|
| Repository parsing and indexing | ⏳ |
| Embedding generation (code, documents) | ⏳ |
| Knowledge graph construction | ⏳ |
| Natural language queries | ⏳ |
| Answer generation from Cortex memory | ⏳ |
| Development task execution | ⏳ |
| Multi-agent orchestration | ⏳ |

---

## Technical Reference

### Architecture

```text
┌────────────────────────────────────────────────┐
│  Frontend (Next.js 15)  http://localhost:3000  │
│  - Auth, Profile, Vault, Admin Dashboard       │
│  - Neural Dark UI, Command Palette (⌘K)        │
└──────────────────────┬─────────────────────────┘
                       │ Direct requests to backend (CORS)
┌──────────────────────▼─────────────────────────┐
│  Backend (FastAPI)    http://localhost:8000    │
│  - Auth, Vault, Memory, Storage                │
└──────┬───────────────────────────┬─────────────┘
       │                           │
  ┌────▼────┐  ┌──────────┐  ┌────▼─────┐
  │PostgreSQL│  │  Qdrant  │  │  Redis   │
  │   16     │  │ (vectors)│  │  (opt)   │
  └──────────┘  └──────────┘  └──────────┘

Filesystem:
  CortexMemory/     <- Shared brain (embeddings, indexes, knowledge)
  <storage_root>/   <- Per-user data (vault, profile, workspace)
```

**Key design:** User data lives outside `CortexMemory/`. Cortex stores only a pointer. Vaults are encrypted.

### Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 15, React 19, TypeScript, Tailwind CSS |
| Frontend UI | framer-motion, Radix UI, cmdk, sonner, Three.js, React Three Fiber |
| Backend | FastAPI, Python 3.12+ |
| Database | PostgreSQL 16 (SQLite in tests only) |
| ORM | SQLAlchemy 2.0 + Alembic |
| Cache | Redis 7 (optional, graceful fallback) |
| Auth | JWT + Argon2 (cookie-based) |
| Encryption | Fernet + PBKDF2 (vault), Fernet (GitHub token) |
| Vector DB | Qdrant (embedded) |
| Embeddings | ONNX Runtime (BGE-M3) |
| Task Queue | arq (Redis-based) |
| CLI | TypeScript, Commander.js |

### Storage Architecture

**Shared:** `CortexMemory/` (project root by default)

```
CortexMemory/
├── logs/
├── cache/
├── runtime/
├── memory/              # AI category folders (scaffolding only)
│   ├── embeddings/
│   ├── vector_db/
│   ├── graph/
│   └── ...
└── postgres/            # Local PG cluster (start.sh, port 5435)
```

Override root with `CORTEX_ROOT` env var.

**Per-user storage (`<storage_root>/`):**

```
<storage_root>/
├── profile/             # Avatar photos
├── vault/               # Encrypted files (PBKDF2 + Fernet)
├── workspace/
├── exports/
└── memory_snapshots/
```

### Database Schema

**`users`** — Account auth, profile, GitHub link, vault state, JSON preferences.

**`auth_events`** — Audit log: user_id, IP, timestamp, event_type, metadata.

**`knowledge_entries`** — Text memory records with vector embeddings.

**`user_storage_registry`** — One row per user: filesystem path pointer.

**`repo_indexes`** — Repository metadata (FK to users).

**`code_chunks`** — Indexed code with embeddings (FK to repo_indexes).

### API Structure

Base URL: `http://localhost:8000`

| Route | Purpose | Auth |
|-------|---------|------|
| `/api/auth/*` | Register, login, refresh, logout, check-username | Varies |
| `/api/memory` | List/create/search knowledge entries | Required |
| `/api/v1/health/*` | live, ready, deep | None |
| `/api/v1/users/*` | Admin: list, get, update, delete, promote, demote | Admin |
| `/api/v1/me/profile` | GET/PUT profile, photo upload/delete | Required |
| `/api/v1/me/github` | GET/POST/DELETE GitHub connection | Required |
| `/api/v1/me/vault/*` | lock/unlock, files CRUD, search | Required |
| `/api/v1/metrics` | Prometheus-style metrics | None |
| `/ws` | WebSocket echo endpoint | None |

Interactive docs: `http://localhost:8000/docs`

### Auth Flow

1. **Register/Login** → backend sets httpOnly cookies (`cortex_access` + `cortex_refresh`)
2. **Requests** → frontend sends requests to `/api/*` which are proxied to the backend by Next.js. Cookies are forwarded through the proxy and sent automatically.
3. **Refresh** → when the access token expires (after 30 min by default), the frontend automatically requests a new access token using the refresh token. No user interaction needed.
4. **Logout** → revoke refresh token, lock vault, clear cookies

**Token Expiry Behavior:**
- **Access token** expires after 30 minutes (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`). The access token is automatically refreshed by the frontend — the user does not need to log in again.
- **Refresh token** expires after 7 days. Once the refresh token expires, the user must log in again.
- **Access tokens only become invalid when the user logs out or the refresh token expires.** During normal use, the session persists indefinitely through automatic token rotation.

**How automatic refresh works:**
- When any API request returns a 401 (token expired), the frontend calls `POST /api/auth/refresh` with the refresh token cookie
- The backend rotates the refresh token (issues new access + refresh tokens, revokes the old ones)
- The original request is automatically retried with the new access token
- This happens transparently — the user sees no interruption

Two password model:
- **Login password** — account auth (Argon2 hash)
- **Vault password** — file encryption (separate hash; cached in memory after unlock)

First registered user is auto-promoted to `admin`.

### Frontend Routes

| Page | Route | Purpose |
|------|-------|---------|
| Landing | `/` | Marketing hero (SSR) + AuthRedirect |
| Auth | `/auth` | Login + 4-step registration wizard |
| Dashboard | `/app` | Quick overview and navigation hub |
| Profile | `/profile` | Avatar, fields, GitHub |
| Vault | `/vault` | Full file browser (table/list/grid) |
| Settings | `/settings` | Vault lock/unlock, account delete |
| Admin | `/admin` | User list, promote/demote/delete |
| Memory | `/memory` | Knowledge base viewer and creator |

**Global:** Command palette available via `⌘K` (or `Ctrl+K`) on any page.

### Configuration (`.env`)

| Variable | Default | Purpose |
|----------|---------|---------|
| `SECRET_KEY` | (empty) | JWT + Fernet derivation |
| `DATABASE_URL` | `postgresql://cortex:cortex@localhost:5435/cortex` | App database |
| `REDIS_URL` | `redis://localhost:6379/0` | Token store / rate limit |
| `CORTEX_ROOT` | `ProjectRoot/CortexMemory` | System storage root |
| `NEXT_PUBLIC_API_BASE_URL` | — | Optional: bypass proxy, hit backend directly (breaks cookie auth if not configured) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | JWT access token lifetime |

---

## Installation

**Prerequisites:** Python 3.12+, [uv](https://github.com/astral-sh/uv), Node.js 24+, Docker (optional).

```bash
git clone <repo-url> Cortex-Workspace
cd Cortex-Workspace

# Infrastructure (PostgreSQL + Redis)
docker compose up -d

# Environment
cp .env.example .env
# Edit .env — generate SECRET_KEY: openssl rand -hex 32

# Dependencies + migrations
make install
make migrate
```

**Port note:** Docker exposes PostgreSQL on **5432**. `.env.example` defaults to **5435** for use with `./start.sh` (embedded PostgreSQL under `CortexMemory/postgres/`).

---

## Running Locally

### Option A — Make (recommended)

```bash
make dev-full    # Backend :8000 + Frontend :3000
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API docs | http://localhost:8000/docs |

### Option B — All-in-one script

```bash
./start.sh
```

Starts embedded PostgreSQL (port 5435), runs migrations, launches backend and frontend. No Docker required if PostgreSQL binaries are installed.

### Option C — Separate terminals

```bash
make dev           # Backend only
make dev-frontend  # Frontend only
```

---

## Development

```bash
make install       # uv sync + npm install
make migrate       # alembic upgrade head
make test          # 156 tests (147 backend pytest + 9 frontend vitest)
make lint          # ruff + mypy
make format        # ruff format
make check         # lint + test
```

### Make targets

```bash
make dev            # Backend hot reload
make dev-frontend   # Frontend dev server
make dev-full       # Both
make db-shell       # psql
make db-reset       # Drop schema + remigrate
make db-backup      # pg_dump
make build-frontend # Production frontend build
```

---

## TLS/HTTPS (Production)

Configure TLS termination at the reverse proxy level.

### Caddy (Recommended)

```caddyfile
cortex.example.com {
    reverse_proxy localhost:8000
}
```

Caddy automatically provisions and renews Let's Encrypt certificates.

### nginx

```nginx
server {
    listen 443 ssl;
    server_name cortex.example.com;
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    location / { proxy_pass http://localhost:8000; }
}
```

### Development

For local HTTPS, generate a self-signed cert:

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout localhost.key -out localhost.crt \
  -subj "/CN=localhost"
```

---

## Backup

### PostgreSQL

```bash
# Daily backup
pg_dump -h localhost -p 5435 -U cortex -d cortex > backup_$(date +%Y%m%d).sql

# With compression
pg_dump -h localhost -p 5435 -U cortex -d cortex | gzip > backup_$(date +%Y%m%d).sql.gz
```

### CortexMemory (User Storage)

```bash
# Backup entire CortexMemory directory
tar -czf cortex_memory_$(date +%Y%m%d).tar.gz -C /path/to CortexMemory/

# Restore
tar -xzf cortex_memory_*.tar.gz -C /path/to/restore/
```

### Restore

```bash
# Database
psql -h localhost -p 5435 -U cortex -d cortex < backup.sql
gunzip -c backup.sql.gz | psql -h localhost -p 5435 -U cortex -d cortex

# After restore, run migrations to catch up:
make migrate
```

---

## Project Structure

```
Cortex-Workspace/
├── backend/app/
│   ├── main.py          # Entry point, lifespan, CORS, routers
│   ├── core/            # Config, security, paths, storage, Redis, middleware, vector_db, websocket, rate_limit
│   ├── auth/            # Register/login/refresh/logout, tokens, rate limit, audit
│   ├── db/              # Bootstrap, session factory
│   ├── models/          # User, AuthEvent, StorageRegistry, RepoIndex, CodeChunk ORM
│   ├── schemas/         # Pydantic request/response models
│   ├── services/        # user, vault, memory_manager, storage_registry, health, embedding_service, repo_scanner
│   ├── intelligence/    # KnowledgeEntry model
│   ├── tasks/           # arq worker, memory_tasks
│   └── api/             # Routers: auth, memory, metrics, v1
├── frontend/
│   ├── app/             # Next.js pages (App Router) with error.tsx boundaries
│   └── src/
│       ├── lib/         # motion.ts (spring physics), utils.ts
│       └── shared/
│           ├── auth/    # AuthProvider, cortexApi client, session
│           ├── design/  # Design tokens
│           ├── layout/  # DashboardShell (adaptive layout)
│           └── ui/      # Button, Card, CommandPalette, Modal, Toast, Tooltip, etc.
├── cli/
│   └── src/
│       ├── index.ts     # CLI entry point (Commander.js)
│       └── commands/    # init, install, build, start, dev, setup, doctor, etc.
├── migrations/          # Alembic revisions (PostgreSQL)
├── tests/               # 147 pytest tests (SQLite) + frontend tests
├── scripts/             # Docker helpers, backup
├── docker-compose.yml   # PostgreSQL + Redis + Qdrant
├── Dockerfile           # Multi-stage build (frontend + backend)
├── start.sh             # Local dev with embedded PG
├── CortexMemory/        # Created at runtime (gitignored)
├── AGENTS.md            # Agent instructions
├── DESIGN.md            # Design system
└── .agents/             # Agent skills and workflow definitions
```

---

## Documentation

| Document | Audience | Contents |
|----------|----------|----------|
| [README.md](./README.md) | Everyone | Overview, setup, architecture, reference |
| [AGENTS.md](./AGENTS.md) | AI Agents | Agent behavior and workflow rules |
| [DESIGN.md](./DESIGN.md) | Designers | Design system, tokens, components |
| `.agents/` | Developers | Agent skills, plans, and workflow definitions |

---

## Roadmap

**Phase 1 — Complete:** Identity, secure storage, Neural Dark UI, cookie-based auth, CLI scaffolding.

**Prerequisites — Complete:** Vector DB, embeddings, task queue, WebSocket, rate limiting, soft delete, JWT cookies, CSP, TLS, logging, metrics, backups, frontend tests.

**Security Audit — Complete:** P0/P1 fixes applied (auth enforcement, path traversal, token expiry, CSRF, CORS, FK constraints).

**Phase 2 (Memory & Indexing) — NEXT:**
1. **Repo scanner** — parse and index codebases
2. **Embeddings** — generate vector representations via ONNX/BGE-M3
3. **Vector search** — semantic search over indexed knowledge
4. **Knowledge graph** — construct and query relationships
5. **CLI implementation** — flesh out command stubs into working commands
6. **Frontend test coverage** — expand from 9 to full page/component coverage
7. **RAG + retrieval API** — query over indexed knowledge (not vault)
8. **Model routing** — local (Ollama) + optional cloud providers
9. **Agent / workflow engine** — task queue, WebSocket chat, orchestration
10. **CRTX portability** — encrypted portable user archives (`.crtx` export/import)
11. **Desktop packaging** — SQLite fallback, Tauri/Electron shell
12. **Production ops** — TLS, metrics, backups, security scanning

---

## CI/CD

GitHub Actions on push/PR to `main`/`develop`:

- **Backend:** ruff lint, ruff format, mypy type check, pytest with PostgreSQL + Redis
- **Frontend:** next lint, TypeScript check, vitest, production build

---

## License

MIT
