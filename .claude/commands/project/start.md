# /project:start — CORTEX Session Launcher

Supreme session initializer. Runs every health system in the ecosystem, auto-resolves all issues, and drops into development with zero friction. Never stops, never asks — detects, fixes, continues.

## Instructions

### 1. Repository Intelligence

Invoke `cortex-repo-discovery`.
Invoke `cortex-repository-intelligence`.

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

**If quick scan clean and time permits:** Run `full` integrity scan for deeper coverage.

### 5. Pre-Flight: Hook Health

```bash
python .claude/hooks/run_hooks.py --help 2>/dev/null && python .claude/hooks/run_hooks.py 2>/dev/null || echo "Hook system not available"
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
# Check if migrations are pending
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
- Log total for the status report

### 9. Pre-Flight: Architecture Drift Check

Invoke `cortex-architecture-drift`.

Check:
- File placement matches GUIDE.md rules
- API patterns match conventions (response_model=, ownership checks)
- Service constructor injection patterns
- Frontend feature module structure matches CONVENTIONS.md

**If drift found:**
- P0/P1: Auto-fix immediately
- P2/P3: Log for phase execution

### 10. Pre-Flight: Documentation Consistency

Invoke `cortex-documentation-consistency`.

Quick check:
- CLAUDE.md paths match actual file locations
- Phase plans reference existing files
- ADR count matches docs/decisions/ count

**If inconsistencies found:** Log them. Fix if mechanical (path updates), escalate if semantic.

### 11. Phase Drift Detection

Compare progress.md claims against git reality:

```bash
# For each phase marked Completed, verify commits exist
grep "Completed" .agents/plans/versions/vX.XX/progress.md
```

- For each "Completed" phase: Check git log for matching commits
- **Phase marked complete but no commits:** Reset to "Not started" in progress.md
- **Phase marked "In Progress":** Count completed tasks vs total from phase plan
- Report: "Resuming P0X: N/M tasks done" or "⚠️ Phase P0X reset — no commits found"

### 12. Find Active Version & Next Phase

Read `.agents/plans/IMPLEMENTATION_STEPS.md`.

Find the first version where progress.md shows incomplete phases. If none active, start with v1.01 (or next after latest complete).

Read active version's progress.md. Find first phase with status "Not started".

### 13. Consolidated Status Report

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
| Tech Debt            | ℹ️     | N markers across M files |

### Auto-Resolve Report
- Git: <cleaned / auto-created branch / already clean>
- Tests: <fixed N failures / all passing>
- Lint: <fixed N errors / clean>
- Integrity: <fixed N issues / clean>
- Hooks: <fixed N failures / all passing>
- Dependencies: <installed N missing / all satisfied>
- Drift: <reset N phases / none detected>

### Git State
- Recent commits:
  <last 5 commits>

Ready to execute. Auto-invoking /project:cortex...
```

### 14. Auto-Execute

Always auto-invoke `/project:cortex` with the active version and phase. No confirmation needed — all health issues were resolved in steps 2-11.

---

## Execution Order Summary

```
Discovery → Git Hygiene → System Validation → Integrity Scan → Hook Health
    → Dependency Health → Migration Status → Tech Debt Scan → Architecture Drift
        → Documentation Consistency → Phase Drift → Find Next → Status Report → Execute
```

**Principles:**
- Never stop for fixable issues — auto-fix and continue
- Never auto-apply migrations (destructive)
- Never auto-update dependencies (risky)
- Max 3 fix attempts per issue, then escalate
- All fixes committed with descriptive messages
- Status report is the single source of truth for session state
