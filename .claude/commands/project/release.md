# /project:release — Release Readiness Check

Determine if the current state is ready for release. Combines verification, documentation, governance, and version completeness.

**Scope:** Version/phase release gate. For just test/lint/build results, use `/project:verify`.

## Instructions

### 1. Read Version Context

Invoke `cortex-repo-discovery` then `cortex-repository-intelligence`. Invoke `cortex-planning-ecosystem`.

Identify phase exit criteria from the active phase plan.

### 2. Run Verification

Invoke `cortex-system-validation`.

### 3. Check Phase Completeness

For each exit criterion in the phase plan: Is it met? What evidence? Flag incomplete items.

### 4. Check Documentation

Invoke `cortex-documentation-consistency`.

### 5. Check Governance

| Check | Status |
|-------|--------|
| All hooks passing | ✅/❌ |
| `progress.md` up to date | ✅/❌ |
| No unresolved P0/P1 from reviews | ✅/❌ |

### 6. Check Git State

| Check | Status |
|-------|--------|
| Clean working tree | ✅/❌ |
| Meaningful commit history | ✅/❌ |
| No merge conflicts | ✅/❌ |

### 7. Check Version Boundaries

- Scope creep from later version? Items belonging in different version?

## Output

```markdown
## Release Readiness: [date]

### Version: VX — Phase N: [name]
### Verification [results]
### Phase Completeness | Criterion | Status | Evidence |
### Documentation | Check | Status |
### Governance | Check | Status |
### Git State | Check | Status |
### Version Boundaries | Check | Status |

### Verdict: READY / NOT READY
### Blockers: [list if any]
```

---

## Feedback Loop

**On entry:** Read `.claude/ecosystem/feedback.json`, filter last 10 entries where `command` matches this command name. If learnings exist, adapt behavior accordingly.

**On exit:** Append entry to `.claude/ecosystem/feedback.json`:
```json
{
  "timestamp": "<ISO-8601>",
  "command": "/project:release",
  "run_id": "<uuid>",
  "outcome": "success|failure|partial",
  "learnings": ["<what was discovered>"],
  "suggestions": ["<improvements for next run>"],
  "duration_ms": 0
}
```
