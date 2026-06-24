# CORTEX Strategic Command System — Design Spec

**Date:** 2026-06-24
**Status:** Proposed

---

## Purpose

CORTEX has governance, hooks, automation, skills, and workflows. It lacks one thing: **structured invocation points** — commands that agents and humans can call to run deeper analysis than hooks provide.

Hooks are fast, automated, and narrow (lint, contract, architecture). Commands are deep, analytical, and broad (reflection, challenge, innovation). They complement each other.

This spec defines 7 slash commands that continuously improve CORTEX — its architecture, workflows, quality, and future direction.

---

## Design Principles

1. **Fewer, not more.** 7 commands, not 20. Each must justify its existence.
2. **Clear triggers.** Every command has a "when to use" — daily vs periodic.
3. **Don't duplicate hooks.** Hooks validate fast. Commands analyze deep.
4. **Output by default.** Terminal output. Significant findings save to files.
5. **Non-blocking.** Commands inform, they don't gate (except reflect, which is mandatory).

---

## Command Architecture

### Location

```
.claude/commands/
└── project/
    ├── reflect.md
    ├── review.md
    ├── challenge.md
    ├── health.md
    ├── architecture.md
    ├── ideas.md
    └── improve.md
```

### Naming Convention

`/project:<name>` — all under a `project/` namespace. Avoids collision with built-in or plugin commands.

### How It Works

Claude Code reads `.md` files from `.claude/commands/` and exposes them as slash commands. Each `.md` file contains the prompt/instructions that execute when invoked.

### Output Convention

- Default: terminal output
- Significant findings: save to `docs/audits/YYYY-MM-DD-<command>.md`
- Never save empty reports

---

## Command Catalog

### 1. `/project:reflect` — Before Every Completion (MANDATORY)

**Frequency:** Before marking any major task complete.
**Mandatory:** Yes (enforced via CLAUDE.md reflection rule).

**Purpose:** Systematic reflection on the current work — quality, improvement opportunities, ecosystem contribution.

**Prompt structure:**

1. Identify the work just completed (files changed, features built, bugs fixed).
2. Run through the reflection framework:
   - **Quality:** Could any code be cleaner, simpler, more readable?
   - **Redundancy:** Is anything duplicated that could be consolidated?
   - **Automation:** Is any manual step that could be automated?
   - **Skill opportunity:** Could this workflow become a reusable skill?
   - **Hook opportunity:** Should any validation here become a hook?
   - **Workflow opportunity:** Does this reveal a new or improved workflow?
   - **Future problem:** What downstream issues might this create?
   - **Future opportunity:** What doors does this open?
   - **Documentation gap:** Is anything undocumented that should be?
   - **Test gap:** Is any behavior untested that should be?
3. For each finding, assign severity: insight / suggestion / action-item.
4. Output structured findings in terminal.
5. If action-items exist, save to `docs/audits/YYYY-MM-DD-reflect.md`.

**Does NOT block** — purely informational. But findings must be documented.

**Difference from hooks:** Hooks check specific rules (ruff, contract, architecture). Reflect asks broader questions about quality, opportunity, and ecosystem growth.

---

### 2. `/project:review` — Before PR/Push

**Frequency:** Before pushing code or creating a PR.

**Purpose:** Code quality review focused on correctness, patterns, and completeness.

**Prompt structure:**

1. Identify changed files (git diff).
2. Run `make lint` and `make test` — report pass/fail.
3. Check each changed file for:
   - Missing error handling
   - Hardcoded values that should be config
   - Missing `response_model=` on API endpoints
   - Missing ownership checks on user-scoped endpoints
   - Missing tests for new logic
   - Missing docstrings on public functions
4. Verify API contracts (backend routes match frontend API calls).
5. Check documentation updates.
6. Review against AGENTS.md patterns.
7. Output pass/fail per check with specific file:line references.

**Difference from hooks:** Hooks validate rules. Review analyzes quality and completeness.

---

### 3. `/project:challenge` — Before Major Decisions

**Frequency:** Before implementing a significant feature or making architectural choice.

**Purpose:** Adversarial review — actively tries to poke holes in the current approach.

**Prompt structure:**

1. Read the current plan/spec/design.
2. Ask "what's wrong with this approach?"
3. Identify:
   - Risks and failure modes
   - Edge cases not considered
   - Over-engineering or under-engineering
   - Assumptions that might be wrong
   - Alternatives not explored
4. Verify alignment with CORTEX principles:
   - Privacy-first
   - Compound learning
   - Two-tier trust
   - Graceful degradation
   - Model freedom
   - Living knowledge
5. Output challenges as a numbered list with severity (critical / warning / nit).

**Does NOT block** — purely analytical. Findings inform the decision.

---

### 4. `/project:health` — Weekly

**Frequency:** Weekly or before major milestones.

**Purpose:** Comprehensive repository health check.

**Prompt structure:**

1. Run `python3 .claude/hooks/run_hooks.py` — all 11 hooks.
2. Run `python3 scripts/automation/run_all.py health` — dead code, duplicates, drift.
3. Run `python3 scripts/automation/run_all.py bug-discovery` — placeholders, security, errors.
4. Check skill health:
   - Are all skills in `.agents/skills/` complete (have definitions)?
   - Are any skills stale (not updated in 30+ days)?
   - Are any skills unused?
5. Check documentation freshness:
   - Do all docs have "Last updated" dates?
   - Are any docs clearly outdated?
6. Check tech debt hotspots:
   - Files changed 5+ times in recent commits
   - Files with many TODO/FIXME comments
7. Output summary: health score, findings by severity, recommendations.
8. Save report to `docs/audits/YYYY-MM-DD-health-report.md`.

---

### 5. `/project:architecture` — Before Big Changes

**Frequency:** Before implementing significant new systems or modifying core architecture.

**Purpose:** Architecture alignment check — verify proposed changes match documented architecture and CORTEX principles.

**Prompt structure:**

1. Read `docs/ARCHITECTURE.md` as source of truth.
2. Read the proposed change (plan, spec, or description).
3. Check alignment:
   - Does the change fit within documented architecture?
   - Does it violate any CORTEX principles?
   - Does it introduce a competing system?
   - Does it affect more than 2 subsystems?
4. Check file placement against conventions (models → `backend/app/models/`, etc.).
5. Check if an ADR is needed (new technology, architecture pattern, security policy, etc.).
6. Check for architecture drift (actual code vs documented structure).
7. Output alignment report with pass/warn/fail per check.
8. Recommend ADR creation if needed.

---

### 6. `/project:ideas` — Weekly/Monthly

**Frequency:** Weekly or monthly during planning/strategy sessions.

**Purpose:** Innovation and opportunity discovery.

**Prompt structure:**

1. Analyze recent commits (last 2 weeks).
2. Read current roadmap (`docs/ROADMAP.md`).
3. Read CORTEX vision (README.md vision section).
4. Identify:
   - Gaps between current state and vision
   - New features that would advance the vision
   - Improvements to existing features
   - Competitive opportunities (what similar projects do well)
   - New use cases for existing capabilities
5. Cross-reference with user's stated goals.
6. Output ideas as a prioritized list with estimated effort.
7. Save to `docs/ideas/YYYY-MM-DD.md` if 3+ ideas found.

---

### 7. `/project:improve` — Weekly

**Frequency:** Weekly or after completing significant work.

**Purpose:** Ecosystem self-improvement — review and enhance skills, hooks, workflows, governance.

**Prompt structure:**

1. Review recent skill usage:
   - Which skills were used this week?
   - Which were skipped? Why?
   - Any skill creation opportunities identified?
2. Review hook effectiveness:
   - Any false positives/negatives?
   - Any missing checks that should be hooks?
3. Review workflow gaps:
   - Any manual steps that could be automated?
   - Any workflows that are unclear or incomplete?
4. Review documentation:
   - Any docs missing or outdated?
   - Any cross-references broken?
5. Review governance rules:
   - Any rules that need updating?
   - Any new patterns that should be codified?
6. Output improvement recommendations as a prioritized list.
7. Save to `docs/audits/YYYY-MM-DD-improve.md` if action-items found.

---

## Integration

### CLAUDE.md — Reflection Rule

Add after "Mandatory Workflow Rules":

```markdown
### Reflection Rule

Before completing any major task, agents MUST run through the reflection framework. Ask:

- What could be improved?
- What could be simplified?
- What could be automated?
- What could become a skill?
- What could become a hook?
- What could become a reusable workflow?
- What future problem does this reveal?
- What future opportunity does this create?

Use `/project:reflect` for structured execution. Document findings. Never skip reflection.
```

### CLAUDE.md — Command Reference

Add new section:

```markdown
## Strategic Commands

| Command | When | Purpose |
|---------|------|---------|
| `/project:reflect` | Before completion (mandatory) | Reflection framework — quality, improvement, ecosystem growth |
| `/project:review` | Before PR/push | Code quality, correctness, patterns |
| `/project:challenge` | Before major decisions | Adversarial review — poke holes in approach |
| `/project:health` | Weekly | Repo health, dead code, drift, debt |
| `/project:architecture` | Before big changes | Architecture alignment, convention check |
| `/project:ideas` | Weekly/monthly | Innovation, future opportunities, gap discovery |
| `/project:improve` | Weekly | Ecosystem improvement — skills, hooks, workflows |
```

### WORKFLOWS.md — Development Lifecycle

Update Stage 5 (Build → Review) to include `/project:review` and `/project:challenge`.
Update Release workflow to include `/project:reflect` before completion.

### GOVERNANCE.md — Code Quality Standards

Add to "Mandatory Before Every PR":
- Run `/project:review` for code quality analysis

---

## What This Does NOT Do

- **Does NOT replace hooks.** Hooks are fast, automated, narrow. Commands are deep, analytical, broad.
- **Does NOT replace skills.** Skills provide specialized workflows. Commands provide structured invocation.
- **Does NOT block completion.** Only the reflection rule is mandatory (via CLAUDE.md). Commands are on-demand.
- **Does NOT generate noise.** 7 commands, not 20. Each has a clear trigger and clear output.

---

## Success Criteria

1. All 7 commands work when invoked via `/project:<name>`.
2. `/project:reflect` is referenced in CLAUDE.md as mandatory.
3. Commands produce useful output that improves code quality.
4. No command duplicates an existing hook's functionality.
5. Commands are used regularly (tracked by invocation).
