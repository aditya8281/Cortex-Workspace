# /project:reflect — Reflection Framework

Before completing any major task, run through this reflection framework systematically.

## Instructions

### 1. Identify Work Completed

Invoke `cortex-repo-discovery`.

```bash
git diff --stat HEAD~1
```

Summarize: files modified, features, fixes, refactors, tests, docs.

### 2. Run Reflection Framework

Invoke `cortex-post-reflection`.

The skill covers: Quality, Redundancy, Automation, Skill/Hook/Workflow Opportunities, Documentation Gaps, Source of Truth Audit, Ecosystem Growth, Configuration Audit, Architecture Review, Performance Review, Security Review, Maintainability Review, Agent Compatibility, Knowledge Capture, Consistency Audit, Regression Risk, Technical Debt, Test Gaps, Repository Consistency Sweep.

After the skill completes, run the specific additional checks below.

### 2a. Command Opportunity Review

Review `.claude/commands/project/`. Determine:
- Existing commands requiring updates
- Examples outdated
- Instructions no longer match implementation
- New commands needed
- Existing commands to merge, split, or extend

### 2b. Repository Consistency Sweep

Review every relevant command under `.claude/commands/project/` and every relevant document under `docs/` outside the modified set. Do not assume consistency simply because files weren't modified.

### 3. Assign Severity

- **insight** — observation, no action needed
- **suggestion** — worth considering, not urgent
- **action-item** — should be completed

### 4. Output Structured Findings

```text
## Reflection: [date]

### Findings
| # | Category | Severity | Finding | Recommendation |

### Summary
- Insights: N
- Suggestions: N
- Action Items: N

### Ecosystem Follow-up
#### Commands (existing updates, new)
#### Workflows (existing updates, new)
#### Hooks (existing updates, new)
#### Skills (existing updates, new)
#### Prompts (existing updates, new)
#### Templates (existing updates, new)
#### Documentation (files requiring updates)
#### Configuration (files requiring updates)
#### Tests (tests to add)
#### Repository Review (files outside modified set requiring updates)
```

### 5. Save Report

If any action-item exists, save to `docs/audits/YYYY-MM-DD-reflect-{N}.md`.

### 6. Final Verdict

- Overall quality score (1–10)
- Release readiness: Ready / Ready with follow-ups / Needs revision
- Top five highest-priority action items

### 7. Completion Checklist

- [ ] Every relevant doc source reviewed against implementation
- [ ] Every relevant file under `docs/` considered
- [ ] Every relevant command under `.claude/commands/project/` reviewed
- [ ] Hooks reviewed
- [ ] Skills reviewed
- [ ] Workflows reviewed
- [ ] Prompts reviewed
- [ ] Templates reviewed
- [ ] Configuration files reviewed
- [ ] Tests reviewed
- [ ] Repository consistency beyond modified files evaluated
- [ ] All recommended ecosystem improvements listed
- [ ] Reflection based on current codebase state, not assumptions

---

## Feedback Loop

**On entry:** Read `.claude/ecosystem/feedback.json`, filter last 10 entries where `command` matches this command name. If learnings exist, adapt behavior accordingly.

**On exit:** Append entry to `.claude/ecosystem/feedback.json`:
```json
{
  "timestamp": "<ISO-8601>",
  "command": "/project:reflect",
  "run_id": "<uuid>",
  "outcome": "success|failure|partial",
  "learnings": ["<what was discovered>"],
  "suggestions": ["<improvements for next run>"],
  "duration_ms": 0
}
```
