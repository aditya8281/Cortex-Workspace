# /project:start — Quick Start

Read current state, auto-resolve issues, and begin development. Never stops — detects problems, fixes them, continues.

## Instructions

### 1. Discovery

Invoke `cortex-repo-discovery`.
Invoke `cortex-repository-intelligence`.

### 2. Pre-Flight Health Check + Auto-Resolve

Run these checks and auto-fix each one. Development must never stop.

#### 2a. Uncommitted Work

```bash
git status --porcelain
```

- If dirty tree exists:
  - If on `main`: create branch `feat/<active-phase-topic>`, commit or stash
  - If on feature branch: commit all current work with message "WIP: auto-save before continuing"
  - Never leave uncommitted work blocking progress

#### 2b. Tests Failing

```bash
make test 2>&1 | tail -10
```

- If tests fail:
  - Read the failing test output
  - Identify the root cause (missing import, broken mock, API mismatch)
  - Fix the code to make tests pass
  - Re-run tests to confirm
  - Commit the fix: `fix: auto-resolve test failures from previous session`
  - Log: "Auto-resolved N test failures"

#### 2c. Lint Errors

```bash
make lint 2>&1 | tail -10
```

- If lint fails:
  - Run `make format` to auto-fix formatting
  - Re-run `make lint` to check remaining issues
  - Fix any remaining issues (unused imports, type errors)
  - Commit: `style: auto-resolve lint errors`
  - Log: "Auto-resolved N lint errors"

#### 2d. Phase Drift Detection

Compare progress.md claims against git reality:
- For each phase marked "Completed", check if commits exist matching the phase topic
- If a phase is marked complete but no commits found:
  - Mark it back to "Not started" in progress.md
  - Log: "⚠️ Phase P0X had no commits — reset to Not started"
  - This phase will now be re-executed

#### 2e. Partial Phase Detection

If the current phase shows "In Progress":
- Read the phase plan
- Check git log for commits matching task descriptions
- Count completed tasks vs total
- Report: "Resuming P0X: N/M tasks done"

#### 2f. On Main Branch

```bash
git branch --show-current
```

- If on `main` with no active work: auto-create `feat/<next-phase-topic>` branch
- Never develop on main

### 3. Find Active Version

Read `.agents/plans/IMPLEMENTATION_STEPS.md`.

Find the first version where progress.md shows incomplete phases.

If no version is active, start with v1.01.

### 4. Find Next Phase

Read the active version's progress.md.

Find the first phase with status "Not started".

### 5. Display Status

Show:
```
## CORTEX Development Status

**Branch:** <current branch>
**Active Version:** vX.XX — <name>
**Next Phase:** P0X — <phase name>
**Phases Complete:** N/M
**Estimated Duration:** X-Y hours

### Auto-Resolve Report
- Uncommitted work: Cleaned (committed on feat/xxx) / Already clean
- Tests: Fixed (2 failures resolved) / Passing
- Lint: Fixed (formatting applied) / Clean
- Drift: None / Reset P03 to Not started (no commits found)

Ready to execute. Auto-invoking /project:cortex...
```

### 6. Auto-Execute

Always auto-invoke `/project:cortex` with the active version and phase. No confirmation needed — health issues were already resolved in step 2.
