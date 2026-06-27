# /project:next — Continue Development

Auto-detect and execute the next phase. Chains phases together for continuous development.

## Instructions

### 1. Discovery

Invoke `cortex-repo-discovery`.

### 2. Find Current State

Read active version's progress.md.

Find the first phase with status "Not started".

### 3. If Phase Exists

Show: "Next: P0X — <name>. Executing..."

Auto-invoke `/project:cortex` with the phase.

### 4. If Version Complete

Show:
```
## Version Complete: vX.XX — <name>

All phases completed.
**Total Duration:** X days
**Capabilities Implemented:** N

Next version: v(Y).XX — <name>
Run /project:start v(Y).XX to continue.
```

### 5. If All Versions Complete

Show: "All versions complete. CORTEX is fully implemented."
