# CLAUDE.md — CORTEX Control Plane

This file is the **execution contract** for Claude Code. It defines what CORTEX is, what to do on entry, and what rules govern all work.

## What CORTEX Is

CORTEX is a local-first machine intelligence layer — a persistent AI brain on your machine. FastAPI backend + Next.js frontend + Rust code intelligence + Python CLI. Encrypted vaults, knowledge graphs, vector search, LLM integration, autonomous agents. Not a chatbot. Not a repo assistant. An entire local AI brain ecosystem.

## Entry Protocol — MANDATORY

When entering this repository, Claude MUST do these in order:

### 1. Determine Active Development State

```bash
# Read the constitution to understand the full system
cat .agents/plans/guide.md

# Find which version is currently being developed
grep -r "in_progress\|active\|current" .agents/plans/versions/*/progress.md

# Read the active version's phase plan
cat .agents/plans/versions/vX/Phase-1.md  # (replace X with active version)
```

If no version is active (all components show "Not started"), start with **V1: The Brain Works** per `.agents/plans/implementation_steps.md`.

### 2. Load the Execution Plan

```bash
# Contributor guide with execution order and constraints
cat .agents/plans/implementation_steps.md

# Architecture constitution (10 principles, what to keep/reject)
cat .agents/plans/guide.md

# Cross-reference matrix (which items go in which version)
cat .agents/plans/FinalCompatibilities.md
```

### 3. Verify Governance Infrastructure

```bash
# Hook system
python .claude/hooks/run_hooks.py --help

# Available slash commands
ls .claude/commands/project/

# Available skills
ls .agents/skills/
```

### 4. Check for Existing Work

```bash
# What's the current branch?
git branch --show-current

# What changed recently?
git log --oneline -10

# Any uncommitted work?
git status
```

## Authority Hierarchy

When documents conflict, this order governs:

| Priority | Document | Purpose |
|----------|----------|---------|
| 1 | **CLAUDE.md** (this file) | Execution contract — what Claude does |
| 2 | **.agents/plans/guide.md** | Constitution — architecture principles, what to build |
| 3 | **AGENTS.md** | Agent behavior rules — security, API patterns |
| 4 | **.agents/plans/implementation_steps.md** | Implementation guide — execution order |
| 5 | **.agents/plans/versions/vX/Phase-N.md** | Active phase plan — current work |
| 6 | **docs/** | Reference — detailed docs for specific domains |

**Rule:** If a topic appears in multiple files, the higher-priority document wins. Lower documents reference, not duplicate.

## What CORTEX Is Building

Six versions, each a complete milestone:

| Version | Name | Duration | What It Delivers |
|---------|------|----------|------------------|
| **V1** | The Brain Works | 11-18 days | Agent loop, daemon lifecycle, CLI, streaming |
| **V2** | The Architecture | 17-25 days | Provider/MCP abstraction, plugin system, memory |
| **V3** | The Desktop | 22-31 days | Tauri shell, TUI, performance optimization |
| **V4** | The Automaton | 21-30 days | Scheduler, MCP server, research, sessions |
| **V5** | The Workspace | 27-38 days | Email, calendar, tasks, notes, documents, contacts |
| **V6** | The Ecosystem | 27-38 days | Marketplace, graph intelligence, cross-encoder, polish |

**Active version:** V1 (if nothing has started yet)
**Phase plan location:** `.agents/plans/versions/vX/Phase-N.md`
**Progress tracking:** `.agents/plans/versions/vX/progress.md`

## Execution Contract

### Before ANY Work

1. **Read the active phase plan** — know what components are in scope
2. **Read the constraints** — .agents/plans/guide.md architecture principles apply always
3. **Verify entry state** — run the entry protocol above
4. **Skill discovery** — check `.agents/skills/` for applicable skills
5. **Branch** — create `feat/<topic>` from `main`

### During Work

1. **TDD when applicable** — write test, verify fail, implement, verify pass
2. **Commit frequently** — after each logical unit
3. **Run hooks on change** — `make hooks-onchange`
4. **Follow architecture** — file placement rules, ownership checks, API conventions
5. **Update progress** — mark components as you complete them in `progress.md`

### After Work

1. **Run completion gate** — `make hooks-merge`
2. **Run tests** — `make test` + `cd frontend && npm test`
3. **Run lint** — `make lint` + `make format`
4. **Reflection** — use `/project:reflect` before marking complete
5. **Update progress** — mark completed components in `progress.md`
6. **Merge** — after all checks pass

### Completion Criteria (for any component)

- [ ] Tests passing
- [ ] Lint clean
- [ ] Build succeeds
- [ ] Documentation updated (if applicable)
- [ ] ADR created (if architectural decision)
- [ ] Progress updated in `progress.md`
- [ ] Hook suite passes (`make hooks-merge`)

## Architecture Constraints

These rules are immutable. See `.agents/plans/guide.md` for full rationale.

### Backend (`backend/app/`)

**Framework:** FastAPI + sync SQLAlchemy 2.0 + Alembic

- **Auth:** JWT access (30min) + refresh (7-day) in httpOnly cookies. CSRF double-submit.
- **DB:** `get_db()` generator. `DynamicSessionLocal` factory. Migrations at startup.
- **Services:** Constructor injection. Global singletons: `llm_manager`, `redis_cache`, `download_manager`.
- **Embeddings:** ONNX → Ollama → mock. 768-dim in Qdrant.
- **RAG:** HybridRetrievalV2 — vector + fulltext + graph via RRF + MMR.
- **Vault:** Fernet-encrypted per-user. SecurePasswordCache.
- **Middleware:** CORS → RequestLogging → GZip → RequestSizeLimit → RateLimit → CSRF → HTTPS redirect.
- **Ownership:** `resource.user_id == current_user.id` on ALL user-scoped endpoints.
- **Routes:** Specific before parameterized. `response_model=` on all decorators.

### Frontend (`frontend/`)

**Framework:** Next.js 15 App Router + React 19 + TypeScript 5.8 + Tailwind 3.4

- **Auth:** `AuthProvider` bootstraps via `GET /me`. Auto token refresh on 401.
- **Proxy:** Client → Next.js API route → FastAPI. Same-origin, no CORS.
- **State:** React Context for auth. Component-local everywhere else.
- **Design:** Dark-only glassmorphism. Tokens in `tokens.ts`. NeuralNetwork canvas background.
- **SSE:** `ReadableStream` line-by-line for chat/agent streaming.
- **Responsive:** Desktop 240px sidebar, tablet overlay, mobile bottom tabs.

### File Placement

| Type | Location |
|------|----------|
| Models | `backend/app/models/` |
| Schemas | `backend/app/schemas/` |
| Routers | `backend/app/api/v1/` |
| Services | `backend/app/services/` |
| Core | `backend/app/core/` (config, security, middleware, DB, Redis) |
| Agents | `backend/app/agents/` (agent system, run manager) |
| Tasks | `backend/app/tasks/` |
| Tests | `tests/` (project root, NOT inside backend/) |
| Migrations | `migrations/versions/` |
| Docs | `docs/` |
| ADRs | `docs/decisions/` |
| Skills | `.agents/skills/` |
| Hooks | `.claude/hooks/` |

### Forbidden Paths

`.trae/`, `.codex/`, `.cortex_bootstrap/`, `skills-lock.json` — must never exist.

## Commands

```bash
make install        # Install all deps
make dev            # Backend hot reload (:8000)
make dev-frontend   # Frontend dev server (:3000)
make dev-full       # Both
make test           # Backend pytest
make lint           # ruff + mypy
make format         # ruff format
make check          # lint + test
make migrate        # Apply Alembic migrations
make migration m=X  # Create migration
make hooks          # Run all hooks
make hooks-push     # Pre-push hooks
make hooks-merge    # Pre-merge hooks (all)
make auto-status    # Show active version/phase
make auto-release   # Pre-release validation
make auto-docs      # Documentation consistency
make auto-skills    # Skill health check
./start.sh          # Self-contained launcher
```

## Mandatory Workflow

```
Branch → Skill Discovery → Brainstorm → Plan → Implement → Test → Validate → Review → Reflect → Merge
```

Every significant task follows this. No shortcuts. See `docs/WORKFLOWS.md` for details.

### Mandatory Reviews

| Review | When | Command |
|--------|------|---------|
| Code quality | Before push | `/project:review` |
| Verification | Before merge | `/project:verify` |
| Adversarial | Before major decisions | `/project:challenge` |
| Reflection | Before completion | `/project:reflect` |
| Architecture | Before big changes | `/project:architecture` |
| Health | Weekly | `/project:health` |
| Release | Before release | `/project:release` |

### Clarification Rules

**MUST ask human:** Irreversible decisions, multiple valid paths, scope ambiguity, >2 subsystems affected, new technology proposed.

**MAY proceed:** Well-defined tasks, established patterns, mechanical changes, test/doc updates.

## Strategic Commands

| Command | When | Purpose |
|---------|------|---------|
| `/project:cortex` | Start development session | Autonomous development iteration |
| `/project:prompt` | Before complex work | Generate ecosystem-aware prompts |
| `/project:audit` | During audits | Deep code-level scan |
| `/project:review` | Before push | Code quality analysis |
| `/project:verify` | Before merge | Automated verification suite |
| `/project:release` | Before release | Release readiness check |
| `/project:architecture` | Before big changes | Architecture alignment |
| `/project:challenge` | Before decisions | Adversarial review |
| `/project:health` | Weekly | Repository health check |
| `/project:ideas` | Weekly | Innovation discovery |
| `/project:improve` | Weekly | Ecosystem self-improvement |
| `/project:reflect` | Before completion | Reflection framework |
| `/project:feature-gap` | During planning | Roadmap vs codebase gaps |

## Common Gotchas

- `start.sh` uses port 5435 (user-space PG). `docker-compose.yml` uses 5432. Different.
- `conftest.py` compiles `JSONB → JSON` for SQLite. Real DB uses JSONB.
- `migrations/env.py` imports all models for Alembic autogenerate.
- Route order: specific routes before parameterized (e.g., `/models/installed` before `/models/{id}`).
- `cortexCode` Rust crate: `cargo build --release` in `crates/code-intel/` before Python use.

## Testing

Tests at project root in `tests/`. SQLite in-memory, mocked external services. No real Postgres/Redis/Qdrant needed.

Frontend: Vitest + jsdom + React Testing Library. `test-setup.ts` polyfills observers.

## Environment

Required: `SECRET_KEY`, `DATABASE_URL` (port 5435), `APP_NAME`, `API_V1_PREFIX`. Optional: `REDIS_URL`, `CORTEX_ROOT`, `MEMORY_PATH`, `VAULT_PATH`.

## Reference Documents

| Topic | Location |
|-------|----------|
| Architecture | `docs/ARCHITECTURE.md` |
| Constitution | `.agents/plans/guide.md` |
| Governance | `docs/GOVERNANCE.md` |
| Workflows | `docs/WORKFLOWS.md` |
| Developer Guide | `docs/DEVELOPER_GUIDE.md` |
| API Reference | `docs/API.md` |
| Database Schema | `docs/DATABASE.md` |
| Design System | `DESIGN.md` |
| Implementation Guide | `.agents/plans/implementation_steps.md` |
| Phase Plans | `.agents/plans/versions/vX/Phase-N.md` |
| Progress Tracking | `.agents/plans/versions/vX/progress.md` |
