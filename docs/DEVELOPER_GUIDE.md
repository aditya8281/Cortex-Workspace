# Cortex Agentic Development Guide

This guide explains how the agentic development ecosystem works in Cortex — the tools, workflows, hooks, and automation that every agent (human or AI) follows.

---

## Quick Reference

| Task | Command | What it does |
|------|---------|--------------|
| Start work | `make auto-pre` | Validates context, plans, architecture |
| During work | `make hooks-onchange` | Validates code quality, contracts |
| Check health | `make auto-health` | Dead code, duplicates, drift |
| Before push | `make hooks-push` | Quality, architecture, contract, docs |
| Before merge | `make hooks-merge` | All 10 hooks |
| Full check | `make auto` | All automation + health + bugs |
| Report | `make auto-report` | Generate health report |

---

## The Workflow

Every task follows this lifecycle:

```
Context → Brainstorm → Plan → Implement → Test → Validate → Review → Simplify → Complete
```

### 1. Context (Pre-Work)

Before starting any work, validate that the project context is ready:

```bash
make auto-pre
```

This checks:
- CLAUDE.md, AGENTS.md, governance docs exist and have content
- No architecture drift (no duplicate systems, no stale files)
- Implementation plan exists (if needed)

**What to do if it fails:** Read the missing docs. If governance files are missing, the ecosystem is broken — stop and fix.

### 2. Brainstorm

For any design work, use the `superpowers:brainstorming` skill:
- Ask clarifying questions one at a time
- Propose 2-3 approaches with trade-offs
- Present design sections, get approval after each
- Write spec to `docs/superpowers/specs/`

### 3. Plan

After design approval, use `superpowers:writing-plans` skill:
- Create implementation plan with explicit steps
- Identify affected files and systems
- Assess blast radius
- Present to human for approval

### 4. Implement

During implementation, run hooks on code changes:

```bash
make hooks-onchange
```

This validates:
- Code quality (ruff, mypy, dangerous patterns)
- Frontend/backend contract (endpoints match)
- Import validation

**After each commit:**
```bash
make format    # Format code
make lint      # Check lint + types
```

### 5. Test

```bash
make test           # Backend pytest
cd frontend && npm test   # Frontend vitest
```

### 6. Validate

Before pushing, run the full validation suite:

```bash
make hooks-push
```

This runs:
- Code quality (ruff, mypy, dangerous patterns, imports)
- Architecture compliance (file placement, model registration, API conventions)
- Frontend/backend contract
- Documentation consistency

### 7. Review

Use `code-review` skill for correctness, `simplify` for quality.
Address all P0/P1 findings.

### 8. Simplify

Use `simplify` skill to clean up code:
- Remove unnecessary complexity
- Consolidate duplicate logic
- Improve naming and structure

### 9. Complete

Before marking work complete, run the completion gate:

```bash
make hooks-merge    # All 10 hooks
make auto-complete  # Tests, docs, build
```

The completion gate blocks completion if:
- Tests are failing
- Lint errors exist
- Type errors exist
- Models changed without migrations

---

## Hook System

### What Are Hooks?

Hooks are automated checks that run at different stages of development. They catch issues early — before code is committed, pushed, or merged.

### The 10 Hooks

| # | Hook | Trigger | Purpose |
|---|------|---------|---------|
| 1 | **UI Review** | Frontend files change | Design tokens, accessibility, states, patterns |
| 2 | **Code Quality** | Any code change | Ruff, MyPy, dangerous patterns, imports |
| 3 | **Contract** | API/schema changes | Frontend/backend endpoint matching |
| 4 | **Architecture** | Major modifications | File placement, model registration, conventions |
| 5 | **Docs Consistency** | Significant changes | Link validity, doc freshness, broken refs |
| 6 | **Planning** | Feature/phase completion | Roadmap drift, ADR format |
| 7 | **Playwright** | Frontend changes | Frontend tests, build validation |
| 8 | **Completion Gate** | Before marking complete | Tests, lint, types, migrations |
| 9 | **Repo Health** | Periodically | Dead code, placeholders, hotspots |
| 10 | **Decision Tracking** | Architecture changes | ADR existence, format validation |

### Running Hooks

```bash
# All hooks
make hooks

# By phase
make hooks-pre       # Pre-commit: UI review + code quality
make hooks-push      # Pre-push: quality + architecture + contract + docs
make hooks-merge     # Pre-merge: all 10 hooks
make hooks-onchange  # On code change: quality + contract

# Single hook
python .claude/hooks/run_hooks.py ui-review
python .claude/hooks/run_hooks.py code-quality
python .claude/hooks/run_hooks.py completion-gate
```

### Hook Output

Each hook returns:
- ✓ **PASS** — no issues found
- ✗ **FAIL** — issues found (check details)
- ⚠ **WARN** — warnings (non-blocking)

---

## Automation Framework

### What Is Automation?

Automation scripts run broader checks than hooks — they validate the entire repository state, not just changed files.

### The 6 Phases

| Phase | Command | What it checks |
|-------|---------|----------------|
| Pre-Work | `make auto-pre` | Context files, plans, architecture consistency |
| Development | `make auto-dev` | Frontend/backend contract, schema, API conventions, types |
| Health | `make auto-health` | Dead code, duplicates, dependencies, drift |
| Bug Discovery | `make auto-bugs` | Placeholders, security, error patterns |
| Completion | `make auto-complete` | Tests, docs, full validation |
| Reports | `make auto-report` | Health report saved to docs/audits/ |

### Running Automation

```bash
# All phases
make auto

# Single phase
make auto-pre
make auto-dev
make auto-health
make auto-bugs
make auto-complete
make auto-report
```

---

## Architecture Rules

### Single Source of Truth

Every topic has exactly one authoritative file:

| Topic | Source |
|-------|--------|
| Agent behavior | CLAUDE.md |
| Security patterns | AGENTS.md |
| Architecture | docs/ARCHITECTURE.md |
| Roadmap | docs/ROADMAP.md |
| API reference | docs/API.md |
| Database schema | docs/DATABASE.md |
| Design system | DESIGN.md |
| Governance | docs/GOVERNANCE.md |
| Workflows | docs/WORKFLOWS.md |
| Decisions | docs/decisions/ |

**Rule:** If a topic appears in multiple files, the source of truth wins. Other files reference it, not duplicate it.

### File Placement Rules

| File type | Location |
|-----------|----------|
| SQLAlchemy models | `backend/app/models/` |
| Pydantic schemas | `backend/app/schemas/` |
| API routers | `backend/app/api/v1/` |
| Services | `backend/app/services/` |
| Managers | `backend/app/managers/` |
| Middleware | `backend/app/middleware/` |
| Background tasks | `backend/app/tasks/` |
| Tests | `tests/` |
| Migrations | `migrations/versions/` |
| Docs | `docs/` |
| ADRs | `docs/decisions/` |
| Audits | `docs/audits/` |
| Skills | `.agents/skills/` |
| Hooks | `.claude/hooks/` |

### Forbidden Paths

These should never exist in the repository:
- `.trae/` — duplicate skill directory
- `.codex/` — stale Codex config
- `.cortex_bootstrap/` — one-time artifact
- `skills-lock.json` — unused lock file

---

## Clarification Rules

### MUST Ask Human

- Irreversible decisions (schema migrations, breaking API changes)
- Multiple valid paths with different trade-offs
- Scope ambiguity or missing requirements
- Changes affecting >2 subsystems
- New technology not in current stack

### MAY Proceed Without Asking

- Well-defined tasks with explicit criteria
- Following established codebase patterns
- Mechanical changes (typos, formatting, imports)
- Updating tests or documentation

---

## Decision Tracking

When making architectural decisions:

1. Create an ADR in `docs/decisions/NNN-name.md`
2. Use the standard format (Status, Date, Context, Decision, Consequences, Alternatives)
3. Get human approval before implementing
4. ADRs are immutable once accepted

---

## Audit Process

### Running an Audit

```bash
make auto-report    # Generate health report
make auto-health    # Check repository health
make auto-bugs      # Find bugs and issues
```

### Audit Report Location

Reports are saved to `docs/audits/YYYY-MM-DD-report.md`.

### What Audits Check

- Architecture drift
- Documentation drift
- Technical debt
- Dead code
- Duplicate code
- Placeholder implementations
- Security vulnerabilities
- Test coverage

---

## CI Pipeline

GitHub Actions runs on every push:

1. **Backend:** ruff lint → mypy → pytest
2. **Frontend:** next lint → tsc → vitest → build

All checks must pass before merge.

---

## Common Patterns

### Adding a New API Endpoint

1. Create router in `backend/app/api/v1/your_domain.py`
2. Register in `backend/app/api/router.py`
3. Add `response_model=` to endpoint decorators
4. Create Pydantic schemas in `backend/app/schemas/`
5. Add frontend API client in `frontend/src/shared/api/`
6. Run `make hooks-onchange` to verify contract

### Adding a New Model

1. Create model in `backend/app/models/your_model.py`
2. Import in `backend/app/main.py` (for Alembic)
3. Run `make migration m="description"`
4. Run `make migrate`
5. Test with `make db-reset`

### Adding a New Skill

1. Create directory in `.agents/skills/your-skill/`
2. Add skill definition file
3. Update AGENTS.md if needed
4. Test the skill

### Adding a New Hook

1. Create directory in `.claude/hooks/your-hook/`
2. Add `hook.py` with `run_hook()` function
3. Register in `.claude/hooks/run_hooks.py`
4. Add to appropriate phase in PHASES dict
5. Test with `make hooks`

---

## Troubleshooting

### "Hooks failing but code looks fine"

Run the specific hook with verbose output:
```bash
python .claude/hooks/run_hooks.py code-quality
```

### "Automation reports stale data"

Clean caches:
```bash
make clean
```

### "Contract hook reports orphaned routes"

Check if the frontend API client calls the route:
```bash
grep -r "your-route" frontend/src/shared/api/
```

### "Architecture hook flags new model"

Import the model in `backend/app/main.py`:
```python
from backend.app.models.your_model import YourModel  # noqa: F401
```

---

## File Structure

```
.claude/
├── hooks/
│   ├── run_hooks.py           # Master hook runner
│   ├── shared/
│   │   └── utils.py           # Shared utilities
│   ├── ui-review/hook.py      # Hook 1
│   ├── code-quality/hook.py   # Hook 2
│   ├── contract/hook.py       # Hook 3
│   ├── architecture/hook.py   # Hook 4
│   ├── docs-consistency/      # Hook 5
│   ├── planning/hook.py       # Hook 6
│   ├── playwright/hook.py     # Hook 7
│   ├── completion-gate/       # Hook 8
│   ├── repo-health/hook.py    # Hook 9
│   └── decision-tracking/     # Hook 10
├── settings.local.json        # Claude Code config

scripts/automation/
├── run_all.py                 # Master automation runner
├── pre_work/                  # Context, plan, architecture checks
├── development/               # Contract, schema, API, types
├── health/                    # Dead code, duplicates, deps, drift
├── bug_discovery/             # Placeholders, security, errors
├── completion/                # Tests, docs, full validation
└── reports/                   # Health, progress, compliance
```

---

## Summary

The Cortex development ecosystem ensures quality through:

1. **Governance docs** — CLAUDE.md, AGENTS.md, docs/GOVERNANCE.md define the rules
2. **Workflows** — docs/WORKFLOWS.md defines the process
3. **Hooks** — 10 automated checks at different stages
4. **Automation** — 6-phase validation framework
5. **CI** — GitHub Actions gates on every push
6. **ADRs** — Architecture decisions are documented and tracked

Every agent follows the same rules. Every change is validated. Every decision is tracked. This is how Cortex maintains quality as it grows.
