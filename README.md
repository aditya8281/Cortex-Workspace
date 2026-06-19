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

**Identity + Secure Storage (Phase 1)** — Complete

- Multi-user authentication with JWT and refresh tokens
- Encrypted private vault per user (separate password)
- Profile management and GitHub account linking
- Admin user management
- Shared memory layer scaffolding (PostgreSQL + filesystem ready)

**Neural Dark Frontend Redesign** — Complete

- Spring-physics animations (framer-motion)
- 3D effects (Three.js / React Three Fiber)
- Command palette (⌘K via cmdk)
- Adaptive layout with glass morphism
- Toast notifications (sonner), Radix UI primitives

**Auth Wiring** — Complete

- Cookie-based authentication (httpOnly cookies, no client-side token storage)
- Automatic token refresh with reuse detection
- API proxy with cookie forwarding

**CLI** — Scaffolded

- Command stubs for all operations (init, install, build, start, dev, setup, doctor, stop, logs, migrate, backup, status, registry, deploy, update)

**Machine Understanding (Phase 2)** — Not started

AI memory, embeddings, repository indexing, knowledge graphs, and agent orchestration are **planned but not yet implemented**.

| Area | State |
|------|-------|
| Tests | 115 (backend 106, frontend 9) |
| Frontend build | Passes |
| Linting | ruff + ESLint configured |
| Auth + vault backend | Production-quality foundation |
| Vault UI | Full file browser with table/list/grid views |
| Neural Dark redesign | Complete |
| CLI | Scaffolded (command stubs) |
| CortexMemory AI dirs | Empty scaffolding |

**Known gaps:**
- Registration hardcodes `~/CortexData` — no storage picker UI
- Landing page describes AI features not yet built
- CLI commands are stubs, not yet implemented
- Frontend tests are minimal (9 tests across 3 files)

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

### CLI (Scaffolded)

| Feature | Status |
|---------|--------|
| Command stubs (15 commands) | ✅ |
| Command implementations | ⏳ |

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
                       │ httpOnly Cookies (auto-forwarded)
┌──────────────────────▼─────────────────────────┐
│  Backend (FastAPI)    http://localhost:8000    │
│  - Auth, Vault, Memory, Storage                │
└─────────────┬───────────────────────┬──────────┘
              │                       │
         ┌────▼────┐            ┌────▼─────┐
         │PostgreSQL│            │  Redis   │
         │   16     │            │  (opt)   │
         └──────────┘            └──────────┘

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
| Backend | FastAPI, Python 3.10+ |
| Database | PostgreSQL 16 (SQLite in tests only) |
| ORM | SQLAlchemy 2.0 + Alembic |
| Cache | Redis 7 (optional, graceful fallback) |
| Auth | JWT + Argon2 (cookie-based) |
| Encryption | Fernet + PBKDF2 (vault), Fernet (GitHub token) |
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

**`knowledge_entries`** — Simple text memory records (not vector embeddings).

**`user_storage_registry`** — One row per user: filesystem path pointer.

### API Structure

Base URL: `http://localhost:8000`

| Route | Purpose |
|-------|---------|
| `/api/auth/*` | Register, login, refresh, logout, check-username |
| `/api/memory` | List/create knowledge entries (paginated) |
| `/api/v1/health/*` | live, ready, deep |
| `/api/v1/users/*` | Admin: list, get, update, delete, promote, demote |
| `/api/v1/me/profile` | GET/PUT profile, photo upload/delete |
| `/api/v1/me/github` | GET/POST/DELETE GitHub connection |
| `/api/v1/me/vault/*` | lock/unlock, files CRUD, search |

Interactive docs: `http://localhost:8000/docs`

### Auth Flow

1. **Register/Login** → backend sets httpOnly cookies (access + refresh tokens)
2. **Requests** → cookies sent automatically, resolved by JWT middleware
3. **Refresh** → automatic rotation with reuse detection (Redis)
4. **Logout** → revoke refresh token, lock vault

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
| `DATABASE_URL` | `postgresql://cortex:cortex@localhost:5432/cortex` | App database |
| `REDIS_URL` | `redis://localhost:6379/0` | Token store / rate limit |
| `CORTEX_ROOT` | `ProjectRoot/CortexMemory` | System storage root |
| `NEXT_PUBLIC_API_BASE_URL` | — | Frontend → backend URL |

---

## Installation

**Prerequisites:** Python 3.10+, [uv](https://github.com/astral-sh/uv), Node.js 24+, Docker (optional).

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
make test          # 106 pytest tests (backend)
make lint          # ruff + mypy
make format        # black + ruff --fix
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
pg_dump -h localhost -p 5432 -U cortex -d cortex > backup_$(date +%Y%m%d).sql

# With compression
pg_dump -h localhost -p 5432 -U cortex -d cortex | gzip > backup_$(date +%Y%m%d).sql.gz
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
psql -h localhost -p 5432 -U cortex -d cortex < backup.sql
gunzip -c backup.sql.gz | psql -h localhost -p 5432 -U cortex -d cortex

# After restore, run migrations to catch up:
make migrate
```

---

## Project Structure

```
Cortex-Workspace/
├── backend/app/
│   ├── main.py          # Entry point, lifespan, CORS, routers
│   ├── core/            # Config, security, paths, storage, Redis, middleware
│   ├── auth/            # Register/login/refresh/logout, tokens, rate limit, audit
│   ├── db/              # Bootstrap, session factory
│   ├── models/          # User, AuthEvent, StorageRegistry ORM
│   ├── schemas/         # Pydantic request/response models
│   ├── services/        # user, vault, memory_manager, storage_registry, health
│   ├── intelligence/    # KnowledgeEntry model only
│   └── api/             # Routers: auth, memory, v1
├── frontend/
│   ├── app/             # Next.js pages (App Router)
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
├── tests/               # 106 pytest tests (SQLite)
├── scripts/             # Docker helpers
├── docker-compose.yml   # PostgreSQL + Redis
├── start.sh             # Local dev with embedded PG
├── CortexMemory/        # Created at runtime (gitignored)
├── AGENTS.md            # Agent instructions
└── DESIGN.md            # Design system
```

---

## Documentation

| Document | Audience | Contents |
|----------|----------|----------|
| [README.md](./README.md) | Everyone | Overview, setup, architecture, reference |
| [AGENTS.md](./AGENTS.md) | AI Agents | Agent behavior and workflow rules |
| [DESIGN.md](./DESIGN.md) | Designers | Design system, tokens, components |
| [.agents/prerequisite.md](./.agents/prerequisite.md) | Developers | Repository alignment requirements |

---

## Roadmap

**Phase 1 — Complete:** Identity, secure storage, Neural Dark UI, cookie-based auth, CLI scaffolding.

1. **Storage boundary fixes** — user-chosen storage in UI; profile assets under `<storage_root>/profile/`
2. **CLI implementation** — flesh out command stubs into working commands
3. **Frontend test coverage** — expand from 9 to full page/component coverage
4. **CortexMemory pipeline** — repository indexing, chunking, embeddings, vector store
5. **RAG + retrieval API** — query over indexed knowledge (not vault)
6. **Model routing** — local (Ollama) + optional cloud providers
7. **Agent / workflow engine** — task queue, WebSocket chat, orchestration
8. **CRTX portability** — encrypted portable user archives (`.crtx` export/import)
9. **Desktop packaging** — SQLite fallback, Tauri/Electron shell
10. **Production ops** — TLS, metrics, backups, security scanning

**Prerequisites:** See [`.agents/prerequisite.md`](./.agents/prerequisite.md) for required repository alignment work before Phase 2.

---

## CI/CD

GitHub Actions on push/PR to `main`/`develop`:

- **Backend:** ruff, mypy (advisory — `continue-on-error: true`), pytest with PostgreSQL + Redis
- **Frontend:** next lint (advisory — `continue-on-error: true`), tsc (advisory — `continue-on-error: true`), production build

---

## License

MIT
