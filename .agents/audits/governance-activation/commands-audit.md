# Commands Audit

**Date:** 2026-06-25
**Auditor:** Claude Code
**Scope:** All 7 slash commands in `.claude/commands/project/`

---

## Command Inventory

| # | Command | File | Size | Lines | Status |
|---|---------|------|------|-------|--------|
| 1 | `/project:reflect` | `reflect.md` | 2,912 B | ~80 | ✅ Present |
| 2 | `/project:review` | `review.md` | 1,727 B | ~50 | ✅ Present |
| 3 | `/project:challenge` | `challenge.md` | 2,363 B | ~65 | ✅ Present |
| 4 | `/project:health` | `health.md` | 1,881 B | ~55 | ✅ Present |
| 5 | `/project:architecture` | `architecture.md` | 2,943 B | ~85 | ✅ Present |
| 6 | `/project:ideas` | `ideas.md` | 2,156 B | ~60 | ✅ Present |
| 7 | `/project:improve` | `improve.md` | 2,207 B | ~60 | ✅ Present |

**All 7 commands present and non-empty** ✅

---

## Command Analysis

### Content Quality

| Command | Has Steps | Has Examples | References Other Docs | Actionable |
|---------|-----------|--------------|----------------------|------------|
| reflect | ✅ 8 questions | ✅ git diff | ✅ references hooks | ✅ |
| review | ✅ checklist | ❌ | ❌ | ✅ |
| challenge | ✅ adversarial | ❌ | ❌ | ✅ |
| health | ✅ health checks | ✅ make commands | ✅ references hooks | ✅ |
| architecture | ✅ architecture checks | ✅ file paths | ✅ references docs | ✅ |
| ideas | ✅ brainstorming | ❌ | ❌ | ✅ |
| improve | ✅ improvement | ✅ make commands | ✅ references hooks | ✅ |

### CLAUDE.md Integration

All 7 commands are referenced in CLAUDE.md's Strategic Commands table ✅

### WORKFLOWS.md Integration

| Command | Referenced in WORKFLOWS.md | Where |
|---------|---------------------------|-------|
| reflect | ✅ | Stage 7: Reflect & Release |
| review | ✅ | Stage 6: Review |
| challenge | ✅ | Stage 6: Review (adversarial) |
| health | ✅ | Audit Workflow |
| architecture | ❌ | Not explicitly mentioned |
| ideas | ❌ | Not explicitly mentioned |
| improve | ❌ | Not explicitly mentioned |

### DEVELOPER_GUIDE.md Integration

| Command | Referenced in DEVELOPER_GUIDE.md | Where |
|---------|----------------------------------|-------|
| reflect | ✅ | Stage 10: Complete |
| review | ✅ | Stage 8: Review |
| challenge | ❌ | Not mentioned |
| health | ✅ | Quick Reference table |
| architecture | ✅ | Quick Reference table |
| ideas | ❌ | Not mentioned |
| improve | ❌ | Not mentioned |

---

## Overlap Analysis

| Pair | Overlap | Issue |
|------|---------|-------|
| reflect ↔ improve | Medium | Both ask "what could be improved?" — reflect is broader (8 questions), improve is ecosystem-focused |
| review ↔ challenge | Low | review = code quality, challenge = adversarial design review. Different purposes. |
| health ↔ architecture | Low | health = repo-wide health, architecture = architecture-specific alignment. Different scope. |
| ideas ↔ improve | Medium | ideas = innovation/discovery, improve = ecosystem improvement. Similar but distinct. |

**No significant overlaps** — each command has a distinct purpose.

---

## Missing Commands

Based on WORKFLOWS.md and DEVELOPER_GUIDE.md, these workflows lack corresponding commands:

| Workflow | Missing Command | Priority |
|----------|----------------|----------|
| Bug-Finding Workflow | `/project:bugs` | P2 |
| Audit Workflow | `/project:audit` | P2 |
| Release Workflow | `/project:release` | P3 |
| Documentation Workflow | `/project:docs` | P3 |
| Refactoring Workflow | `/project:refactor` | P3 |

---

## Findings

### CRITICAL

None.

### IMPORTANT

1. **3 commands not referenced in WORKFLOWS.md** — `architecture`, `ideas`, `improve` are missing from workflow definitions.
   - **Fix:** Add references in WORKFLOWS.md or remove from CLAUDE.md if not needed.

2. **3 commands not referenced in DEVELOPER_GUIDE.md** — `challenge`, `ideas`, `improve` are missing from the developer guide.
   - **Fix:** Add to DEVELOPER_GUIDE.md's Quick Reference table.

### MINOR

3. **No `/project:audit` command** — The Audit Workflow in WORKFLOWS.md describes a process but has no corresponding slash command.
   - **Fix:** Create `/project:audit` command.

4. **No command for version/phase navigation** — Claude must manually `grep` progress files to determine active state.
   - **Fix:** Create `/project:status` command that reads progress.md files and reports active version/phase.

---

## Recommended Actions

| Priority | Action | Effort |
|----------|--------|--------|
| P1 | Add missing references to WORKFLOWS.md and DEVELOPER_GUIDE.md | 15 min |
| P2 | Create `/project:status` command for active state discovery | 30 min |
| P2 | Create `/project:audit` command | 30 min |
| P3 | Create `/project:release` command | 30 min |
