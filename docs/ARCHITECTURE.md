# Cortex Architecture

## Overview

Cortex is a local-first machine intelligence layer. It runs entirely on the user's machine and transforms a personal computer into a context-aware development environment. All embeddings, vector search, LLM inference, and file indexing happen locally — no user data leaves the machine.

### Core Principles

| Principle | Meaning |
|-----------|---------|
| **Privacy-first** | No telemetry, no cloud sync, no external API calls unless user-configured (e.g., Ollama). |
| **Compound learning** | Memories, graph edges, and long-term facts accumulate over time. The system grows more useful with use. |
| **Two-tier trust** | Account access and vault access use separate passwords. Compromising one does not compromise the other. |
| **Graceful degradation** | Redis, Ollama, ONNX, and Qdrant are all optional. Core features work without them. |

### User Mental Model

Users think of Cortex as a companion that knows their machine — what files exist, what conversations happened, what documents are stored, what skills and interests the user has declared. It responds to natural language by grounding answers in actual code and files.

---

## System Architecture

```
┌────────────────────────────────────────────────┐
│  Frontend (Next.js 15)  http://localhost:3000  │
│  - Auth, Profile, Vault, Memory, Admin         │
│  - Neural Dark UI, Neural Network background   │
│  - Models, Chat, Downloads pages               │
└──────────────────────┬─────────────────────────┘
                       │ Direct requests (CORS)
┌──────────────────────▼─────────────────────────┐
│  Backend (FastAPI)    http://localhost:8000    │
│  - Auth, Vault, Memory, Intelligence           │
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

---

## Backend Architecture

### FastAPI Application Structure

```
backend/app/
├── main.py              # Lifespan, middleware, router mounting
├── api/
│   ├── router.py        # Central API router (v1 prefix)
│   ├── deps.py          # Dependency injection (get_db, get_current_user)
│   ├── metrics.py       # /metrics Prometheus endpoint
│   ├── ws.py            # WebSocket upgrade endpoint
│   └── v1/              # 18 domain routers
├── auth/                # Auth domain (service, dependencies, audit)
├── core/                # Cross-cutting concerns (config, security, redis, vector_db)
├── db/                  # Database layer (bootstrap, session factory)
├── models/              # SQLAlchemy ORM models (19 files)
├── schemas/             # Pydantic request/response schemas
├── services/            # Business logic (48 files)
│   ├── llm/             # LLM provider abstraction
│   └── ...              # embedding, retrieval, vault, indexing, etc.
├── agents/              # Agent system (base, planner, executor, tools)
├── intelligence/        # Intelligence features
└── tasks/               # arq task queue (worker, memory_tasks)
```

### Service Layer Pattern

Services are instantiated via factory functions or singletons. They receive a `Session` and operate on it. Some hold caches or connections.

```python
class HybridRetrievalV2:
    def __init__(self, db: Session, ...):
        self._db = db
        self._embedder = embedding_service or get_embedding_service()

def get_hybrid_retrieval(db: Session) -> HybridRetrievalV2:
    return HybridRetrievalV2(db)
```

### Agent System

```
User Request → PlannerAgent → ExecutorAgent → RunManager
                 │                │                │
                 Decompose        Execute tools    Track lifecycle
                 into subtasks    (search, read,   (running → completed/failed)
                 (JSON array)     write, exec,     Persist to AgentRun
                                  git_*)           Cleanup orphaned runs
                                  Approval gates
                                  for dangerous ops
```

### Task Queue (arq + Redis)

- **Worker**: arq worker with Redis backend
- **Tasks**: `embed_memory_task`, `scan_repo_task`, `bulk_embed_task`, `index_repo_task`, `build_graph_task`
- **Cron**: Health check every 30 minutes
- **Degradation**: If Redis is unavailable, tasks fail gracefully; core features still work

### Vector Search (Qdrant)

- **Collections**: `cortex_code` (file chunks), `cortex_memory` (user memories)
- **Vector size**: 768 (configurable via `EMBEDDING_DIM`)
- **Distance**: Cosine similarity
- **Filtering**: Payload-based (repo_id, file_path, document_id)

### Embeddings (ONNX / BGE-M3 / Ollama)

- **Primary**: ONNX Runtime with `nomic-embed-text` model
- **Fallback**: Ollama HTTP API (`/api/embeddings`)
- **Last resort**: Deterministic mock (MD5 hash → normalized vector) — not semantically meaningful
- **Caching**: `EmbeddingService.embed_with_cache()` checks `EmbeddingCache` table before computing

---

## Frontend Architecture

### Next.js 15 App Router

```
frontend/
├── app/                        # Pages (all "use client")
│   ├── layout.tsx              # Root layout (providers, fonts)
│   ├── api/[...path]/          # Catch-all proxy → FastAPI backend
│   └── [route]/page.tsx        # Page components
├── src/
│   ├── shared/
│   │   ├── api/                # Modular API clients (barrel-exported)
│   │   ├── auth/               # AuthProvider, cortexApi, session helpers
│   │   ├── design/             # Design tokens (tokens.ts)
│   │   ├── hooks/              # useLiveMetrics, useSystemWebSocket, useFolderPicker
│   │   ├── layout/             # DashboardShell (sidebar, header, mobile tabs)
│   │   └── ui/                 # 20 custom components
│   └── lib/utils.ts            # cn() helper (clsx + tailwind-merge)
└── vitest.config.ts
```

### Key Patterns

- **Auth**: `AuthProvider` bootstraps via `GET /me`. Login sets httpOnly cookies. Auto token refresh on 401.
- **API proxy**: Client-side fetch → Next.js API route → FastAPI. Same-origin, no CORS.
- **State**: React Context for auth. Component-local state everywhere else. No external store.
- **Design**: Dark-only glassmorphism. Custom tokens in `tokens.ts`. NeuralNetwork Canvas 2D animated background.
- **SSE streaming**: Chat and agent responses stream via `ReadableStream` line-by-line parsing.
- **Responsive**: Desktop (fixed 240px sidebar), tablet (overlay sidebar), mobile (bottom tab bar).

---

## Storage Architecture

**Shared:** `CortexMemory/` (project root by default)

```
CortexMemory/
├── logs/
├── cache/
├── runtime/
├── memory/              # AI category folders
│   ├── embeddings/
│   ├── vector_db/
│   └── graph/
└── postgres/            # Local PG cluster (start.sh, port 5435)
```

**Per-user (`<storage_root>/`):**

```
<storage_root>/
├── profile/             # Avatar photos
├── vault/               # Encrypted files (PBKDF2 + Fernet)
├── workspace/
├── exports/
└── memory_snapshots/
```

Storage paths resolved via `storage_registries` table → `storage_root` pointer.

---

## Database

PostgreSQL 16 with SQLAlchemy 2.0 + Alembic migrations. 34+ tables across 25 migrations.

- **ORM**: `Mapped[T]`, `mapped_column` syntax
- **Migrations**: Sequential prefix naming (`a00000000001_...`)
- **Session**: Dynamic `SessionLocal` proxy; `get_engine()` creates engine lazily
- **Bootstrap**: `bootstrap_database()` runs `alembic upgrade head` on startup

### Schema Principles

1. **JSONB for flexible data**: `handles_json`, `preferences_json`, `tools_json`, `parameters_json`
2. **Soft deletes**: `deleted_at` column on user-facing tables
3. **Timestamps**: `created_at` and `updated_at` with `server_default=func.now()`
4. **Foreign keys with ON DELETE**: Explicit cascade rules
5. **Indexes**: Composite indexes for common query patterns

See [DATABASE.md](./DATABASE.md) for full schema reference.

---

## Authentication

### Two-Password Model

| Password | Purpose | Storage |
|----------|---------|---------|
| Login password | Account authentication | Argon2 hash in `users.hashed_password` |
| Vault password | Encrypt/decrypt vault files | Argon2 hash + Fernet key derivation in-memory |

### Cookie-Based Auth

- **Access tokens**: httpOnly cookies, 30-minute expiry, auto-refreshed
- **Refresh tokens**: httpOnly cookies with rotation on each use, 7-day expiry
- **CSRF**: Double-submit cookie pattern (`cortex_csrf` cookie + `X-CSRF-Token` header)
- **Flow**: Register/Login → set cookies → requests forward cookies via proxy → auto-refresh on 401

See [SECURITY.md](./SECURITY.md) for detailed patterns.

---

## Infrastructure

### Docker Compose

```yaml
services:
  db:      postgres:16-alpine (port 5432)
  redis:   redis:7-alpine (port 6379)
  qdrant:  qdrant/qdrant:v1.18.0 (ports 6333, 6334)
```

### Embedded PostgreSQL

`start.sh` runs PostgreSQL in user-space on port 5435 (not Docker). Docker uses port 5432. These are different.

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Cookie-based auth (not Bearer)** | Browser-native CSRF protection. No localStorage (XSS-resistant). |
| **SQLAlchemy + Alembic (not Drizzle)** | Python ecosystem standard. Robust migration tooling with autogenerate. |
| **Local-first (no cloud)** | Privacy principle. All inference and search happens on user's machine. |
| **Shared memory vs private vault** | Memory is indexed and participates in RAG. Vault is pure encrypted file storage, never indexed. |
| **Graceful degradation** | Redis, Ollama, ONNX, Qdrant all optional. Core features work without them. |
