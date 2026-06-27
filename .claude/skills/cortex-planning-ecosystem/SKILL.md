# cortex-planning-ecosystem

Load and understand all planning artifacts.

## When to Use

Before planning analysis, drift detection, or any operation needing the full planning context.

## Process

### 1. Ensure Repo Root

Run `cortex-repository-intelligence` first if not already done.

### 2. Load Planning Artifacts

Read:

- `.agents/plans/GUIDE.md` — The constitution: architecture principles, what to build/reject
- `.agents/plans/IMPLEMENTATION_STEPS.md` — Execution order: version phases, deliverables
- `.agents/plans/FinalCompatibilities.md` — reference architecture cross-reference matrix
- `.agents/plans/IMPLEMENTATION_STEPS.md` — Version timeline, execution order
- Active phase plan: `.agents/plans/versions/v{ACTIVE}/Phase-{N}.md`
- Active progress: `.agents/plans/versions/v{ACTIVE}/progress.md`

### 3. Note Available Ecosystem

```bash
echo "Commands:" && ls .claude/commands/project/ 2>/dev/null
echo "Hooks:" && ls .claude/hooks/ 2>/dev/null
echo "Skills (cortex):" && ls -d .claude/skills/cortex-*/ 2>/dev/null
```

## Output

Complete understanding of planned state — roadmap, versions, phases, deliverables, exit criteria.

## Examples

**Before planning drift analysis:**
```
Invoke cortex-planning-ecosystem, then cortex-architecture-drift.
```
