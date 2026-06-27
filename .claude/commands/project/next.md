# /project:next — Continue Development

Auto-detect and execute the next phase. Chains phases together for continuous development.

## Instructions

### 1. Discovery

Invoke `cortex-repo-discovery`.

### 2. Pre-Flight Check

Quick health gate before chaining:
```bash
git status --porcelain
make test 2>&1 | tail -3
```

- If uncommitted work exists: "⚠️ Uncommitted changes. Commit or stash before chaining."
- If tests failing: "⚠️ Tests failing from previous phase. Fix before proceeding."
- Block auto-execute if critical issues found.

### 3. Find Current State

Read active version's progress.md.

Find the first phase with status "Not started".

### 4. If Phase Exists

Verify the previous phase (if any) was genuinely completed:
- Check git log for commits matching the previous phase's task descriptions
- If marked complete but no commits found: "⚠️ Phase drift detected. Run `/project:verify` first."
- If OK: Show "Next: P0X — <name>. Executing..." and auto-invoke `/project:cortex`.

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
