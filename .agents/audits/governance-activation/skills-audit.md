# Skills Audit

**Date:** 2026-06-25
**Auditor:** Claude Code
**Scope:** All 66 skill directories in `.claude/skills/`

---

## Skill Inventory

| Category | Count | Skills |
|----------|-------|--------|
| **Caveman family** | 7 | caveman, caveman-commit, caveman-compress, caveman-help, caveman-review, caveman-stats, cavecrew |
| **Design/Visual** | 12 | brainstorming, brandkit, codebase-design, design-an-interface, design-md, design-motion-principles, design-taste-frontend, design-taste-frontend-v1, frontend-design, high-end-visual-design, industrial-brutalist-ui, minimalist-ui |
| **Implementation** | 8 | implement, tdd, subagent-driven-development, writing-plans, prototype, image-to-code, imagegen-frontend-mobile, imagegen-frontend-web |
| **Review/Quality** | 6 | review, grill-me, grill-with-docs, grilling, diagnosing-bugs, qa |
| **Writing** | 4 | writing-beats, writing-fragments, writing-great-skills, writing-shape |
| **Architecture/Planning** | 5 | domain-modeling, decision-mapping, improve-codebase-architecture, request-refactor-plan, ubiquitous-language |
| **Git/Workflow** | 4 | git-guardrails-claude-code, resolving-merge-conflicts, handoff, to-issues |
| **Tools/Integration** | 6 | ai-sdk, fastapi, postgresql-optimization, obsidian-vault, setup-pre-commit, setup-matt-pocock-skills |
| **Prompting/AI** | 3 | enhance-prompt, gpt-taste, ui-ux-pro-max |
| **Other** | 11 | ask-matt, edit-article, find-skills, full-output-enforcement, migrate-to-shoehorn, prototype, redesign-existing-projects, scaffold-exercises, stitch-design-taste, teach, to-prd, triage, ubiquitous-language |

**Total: 66 skills, 105 files, 104 markdown + 1 license**

---

## Skills Relevant to CORTEX Development

| Skill | Relevance | Used in Workflow |
|-------|-----------|-----------------|
| brainstorming | **HIGH** — Mandatory before design work | CLAUDE.md workflow |
| writing-plans | **HIGH** — Mandatory after design approval | CLAUDE.md workflow |
| tdd | **HIGH** — TDD during implementation | CLAUDE.md workflow |
| subagent-driven-development | **HIGH** — Multi-file implementation | AGENTS.md |
| review | **HIGH** — Code review before push | CLAUDE.md workflow |
| fastapi | **HIGH** — Backend framework | CORTEX backend |
| postgresql-optimization | **MEDIUM** — Database optimization | CORTEX database |
| domain-modeling | **MEDIUM** — Domain modeling | CORTEX architecture |
| decision-mapping | **MEDIUM** — Decision tracking | CORTEX ADRs |
| improve-codebase-architecture | **MEDIUM** — Architecture improvement | CORTEX refactoring |
| git-guardrails-claude-code | **MEDIUM** — Git safety | CORTEX branching |
| diagnosing-bugs | **MEDIUM** — Bug finding | CORTEX debugging |
| writing-great-skills | **LOW** — Skill creation | Ecosystem growth |

---

## CORTEX-Specific Skills (from GOVERNANCE.md)

GOVERNANCE.md lists these as candidates but NONE exist yet:

| Candidate Skill | Exists | Priority |
|----------------|--------|----------|
| CORTEX Architecture Audit | ❌ | P1 |
| CORTEX Repository Health Review | ❌ | P1 |
| CORTEX Planning Consistency Audit | ❌ | P2 |
| CORTEX Documentation Consistency Audit | ❌ | P2 |
| CORTEX Frontend/Backend Contract Audit | ❌ | P2 |
| CORTEX Release Readiness Audit | ❌ | P3 |
| CORTEX Memory Review | ❌ | P3 |
| CORTEX Retrieval Review | ❌ | P3 |
| CORTEX Agent Review | ❌ | P3 |
| CORTEX Desktop Readiness Audit | ❌ | P3 |

**0 of 10 planned Cortex-specific skills exist.**

---

## Skill Discovery Mechanism

### How Skills Are Found

1. **system-reminder messages** — Claude Code lists available skills automatically
2. **`ls .claude/skills/`** — Manual discovery
3. **`find-skills/` skill** — Meta-skill for finding other skills (just a SKILL.md)

### What's Missing

- ❌ No manifest/index file listing all skills with descriptions
- ❌ No categorization system (skills are just directories)
- ❌ No auto-discovery based on file types being edited
- ❌ No skill-to-workflow mapping (which skill for which workflow stage)

---

## Findings

### CRITICAL

None.

### IMPORTANT

1. **Zero Cortex-specific skills exist** — GOVERNANCE.md lists 10 candidates, none implemented. The ecosystem claims to be "skill-driven" but has no domain-specific skills.
   - **Fix:** Create at least `cortex-architecture-audit` and `cortex-health-review` skills.

2. **No skill manifest** — 66 skills with no index. Claude must `ls` or rely on system-reminder. No way to query "which skill for database work?"
   - **Fix:** Create `.claude/skills/INDEX.md` with categories and descriptions.

3. **Duplicate/overlapping skills** — `design-taste-frontend` and `design-taste-frontend-v1` exist. `grill-me`, `grill-with-docs`, and `grilling` overlap. `ask-matt` and `setup-matt-pocock-skills` overlap.
   - **Fix:** Audit and consolidate overlapping skills.

### MINOR

4. **Some skills have scripts that may be stale** — `caveman-compress/scripts/`, `ui-ux-pro-max/scripts/`, `brainstorming/scripts/` contain executable code that may not work in all environments.
   - **Fix:** Verify script executability.

5. **`find-skills/` is just a SKILL.md** — No actual search logic, just instructions. Could be more useful.
   - **Fix:** Enhance with actual search capabilities or remove if redundant with system-reminder.

---

## Recommended Actions

| Priority | Action | Effort |
|----------|--------|--------|
| P1 | Create `.claude/skills/INDEX.md` manifest | 30 min |
| P1 | Create `cortex-architecture-audit` skill | 1 hr |
| P2 | Create `cortex-health-review` skill | 1 hr |
| P2 | Audit and consolidate duplicate skills | 2 hr |
| P3 | Create remaining Cortex-specific skills | 4 hr |
| P3 | Enhance `find-skills/` with search logic | 1 hr |
