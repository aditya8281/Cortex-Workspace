# /project:start — CORTEX Session Launcher

Supreme session initializer. Runs every health system in the ecosystem, auto-resolves all issues, and drops into development with zero friction. Never stops, never asks — detects, fixes, continues.

## Absolute Rules

### Rule 1: Skill-First — ALWAYS

Before ANY action, check for applicable skills. This is non-negotiable.

```
User request received
    ↓
Check: does a skill exist for this?
    YES → Invoke skill. Follow it exactly.
    NO  → Check: is this repeatable or could a skill be created?
        YES → Execute once, then create skill via superpowers:writing-skills
        NO  → Execute directly
```

**Applies to:** Every response, every action, every task. No exceptions.

**Available skill families:**
- **Cortex skills** (`.claude/skills/cortex-*`) — 18 skills for repo management
- **Superpowers skills** (via Skill tool) — brainstorming, TDD, writing-plans, writing-skills, systematic-debugging, code-review, verification-before-completion, subagent-driven-development
- **MCP tools** — context7 (library docs), sequential-thinking (reasoning), playwright (browser automation), context-mode (knowledge base)

### Rule 2: Frontend = Design Excellence

Any work touching `frontend/` MUST invoke these skills:
- `superpowers:brainstorming` — before any UI design decision
- `superpowers:writing-plans` — before any frontend implementation
- UI Review hook (`.claude/hooks/ui-review/`) — auto-triggers on `.tsx/.ts/.css` changes
- Playwright hook — validates build + visual regression
- Context7 — for latest React/Next.js/Tailwind docs before any frontend code

### Rule 3: Create Skills for Repeated Patterns

If you execute a workflow 2+ times that could be automated:
1. Complete the current execution
2. Invoke `superpowers:writing-skills` to create a persistent skill
3. Save to `.claude/skills/<skill-name>/SKILL.md`
4. Log: "Created skill: <name> for <pattern>"

### Rule 4: Use MCP Servers

- **context7** — Always fetch latest docs for React, Next.js, Tailwind, FastAPI, SQLAlchemy before coding
- **sequential-thinking** — Use for complex reasoning before architectural decisions
- **playwright** — Browser automation for visual testing
- **context-mode** — Knowledge base for session memory, batch analysis, code derivation

### Rule 5: Hooks Enforce Quality

Every code change triggers relevant hooks automatically:
- **UI Review** → frontend file changes
- **Architecture** → structural changes
- **Code Quality** → all code changes
- **Skill Discovery** → checks for skill gaps
- **Contract** → API contract validation
- **Completion Gate** → pre-merge validation

---

## Instructions

### 1. Repository Intelligence + Ecosystem Integration

Invoke `cortex-repo-discovery`.
Invoke `cortex-repository-intelligence`.
Invoke `cortex-ecosystem-integration`.

**Collect:**
- Git branch, status, recent commits, stash
- Active version from progress.md
- Current phase, completion state
- Repo structure snapshot

### 2. Pre-Flight: Git Hygiene

```bash
git status --porcelain
git branch --show-current
git stash list 2>/dev/null
```

- **Dirty tree + on main:** Create `feat/<next-phase-topic>`, commit all as `WIP: auto-save before continuing`
- **Dirty tree + on feature branch:** Commit all as `WIP: auto-save before continuing`
- **On main + no active work:** Auto-create `feat/<next-phase-topic>`
- **Detached HEAD:** Create branch or return to main
- **Never develop on main. Never leave uncommitted work blocking progress.**

### 3. Pre-Flight: System Validation

Invoke `cortex-system-validation`. This runs the full pipeline:

1. **Backend tests:** `make test`
2. **Lint:** `make lint`
3. **Format check:** `make format --check`
4. **Frontend tests:** `cd frontend && npm test` (if frontend exists)
5. **Frontend build:** `cd frontend && npm run build` (if frontend exists)

**Auto-resolve any failure:**
- Test failures: Read output → identify root cause → fix code (not test) → re-run → commit `fix: auto-resolve test failures`
- Lint errors: `make format` → re-run lint → fix remaining → commit `style: auto-resolve lint errors`
- Build failures: Read error → fix → re-run → commit `fix: auto-resolve build failure`
- **Max 3 fix attempts per issue, then escalate to user.**

### 4. Pre-Flight: Integrity Scan

Invoke `cortex-integrity` with mode `quick` (changed files only).

This scans:
- **Structural:** Import correctness, module boundaries, file placement
- **Dependency:** Missing or circular imports, broken references
- **Configuration:** settings.py consistency, environment variable usage

**If findings found:**
- CRITICAL/HIGH: Auto-fix immediately (fix the code, not the finding)
- MEDIUM: Log and continue
- LOW: Log only

**If quick scan clean:** Run `full` integrity scan for deeper coverage.

### 5. Pre-Flight: Hook Health

```bash
python .claude/hooks/run_hooks.py 2>/dev/null || echo "Hook system not available"
```

- Report pass/fail per hook
- If hooks fail: Read error, fix the underlying issue, re-run
- Log hook health status

### 6. Pre-Flight: Dependency Health

```bash
# Backend
pip check 2>&1 | head -20

# Frontend (if exists)
cd frontend && npm ls --depth=0 2>&1 | head -20
```

- **Missing deps:** Auto-install (`pip install -r requirements.txt` / `npm install`)
- **Conflicts:** Log as warning, continue
- **Outdated:** Log only, do not auto-update

### 7. Pre-Flight: Migration Status

```bash
.venv/bin/alembic history --indicate-head 2>/dev/null | tail -5
```

- If pending migrations exist: Log warning "N pending Alembic migrations"
- Do NOT auto-apply (destructive action requires user confirmation)

### 8. Pre-Flight: Tech Debt Quick Scan

```bash
grep -rn "TODO\|FIXME\|HACK\|XXX" backend/ frontend/src/ --include="*.py" --include="*.ts" --include="*.tsx" 2>/dev/null | wc -l
```

- Count total debt markers
- If >50: Log warning with top 5 files by count

### 9. Pre-Flight: Architecture Drift Check

Invoke `cortex-architecture-drift`.

Check:
- File placement matches GUIDE.md rules
- API patterns match conventions (response_model=, ownership checks)
- Service constructor injection patterns
- Frontend feature module structure matches CONVENTIONS.md

### 10. Pre-Flight: Documentation Consistency

Invoke `cortex-documentation-consistency`.

Quick check:
- CLAUDE.md paths match actual file locations
- Phase plans reference existing files
- ADR count matches docs/decisions/ count

### 11. Pre-Flight: Skill Gap Detection

Invoke `cortex-repo-health-scan`.

Check:
- All skills in `.claude/skills/` have definition files
- No stale skills (>30 days without update)
- No unused skills (no references in docs/commands/workflows)
- Skill coverage for common workflows

### 12. Pre-Flight: MCP Server Availability

Verify connected MCP servers:
- **context7** — Library documentation fetching
- **sequential-thinking** — Complex reasoning support
- **playwright** — Browser automation for visual testing
- **context-mode** — Knowledge base and code derivation

If any MCP server is unavailable, log warning but continue.

### 13. Phase Drift Detection

Compare progress.md claims against git reality:

```bash
grep "Completed" .agents/plans/versions/vX.XX/progress.md
```

- For each "Completed" phase: Check git log for matching commits
- **Phase marked complete but no commits:** Reset to "Not started" in progress.md
- **Phase marked "In Progress":** Count completed tasks vs total
- Report: "Resuming P0X: N/M tasks done" or "⚠️ Phase P0X reset"

### 14. Find Active Version & Next Phase

Read `.agents/plans/IMPLEMENTATION_STEPS.md`.

Find the first version where progress.md shows incomplete phases. If none active, start with v1.01 (or next after latest complete).

Read active version's progress.md. Find first phase with status "Not started".

### 15. Consolidated Status Report

Display the full session status:

```
## CORTEX Session Launch — [date]

**Branch:** <current branch>
**Active Version:** vX.XX — <name>
**Next Phase:** P0X — <phase name>
**Phases Complete:** N/M

### System Health
| Check                | Status | Details |
|----------------------|--------|---------|
| Backend Tests        | ✅/❌  | N passed, M failed |
| Frontend Tests       | ✅/❌  | N passed / skipped |
| Lint                 | ✅/❌  | Clean / N errors fixed |
| Format               | ✅/❌  | Clean / applied |
| Frontend Build       | ✅/❌  | Clean / N errors |
| Integrity (quick)    | ✅/❌  | N findings (C:H:M:L) |
| Hooks                | ✅/❌  | N/N passing |
| Dependencies         | ✅/❌  | Backend OK / Frontend OK |
| Migrations           | ✅/⚠️  | Up to date / N pending |
| Architecture Drift   | ✅/❌  | Clean / N issues |
| Docs Consistency     | ✅/⚠️  | Clean / N inconsistencies |
| Skill Health         | ✅/⚠️  | N skills, M stale |
| MCP Servers          | ✅/⚠️  | N/M available |
| Tech Debt            | ℹ️     | N markers across M files |

### Auto-Resolve Report
- Git: <cleaned / auto-created branch / already clean>
- Tests: <fixed N failures / all passing>
- Lint: <fixed N errors / clean>
- Integrity: <fixed N issues / clean>
- Hooks: <fixed N failures / all passing>
- Dependencies: <installed N missing / all satisfied>
- Drift: <reset N phases / none detected>

### Skill Coverage
- Available: N cortex + M superpowers skills
- Gaps: <list any missing skill for common workflows>
- Recommendation: <create skill X for repeated pattern Y>

Ready to execute. Auto-invoking /project:cortex...
```

### 16. Auto-Execute

Always auto-invoke `/project:cortex` with the active version and phase. No confirmation needed — all health issues were resolved in steps 2-14.

---

## Execution Order Summary

```
Discovery → Git Hygiene → System Validation → Integrity Scan → Hook Health
    → Dependency Health → Migration Status → Tech Debt → Architecture Drift
        → Docs Consistency → Skill Gaps → MCP Check → Phase Drift
            → Find Next → Status Report → Execute
```

**Principles:**
- Never stop for fixable issues — auto-fix and continue
- Never auto-apply migrations (destructive)
- Never auto-update dependencies (risky)
- Max 3 fix attempts per issue, then escalate
- All fixes committed with descriptive messages
- Status report is the single source of truth for session state
- **Skill-first ALWAYS** — check before every action
- **Frontend = design excellence** — invoke design skills proactively
- **Create skills for repeated patterns** — evolve the ecosystem
- **Use MCP servers** — leverage external knowledge and automation
- **Hooks enforce quality** — let governance work automatically

---

## Feedback Loop

**On entry:** Read `.claude/ecosystem/feedback.json`, filter last 10 entries where `command` matches this command name. If learnings exist, adapt behavior accordingly.

**On exit:** Append entry to `.claude/ecosystem/feedback.json`:
```json
{
  "timestamp": "<ISO-8601>",
  "command": "/project:start",
  "run_id": "<uuid>",
  "outcome": "success|failure|partial",
  "learnings": ["<what was discovered>"],
  "suggestions": ["<improvements for next run>"],
  "duration_ms": 0
}
```
