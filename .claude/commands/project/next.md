# /project:next — Continue Development

Auto-detect next phase, auto-resolve any issues, and execute. Never stops — chains phases continuously.

## Instructions

### 1. Discovery

Invoke `cortex-repo-discovery`.

### 2. Pre-Flight Auto-Resolve

Run quick fixes before chaining. Development must never stop.

#### 2a. Uncommitted Work

```bash
git status --porcelain
```

- If dirty: commit with `WIP: auto-save before phase chain` on current branch
- If on main: create feature branch first, then commit

#### 2b. Tests Failing

```bash
make test 2>&1 | tail -10
```

- If tests fail: read failures, fix code, re-run, commit fix
- Log: "Auto-resolved N test failures from previous phase"

#### 2c. Previous Phase Drift

- Check git log for commits matching the last completed phase's topic
- If marked complete but no commits: reset that phase to "Not started" in progress.md
- Log: "⚠️ Phase P0X had no commits — will re-execute"

### 3. Find Current State

Read active version's progress.md.

Find the first phase with status "Not started".

### 4. If Phase Exists

Show: "Next: P0X — <name>. Executing..."

Auto-invoke `/project:cortex` with the phase.

### 5. If Version Complete

Show:
```
## Version Complete: vX.XX — <name>

All phases completed.
**Total Duration:** X days
**Capabilities Implemented:** N

Next version: v(Y).XX — <name>
Run /project:start v(Y).XX to continue.
```

### 6. If All Versions Complete

Show: "All versions complete. CORTEX is fully implemented."
