# CORTEX Architecture

## Overview

CORTEX is a local-first machine intelligence layer — a persistent AI brain that lives on your machine. It runs entirely on the user's machine and transforms a personal computer into a context-aware, memory-equipped, reasoning-capable companion. All embeddings, vector search, LLM inference, and file indexing happen locally — no user data leaves the machine.

CORTEX is not a chatbot, repo assistant, or RAG platform. It is an entire local AI brain ecosystem that understands your files, code, conversations, projects, and habits as a connected system. It remembers, reasons, learns, and acts.

### Core Principles

| Principle | Meaning |
|-----------|---------|
| **Privacy-first** | No telemetry, no cloud sync, no external API calls unless user-configured (e.g., Ollama). |
| **Compound learning** | Memories, graph edges, and long-term facts accumulate over time. The system grows more useful with use. |
| **Two-tier trust** | Account access and vault access use separate passwords. Compromising one does not compromise the other. |
| **Graceful degradation** | Redis, Ollama, ONNX, and Qdrant are all optional. Core features work without them. |
| **Model freedom** | Runs any model (Ollama, llama.cpp, OpenAI, Anthropic) or degrades gracefully. The user chooses the brain; CORTEX provides the mind. |
| **Living knowledge** | Files, conversations, memories, and relationships are connected into a coherent, evolving model of the user's digital life. |

### User Mental Model

Users think of CORTEX as a companion that knows their machine — what files exist, what conversations happened, what documents are stored, what skills and interests the user has declared. It responds to natural language by grounding answers in actual code and files. Over time, it develops a persistent understanding that survives sessions and grows more useful with use.

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
│   └── v1/              # 10 domain routers
├── auth/                # Auth domain (service, dependencies, audit)
├── core/                # Cross-cutting concerns (config, security, redis, vector_db)
├── db/                  # Database layer (bootstrap, session factory)
├── models/              # SQLAlchemy ORM models (19 files)
├── schemas/             # Pydantic request/response schemas
├── services/            # Business logic (106 files)
│   ├── llm/             # LLM provider abstraction
│   └── ...              # embedding, retrieval, vault, indexing, etc.
├── agents/              # Agent system (tools, integrity, run_manager, run_store)
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

The agent system is implemented and operational with intent classification, streaming loops, tool policies, and completion verification.

```
User Request → Intent Classifier → [casual: fast path | agent: streaming loop]
Agent loop:  single async generator, max 25 iter, stall detection
             @tool decorator → ToolRegistry → JSON Schema for LLM function-calling
             per-turn ToolPolicy (allow/deny/ask)
             auto-compaction at 85% (tiktoken)
             completion verifier (fresh-context LLM subagent)
```

Feature flag: `CORTEX_NEW_AGENT_LOOP` (default: False) in Settings. When True, dispatch to the new streaming loop instead of the legacy Planner→Executor path.

**Tool System (`backend/app/agents/tools/`):**

| Module | Purpose |
|--------|---------|
| `registry.py` | `@tool` decorator + `ToolRegistry` singleton — auto-registers tools with JSON Schema |
| `schemas.py` | Generate OpenAI-compatible function-calling schemas from Python type hints + docstrings |
| `policy.py` | Per-turn tool policy — ordered `ToolRule` list with first-match-wins, allow/deny/ask decisions |
| `security.py` | SSRF protection (`is_private_url`), command blocklist (`has_blocked_command`), path traversal prevention |

**Tool Registration:**
```python
from backend.app.agents.tools import tool, get_tool_registry

@tool(description="Search the codebase", requires_approval=False, category="code")
async def search(query: str, limit: int = 10) -> str:
    \"\"\"Search for matching code.

    Args:
        query: The search term
        limit: Maximum results to return
    \"\"\"
    ...

registry = get_tool_registry()
all_tools = registry.get_all()
schemas = registry.schemas_for(names=["search", "read_file"])
```

**Tool Policy:**
```python
from backend.app.agents.tools import ToolPolicy, ToolRule, default_policy

policy = default_policy()
decision = policy.evaluate("exec_command", iteration=0)
# → "ask" (shell commands require approval)
```

**Integrity System (`backend/app/agents/integrity/`):**

The Integrity System provides repository integrity analysis — exploring codebases as structured knowledge graphs, extracting entities and relationships, validating consistency. Public API is `IntegrityService`; commands and skills never access engines directly.

**Core Model:**

| File | Purpose |
|------|---------|
| `model/_base.py` | **EntityBase** — frozen dataclass with UUID, confidence `[0,1]`, source metadata |
| `model/__init__.py` | **RepositoryKnowledgeModel (RKM)** — facade over 5 frozen sub-models (Metadata, Code, Ecosystem, Documentation, Relationships) |
| `model/context.py` | ExecutionProfile enum (QUICK, INCREMENTAL, VERIFICATION, FULL, COMPLETE, TARGET) |
| `model/finding.py` | **Finding** — 16-field dataclass with severity, classification, candidate fixes |
| `model/relationship_model.py` | 18 relationship types, direction, edge strength, multiplicity |
| `model/metrics.py` | IntegrityScores, RepositoryAnalytics, PerformanceMetrics |

**Extraction & Validation:**

| File | Purpose |
|------|---------|
| `extractors/python_extractor.py` | **PythonExtractor** — `ast.parse`-based entity extraction (classes, functions, imports) |
| `extractors/python_normalizer.py` | **PythonNormalizer** — normalizes to `FileEntity` objects |
| `validation.py` | **Validator** — validates EntityBase confidence, Relationship self-refs, RKM version |

**Analysis Engines (10 engines across 3 domains):**

| File | Purpose |
|------|---------|
| `registry.py` | **EngineRegistry** — singleton with `@register` decorator, `for_profile()`, DFS topological sort |
| `engines/structural/` | 5 engines: import-graph, dependency, migration, filesystem, configuration |
| `engines/semantic/` | 3 engines: schema-engine, api-contract, cross-layer |
| `engines/evolution/` | 2 engines: documentation, planning |
| `views.py` | **ViewRegistry** — lazy-built, cached, invalidatable derived views (9 graph types) |
| `query.py` | **RepositoryQueryService** — graph traversal, BFS impact analysis, find_consumers/find_producers |
| `closure.py` | **DependencyClosureService** — impact set computation via BFS on relationship edges |
| `workflow.py` | **IntegrityWorkflow** — internal orchestrator: build_model → build_views → run engines → aggregate |

**Public API:**

| File | Purpose |
|------|---------|
| `service.py` | **IntegrityService** — `analyze()`, `analyze_incremental()`, `analyze_target()`, `build_model()`, `query()` |
| `report.py` | **Aggregator** + **Reporter** — aggregate by severity/classification; Markdown and JSON output |

**Engine Registration:**
```python
from backend.app.agents.integrity.registry import register
from backend.app.agents.integrity.engines._base import IntegrityEngine

@register(name="import-graph", domain=IntegrityDomain.STRUCTURAL,
          capabilities={Capability.IMPORT, Capability.GRAPH},
          required_dependencies=[],
          profiles={ExecutionProfile.QUICK, ExecutionProfile.VERIFICATION})
class ImportGraphEngine(IntegrityEngine):
    ...
```

Feature flag: `CORTEX_NEW_AGENT_LOOP` (default: False) in Settings. When True, dispatch to the new streaming loop instead of the legacy Planner→Executor path.

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

17 real pages + 4 Coming Soon placeholders. Dark-only design system. 10 shared UI components. 38 feature components.

```
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx              # Root layout (Geist font, dark bg)
│   │   ├── globals.css             # Tailwind directives + design tokens
│   │   ├── api/[...path]/          # Catch-all proxy → FastAPI backend
│   │   ├── auth/page.tsx           # Login page
│   │   ├── auth/register/          # Registration page
│   │   ├── chat/                   # Conversations, streaming, code blocks
│   │   ├── agents/                 # Agent management, chat, run history
│   │   ├── models/                 # Browse, download, compare, installed
│   │   ├── awareness/              # System overview (device, env, health, project)
│   │   ├── awareness/repos/        # Repository management
│   │   ├── awareness/indexing/     # Indexing config, graph view
│   │   ├── memory/                 # Knowledge graph, search, memory CRUD
│   │   ├── search/                 # Unified search
│   │   ├── vault/                  # Encrypted document locker
│   │   ├── privacy/                # Privacy overview dashboard
│   │   ├── privacy/audit/          # Audit log viewer
│   │   ├── privacy/consent/        # Consent management
│   │   ├── system/                 # System health monitoring
│   │   ├── settings/               # User settings, profile
│   │   ├── marketplace/            # Coming Soon
│   │   ├── notes/                  # Coming Soon
│   │   ├── scheduler/              # Coming Soon
│   │   └── tasks/                  # Coming Soon
│   ├── shared/
│   │   ├── ui/                     # Badge, Button, Card, Modal, Skeleton, Toast, etc.
│   │   ├── layout/                 # AppShell, Header, Sidebar
│   │   ├── auth/                   # AuthProvider, ProtectedRoute
│   │   └── lib/                    # cn(), apiFetch()
│   └── features/
│       ├── dashboard/              # SystemOverview, MetricsRow
│       ├── chat/                   # MessageBubble, CodeBlock, ConversationItem, SourcesPanel
│       ├── agents/                 # Agent cards, chat, RunHistory
│       ├── models/                 # ModelCard, BrowseView, InstalledView, DownloadsView, CompareView
│       ├── awareness/              # DeviceCard, HealthCard, EnvironmentCard, ProjectCard, etc.
│       ├── memory/                 # API client (memory/graph/search)
│       ├── search/                 # API client (unified search)
│       ├── vault/                  # API client (encrypted files)
│       ├── privacy/                # ConsentToggle, AccessControlCard, StorageCard
│       ├── developer/              # API client (developer tools)
│       ├── settings/               # Settings page component
│       └── system/                 # System health page component
```

### Key Patterns

- **Auth**: `AuthProvider` bootstraps via `GET /me`. Login sets httpOnly cookies. Auto token refresh on 401.
- **API proxy**: Client-side fetch → Next.js API route → FastAPI. Same-origin, no CORS.
- **State**: React Context for auth. Component-local state everywhere else. No external store.
- **Design**: DESIGN.md tokens. Dark-only. Geist font. Tonal elevation (Void → Elevated → Surface → Hover).
- **SSE streaming**: Chat and agent responses stream via `ReadableStream` line-by-line parsing.
- **Responsive**: Desktop (fixed 240px sidebar), tablet (overlay sidebar), mobile (bottom tab bar).
- **Token mapping**: `text-text-primary`, `text-text-secondary`, `text-text-muted`, `bg-bg-surface`, `bg-bg-elevated` — NOT `text-primary`, `text-secondary`, `text-muted`, `bg-surface`.

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

PostgreSQL 16 with SQLAlchemy 2.0 + Alembic migrations. 37 migrations across 10 domain routers.

- **ORM**: `Mapped[T]`, `mapped_column` syntax
- **Models**: 44 model files
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

See [GOVERNANCE.md](./GOVERNANCE.md) (Security section) for detailed patterns.

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

---

## Agent System

### Domain Documentation

When exploring the codebase, agents should consume domain documentation before working:

- **`CONTEXT.md`** at the repo root, or
- **`CONTEXT-MAP.md`** at the repo root if it exists — it points at one `CONTEXT.md` per context. Read each one relevant to the topic.
- **`docs/decisions/`** — read ADRs that touch the area you're about to work in.

If any of these files don't exist, **proceed silently**. Don't flag their absence; don't suggest creating them upfront.

**Single-context repo (most repos):**

```
/
├── CONTEXT.md
├── docs/decisions/
│   ├── 001-agentic-ecosystem.md
│   └── 002-postgresql-primary-database.md
└── src/
```

**Multi-context repo (presence of `CONTEXT-MAP.md` at the root):**

```
/
├── CONTEXT-MAP.md
├── docs/decisions/              ← system-wide decisions
└── src/
    ├── ordering/
    │   ├── CONTEXT.md
    │   └── docs/decisions/      ← context-specific decisions
    └── billing/
        ├── CONTEXT.md
        └── docs/decisions/
```

**Glossary usage:** When your output names a domain concept (in an issue title, a refactor proposal, a hypothesis, a test name), use the term as defined in `CONTEXT.md`. Don't drift to synonyms the glossary explicitly avoids.

**Flag ADR conflicts:** If your output contradicts an existing ADR, surface it explicitly rather than silently overriding:

> _Contradicts ADR-0007 (event-sourced orders) — but worth reopening because…_

### Issue Tracker

Issues and PRDs live as GitHub issues. Use the `gh` CLI for all operations.

**Conventions:**
- **Create an issue**: `gh issue create --title "..." --body "..."`. Use a heredoc for multi-line bodies.
- **Read an issue**: `gh issue view <number> --comments`, filtering comments by `jq` and also fetching labels.
- **List issues**: `gh issue list --state open --json number,title,body,labels,comments` with appropriate `--label` and `--state` filters.
- **Comment on an issue**: `gh issue comment <number> --body "..."`
- **Apply / remove labels**: `gh issue edit <number> --add-label "..."` / `--remove-label "..."`
- **Close**: `gh issue close <number> --comment "..."`

Infer the repo from `git remote -v` — `gh` does this automatically when run inside a clone.

**Pull requests as a triage surface:**
- **Read a PR**: `gh pr view <number> --comments` and `gh pr diff <number>` for the diff.
- **List external PRs for triage**: `gh pr list --state open --json number,title,body,labels,author,authorAssociation,comments` then keep only `authorAssociation` of `CONTRIBUTOR`, `FIRST_TIME_CONTRIBUTOR`, or `NONE`.
- **Comment / label / close**: `gh pr comment`, `gh pr edit --add-label`/`--remove-label`, `gh pr close`.

GitHub shares one number space across issues and PRs, so a bare `#42` may be either — resolve with `gh pr view 42` and fall back to `gh issue view 42`.

### Triage Labels

The skills speak in terms of five canonical triage roles:

| Label in skills   | Label in our tracker | Meaning                                  |
| ----------------- | -------------------- | ---------------------------------------- |
| `needs-triage`    | `needs-triage`       | Maintainer needs to evaluate this issue  |
| `needs-info`      | `needs-info`         | Waiting on reporter for more information |
| `ready-for-agent` | `ready-for-agent`    | Fully specified, ready for an AFK agent  |
| `ready-for-human` | `ready-for-human`    | Requires human implementation            |
| `wontfix`         | `wontfix`            | Will not be actioned                     |
