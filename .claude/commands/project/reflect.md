# /project:reflect — Reflection Framework

Before completing any major task, run through this reflection framework systematically.

## Instructions

1. **Identify the work just completed.** Run `git diff --stat HEAD~1` to see what changed. Summarize: files modified, features built, bugs fixed.

2. **Run through the reflection framework.** For each question, analyze the actual code and changes — don't just answer abstractly.

### Quality
- Could any code be cleaner, simpler, more readable?
- Are there functions that do too much?
- Are variable/function names clear and descriptive?
- Is error handling comprehensive?

### Redundancy
- Is anything duplicated that could be consolidated?
- Are there similar patterns in different files that could share a utility?
- Are there repeated strings/values that should be constants?

### Automation
- Is any manual step that could be automated?
- Are there repetitive commands the developer runs that could be a Make target?
- Are there manual checks that could become hooks?

### Skill Opportunity
- Could this workflow become a reusable skill?
- Is this a Cortex-specific process that agents should follow consistently?
- Would a skill prevent mistakes in future executions?

### Hook Opportunity
- Should any validation here become a hook?
- Is there a check that should run automatically on every commit/push?
- Would a hook catch this class of issue earlier?

### Workflow Opportunity
- Does this reveal a new or improved workflow?
- Is there a gap in the current workflow definitions?
- Should docs/WORKFLOWS.md be updated?

### Future Problem
- What downstream issues might this create?
- Does this introduce technical debt?
- Will this scale poorly as the codebase grows?

### Future Opportunity
- What doors does this open?
- Could this capability be extended or composed with other features?
- Does this enable new use cases?

### Documentation Gap
- Is anything undocumented that should be?
- Are there new APIs, patterns, or decisions that need documenting?
- Should docs/ARCHITECTURE.md or other docs be updated?

### Test Gap
- Is any behavior untested that should be?
- Are edge cases covered?
- Would integration tests catch issues unit tests miss?

3. **Assign severity** to each finding:
- **insight** — observation, no action needed
- **suggestion** — worth considering, not urgent
- **action-item** — should be done, create a task or issue

4. **Output** structured findings in terminal with this format:

```
## Reflection: [date]

### Findings
| # | Category | Severity | Finding | Recommendation |
|---|----------|----------|---------|----------------|
| 1 | quality | action-item | ... | ... |

### Summary
- Insights: N
- Suggestions: N
- Action items: N
```

5. If action-items exist, save report to `docs/audits/YYYY-MM-DD-reflect.md`.

6. If skill/hook/workflow creation opportunities found, list them explicitly for follow-up.
