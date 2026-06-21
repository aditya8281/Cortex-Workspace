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
- Spring-physics animations, command palette, glass morphism UI
- Cookie-based authentication with automatic refresh
- Neural Dark redesign with OLED black backgrounds
- Neural Network canvas background on all pages
- Neural Pulse sidebar with pulsing active indicators and glow effects
- Folder picker abstraction (browser + Tauri-ready adapters)

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
- CSRF exemptions for authenticated API endpoints (vault, profile photo)
- IDOR vulnerabilities patched (ownership checks on all user-scoped resources)

**Phase 2 (Indexing & Knowledge Graph)** — Complete

- Incremental indexer (hash-based change detection)
- Knowledge graph (graph_nodes, graph_edges)
- File index tracking (indexed_files)
- Cross-file search (vector + graph enrichment)
- Unified search API
- Repository management API (CRUD + indexing triggers)
- Frontend: Search page with filters, results, graph view
- Background tasks: index_repo, build_graph

**Phase 3 (Unified Search & Agents)** — Complete

- Agent system (base agent, planner, executor)
- Agent run manager with step tracking
- Agent CRUD API + run/step/feedback API
- Frontend: Agent chat interface, Agents management page
- Navigation: sidebar + command palette integration

**Phase 4A (LLM Integration & Local Models)** — Partially Complete

- LLM manager with provider abstraction (llama.cpp, Ollama)
- Model catalog with providers, variants, capabilities, benchmarks
- Hardware detection and quantization recommendations
- Model download manager with progress tracking
- User model settings (persisted per-user)
- Model comparison endpoint
- Frontend: Models page with catalogue, installed models, download queue

**Phase 4B (Smart Indexing & Retrieval)** — Partially Complete

- Semantic chunker with language-aware splitting
- Indexing configuration (include/exclude paths, file types)
- Full-text search (PostgreSQL ts_vector)
- Hybrid retrieval (vector + keyword + graph)
- Document indexer for non-code files (markdown, PDF, notebooks, etc.)
- Retrieval quality metrics
- File watcher v2 with sync state persistence
- Batch indexer for bulk operations

**Phase 5 (Conversation & Context)** — Partially Complete

- Conversation model with message history and token tracking
- Conversation-to-memory pipeline (extract insights from chats)
- Long-term memory model with decay, confidence, and access tracking
- SSE streaming for real-time agent responses
- Conversation service with context building

**Phase 6 (Agent Intelligence)** — Partially Complete

- Agent SSE streaming
- Expanded tool registry
- RAG pipeline integration
- Entity extraction service
- Search clustering and recommendations

| Area | State |
|------|-------|
| Tests | 486+ passing (backend pytest + frontend vitest) |
| Frontend build | Passes |
| Linting | ruff + ESLint + mypy — all clean |
| Auth + vault backend | Production-quality foundation |
| Vault UI | Full file browser with table/list/grid views |
| Neural Dark redesign | Complete (OLED black, Neural Pulse sidebar) |
| CLI | Scaffolded (command stubs) |
| LLM Integration | llama.cpp + Ollama with provider abstraction |
| Model Catalog | Full catalogue with providers, variants, benchmarks |

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
| Command palette (⌘K via cmdk) | ✅ |
| Glass morphism UI | ✅ |
| Adaptive layout (DashboardShell) | ✅ |
| Toast notifications (sonner) | ✅ |
| Radix UI primitives (dialog, dropdown, tooltip) | ✅ |
| Page transitions + stagger animations | ✅ |
| OLED black backgrounds (#000000) | ✅ |
| Neural Network canvas background (all pages) | ✅ |
| Neural Pulse sidebar (pulsing dots, glow effects) | ✅ |
| Status bar (vault state + memory count) | ✅ |
| Folder picker abstraction (browser + Tauri) | ✅ |

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
| IDOR prevention (ownership checks on user-scoped resources) | ✅ |

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
| Code chunker (language detection, regex symbols) | ✅ |
| Repository scanner (walk, chunk, embed, store) | ✅ |
| Memory manager (CRUD + vector search) | ✅ |
| Task queue (arq) | ✅ |
| WebSocket endpoint | ✅ |
| Global rate limiting | ✅ |
| Soft delete + restore | ✅ |
| JWT in httpOnly cookies | ✅ |
| CSP headers | ✅ |
| Structured logging + correlation IDs | ✅ |
| Metrics endpoint | ✅ |
| Frontend test framework (Vitest) | ✅ |

### Phase 4A: LLM Integration & Local Models (Partial)

| Feature | Status |
|---------|--------|
| LLM manager with provider abstraction | ✅ |
| llama.cpp integration | ✅ |
| Ollama integration | ✅ |
| Model catalog (providers, variants, capabilities) | ✅ |
| Hardware detection (CPU/RAM/GPU) | ✅ |
| Quantization recommendations | ✅ |
| Model download manager | ✅ |
| User model settings (per-user persistence) | ✅ |
| Model comparison | ✅ |
| Frontend: Models page | ✅ |
| Model detail scraping | ✅ |
| Catalogue refresh from Ollama | ✅ |

### Phase 4B: Smart Indexing & Retrieval (Partial)

| Feature | Status |
|---------|--------|
| Semantic chunker | ✅ |
| Indexing configuration (include/exclude) | ✅ |
| Full-text search (ts_vector) | ✅ |
| Hybrid retrieval (vector + keyword) | ✅ |
| Document indexer (markdown, PDF, notebooks, etc.) | ✅ |
| Retrieval quality metrics | ✅ |
| File watcher v2 with sync state | ✅ |
| Batch indexer | ✅ |
| Path index tracking | ✅ |
| Deletion pipeline | ✅ |
| Search clustering | ✅ |

### Phase 5: Conversation & Context (Partial)

| Feature | Status |
|---------|--------|
| Conversation model + message history | ✅ |
| Conversation API (CRUD + SSE streaming) | ✅ |
| Conversation-to-memory pipeline | ✅ |
| Long-term memory (decay, confidence, access tracking) | ✅ |
| Long-term memory API | ✅ |
| Entity extraction | ✅ |
| Usage tracking | ✅ |

### Phase 6: Agent Intelligence (Partial)

| Feature | Status |
|---------|--------|
| Agent SSE streaming | ✅ |
| Expanded tool registry | ✅ |
| RAG pipeline | ✅ |
| Knowledge system health/stats | ✅ |
| Recommendation engine | ✅ |
| Threaded scanner | ✅ |

### UI Refactor (Implemented)

| Feature | Status |
|---------|--------|
| Warmer dark theme (#0a0a0f, #0ea5c9 accent) | ✅ |
| DashboardShell on all pages (Work/You nav groups) | ✅ |
| Dashboard with hero, MetricRing, tabbed content | ✅ |
| Conversational search (AI-first with citations) | ✅ |
| Hybrid agent chat with CollapsiblePanel | ✅ |
| Memory graph-first view with list toggle | ✅ |
| Glass panels, micro-interactions, organic animations | ✅ |
| MetricRing, TabGroup, CollapsiblePanel components | ✅ |
| Profile/Settings with hero headers | ✅ |
| System metrics with real-time processes | ✅ |
| Chat page (conversations UI) | ✅ |
| Models page (catalogue, installed, downloads) | ✅ |
| Downloads page (model download queue) | ✅ |

---

## Roadmap

### Upcoming Phases

| Phase | Name | Focus | Status |
|-------|------|-------|--------|
| 4A | LLM Integration & Local Models | Local LLM inference, model management, hardware detection | 🟡 Partial |
| 4B | Smart Indexing & Retrieval | Intelligent exclusion, file watching, hybrid retrieval | 🟡 Partial |
| 5 | Conversation & Context | Persistent chat, context builder, conversation history | 🟡 Partial |
| 6 | Agent Intelligence | Multi-step reasoning, tool chaining, workflows, SSE streaming | 🟡 Partial |
| 7 | Desktop Preparation | Service abstraction, filesystem abstraction, Tauri readiness | ⬜ Next |
| 8 | Learning Loop | Pattern recognition, correction tracking, proactive assistant | ⬜ |
| 9 | Observability & Monitoring | Dashboards, metrics, health monitoring | ⬜ |
| 10 | Production Hardening | Test coverage, security, performance, Docker, CI/CD | ⬜ |

---

## Technical Reference

### Architecture

```text
┌────────────────────────────────────────────────┐
│  Frontend (Next.js 15)  http://localhost:3000  │
│  - Auth, Profile, Vault, Memory, Admin         │
│  - Neural Dark UI, Neural Network background   │
│  - Neural Pulse sidebar, Command Palette (⌘K)  │
│  - Models, Chat, Downloads pages               │
└──────────────────────┬─────────────────────────┘
                       │ Direct requests to backend (CORS)
┌──────────────────────▼─────────────────────────┐
│  Backend (FastAPI)    http://localhost:8000    │
│  - Auth, Vault, Memory, Storage, Intelligence  │
│  - LLM Manager (llama.cpp, Ollama)            │
│  - Model Catalog, Conversations, Sync          │
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
| LLM | llama.cpp, Ollama (provider abstraction) |
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

**`knowledge_entries`** — Text memory records with vector embeddings, category, tags.

**`user_storage_registry`** — One row per user: filesystem path pointer.

**`repo_indexes`** — Repository metadata (FK to users), scan status, file/chunk counts.

**`code_chunks`** — Indexed code with embeddings (FK to repo_indexes), symbol info, language.

**`graph_nodes`** — Knowledge graph nodes (type, label, properties, embedding).

**`graph_edges`** — Knowledge graph edges (source_id, target_id, relation, weight).

**`indexed_files`** — File tracking for incremental indexing (path, hash, mtime, size).

**`notifications`** — System notifications for users.

**`agents`** — Agent definitions (name, description, config, is_active).

**`agent_runs`** — Agent execution history (status, task, result, metrics).

**`agent_steps`** — Individual steps within an agent run (action, input, output, duration_ms).

**`agent_feedback`** — User feedback on agent runs (rating, comment).

**`conversations`** — Conversation sessions (title, repo_id, model_used, token counts).

**`conversation_messages`** — Individual messages within conversations (role, content, tokens).

**`long_term_memories`** — Persistent memories with decay, confidence, access tracking, tags.

**`documents`** — Non-code knowledge files (markdown, PDF, notebooks, etc.) with type enum.

**`document_chunks`** — Chunked document content with embeddings.

**`model_catalog`** — LLM model metadata (family, provider, capabilities, benchmarks).

**`model_variants`** — Quantization variants per model (size, speed, quality tradeoffs).

**`model_downloads`** — Download tracking (status, progress, file path).

**`model_usage`** — Per-user model usage statistics.

**`providers`** — LLM providers (Ollama, llama.cpp, etc.).

**`provider_models`** — Models available per provider.

**`capabilities`** — Model capability tags (chat, code, vision, etc.).

**`quantizations`** — Quantization level definitions (Q4, Q8, FP16, etc.).

**`hardware_profiles`** — Detected hardware configurations.

**`sync_states`** — File watcher sync state per repo per user.

**`user_model_settings`** — Per-user model preferences (provider, model, context size, etc.).

**`indexing_configs`** — Indexing rules (include/exclude paths, file types).

**`embedding_cache`** — Cached embeddings to avoid recomputation.

### API Structure

Base URL: `http://localhost:8000`

| Route | Purpose | Auth |
|-------|---------|------|
| `/api/auth/*` | Register, login, refresh, logout, check-username | Varies |
| `/api/memory` | List/create/search knowledge entries | Required |
| `/api/memory/search` | Semantic search over memory | Required |
| `/api/memory/scan-repo` | Trigger repository scanning | Required |
| `/api/memory/bulk-embed` | Bulk embedding generation | Required |
| `/api/v1/health/*` | live, ready, deep | None |
| `/api/v1/users/*` | Admin: list, get, update, delete, promote, demote | Admin |
| `/api/v1/me/profile` | GET/PUT profile, photo upload/delete | Required |
| `/api/v1/me/github` | GET/POST/DELETE GitHub connection | Required |
| `/api/v1/me/vault/*` | lock/unlock, files CRUD, search | Required |
| `/api/v1/notifications` | List/read notifications | Required |
| `/api/v1/search` | Unified search across all data types | Required |
| `/api/v1/repos` | Repository CRUD + indexing + graph | Required |
| `/api/v1/agents` | Agent CRUD + runs + steps + feedback | Required |
| `/api/v1/models` | Model catalog, download, compare, settings | Required |
| `/api/v1/conversations` | Conversation CRUD + SSE streaming | Required |
| `/api/v1/long-term-memory` | Long-term memory CRUD + decay | Required |
| `/api/v1/knowledge` | Knowledge system health + stats | Required |
| `/api/v1/indexing` | Indexing config CRUD + preview | Required |
| `/api/v1/sync` | File watcher start/stop + validation | Required |
| `/api/v1/system/*` | System status, metrics | Varies |
| `/ws` | WebSocket echo + demo + system metrics | None |
| `/ws/models` | WebSocket for model download progress | None |
| `/ws/system` | WebSocket for system metrics stream | None |

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
| Search | `/search` | Unified search with filters, results, graph view |
| Agents | `/agents` | Agent management + chat interface |
| Chat | `/chat` | Conversation interface with SSE streaming |
| Models | `/models` | Model catalog, installed models, download queue |
| Downloads | `/downloads` | Active model downloads with progress |

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
| `LLM_PROVIDER` | `auto` | LLM provider: `auto`, `llama.cpp`, `ollama`, `none` |
| `LLM_MODEL_PATH` | — | Path to local GGUF model file |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `LLM_CONTEXT_SIZE` | `4096` | LLM context window size |
| `LLM_GPU_LAYERS` | `0` | GPU layers for llama.cpp |

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
make test          # 486+ tests (backend pytest + frontend vitest)
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
│   ├── core/            # Config, security, paths, storage, Redis, middleware, vector_db, websocket, rate_limit, csrf
│   ├── auth/            # Register/login/refresh/logout, tokens, rate limit, audit, dependencies
│   ├── db/              # Bootstrap, session factory
│   ├── models/          # ORM models (see below)
│   ├── schemas/         # Pydantic request/response models
│   ├── services/        # Business logic (see below)
│   ├── intelligence/    # KnowledgeEntry model
│   ├── agents/          # BaseAgent, PlannerAgent, ExecutorAgent, AgentRunManager
│   ├── tasks/           # arq worker, memory_tasks
│   └── api/             # Routers: auth, memory, metrics, deps, ws, v1/*
├── frontend/
│   ├── app/             # Next.js pages (App Router) with error.tsx boundaries
│   │   ├── search/      # Unified search page
│   │   ├── agents/      # Agent management + chat
│   │   ├── chat/        # Conversation interface
│   │   ├── models/      # Model catalog + downloads
│   │   └── downloads/   # Download queue
│   └── src/
│       ├── lib/         # utils.ts (cn helper)
│       └── shared/
│           ├── api/     # agent.ts, index.ts (API clients)
│           ├── auth/    # AuthProvider, cortexApi client, session
│           ├── design/  # Design tokens
│           ├── layout/  # DashboardShell (Neural Pulse sidebar)
│           ├── services/ # folder-picker (browser + Tauri adapters)
│           └── ui/      # Button, Card, CommandPalette, Modal, NeuralNetwork, Toast, Tooltip, etc.
├── cli/
│   └── src/
│       ├── index.ts     # CLI entry point (Commander.js)
│       └── commands/    # init, install, build, start, dev, setup, doctor, etc.
├── migrations/          # Alembic revisions (PostgreSQL, 25 migrations)
├── tests/               # 486+ pytest tests (SQLite) + frontend tests
├── scripts/             # Docker helpers, backup
├── docker-compose.yml   # PostgreSQL + Redis + Qdrant
├── Dockerfile           # Multi-stage build (frontend + backend)
├── start.sh             # Local dev with embedded PG
├── CortexMemory/        # Created at runtime (gitignored)
├── AGENTS.md            # Agent instructions
├── DESIGN.md            # Design system (Neural Dark + Neural Pulse)
├── README.md            # This file
└── .agents/             # Agent skills, plans, and workflow definitions
```

### Backend Models

| Model | File | Purpose |
|-------|------|---------|
| User, AuthEvent | `models/user.py`, `models/auth_event.py` | Auth + audit |
| StorageRegistry | `models/storage_registry.py` | Per-user storage paths |
| RepoIndex, CodeChunk | `models/repo_index.py` | Repository indexing |
| GraphNode, GraphEdge | `models/graph.py` | Knowledge graph |
| IndexedFile | `models/file_index.py` | Incremental indexing tracking |
| Notification | `models/notification.py` | System notifications |
| Agent, AgentRun, AgentStep, AgentFeedback | `models/agent.py` | Agent system |
| Conversation, ConversationMessage | `models/conversation.py` | Chat history |
| LongTermMemory | `models/long_term_memory.py` | Persistent memories with decay |
| Document, DocumentChunk | `models/document.py` | Non-code knowledge files |
| ModelCatalog, ModelVariant, ModelDownload, etc. | `models/model_catalog.py` | LLM model metadata |
| Provider, ProviderModel, Capability, Quantization | `models/model_catalog.py` | Provider + capability system |
| HardwareProfile | `models/model_catalog.py` | Hardware detection |
| SyncState | `models/sync_state.py` | File watcher state |
| UserModelSettings | `models/user_settings.py` | Per-user model preferences |
| IndexingConfig | `models/indexing_config.py` | Indexing rules |
| EmbeddingCache | `models/embedding_cache.py` | Cached embeddings |
| KnowledgeEntry | `intelligence/` | Text memory with embeddings |

### Backend Services

| Service | File | Purpose |
|---------|------|---------|
| embedding_service | `services/embedding_service.py` | ONNX/BGE-M3 embeddings |
| repo_scanner | `services/repo_scanner.py` | Repository walk + chunk + embed |
| chunker | `services/chunker.py` | Code chunking |
| semantic_chunker | `services/semantic_chunker.py` | Language-aware semantic chunking |
| memory_manager | `services/memory_manager.py` | Knowledge entry CRUD + search |
| graph_builder | `services/graph_builder.py` | Knowledge graph construction |
| cross_file_search | `services/cross_file_search.py` | Vector + graph search |
| incremental_indexer | `services/incremental_indexer.py` | Hash-based change detection |
| path_index | `services/path_index.py` | Path tracking for files |
| document_indexer | `services/document_indexer.py` | Non-code file indexing |
| indexing_orchestrator | `services/indexing_orchestrator.py` | Coordinates indexing pipeline |
| batch_indexer | `services/batch_indexer.py` | Bulk indexing operations |
| file_watcher_v2 | `services/file_watcher_v2.py` | File system watcher |
| sync_service | `services/sync_service.py` | Sync state management |
| llm/manager | `services/llm/manager.py` | LLM provider abstraction |
| llm/llama_cpp | `services/llm/llama_cpp.py` | llama.cpp provider |
| llm/ollama | `services/llm/ollama.py` | Ollama provider |
| model_downloader | `services/model_downloader.py` | Model download management |
| ollama_catalog | `services/ollama_catalog.py` | Ollama model catalog |
| catalogue | `services/catalogue.py` | Model catalog management |
| model_comparison | `services/model_comparison.py` | Model benchmarking |
| model_search | `services/model_search.py` | Model search + recommendations |
| hardware | `services/hardware.py` | Hardware detection |
| conversation_service | `services/conversation_service.py` | Chat + context building |
| long_term_memory | `services/long_term_memory.py` | Persistent memory with decay |
| entity_extractor | `services/entity_extractor.py` | Extract entities from text |
| rag_pipeline | `services/rag_pipeline.py` | Retrieval-augmented generation |
| hybrid_retrieval | `services/hybrid_retrieval.py` | Multi-strategy search |
| fulltext_search | `services/fulltext_search.py` | PostgreSQL ts_vector search |
| search_clustering | `services/search_clustering.py` | Cluster search results |
| recommendation | `services/recommendation.py` | Recommendation engine |
| retrieval_metrics | `services/retrieval_metrics.py` | Search quality metrics |
| embedding_cache | `services/embedding_cache.py` | Cache embeddings |
| deletion_pipeline | `services/deletion_pipeline.py` | Cascade deletion |
| threaded_scanner | `services/threaded_scanner.py` | Multi-threaded file scanning |
| quantization_db | `services/quantization_db.py` | Quantization data |
| indexing_rules | `services/indexing_rules.py` | Indexing include/exclude rules |
| document_statistics | `services/document_statistics.py` | Document stats |
| seed_data | `services/seed_data.py` | Seed data for catalog |
| usage_tracker | `services/usage_tracker.py` | Model usage tracking |

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

**Security Audit — Complete:** P0/P1 fixes applied (auth enforcement, path traversal, token expiry, CSRF, CORS, FK constraints, IDOR prevention).

**Phase 2 (Indexing & Knowledge Graph) — Complete:**
1. ~~Repo scanner~~ — walk, chunk, embed, store pipeline complete
2. ~~Embeddings~~ — ONNX/BGE-M3 service with mock fallback
3. ~~Vector search~~ — Qdrant integration for semantic search
4. ~~Incremental indexing~~ — hash-based change detection
5. ~~Knowledge graph~~ — graph_nodes, graph_edges, graph_builder
6. ~~Cross-file search~~ — vector + graph enrichment
7. ~~Unified search API~~ — search across all data types
8. ~~Repository management~~ — CRUD + indexing triggers
9. ~~Graph visualization frontend~~ — Cytoscape.js interactive canvas

**Phase 3 (Unified Search & Agents) — Complete:**
1. ~~Base agent class~~ — tool registration, execution loop
2. ~~Planner agent~~ — task decomposition with structured plans
3. ~~Executor agent~~ — tool-use loop (search, read, write, list)
4. ~~Agent run manager~~ — orchestration with step tracking
5. ~~Agent API~~ — CRUD + runs + steps + feedback
6. ~~Agent frontend~~ — chat interface, agents management page
7. ~~Navigation~~ — sidebar + command palette integration

**Phase 4A (LLM Integration) — Partially Complete:**
1. ~~LLM manager~~ — provider abstraction (llama.cpp, Ollama)
2. ~~Model catalog~~ — providers, variants, capabilities, benchmarks
3. ~~Hardware detection~~ — CPU/RAM/GPU profiling
4. ~~Model downloads~~ — download manager with progress tracking
5. ~~User settings~~ — per-user model preferences
6. ~~Frontend~~ — Models page with catalogue, installed, downloads
7. Conversation-to-memory pipeline — ✅ done
8. Long-term memory with decay — ✅ done

**Phase 4B (Smart Indexing) — Partially Complete:**
1. ~~Semantic chunker~~ — language-aware splitting
2. ~~Indexing config~~ — include/exclude paths, file types
3. ~~Full-text search~~ — PostgreSQL ts_vector
4. ~~Hybrid retrieval~~ — vector + keyword + graph
5. ~~Document indexer~~ — markdown, PDF, notebooks
6. ~~File watcher v2~~ — sync state persistence
7. ~~Batch indexer~~ — bulk operations
8. ~~Retrieval metrics~~ — search quality tracking

---

## CI/CD

GitHub Actions on push/PR to `main`/`develop`:

- **Backend:** ruff lint, ruff format, mypy type check, pytest with PostgreSQL + Redis
- **Frontend:** next lint, TypeScript check, vitest, production build

---

## License

MIT
