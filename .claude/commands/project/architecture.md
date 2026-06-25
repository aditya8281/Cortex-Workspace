# /project:architecture — Architecture Alignment Check

Run before implementing significant new systems or modifying core architecture.

## Instructions

1. **Read the source of truth.** Read `docs/ARCHITECTURE.md` completely.

2. **Check version context.** Read `.agents/plans/ACTIVE_VERSION.md`. Verify the proposed change is appropriate for the current version. Changes that belong in a later version should be deferred.

3. **Understand the proposed change.** Check:
- Recent git commits (`git log --oneline -10`)
- Active plan files (`docs/superpowers/plans/`)
- Active spec files (`docs/superpowers/specs/`)
- The user's stated goal in the current conversation

4. **Check alignment with documented architecture:**
- Does the change fit within the documented system structure?
- Does it follow the existing service layer pattern?
- Does it use the correct database conventions (SQLAlchemy + Alembic)?
- Does it follow the auth model (JWT + cookies, ownership checks)?

5. **Check alignment with CORTEX principles:**
- Privacy-first: No external data leaks introduced?
- Compound learning: Contributes to knowledge accumulation?
- Two-tier trust: Respects account/vault separation?
- Graceful degradation: Works without optional services?
- Model freedom: Not locked to specific provider?
- Living knowledge: Connects to knowledge graph?
- Version alignment: Is this change appropriate for the current version (V1-V6)?

6. **Check file placement:**
- Models → `backend/app/models/`
- Schemas → `backend/app/schemas/`
- Routers → `backend/app/api/v1/`
- Services → `backend/app/services/`
- Managers → `backend/app/managers/`
- Middleware → `backend/app/middleware/`
- Tasks → `backend/app/tasks/`
- Tests → `tests/`
- Migrations → `migrations/versions/`
- Docs → `docs/`
- ADRs → `docs/decisions/`

7. **Check for architecture drift:**
- Are there any competing doc systems?
- Are there any duplicate skill directories?
- Are there files in the wrong location?
- Are there unused or stale files?

8. **Check if ADR is needed.** An ADR is required when:
- New technology is introduced
- Architecture pattern changes
- Security policy changes
- API design decisions
- Database schema philosophy changes
- Testing strategy changes
- Deployment approach changes

Check `docs/decisions/` for existing ADRs. If the change qualifies and no ADR exists, recommend creating one.

9. **Output** format:

```
## Architecture Alignment: [date]

### Proposed Change
[Brief description]

### Architecture Fit: PASS/WARN/FAIL
| Check | Status | Notes |
|-------|--------|-------|
| Fits documented architecture | ✅/⚠️/❌ | ... |
| Follows service layer pattern | ✅/⚠️/❌ | ... |
| Correct DB conventions | ✅/⚠️/❌ | ... |
| Auth model respected | ✅/⚠️/❌ | ... |

### CORTEX Principles: PASS/WARN/FAIL
| Principle | Status | Notes |
|-----------|--------|-------|
| Privacy-first | ✅/⚠️/❌ | ... |

### File Placement: PASS/WARN/FAIL
[Files that are in wrong locations]

### Architecture Drift: PASS/WARN/FAIL
[Drift findings]

### ADR Required: YES/NO
[If yes, recommend title and key decisions]

### Summary
- Overall: PASS/WARN/FAIL
- Issues: N
- Recommendations: N
```
