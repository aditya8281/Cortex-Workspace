Last updated: 2026-06-28

# CLAUDE.md — CORTEX Control Plane

This file is the **execution contract** for Claude Code. It defines what CORTEX is, what to do on entry, and what rules govern all work.

## What CORTEX Is

CORTEX is a local-first machine intelligence layer — a persistent AI brain on your machine. FastAPI backend + Next.js frontend. Encrypted vaults, knowledge graphs, vector search, LLM integration, autonomous agents. Not a chatbot. Not a repo assistant. An entire local AI brain ecosystem.

## Entry Protocol — MANDATORY

When entering this repository, Claude MUST do these in order:

### 1. Determine Active Development State

```bash
# Check what's currently being worked on
git log --oneline -5
git status

# Check backend API routes (what features exist)
ls backend/app/api/v1/

# Check frontend state
ls frontend/src/ 2>/dev/null || echo "Frontend not yet scaffolded"
```

### 2. Verify Governance Infrastructure

```bash
# Available slash commands
ls .claude/commands/project/

# Available skills
ls .claude/skills/
```

### 3. Check for Existing Work

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
| 2 | **.agents/plans/GUIDE.md** | Constitution — architecture principles, what to build |
| 3 | **AGENTS.md** | Agent behavior rules — security, API patterns |
| 4 | **.agents/plans/IMPLEMENTATION_STEPS.md** | Implementation guide — execution order |
| 5 | **.agents/plans/versions/vX/Phase-N.md** | Active phase plan — current work |
| 6 | **docs/** | Reference — detailed docs for specific domains |

**Rule:** If a topic appears in multiple files, the higher-priority document wins. Lower documents reference, not duplicate.

## What CORTEX Is Building

Six versions, each a complete milestone:

| Version | Name | What It Delivers |
|---------|------|------------------|
| **V1** | The Brain Works | Agent loop, daemon lifecycle, streaming, chat, system monitoring |
| **V2** | The Architecture | Provider/MCP abstraction, plugin system, memory, knowledge graph |
| **V3** | The Desktop | Tauri shell, TUI, performance optimization |
| **V4** | The Automaton | Scheduler, MCP server, research, sessions |
| **V5** | The Workspace | Email, calendar, tasks, notes, documents, contacts |
| **V6** | The Ecosystem | Marketplace, graph intelligence, cross-encoder, polish |

**Current focus:** Backend is production-ready. Frontend is being built from scratch via `/project:design`.

## Execution Contract

### Before ANY Work

1. **Skill discovery** — check `.claude/skills/` for applicable skills. **Skill-first ALWAYS**
2. **Branch** — create `feat/<topic>` from `main`

### During Work

1. **TDD when applicable** — write test, verify fail, implement, verify pass
2. **Skill-first** — check for applicable skills before every significant action
3. **Frontend = design excellence** — invoke brainstorming + writing-plans + UI review for any frontend work
4. **Use MCP servers** — context7 for docs, sequential-thinking for reasoning, playwright for visual testing
5. **Create skills for repeated patterns** — invoke `superpowers:writing-skills` when workflow repeats 2+ times
6. **Commit frequently** — after each logical unit
7. **Run hooks on change** — `make hooks-onchange`
8. **Follow architecture** — file placement rules, ownership checks, API conventions

### After Work

1. **Run tests** — `make test` + `cd frontend && npm test` (if frontend exists)
2. **Run lint** — `make lint` + `make format`
3. **Reflection** — use `/project:reflect` before marking complete
4. **Merge** — after all checks pass

### Completion Criteria (for any component)

- [ ] Tests passing
- [ ] Lint clean
- [ ] Build succeeds
- [ ] Documentation updated (if applicable)
- [ ] ADR created (if architectural decision)

## Architecture Constraints

These rules are immutable.

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

**Framework:** Next.js 15 App Router + React 19 + TypeScript + Tailwind CSS

- **Build:** Run via `/project:design` — builds from scratch in 13 phases.
- **Auth:** `AuthProvider` bootstraps via `GET /me`. Auto token refresh on 401.
- **Proxy:** Client → Next.js API route → FastAPI. Same-origin, no CORS.
- **State:** React Context for auth. Component-local everywhere else.
- **Design:** DESIGN.md tokens. Dark-only. Geist font. Tonal elevation.
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
| Frontend Features | `frontend/src/features/<module>/` |
| Frontend Shared | `frontend/src/shared/` |
| Tests | `tests/` (project root) |
| Migrations | `migrations/versions/` |
| Docs | `docs/` |
| ADRs | `docs/decisions/` |
| Skills | `.claude/skills/` |
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
make design         # Rebuild frontend from scratch
./start.sh          # Self-contained launcher
```

## Mandatory Workflow

```
Branch → Skill Discovery → Brainstorm → Plan → Implement → Test → Validate → Review → Reflect → Merge
```

Every significant task follows this.

### Quick Start — Frontend Build

```
/project:design          → Rebuild entire frontend from scratch (13 phases)
/project:design resume   → Continue from last built phase
/project:design validate → Just verify build passes
/project:design polish   → Final quality pass
```

### Skill-First Architecture

```text
Commands (orchestrate)
    ↓
Workflows (coordinate)
    ↓
Skills (contain reusable intelligence)
    ↓
Hooks (enforce quality automatically)
```

- **Commands** are thin orchestrators. They invoke skills and compose workflows.
- **Skills** (in `.claude/skills/`) contain reusable intelligence.
- **Discovery is automatic.** Every command starts with `cortex-repo-discovery`.

### CORTEX Skills Reference

| Skill | When to Use |
|-------|-------------|
| `cortex-repo-discovery` | First step of every command — find repo root, set CWD |
| `cortex-repository-intelligence` | Before planning or analysis — discover git state, phase, repo structure |
| `cortex-repo-health-scan` | Weekly health check, before release, quality concerns |
| `cortex-ecosystem-integration` | After significant changes — verify ecosystem coherence |
| `cortex-architecture-drift` | Before big changes — check architecture alignment |
| `cortex-adversarial-challenge` | Before major decisions — poke holes in approach |
| `cortex-system-validation` | Before merge — run full test/lint/build verification |
| `cortex-engineering-review` | Before push — code quality, patterns, correctness |
| `cortex-progress-tracker` | After completing work — update progress.md |
| `cortex-post-reflection` | Before completion — systematic reflection framework |
| `cortex-documentation-consistency` | After structural changes — verify doc accuracy |

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
| Frontend design | Before merge | `/impeccable polish` |

### Clarification Rules

**MUST ask human:** Irreversible decisions, multiple valid paths, scope ambiguity, >2 subsystems affected, new technology proposed.

**MAY proceed:** Well-defined tasks, established patterns, mechanical changes, test/doc updates.

**COMMIT RULE:** Always make git msg one line in standard manner. Never add any co-authored-by text.

## Strategic Commands

### Orchestrators

| Command | When | Purpose |
|---------|------|---------|
| `/project:update` | Before significant changes | Transforms ideas into approved plans |
| `/project:develop` | Start of session | Determines next work, delegates to cortex workflow |
| `/project:design` | Frontend work | Rebuilds frontend from scratch in phases |

### Specialist Commands

| Command | When | Purpose |
|---------|------|---------|
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

## Common Gotchas

- `start.sh` uses port 5435 (user-space PG). `docker-compose.yml` uses 5432. Different.
- `conftest.py` compiles `JSONB → JSON` for SQLite. Real DB uses JSONB.
- `migrations/env.py` imports all models for Alembic autogenerate.
- Route order: specific routes before parameterized (e.g., `/models/installed` before `/models/{id}`).
- `cortexCode` Rust crate: `cargo build --release` in `crates/code-intel/` before Python use.

## Testing

Tests at project root in `tests/`. SQLite in-memory, mocked external services. No real Postgres/Redis/Qdrant needed.

Frontend: Vitest + jsdom + React Testing Library (once scaffolded via `/project:design`).

## Codebase Metrics

| Metric | Value |
|--------|-------|
| Backend Python files | 379 |
| Backend LoC | 40,947 |
| Frontend TSX/TS files | 107 |
| Frontend LoC | 9,933 |
| Test files | 169 |
| Test LoC | 18,041 |
| Backend tests | 1,743 passing |
| API endpoints | 186 (domain) + 9 (auth) |
| Frontend pages | 17 real + 4 Coming Soon |
| Frontend components | 38 feature + 10 shared UI |
| Database migrations | 37 |
| Documentation files | 57 |
| Git commits | 636 |

## Environment

Required: `SECRET_KEY`, `DATABASE_URL` (port 5435), `APP_NAME`, `API_V1_PREFIX`. Optional: `REDIS_URL`, `CORTEX_ROOT`, `MEMORY_PATH`, `VAULT_PATH`.

## Reference Documents

| Topic | Location |
|-------|----------|
| Architecture | `docs/architecture/overview.md` |
| Design System | `DESIGN.md` |
| Product Definition | `PRODUCT.md` |
| API Reference | `docs/reference/api.md` |
| Database Schema | `docs/reference/database.md` |
| Governance | `docs/guides/governance.md` |
| ADRs | `docs/decisions/` |
| Domain Docs | `docs/domains/` |
