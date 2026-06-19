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

**Identity + Secure Storage (Phase 1)** ✅ Complete

- Multi-user authentication with JWT and refresh tokens
- Encrypted private vault per user (separate password)
- Profile management and GitHub account linking
- Admin user management
- Shared memory layer scaffolding (PostgreSQL + filesystem ready)

**Machine Understanding (Phase 2)** 🔄 In Development

AI memory, embeddings, repository indexing, knowledge graphs, and agent orchestration are **planned but not yet implemented**.

| Area | State |
|------|-------|
| Tests | 108/108 passing |
| Frontend build | Passes |
| Linting | ruff + ESLint configured |
| Auth + vault backend | Production-quality foundation |
| Vault UI | Full file browser with table/list/grid views |
| CortexMemory AI dirs | Empty scaffolding |

**Known gaps:**
- Registration hardcodes `~/CortexData` — no storage picker UI
- Landing page describes AI features not yet built

---

## Features

### Phase 1: Identity + Secure Storage (Implemented)

| Feature | Status |
|---------|--------|
| Multi-user authentication (register, login, logout) | ✅ |
| JWT with automatic refresh token rotation | ✅ |
| Encrypted vault with separate password | ✅ |
| User profile + avatar upload | ✅ |
| GitHub account linking | ✅ |
| Rate limiting on auth endpoints | ✅ |
| Audit logging (auth events) | ✅ |
| Admin user management | ✅ |
| Health checks + CI tests | ✅ |

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
└──────────────────────┬─────────────────────────┘
                       │ JWT Bearer Token
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
  CortexMemory/     ← Shared brain (embeddings, indexes, knowledge)
  <storage_root>/   ← Per-user data (vault, profile, workspace)
```

**Key design:** User data lives outside `CortexMemory/`. Cortex stores only a pointer. Vaults are encrypted.

### Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 15, React 19, TypeScript, Tailwind CSS |
| Backend | FastAPI, Python 3.10+ |
| Database | PostgreSQL 16 (SQLite in tests only) |
| ORM | SQLAlchemy 2.0 + Alembic |
| Cache | Redis 7 (optional, graceful fallback) |
| Auth | JWT + Argon2 |
| Encryption | Fernet + PBKDF2 (vault), Fernet (GitHub token) |

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
make test          # 108 pytest tests
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
│   └── src/shared/      # Auth, API client, UI components, design tokens
├── migrations/          # Alembic revisions (PostgreSQL)
├── tests/               # 81 pytest tests (SQLite)
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

1. **Storage boundary fixes** — user-chosen storage in UI; profile assets under `<storage_root>/profile/`
2. **Vault UI + session hardening** — file browser; refresh token flow; block unencrypted uploads
3. **CortexMemory pipeline** — repository indexing, chunking, embeddings, vector store
4. **RAG + retrieval API** — query over indexed knowledge (not vault)
5. **Model routing** — local (Ollama) + optional cloud providers
6. **Agent / workflow engine** — task queue, WebSocket chat, orchestration
7. **CRTX portability** — encrypted portable user archives (`.crtx` export/import)
8. **Desktop packaging** — SQLite fallback, Tauri/Electron shell
9. **Production ops** — TLS, metrics, backups, security scanning

**Prerequisites:** See [`.agents/prerequisite.md`](./.agents/prerequisite.md) for required repository alignment work before Phase 2.

---

## CI/CD

GitHub Actions on push/PR to `main`/`develop`:

- **Backend:** ruff, mypy (advisory — `continue-on-error: true`), pytest with PostgreSQL + Redis
- **Frontend:** next lint (advisory — `continue-on-error: true`), tsc (advisory — `continue-on-error: true`), production build

---

## License

MIT
