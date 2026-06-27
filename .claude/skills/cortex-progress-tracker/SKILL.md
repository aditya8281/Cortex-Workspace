# cortex-progress-tracker

Track and update version/phase progress. Provides read/write access to progress.md files.

## When to Use

After completing a phase, task, or version. Before starting new work to check current state.

## Process

### 1. Read Current State

Read the version's progress.md file.

Parse: phases, statuses, completion times.

### 2. Update Status

After phase completion:
- Set phase status to "Completed"
- Record completion timestamp
- Update summary (completed count, remaining count)

### 3. Generate Report

Output:
```
## Progress: vX.XX — <name>

| Phase | Status | Completed |
|-------|--------|-----------|
| P01 | ✅ Completed | 2026-06-27 |
| P02 | ✅ Completed | 2026-06-27 |
| P03 | 🔄 In Progress | — |
| P04 | ⏳ Not started | — |

**Progress:** 2/4 phases (50%)
**Estimated Remaining:** 2-3 hours
```

### 4. Milestone Detection

When a version completes:
- Mark version as complete in progress.md
- Check if all dependencies for next version are met
- Report: "vX.XX complete. Ready for v(Y).XX."
