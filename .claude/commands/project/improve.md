# /project:improve — Ecosystem Self-Improvement

Run weekly or after completing significant work. Reviews and enhances skills, hooks, workflows, and governance.

## Instructions

1. **Review skill usage.**
- Check git log for recent skill invocations
- Which skills from `.agents/skills/` were used?
- Which were skipped? Why?
- Were there skill creation opportunities that weren't acted on?
- Are any skills stale (not updated in 30+ days)?

2. **Review hook effectiveness.**
- Run `python3 .claude/hooks/run_hooks.py` — any false positives?
- Are there checks that should be hooks but aren't?
- Are any hooks producing noisy/irrelevant findings?
- Is the hook phase configuration optimal?

3. **Review workflow gaps.**
- Read `docs/WORKFLOWS.md`
- Are there manual steps that could be automated?
- Are any workflows unclear or incomplete?
- Do workflows match actual development practices?
- Are there missing workflows for common tasks?

4. **Review documentation.**
- Check all docs in `docs/` for completeness
- Are cross-references valid?
- Are there topics not covered by any doc?
- Is the developer guide up to date?

5. **Review governance rules.**
- Read `docs/GOVERNANCE.md`
- Are there rules that need updating?
- Are there new patterns that should be codified?
- Are clarification rules still appropriate?

6. **Check for generation opportunities.** Based on patterns observed during this review:
   - Should any new command be created? (recurring manual process)
   - Should any new hook be created? (recurring quality issue)
   - Should any new skill be created? (recurring workflow pattern)
   - If yes, recommend with justification.

7. **Generate improvement recommendations.** For each:
- What: specific improvement
- Why: what problem it solves
- Effort: S/M/L
- Priority: now / soon / later

8. **Output** format:

```
## Ecosystem Improvement: [date]

### Skill Review
- Used: N
- Stale: N
- Creation opportunities: N

### Hook Review
- False positives: N
- Missing hooks: N
- Recommendations: N

### Workflow Review
- Gaps found: N
- Recommendations: N

### Documentation Review
- Outdated: N
- Missing topics: N
- Recommendations: N

### Governance Review
- Updates needed: N
- Recommendations: N

### Improvement Recommendations
| # | Priority | Category | What | Why | Effort |
|---|----------|----------|------|-----|--------|
| 1 | now | skill | ... | ... | S |

### Summary
- Total recommendations: N
- Now: N, Soon: N, Later: N
```

9. If action-items found, save to `docs/audits/YYYY-MM-DD-improve.md`.
