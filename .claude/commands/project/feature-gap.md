# /project:feature-gap — Roadmap vs Codebase Gap Analysis

Cross-reference roadmap/phase plans against the actual codebase. Find what's planned but not implemented.

## Instructions

### 1. Read the Roadmap

Invoke `cortex-repo-discovery` then `cortex-repository-intelligence`. Invoke `cortex-planning-ecosystem`.

### 2. Scan the Codebase

```bash
ls backend/app/services/ backend/app/api/v1/ backend/app/models/ frontend/src/app/ frontend/src/components/
```

### 3. Cross-Reference

For each planned component:

| Check | How |
|-------|-----|
| Service exists? | `backend/app/services/<name>.py` |
| Service complete? | More than stub? Real logic? |
| API endpoint exists? | Registered in `backend/app/api/v1/`? |
| Model exists? | In `backend/app/models/`? |
| Migration exists? | In `migrations/versions/`? |
| Tests exist? | In `tests/`? |
| Frontend support? | UI in `frontend/src/`? |
| Documented? | In relevant docs/ file? |

### 4. Classify Gaps

- **Complete** — fully implemented and tested
- **Partial** — started but incomplete
- **Stubbed** — scaffolded but no real implementation
- **Missing** — not started at all

### 5. Estimate Effort

XS (hours, 1 file) / S (half day, 1-2) / M (1-2 days, 3-5) / L (3-5 days, 5-10) / XL (1+ weeks, cross-cutting)

### 6. Prioritize

1. Blocks downstream work
2. High impact, low effort (quick wins)
3. High impact, high effort (major features)
4. Low impact (nice-to-haves)

## Output

```markdown
## Feature Gap: [date]

### Version: VX — Phase N: [name]
| Component | Planned | Exists | Status | Tests | Effort |

### Summary
Complete: N, Partial: N, Stubbed: N, Missing: N, Total effort: XS-L

### Recommended Priority
1. [Component] — [reason]

### Quick Wins (high impact, low effort)
- [Component] — [effort]
```

---

## Feedback Loop

**On entry:** Read `.claude/ecosystem/feedback.json`, filter last 10 entries where `command` matches this command name. If learnings exist, adapt behavior accordingly.

**On exit:** Append entry to `.claude/ecosystem/feedback.json`:
```json
{
  "timestamp": "<ISO-8601>",
  "command": "/project:feature-gap",
  "run_id": "<uuid>",
  "outcome": "success|failure|partial",
  "learnings": ["<what was discovered>"],
  "suggestions": ["<improvements for next run>"],
  "duration_ms": 0
}
```
