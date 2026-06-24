# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CORTEX is a local-first machine intelligence layer — a persistent AI brain that lives on your machine. It gives a computer its own understanding, memory, reasoning, and agency. It combines a FastAPI backend, Next.js frontend, Rust-based code intelligence, and a Python CLI into a single workspace. The architecture is designed around encrypted vaults, knowledge graphs, vector search, LLM integration, and autonomous agents. CORTEX is not a chatbot, repo assistant, or model wrapper — it is an entire local AI brain ecosystem.

**For detailed architecture, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).**
**For ecosystem governance, see [docs/GOVERNANCE.md](docs/GOVERNANCE.md).**
**For workflow definitions, see [docs/WORKFLOWS.md](docs/WORKFLOWS.md).**
**For developer guide, see [docs/DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md).**

## Commands

### Full Stack

```bash
make install        # Install all deps (uv sync + npm install)
make dev            # Backend hot reload (uvicorn on :8000)
make dev-frontend   # Frontend dev server (Next.js on :3000)
make dev-full       # Both backend + frontend
./start.sh          # Self-contained: starts PG in user-space, runs migrations, launches both
```

### Testing

```bash
make test           # Backend pytest (all tests in tests/ at project root)
make test-cov       # Backend coverage report
cd frontend && npm test   # Frontend Vitest
make check          # lint + test
```

### Linting & Formatting

```bash
make lint           # ruff check + mypy (backend/tests)
make format         # ruff format + ruff check --fix
```

### Database

```bash
make migrate                       # Apply all Alembic migrations
make migration m="description"     # Create new migration
make db-reset                      # Drop+recreate schema, reapply migrations
make db-shell                      # PostgreSQL CLI
```

### Docker

```bash
make docker-build   # Build production image
make docker-up      # Start postgres, redis, qdrant
make docker-down    # Stop containers
```

### Task Queue

```bash
make worker         # Start arq worker for background tasks (embed, index, graph)
```

### Frontend Build

```bash
cd frontend && npm run build    # Next.js standalone output (Docker-ready)
```

## Architecture

### Backend (`backend/app/`)

**Framework**: FastAPI with sync SQLAlchemy 2.0 + Alembic migrations

```
backend/app/
├── main.py              # App factory, middleware stack, startup (DB bootstrap, Redis, Ollama)
├── core/                # Config, security, CSRF, rate limiting, Redis, vector_db
├── api/
│   ├── router.py        # Root router — mounts all v1 sub-routers
│   └── v1/              # Domain routers (auth, users, vault, memory, search, models, agents, etc.)
├── models/              # SQLAlchemy models (~20 model files)
├── schemas/             # Pydantic request/response schemas (from_attributes=True)
├── services/            # Business logic (vault, embedding, vector_db, rag_pipeline, etc.)
├── managers/            # Manager classes (llm_manager, download_manager, etc.)
├── tasks/               # arq background tasks (embed, index, build_graph)
└── middleware/           # CORS, rate limiting, CSRF, request logging
```

**Key patterns**:
- **Auth**: JWT access tokens (30min) + refresh tokens (7-day rotation) stored in httpOnly cookies. CSRF double-submit pattern. All `/api/v1/*` endpoints require auth unless explicit.
- **DB**: `get_db()` generator for session injection. `DynamicSessionLocal` factory. Migrations run at startup via `bootstrap_database()`.
- **Services**: Constructor injection with optional overrides. Global singletons for `llm_manager`, `redis_cache`, `download_manager`.
- **Embeddings**: Three-tier fallback: ONNX → Ollama → mock. 768-dim vectors stored in Qdrant.
- **RAG**: HybridRetrievalV2 merges vector + fulltext + graph results via RRF + MMR diversity reranking.
- **Vault**: Fernet-encrypted per-user file storage with separate vault password. SecurePasswordCache.
- **Middleware stack order**: CORS → RequestLogging → GZip → RequestSizeLimit → RateLimit → CSRF → HTTPS redirect.

**Ownership rules** (AGENTS.md): Every user-scoped endpoint must verify `resource.user_id == current_user.id`. Use `Depends(get_current_user)`, never trust client-provided user IDs.

**API conventions** (AGENTS.md): Specific routes before parameterized routes. Always use `response_model=` on decorators. Router files per domain in `api/v1/`, registered in `api/router.py`.

### Frontend (`frontend/`)

**Framework**: Next.js 15 (App Router) + React 19 + TypeScript 5.8 + Tailwind CSS 3.4

```
frontend/
├── app/                  # Pages (all "use client")
│   ├── layout.tsx        # Root layout (AuthProvider, fonts)
│   ├── api/[...path]/    # Catch-all proxy → FastAPI backend
│   └── [route]/page.tsx  # Page components
├── src/
│   ├── shared/
│   │   ├── api/          # Modular API clients (barrel-exported)
│   │   ├── auth/         # AuthProvider, cortexApi (monolithic client), session helpers
│   │   ├── hooks/        # useLiveMetrics, useSystemWebSocket, useFolderPicker
│   │   ├── layout/       # DashboardShell (sidebar, header, mobile tabs)
│   │   ├── design/       # tokens.ts (palette, shadows, fonts)
│   │   ├── ui/           # 17 custom components (Button, Card, Modal, CommandPalette, NeuralNetwork, etc.)
│   │   └── types.ts      # ~800 lines of TypeScript interfaces
│   └── lib/utils.ts      # cn() helper (clsx + tailwind-merge)
└── vitest.config.ts
```

**Key patterns**:
- **Auth flow**: `AuthProvider` bootstraps via `GET /me`. Login sets httpOnly cookies. Logout locks vault, clears session. Auto token refresh on 401.
- **API proxy**: Client-side fetch → Next.js API route → FastAPI. Same-origin, no CORS.
- **State**: No external store. React Context for auth. Component-local state everywhere else.
- **Design system**: Dark-only glassmorphism. Custom tokens in `tokens.ts`. NeuralNetwork Canvas 2D animated background.
- **SSE streaming**: Chat and agent responses stream via `ReadableStream` line-by-line parsing.
- **Responsive**: Desktop (fixed 240px sidebar), tablet (overlay sidebar), mobile (bottom tab bar).

### Rust Crates (`crates/`)

- **`cortex-code-intel`**: PyO3 Python extension using tree-sitter to parse Python source into AST nodes.
- **`cortex-file-watcher`**: Standalone binary using the `notify` crate to watch filesystem events.

### CLI (`cli/`)

TypeScript/Commander.js CLI (`cortex-cli`). 15 command stubs scaffolded but not yet implemented.

## Database Schema

Migrations live in `migrations/versions/`. Alphabetical-prefix naming (`b00000000000` baseline, `c0000000000X` current chain). Archived migrations in `_archive/`.

**Important**: After any model change, run `make migration m="description"` then `make migrate`. Both `upgrade()` and `downgrade()` must be defined. Test with `make db-reset`.

Core models: User/Profile/Vault, Memory/LongTermMemory, Agent/AgentRun/AgentStep, Conversation/ConversationMessage, Document/DocumentChunk, ModelCatalog/ModelVariant/Provider/Quantization, RepoIndex/CodeChunk/IndexedFile, GraphNode/GraphEdge, EmbeddingCache, PathIndex, StorageRegistry, SyncState.

See [docs/DATABASE.md](docs/DATABASE.md) for full schema reference.

## Testing

Tests live at the project root in `tests/` (not inside `backend/`). Two-level conftest:

1. **Root `conftest.py`**: SQLite in-memory engine, per-test session rollback isolation, `mock_auth` fixture, `TestClient` with mocked external services.
2. **`tests/conftest.py`**: Blanket mocks for all external infrastructure (Qdrant, Ollama, embedding service, file watcher, RAG pipeline, fulltext search — 13 patched paths).

Tests run without real PostgreSQL, Redis, or Qdrant. The `tests/` conftest autouse fixtures handle this.

Frontend tests use Vitest + jsdom + React Testing Library. `test-setup.ts` polyfills `IntersectionObserver`, `ResizeObserver`, `matchMedia`, and `HTMLCanvasElement.getContext`.

## Environment

Required env vars (see `.env.example`): `SECRET_KEY`, `DATABASE_URL` (port 5435 for user-space PG), `REDIS_URL` (optional), `APP_NAME`, `API_V1_PREFIX`. Optional: `CORTEX_ROOT`, `MEMORY_PATH`, `VAULT_PATH`.

Docker services: PostgreSQL 16, Redis 7, Qdrant v1.18 — all on localhost-only ports.

## Common Gotchas

- `start.sh` runs PostgreSQL in user-space on port 5435 (not Docker). `docker-compose.yml` uses port 5432. These are different.
- The root `conftest.py` compiles `JSONB → JSON` for SQLite compatibility. Real DB uses JSONB.
- `backend/app/main.py` imports all models at module level for Alembic autogenerate to work.
- Route registration order matters: specific routes (e.g., `/models/installed`) must come before parameterized routes (`/models/{model_id}`).
- The `cortexCode` Rust crate must be built separately (`cargo build --release` in `crates/code-intel/`) before Python can use it.

## Ecosystem Integration

This repository uses a multi-agent development ecosystem. All agents must follow these rules:

### Mandatory Workflow Rules

1. **Branching:** Always create a feature branch before any significant change. Never commit directly to `main`. Name branches `feat/<topic>`, `fix/<topic>`, or `docs/<topic>`. After all work is done and verified, merge to `main`. Minimize parallel branches to avoid merge conflicts — finish one branch before starting the next.
2. **Skill Discovery:** Before any task, search for existing skills. Use `superpowers:brainstorming`, `superpowers:writing-plans`, `superpowers:test-driven-development`, `superpowers:systematic-debugging`, `code-review`, `simplify`, and other available skills. Never skip skill discovery.
3. **Brainstorming:** Use `superpowers:brainstorming` skill before any design work. Present design, get approval, write spec, then implement.
4. **Planning:** Use `superpowers:writing-plans` skill after design approval. Create implementation plan with explicit steps.
5. **Implementation:** Follow TDD when applicable. Commit after each logical unit. Run `make lint` + `make format` after each commit.
6. **Testing:** Run `make test` (backend) and `cd frontend && npm test` (frontend) before every push. No regressions.
7. **Validation:** Pre-commit hooks run automatically. Run `make check` before push.
8. **Review:** Use `code-review` skill for correctness, `simplify` for quality. Address all P0/P1 findings.
9. **Documentation:** Update relevant docs when changing APIs, schemas, security patterns, or architecture.
10. **Completion:** All tests pass, lint clean, build succeeds, docs updated, ADR created if architectural decision. Run full hook suite before merge.
11. **Hooks:** Run `make hooks-push` before push, `make hooks-merge` before merge. Hook system validates quality at every stage.
12. **Skill Creation:** When a reusable workflow is identified during development, create a skill. Skills are a normal part of Cortex development, not a separate activity.

### Reflection Rule

Before completing any major task, agents MUST run through the reflection framework. Ask:

- What could be improved?
- What could be simplified?
- What could be automated?
- What could become a skill?
- What could become a hook?
- What could become a reusable workflow?
- What future problem does this reveal?
- What future opportunity does this create?

Use `/project:reflect` for structured execution. Document findings. Never skip reflection.

### Skill Usage Rules

- **Always check for applicable skills** before any task. The skill list is in system-reminder messages.
- **Use skills in priority order:** Process skills first (brainstorming, systematic-debugging), then implementation skills.
- **Never skip skills** because a task "seems simple." Every task goes through the appropriate workflow.
- **Skills are mandatory** when they apply. Do not rationalize skipping them.

### Clarification Rules

**Agent MUST ask human when:**
- Decision is irreversible (schema migrations, breaking API changes, security policy)
- Multiple valid paths exist with different trade-offs
- Scope is ambiguous or requirements are missing
- Change affects >2 subsystems
- New technology or pattern not in current stack is proposed

**Agent MAY proceed without asking when:**
- Task is well-defined with explicit acceptance criteria
- Following established codebase patterns
- Mechanical changes (typos, formatting, imports)
- Updating existing tests or documentation

See [docs/GOVERNANCE.md](docs/GOVERNANCE.md) for full governance rules.
See [docs/WORKFLOWS.md](docs/WORKFLOWS.md) for complete workflow definitions.

## Strategic Commands

| Command | When | Purpose |
|---------|------|---------|
| `/project:reflect` | Before completion (mandatory) | Reflection framework — quality, improvement, ecosystem growth |
| `/project:review` | Before PR/push | Code quality, correctness, patterns |
| `/project:challenge` | Before major decisions | Adversarial review — poke holes in approach |
| `/project:health` | Weekly | Repo health, dead code, drift, debt |
| `/project:architecture` | Before big changes | Architecture alignment, convention check |
| `/project:ideas` | Weekly/monthly | Innovation, future opportunities, gap discovery |
| `/project:improve` | Weekly | Ecosystem improvement — skills, hooks, workflows |

## Agent Skills

### Issue tracker

GitHub Issues via `gh` CLI. External PRs are not treated as triage requests. See `docs/agents/issue-tracker.md`.

### Triage labels

Default vocabulary: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context — one `CONTEXT.md` at the repo root, `docs/adr/` for architectural decisions. See `docs/agents/domain.md`.
