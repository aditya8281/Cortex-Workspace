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
