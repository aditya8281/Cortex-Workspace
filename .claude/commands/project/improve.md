# /project:improve — Ecosystem Self-Improvement

Run weekly or after completing significant work. Reviews and enhances skills, hooks, workflows, and governance.

## Instructions

### 0. Load Ecosystem State

Invoke `cortex-repo-discovery`. Invoke `cortex-repository-intelligence`. Invoke `cortex-repo-health-scan`.

### 1. Review Skill Usage

- Check git log for recent skill invocations
- Which skills from `.claude/skills/` were used? Which skipped? Why?
- Skill creation opportunities not acted on?
- Stale skills (not updated in 30+ days)?

### 2. Review Hook Effectiveness

- Run hooks — any false positives?
- Checks that should be hooks but aren't?
- Hooks producing noisy/irrelevant findings?

### 3. Review Workflow Gaps

- Read `docs/WORKFLOWS.md`
- Manual steps that could be automated?
- Unclear or incomplete workflows?
- Missing workflows for common tasks?

### 4. Review Documentation

- Check all docs in `docs/` for completeness
- Cross-references valid?
- Topics not covered?

### 5. Review Governance Rules

- Read `docs/GOVERNANCE.md`
- Rules needing updating?
- New patterns to codify?

### 6. Generation Opportunities

- New command needed? (recurring manual process)
- New hook needed? (recurring quality issue)
- New skill needed? (recurring workflow pattern)

### 7. Output

```text
## Ecosystem Improvement: [date]

### Skill Review (Used: N, Stale: N, Creation opportunities: N)
### Hook Review (False positives: N, Missing hooks: N, Recommendations: N)
### Workflow Review (Gaps found: N, Recommendations: N)
### Documentation Review (Outdated: N, Missing topics: N, Recommendations: N)
### Governance Review (Updates needed: N, Recommendations: N)

### Improvement Recommendations
| # | Priority | Category | What | Why | Effort |

### Summary (Total: N, Now: N, Soon: N, Later: N)
```

### 8. Save

If action-items found, save to `docs/audits/YYYY-MM-DD-improve-{N}.md`.
