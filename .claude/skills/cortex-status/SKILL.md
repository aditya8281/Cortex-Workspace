# CORTEX Status

Report the current development status of the Cortex project.

## When to Use

- On entry to the repository
- When asked "what version are we on?"
- When asked "what's the current phase?"
- On request via `/project:status`

## Steps

1. Read `.agents/plans/ACTIVE_VERSION.md` for current version/phase
2. Read `.agents/plans/versions/vX/progress.md` for component status
3. Count completed vs pending components
4. Check recent git history for active work
5. Generate status report

## Output Format

```markdown
# CORTEX Status

## Current Version
**V1: The Brain Works** — Phase 1: Agent Intelligence

## Progress
- Components: N completed / M total (P%)
- Phase: N/M phases complete
- Active branch: feat/xxx

## Recent Activity
- Last commit: [message] (time ago)
- Files changed: N

## Next Steps
1. [Component name] — [what needs to be done]
2. [Component name] — [what needs to be done]
```
