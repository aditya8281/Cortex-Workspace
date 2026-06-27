# CLAUDE.md — CORTEX Control Plane

This file is the **execution contract** for Claude Code. It defines what CORTEX is, what to do on entry, and what rules govern all work.

## What CORTEX Is

CORTEX is a local-first machine intelligence layer — a persistent AI brain on your machine. FastAPI backend + Next.js frontend + Rust code intelligence + Python CLI. Encrypted vaults, knowledge graphs, vector search, LLM integration, autonomous agents. Not a chatbot. Not a repo assistant. An entire local AI brain ecosystem.

## Entry Protocol — MANDATORY

When entering this repository, Claude MUST do these in order:

### 1. Determine Active Development State

```bash
# Read the constitution to understand the full system
cat .agents/plans/GUIDE.md

# Find which version is currently being developed
grep -r "in_progress\|active\|current" .agents/plans/versions/*/progress.md

# Read the active version's phase plan
cat .agents/plans/versions/vX/Phase-1.md  # (replace X with active version)
```

If no version is active (all components show "Not started"), start with **V1: The Brain Works** per `.agents/plans/IMPLEMENTATION_STEPS.md`.

### 2. Load the Execution Plan

```bash
# Contributor guide with execution order and constraints
cat .agents/plans/IMPLEMENTATION_STEPS.md

# Architecture constitution (13 binding principles)
cat .agents/plans/GUIDE.md
```

### 3. Verify Governance Infrastructure

```bash
# Hook system
python .claude/hooks/run_hooks.py --help

# Available slash commands
ls .claude/commands/project/

# Available skills
ls .claude/skills/
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
| 2 | **.agents/plans/GUIDE.md** | Constitution — architecture principles, what to build |
| 3 | **AGENTS.md** | Agent behavior rules — security, API patterns |
| 4 | **.agents/plans/IMPLEMENTATION_STEPS.md** | Implementation guide — execution order |
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
2. **Read the constraints** — .agents/plans/GUIDE.md architecture principles apply always
3. **Verify entry state** — run the entry protocol above
4. **Skill discovery** — check `.claude/skills/` for applicable skills
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

These rules are immutable. See `.agents/plans/GUIDE.md` for full rationale.

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

Every significant task follows this. No shortcuts. See `.agents/plans/IMPLEMENTATION_STEPS.md` for details.

### Quick Start — Automated Plan-Oriented Development

```
/project:start          → Show current state, find next phase
    ↓ (auto-invoke)
/project:cortex         → Execute phase (TDD: test → implement → verify → commit per task)
    ↓ (auto-invoke after completion)
/project:next           → Chain to next phase, or report version complete
    ↓ (repeat)
/project:phase vX P0N   → Manual jump to any phase
```

**Every command reads GUIDE.md and IMPLEMENTATION_STEPS.md for architecture context.**

### Skill-First Architecture

The Cortex ecosystem follows a skill-first hierarchy:

```text
Commands (orchestrate)
    ↓
Workflows (coordinate)
    ↓
Skills (contain reusable intelligence)
    ↓
Hooks (enforce quality automatically)
```

- **Commands** are thin orchestrators. They invoke skills and compose workflows. They do not contain reusable logic.
- **Skills** (in `.claude/skills/`) contain reusable intelligence. Each has a documented purpose, step-by-step process, and output definition.
- **Shared phases** (`.agents/plans/shared-phases.md`) delegate to skills. Updating a skill updates all commands that reference it.
- **Discovery is automatic.** Every command starts with `cortex-repo-discovery` to find the repository root from any directory.

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

**WHENECER COMMIT** RULE (SHOULD ALWAYS FOLLOW) : always make git msg of one line in standard manner, and never add any co authored by text never.

## Strategic Commands

### Orchestrators (design → improve → develop)

| Command | When | Purpose |
|---------|------|---------|
| `/project:update` | Before significant changes | **Top-level orchestrator.** Transforms ideas into approved plans. 8 phases: intelligence → exploration → specification → impact analysis → planning integration → adversarial review → approval → handoff. Never implements. |
| `/project:enhance_plan` | After phases or when plans drift | **Planning ecosystem improver.** Reviews all plans for implementation/planning/architecture/vision drift. Actively improves plans. Never changes product vision. |
| `/project:develop` | Start of session | **Development orchestrator.** Determines next work, generates brief if ambiguous, delegates to cortex workflow, runs reflection, produces completion report. |

### Autonomous Agent

| Command | When | Purpose |
|---------|------|---------|
| `/project:start` | Start of session | **Quick start.** Reads active version/phase from progress.md, displays status, offers to execute next phase automatically. |
| `/project:cortex` | After /project:start | Full autonomous development iteration: discovery → branch → TDD implementation → validation → review → reflection → cleanup → version integration. |
| `/project:next` | After completing a phase | **Phase chaining.** Auto-detects next incomplete phase and invokes /project:cortex. Continues until version complete. |
| `/project:phase` | Manual phase selection | Execute a specific phase by name (e.g., `/project:phase v1.02 P03`). Shows available phases if no args. |

### Specialist Commands

| Command | When | Purpose |
|---------|------|---------|
| `/project:prompt` | Before complex work | Generate ecosystem-aware prompts |
| `/project:audit` | During audits | Deep code-level scan (runtime errors, dead code, integration issues) |
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
| Architecture | `docs/architecture/overview.md` |
| Constitution | `.agents/plans/GUIDE.md` |
| Governance | `docs/guides/governance.md` |
| Implementation Guide | `.agents/plans/IMPLEMENTATION_STEPS.md` |
| API Reference | `docs/reference/api.md` |
| Database Schema | `docs/reference/database.md` |
| Design System | `DESIGN.md` |
| Phase Plans | `.agents/plans/versions/vX/Phase-N.md` |
| Progress Tracking | `.agents/plans/versions/vX/progress.md` |
| ADRs | `docs/decisions/` |
| Domain Docs | `docs/domains/` |
