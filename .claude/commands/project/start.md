# /project:start — Quick Start

Read current state and begin development.

## Instructions

### 1. Discovery

Invoke `cortex-repo-discovery`.
Invoke `cortex-repository-intelligence`.

### 2. Find Active Version

Read `.agents/plans/IMPLEMENTATION_STEPS.md`.

Find the first version where progress.md shows incomplete phases.

If no version is active, start with v1.01.

### 3. Find Next Phase

Read the active version's progress.md.

Find the first phase with status "Not started".

### 4. Display Status

Show:
```
## CORTEX Development Status

**Branch:** <current branch>
**Active Version:** vX.XX — <name>
**Next Phase:** P0X — <phase name>
**Phases Complete:** N/M
**Estimated Duration:** X-Y hours

Ready to execute? Run /project:cortex
```

### 5. Auto-Execute (if user confirms)

If user says "yes" or "go", auto-invoke /project:cortex with the active version and phase.
