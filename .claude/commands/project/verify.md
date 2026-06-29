# /project:verify — Verification Suite

Run the full verification pipeline and report pass/fail. Fast, focused, no analysis.

**Scope:** Automated pass/fail checks. For code quality, use `/project:review`.

## Instructions

Invoke `cortex-repo-discovery`.

### 1. System Validation

Invoke `cortex-system-validation`.

Report: pass/fail per check with details.

## Output

```markdown
## Verification: [date]

| Check | Status | Details |
|-------|--------|---------|
| Backend tests | ✅/❌ N/N | |
| Frontend tests | ✅/❌ N/N | |
| Lint | ✅/❌ | |
| Format | ✅/❌ | |
| Build | ✅/❌ | |
| Hooks | ✅/❌ N/N | |
| Migrations | ✅/❌ | |

### Verdict: PASS / FAIL
```

**Block merge on any FAIL.**

---

## Feedback Loop

**On entry:** Read `.claude/ecosystem/feedback.json`, filter last 10 entries where `command` matches this command name. If learnings exist, adapt behavior accordingly.

**On exit:** Append entry to `.claude/ecosystem/feedback.json`:
```json
{
  "timestamp": "<ISO-8601>",
  "command": "/project:verify",
  "run_id": "<uuid>",
  "outcome": "success|failure|partial",
  "learnings": ["<what was discovered>"],
  "suggestions": ["<improvements for next run>"],
  "duration_ms": 0
}
```
