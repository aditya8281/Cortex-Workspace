# /project:start — Quick Start

Read current state, verify health, and begin development.

## Instructions

### 1. Discovery

Invoke `cortex-repo-discovery`.
Invoke `cortex-repository-intelligence`.

### 2. Pre-Flight Health Check

Before showing status, verify the repository is healthy:

```bash
# Uncommitted work?
git status --porcelain

# Current branch
git branch --show-current

# Recent commits (last 5)
git log --oneline -5

# Quick test health
make test 2>&1 | tail -5

# Lint health
make lint 2>&1 | tail -5
```

Report any issues found:
- **Uncommitted work:** "⚠️ N uncommitted changes. Resolve before continuing."
- **Tests failing:** "⚠️ Tests failing. Last session may have left broken code."
- **Lint errors:** "⚠️ Lint errors present. Run `make lint` for details."
- **Dirty tree on main:** "⚠️ Uncommitted work on main. Branch first."

If critical issues found (tests failing), ask user to resolve before proceeding.

### 3. Find Active Version

Read `.agents/plans/IMPLEMENTATION_STEPS.md`.

Find the first version where progress.md shows incomplete phases.

If no version is active, start with v1.01.

### 4. Find Next Phase

Read the active version's progress.md.

Find the first phase with status "Not started".

If the current phase shows "In Progress", check for partially completed work:
- Read the phase plan
- Check git log for commits matching the phase's task descriptions
- Report: "Phase P0X appears in progress. Tasks completed: N/M. Resume or restart?"

### 5. Phase Drift Check

Compare progress.md claims against reality:
- If a phase is marked "Completed", verify related commits exist
- If no commits match a completed phase, flag: "⚠️ Phase P0X marked complete but no matching commits found. Possible drift."
- If drift detected, suggest running `/project:verify` before continuing.

### 6. Display Status

Show:
```
## CORTEX Development Status

**Branch:** <current branch>
**Active Version:** vX.XX — <name>
**Next Phase:** P0X — <phase name>
**Phases Complete:** N/M
**Estimated Duration:** X-Y hours

### Health Check
- Tests: PASS / FAIL
- Lint: PASS / FAIL
- Git: Clean / N uncommitted changes
- Drift: None detected / Warning: ...

Ready to execute? Run /project:cortex
```

### 7. Auto-Execute (if user confirms)

If user says "yes" or "go" AND health check passed, auto-invoke `/project:cortex` with the active version and phase.

If health check has warnings, ask user to confirm despite warnings.
