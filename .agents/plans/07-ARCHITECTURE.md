# Cortex Architecture Document

## 1. System Overview

### What Cortex Is

Cortex is a **local-first machine intelligence layer** that runs entirely on the user's machine. It transforms a personal computer into a context-aware development environment by indexing codebases, managing memories, providing encrypted document storage (vault), and enabling AI-powered conversations grounded in the user's actual code and knowledge.

Cortex does not ship user data to any cloud service. All embeddings, vector search, LLM inference, and file indexing happen locally.

### Core Principles

| Principle | Meaning |
|-----------|---------|
| **Privacy-first** | All data stays on the user's machine. No telemetry, no cloud sync, no external API calls unless the user explicitly configures one (e.g., Ollama). |
| **Compound learning** | Cortex remembers across sessions. Memories, graph edges, and long-term facts accumulate over time, making the system more useful the longer it runs. |
| **Zero-config** | `make dev` or `docker compose up` should get a working system. Embedded PostgreSQL eliminates the need for a separate database server in development. |
| **Two-tier trust** | Account access and vault access are separated by two distinct passwords. Compromising one does not compromise the other. |
| **Graceful degradation** | Redis, Ollama, ONNX, and Qdrant are all optional. The system starts and serves core features even when external services are unavailable. |

### User Mental Model

Users think of Cortex as **a friend that knows their machine**. It knows:

- What files exist and what they contain
- What the user has discussed in previous conversations
- What documents the user has stored in their vault
- What skills, projects, and interests the user has declared

Cortex responds to natural language queries by grounding answers in the user's actual code and files, not generic knowledge.

---

## 2. Current Architecture Assessment

### What Works Well

| Area | Details |
|------|---------|
| **Authentication** | JWT + refresh token rotation with httpOnly cookies. Argon2 password hashing. CSRF double-submit cookie pattern. Rate limiting on auth endpoints. |
| **Vault** | Two-password architecture (login + vault password). Per-file Fernet encryption with PBKDF2 key derivation. In-memory password cache with secure wipe. Path traversal protection on every file operation. |
| **Model management** | LLM provider abstraction (llama.cpp, Ollama). Auto-discovery of available providers. Retry with exponential backoff. Usage tracking per model. |
| **Agent system** | Planner → Executor → Tools pipeline. Tool approval gates for dangerous operations. LLM-driven or keyword-fallback routing. Background run management. |
| **Hybrid retrieval** | Vector (Qdrant) + fulltext (PostgreSQL tsvector) + graph search. Reciprocal Rank Fusion merging. MMR diversity reranking. Deduplication by file path and line range. |
| **RAG pipeline** | Conversation-aware context injection. Token-budgeted context windowing. Source citation with file paths and line numbers. |

### What Needs Improvement

| Area | Issue |
|------|-------|
| **API client duplication** | Frontend has two API layers: `client.ts` (modular, typed) and legacy patterns scattered across components. Should consolidate on `client.ts`. |
| **Response model inconsistency** | Some endpoints use Pydantic response models, others return raw dicts. No standardized error envelope. |
| **Test coverage** | Backend tests exist but coverage is uneven. Many service-layer tests are missing. No E2E tests. Frontend has vitest but minimal component tests. |
| **Input validation** | Some endpoints accept unvalidated input. Not all path parameters are sanitized against traversal. Not all body fields have validators. |
| **Rate limiting granularity** | Global IP-based rate limiting only. No per-user or per-endpoint limits. Auth endpoints share the same limit as general endpoints. |
| **N+1 queries** | Some list endpoints load related objects in loops instead of using `joinedload` or `selectinload`. |

### Technical Debt Inventory

1. **Legacy cortexApi.ts** — not fully removed; some components still import from it
2. **Mixed async patterns** — some services use `asyncio.run()` inside async context, causing potential event loop issues
3. **Inconsistent session management** — `SessionLocal` is a dynamic proxy; some code creates sessions manually instead of using `Depends(get_db)`
4. **Mock embeddings fallback** — the embedding service silently falls back to deterministic mock vectors, which produce meaningless search results
5. **Vault password cache** — stored as `SecurePasswordCache` in-process; lost on restart (by design, but users may not expect it)

---

## 3. Backend Architecture

### FastAPI Application Structure

```
backend/
├── app/
│   ├── main.py                  # Lifespan, middleware, router mounting
│   ├── api/
│   │   ├── auth.py              # /api/v1/auth/* routes
│   │   ├── memory.py            # /api/v1/memory/* routes
│   │   ├── router.py            # Central API router (v1 prefix)
│   │   ├── deps.py              # Dependency injection (get_db, get_current_user)
│   │   ├── metrics.py           # /metrics Prometheus endpoint
│   │   ├── ws.py                # WebSocket upgrade endpoint
│   │   └── v1/                  # 18 domain routers
│   │       ├── agents.py
│   │       ├── conversations.py
│   │       ├── github.py
│   │       ├── health.py
│   │       ├── indexing.py
│   │       ├── knowledge.py
│   │       ├── long_term_memory.py
│   │       ├── models.py
│   │       ├── notifications.py
│   │       ├── profile.py
│   │       ├── repository.py
│   │       ├── search.py
│   │       ├── sync.py
│   │       ├── system.py
│   │       ├── users.py
│   │       ├── vault.py
│   │       ├── ws_models.py
│   │       └── ws_system.py
│   ├── auth/                    # Auth domain (service, dependencies, audit)
│   │   ├── dependencies.py
│   │   ├── service.py
│   │   ├── security.py
│   │   ├── audit.py
│   │   └── rate_limit.py
│   ├── core/                    # Cross-cutting concerns
│   │   ├── config.py            # Pydantic Settings (env-based)
│   │   ├── security.py          # JWT, password hashing, token rotation
│   │   ├── csrf.py              # Double-submit cookie CSRF middleware
│   │   ├── rate_limit.py        # Redis sliding-window rate limiter
│   │   ├── middleware.py         # Request logging + security headers
│   │   ├── redis.py             # Async Redis client with fallback
│   │   ├── vector_db.py         # Qdrant wrapper (upsert/search/delete)
│   │   ├── storage_abstraction.py
│   │   ├── storage_manager.py
│   │   ├── system_info.py
│   │   ├── system_paths.py
│   │   ├── paths.py
│   │   └── websocket.py
│   ├── db/                      # Database layer
│   │   ├── base.py              # SQLAlchemy DeclarativeBase
│   │   ├── bootstrap.py         # Engine creation, session factory
│   │   └── session.py           # Dynamic SessionLocal re-export
│   ├── models/                  # SQLAlchemy ORM models (19 files)
│   ├── schemas/                 # Pydantic request/response schemas
│   ├── services/                # Business logic (48 files)
│   │   ├── llm/                 # LLM provider abstraction
│   │   │   ├── manager.py       # LLMManager singleton
│   │   │   ├── provider.py      # LLMProvider base + dataclasses
│   │   │   ├── ollama.py        # Ollama HTTP provider
│   │   │   └── llama_cpp.py     # llama.cpp native provider
│   │   ├── embedding_service.py # ONNX/Ollama/mock embeddings
│   │   ├── hybrid_retrieval.py  # Vector + fulltext + graph retrieval
│   │   ├── rag_pipeline.py      # RAG context injection
│   │   ├── vault_service.py     # Encrypted file locker
│   │   └── ...                  # 35+ other services
│   ├── agents/                  # Agent system
│   │   ├── base.py              # BaseAgent (tool registry)
│   │   ├── planner.py           # PlannerAgent (task decomposition)
│   │   ├── executor.py          # ExecutorAgent (tool execution)
│   │   ├── tools.py             # Tool implementations + approval gates
│   │   ├── run_manager.py       # Background run lifecycle
│   │   └── background.py        # Background task runner
│   ├── intelligence/            # Intelligence features
│   │   └── models.py
│   └── tasks/                   # arq task queue
│       ├── worker.py            # WorkerSettings, enqueue_task
│       └── memory_tasks.py      # Embed, scan, index, graph tasks
```

### Service Layer Pattern

Services are instantiated via factory functions or singletons. They receive a `Session` (or `db` parameter) and operate on it. They are not stateless in the traditional sense — some hold caches or connections.

```python
# Typical pattern:
class HybridRetrievalV2:
    def __init__(self, db: Session, ...):
        self._db = db
        self._embedder = embedding_service or get_embedding_service()
        ...

def get_hybrid_retrieval(db: Session) -> HybridRetrievalV2:
    return HybridRetrievalV2(db)
```

### Agent System Architecture

```
User Request
    │
    ▼
PlannerAgent
    │  Decomposes into subtask plan (JSON array)
    │  Uses LLM if available, else single-step fallback
    ▼
ExecutorAgent
    │  Receives each subtask
    │  Routes to LLM with tool schemas, or keyword fallback
    │  Executes tools (search, read_file, write_file, exec_command, git_*)
    │  Approval gates for dangerous tools (write_file, exec_command, web_fetch)
    ▼
RunManager
    │  Tracks run lifecycle (running → completed/failed)
    │  Persists to AgentRun table
    │  Cleanup of orphaned runs on startup
```

### Task Queue (arq + Redis)

- **Worker**: `arq` worker with Redis backend
- **Tasks**: `embed_memory_task`, `scan_repo_task`, `bulk_embed_task`, `index_repo_task`, `build_graph_task`
- **Cron**: Health check every 30 minutes
- **Enqueue**: `await enqueue_task("task_name", *args)` creates a job in Redis
- **Degradation**: If Redis is unavailable, tasks fail gracefully; core features still work

### Database (PostgreSQL + Alembic)

- **ORM**: SQLAlchemy 2.0 with mapped columns (`Mapped[T]`, `mapped_column`)
- **Migrations**: Alembic with sequential prefix naming (`a00000000001_...` through `z00000000025_...`)
- **Session**: Dynamic `SessionLocal` proxy; `get_engine()` creates engine lazily
- **Bootstrap**: `bootstrap_database()` runs `alembic upgrade head` on startup if DB URL points to a local PostgreSQL

### Vector Search (Qdrant)

- **Client**: `qdrant_client.QdrantClient` (HTTP mode)
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

## 4. Frontend Architecture

### Next.js 15 App Router

```
frontend/
├── app/                        # Next.js App Router pages
│   ├── layout.tsx              # Root layout (providers, fonts)
│   ├── page.tsx                # Dashboard / home
│   ├── globals.css             # Global styles (Warm Neural Dark)
│   ├── auth/                   # Login, register
│   ├── chat/                   # Conversation interface
│   ├── models/                 # Model management
│   ├── vault/                  # Encrypted file locker
│   ├── memory/                 # Memory browser
│   ├── search/                 # Semantic search
│   ├── agents/                 # Agent management
│   ├── settings/               # User settings
│   ├── profile/                # User profile
│   ├── downloads/              # Model downloads
│   ├── admin/                  # Admin panel
│   ├── api/                    # Next.js API routes (proxy)
│   ├── error.tsx               # Error boundary
│   ├── loading.tsx             # Loading skeleton
│   └── not-found.tsx
├── src/
│   ├── shared/
│   │   ├── api/                # API client layer
│   │   │   ├── client.ts       # Base HTTP client (auto-refresh, CSRF)
│   │   │   ├── index.ts        # Re-exports
│   │   │   ├── agent.ts        # Agent API calls
│   │   │   ├── indexing.ts     # Indexing API calls
│   │   │   ├── knowledge.ts    # Knowledge API calls
│   │   │   ├── memory.ts       # Memory API calls
│   │   │   ├── models.ts       # Model API calls
│   │   │   ├── repo.ts         # Repository API calls
│   │   │   ├── search.ts       # Search API calls
│   │   │   ├── sync.ts         # Sync API calls
│   │   │   └── vault.ts        # Vault API calls
│   │   ├── auth/               # Auth context/hooks
│   │   ├── components/         # Shared components
│   │   ├── design/             # Design tokens (Warm Neural Dark)
│   │   │   └── tokens.ts       # Colors, fonts, shadows, radii
│   │   ├── hooks/              # Custom hooks
│   │   │   ├── useFolderPicker.ts
│   │   │   └── useSystemWebSocket.ts
│   │   ├── layout/             # Layout components
│   │   ├── services/           # Client-side services
│   │   ├── types.ts            # Shared TypeScript types
│   │   └── ui/                 # 20 UI primitives
│   │       ├── Badge.tsx
│   │       ├── Button.tsx
│   │       ├── Card.tsx
│   │       ├── CollapsiblePanel.tsx
│   │       ├── CommandPalette.tsx
│   │       ├── Dropdown.tsx
│   │       ├── ErrorBoundary.tsx
│   │       ├── Input.tsx
│   │       ├── MetricRing.tsx
│   │       ├── Modal.tsx
│   │       ├── NeuralNetwork.tsx
│   │       ├── PageTransition.tsx
│   │       ├── PasswordStrength.tsx
│   │       ├── Skeleton.tsx
│   │       ├── StaggerChildren.tsx
│   │       ├── Steps.tsx
│   │       ├── TabGroup.tsx
│   │       ├── Toast.tsx
│   │       └── Tooltip.tsx
│   ├── lib/
│   │   └── utils.ts            # Utility functions (cn, etc.)
│   ├── test-setup.ts
│   └── test-utils.tsx
├── next.config.ts
├── tailwind.config.ts
├── tsconfig.json
└── vitest.config.ts
```

### Component Library

- **Base**: Radix UI primitives (unstyled)
- **Custom**: 20 UI components in `src/shared/ui/`
- **Styling**: Tailwind CSS with design tokens from `tokens.ts`
- **Animations**: Framer Motion (PageTransition, StaggerChildren)
- **Toast**: Custom toast system (Toast.tsx)

### State Management

- **Server state**: React Server Components + fetch
- **Client state**: React Context (auth, theme) + custom hooks
- **No Redux/Zustand**: Deliberate choice to keep state minimal and close to usage

### API Client Architecture

```
client.ts (base)
├── Auto token refresh on 401
├── CSRF token injection from cookie
├── Credentials: include (httpOnly cookies)
├── Error normalization
└── Request/response typing

Domain modules (agent.ts, vault.ts, etc.)
├── Import api from client.ts
├── Type-safe request/response
└── Domain-specific error handling
```

### Design System (Warm Neural Dark)

| Token | Value |
|-------|-------|
| Background | `#0a0a0f` (deep void) |
| Surface | `#16161f` |
| Accent | `#0ea5c9` (cyan-blue pulse) |
| Text | `#e8e8ed` |
| Text secondary | `#7a7a8a` |
| Border | `rgba(255,255,255,0.12)` |
| Font sans | Inter |
| Font mono | JetBrains Mono |
| Font display | Geist |

---

## 5. Database Architecture

### All Tables (25 migrations, 34+ tables)

| Table | Migration | Purpose |
|-------|-----------|---------|
| `users` | `a00000000001` | User accounts, credentials, profile |
| `user_settings` | `x00000000023` | Per-user model settings |
| `user_model_settings` | `x00000000023` | Per-user model preferences |
| `documents` | `a00000000001` | Indexed documents |
| `embeddings` | `a00000000001` | Embedding vectors |
| `memories` | `a00000000001` | User memories |
| `repositories` | `j00000000010` | Indexed repositories |
| `file_indices` | `m00000000013` | File index entries |
| `path_indices` | `y00000000024` | Path-based file lookup |
| `repo_indices` | `j00000000010` | Repository index metadata |
| `graph_nodes` | `m00000000013` | Knowledge graph nodes |
| `graph_edges` | `m00000000013` | Knowledge graph edges |
| `conversations` | `q00000000016` | Chat conversations |
| `messages` | `q00000000016` | Conversation messages |
| `agents` | `n00000000014` | Agent definitions |
| `agent_runs` | `n00000000014` | Agent execution history |
| `indexing_configs` | `p00000000015` | Per-repo indexing rules |
| `model_catalog` | `r00000000017` | Available model registry |
| `sync_states` | `w00000000022` | File sync state tracking |
| `notifications` | `k00000000011` | User notifications |
| `long_term_memory` | `i00000000009` | Persistent facts |
| `knowledge_entries` | `t00000000019` | Knowledge base entries |
| `storage_registries` | `e00000000005` | Storage root pointers |
| `embedding_cache` | `r00000000017` | Embedding dedup cache |
| `auth_events` | `a00000000001` | Auth audit log |

### Migration Conventions

- **Naming**: Sequential prefix + descriptive name (`{letter}0000000000N_description.py`)
- **Both directions**: Every migration defines `upgrade()` and `downgrade()`
- **DDL**: Use `op.execute()` for raw SQL
- **Seed data**: Use `op.bulk_insert()` in migrations
- **Test**: Run `make db-reset` to verify migration chain

### Schema Design Principles

1. **JSONB for flexible data**: `handles_json`, `preferences_json`, `tools_json`, `parameters_json` — avoids schema migration for semi-structured fields
2. **Soft deletes**: `deleted_at` column on user-facing tables
3. **Timestamps**: `created_at` and `updated_at` with `server_default=func.now()`
4. **Foreign keys with ON DELETE**: Explicit cascade rules in `f00000000006a`
5. **Indexes**: Composite indexes for common query patterns (added in `d00000000004`)

---

## 6. Infrastructure

### Docker Compose Setup

```yaml
services:
  db:        postgres:16-alpine (port 5432)
  redis:     redis:7-alpine (port 6379)
  qdrant:    qdrant/qdrant:v1.18.0 (ports 6333, 6334)
```

### Embedded PostgreSQL Option

The `start.sh` script can launch an embedded PostgreSQL instance using `pg_ctl` from a local data directory. This eliminates the need for a system-installed PostgreSQL in development.

### Storage Architecture

```
CortexMemory/                    # Shared storage root
├── memory/                      # Shared memories (all users)
├── {user_id}/
│   ├── vault/                   # Encrypted personal files
│   ├── repos/                   # Indexed repository data
│   └── knowledge/               # User-specific knowledge
```

Storage paths are resolved via `storage_registries` table → `storage_root` pointer. The `StorageRegistry` model maps users to their storage roots.

---

## 7. Key Design Decisions

### Two-Password Model

| Password | Purpose | Storage |
|----------|---------|---------|
| Login password | Account authentication | Argon2 hash in `users.hashed_password` |
| Vault password | Encrypt/decrypt vault files | Argon2 hash in `users.vault_password_hash` + Fernet key derivation in-memory |

**Rationale**: A compromised login password does not expose encrypted vault files. The vault password never leaves the server in plaintext after unlock (cached as `SecurePasswordCache` with bytearray wipe).

### Cookie-Based Auth (Not Bearer Tokens)

- **Access tokens**: Stored in httpOnly cookies, auto-sent with requests
- **Refresh tokens**: Stored in httpOnly cookies with rotation on each use
- **CSRF**: Double-submit cookie pattern (`cortex_csrf` cookie + `X-CSRF-Token` header)
- **Rationale**: Browser-native protection against CSRF. No token storage in localStorage (XSS-resistant).

### Shared Memory vs Private Vault

- **Memory**: Shared across all users in `CortexMemory/memory/`. Indexed into Qdrant `cortex_memory` collection. Participates in RAG.
- **Vault**: Per-user, encrypted, never indexed, never used in AI processing. Pure encrypted file storage.

### Local-First (No Cloud Dependency)

- Embeddings: ONNX (local) → Ollama (local) → mock (no network)
- LLM: llama.cpp (local) → Ollama (local) → fail with clear error
- Vector DB: Qdrant (local Docker or embedded)
- Database: PostgreSQL (local Docker or embedded)
- Redis: Local Docker or in-memory fallback

### SQLAlchemy + Alembic (Not Drizzle)

- **Rationale**: Python ecosystem standard. Alembic provides robust migration tooling with autogenerate. SQLAlchemy 2.0 `mapped_column` syntax is declarative and type-safe.
- **Not Drizzle**: Drizzle is a TypeScript ORM; Cortex backend is Python.

---

## 8. Improvement Roadmap

### Phase 1: Consolidation

- [ ] Remove legacy `cortexApi.ts` — migrate all imports to `client.ts` domain modules
- [ ] Standardize API response envelope: `{ data: T, error: null } | { data: null, error: { code, message } }`
- [ ] Add `response_model=` to all v1 endpoints for OpenAPI schema completeness
- [ ] Replace manual session creation with `Depends(get_db)` everywhere

### Phase 2: Quality

- [ ] Achieve 80%+ backend test coverage (focus on services)
- [ ] Achieve 60%+ frontend test coverage (focus on hooks and API modules)
- [ ] Add E2E tests (Playwright or Cypress) for auth flow, vault, chat
- [ ] Add N+1 query detection to CI (e.g., `pytest-detect-n-plus-one`)

### Phase 3: Security Hardening

- [ ] Account lockout after 5 consecutive failed login attempts
- [ ] Input sanitization audit (XSS, SQL injection, path traversal)
- [ ] API key authentication for programmatic access
- [ ] Audit logging for all state-changing operations

### Phase 4: Performance

- [ ] Redis caching for frequently queried data (model catalog, user settings)
- [ ] Response caching headers for static assets
- [ ] Query optimization (prefetch related objects, pagination cursors)
- [ ] Frontend bundle analysis and code splitting

### Phase 5: Observability

- [ ] Structured logging with correlation IDs (partially done via `RequestIdFilter`)
- [ ] Metrics export (Prometheus `/metrics` endpoint exists, needs expansion)
- [ ] Distributed tracing (OpenTelemetry)
- [ ] Health check deep probes (database, Redis, Qdrant, LLM)
