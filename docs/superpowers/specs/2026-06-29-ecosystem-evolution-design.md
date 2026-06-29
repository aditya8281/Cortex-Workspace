# CORTEX Ecosystem Evolution

**Date:** 2026-06-29
**Status:** Approved
**Scope:** Ecosystem cleanup, self-improvement mechanism, command consolidation, skill review

## Problem

The CORTEX ecosystem has accumulated cruft:
- 87 skills (many third-party, some duplicated)
- 22 commands (many overlapping)
- 11 one-off audit reports (findings already fixed)
- Stale docs (STATUS.md, frontend duplicates)
- No learning mechanism — commands are static .md files

## Design

### 1. Cleanup

**Delete:**
- `frontend/DESIGN.md` — duplicate of root `DESIGN.md`
- `frontend/PRODUCT.md` — duplicate of root `PRODUCT.md`
- `STATUS.md` — stale (says branch=frontend-design, 636 commits)
- 9 individual audit reports (keep only `EXECUTION_PLAN.md` + `EXECUTION_TRACE_REPORT.md`)
- `docs/audits/2026-06-27-reflect-1.md` — stale daily
- `docs/audits/2026-06-28-improve-1.md` — stale daily

**Update:** `docs/audits/index.md` to reflect trimmed set.

### 2. Self-Improvement Mechanism (Hybrid)

**Feedback Log:** `.claude/ecosystem/feedback.json`

```json
{
  "entries": [
    {
      "timestamp": "2026-06-29T22:00:00Z",
      "command": "/project:audit",
      "run_id": "abc123",
      "outcome": "success|failure|partial",
      "learnings": ["WS endpoints need SessionLocal() not get_db()"],
      "suggestions": ["Add WS auth test pattern to audit checklist"],
      "duration_ms": 12000
    }
  ]
}
```

**Command integration:**
- **Header:** Read last 10 feedback entries relevant to this command. Adapt behavior if learnings exist.
- **Footer:** Append outcome + learnings + suggestions to feedback.json.

**Meta-skill:** `cortex-ecosystem-evolution` — runs quarterly or via `/project:improve`. Reads accumulated feedback, proposes command/skill improvements as a PR. Never auto-applies.

### 3. Command Consolidation (22 → 14)

| Current | Action | Result |
|---------|--------|--------|
| `/project:audit` | Enhance — merge forensic depth | `/project:audit` |
| `/project:review` | Remove — merge into audit | — |
| `/project:challenge` | Remove — merge into audit | — |
| `/project:integrity` | Remove — merge into audit | — |
| `/project:health` | Keep | `/project:health` |
| `/project:verify` | Keep | `/project:verify` |
| `/project:release` | Keep | `/project:release` |
| `/project:cortex` | Keep | `/project:cortex` |
| `/project:develop` | Remove — overlap with cortex | — |
| `/project:next` | Remove — overlap with cortex | — |
| `/project:phase` | Remove — overlap with cortex | — |
| `/project:design` | Keep | `/project:design` |
| `/project:redesign` | Remove — overlap with design | — |
| `/project:update` | Keep | `/project:update` |
| `/project:enhance_plan` | Remove — merge into update | — |
| `/project:feature-gap` | Keep | `/project:feature-gap` |
| `/project:reflect` | Keep | `/project:reflect` |
| `/project:prompt` | Keep | `/project:prompt` |
| `/project:ideas` | Keep | `/project:ideas` |
| `/project:improve` | Enhanced — reads feedback log | `/project:improve` |
| `/project:start` | Keep | `/project:start` |
| `/project:architecture` | Keep | `/project:architecture` |

### 4. Skill Review

Cortex-specific skills: consolidate duplicates, remove dead ones.
Third-party skills: leave as-is (plugin system manages them).

### 5. Learning Loop

Every command gets:
```markdown
## Feedback Loop

**On entry:** Read `.claude/ecosystem/feedback.json`, filter last 10 entries for this command.
Adapt behavior if learnings exist.

**On exit:** Append entry with outcome, learnings, suggestions.
```

### 6. Update Docs

- `CLAUDE.md` — commands table, feedback loop section
- `README.md` — commands list
- `AGENTS.md` — feedback loop rules
- `.agents/plans/` — current version plans
