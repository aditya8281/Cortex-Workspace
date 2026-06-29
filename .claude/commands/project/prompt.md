# /project:prompt — Ecosystem-Aware Prompt Generator

Generate development prompts that integrate with the Cortex ecosystem. Not a text rewriter — an intelligent prompt architect.

## Instructions

### Step 0: DISCOVER

Invoke `cortex-repo-discovery` then `cortex-repository-intelligence`.

Specifically identify: project layout, major modules, docs, commands, hooks, workflows, skills, prompts, templates, plans, tests, build system.

### Step 1: UNDERSTAND

Invoke `cortex-planning-ecosystem`.

### Step 1.5: DISCOVER EXISTING IMPLEMENTATION

Before proposing a solution, check whether similar work exists. Review existing implementations, services, utilities, abstractions, commands, workflows, hooks, skills, prompts, templates, docs, ADRs, tests.

Determine whether work should extend, replace, deprecate, or remove existing implementations. Prefer evolution over duplication.

### Step 2: CLASSIFY

Classify the user's goal:

| Category | When | Ecosystem Leverage |
|----------|------|-------------------|
| **Planning** | Brainstorming design | brainstorming skill, guide.md |
| **Architecture** | Architecture decisions | /architecture or /challenge, ADRs |
| **Feature** | New functionality | /cortex workflow, phase plan |
| **Bug Fix** | Diagnosing bugs | TDD, test infrastructure |
| **Audit** | Codebase audit | /audit, hooks, automation |
| **Documentation** | Docs | docs/ structure, governance |
| **Refactor** | Restructuring | /review + /challenge, architecture |
| **Performance** | Optimization | Benchmarks, profiling |
| **Frontend** | UI/UX | DESIGN.md, CLAUDE.md frontend |
| **Backend** | API/service | Backend architecture, auth model |
| **DevOps** | Infrastructure | Makefile, docker-compose, CI |
| **Security** | Security review | AGENTS.md, docs/GOVERNANCE.md |
| **Testing** | Test improvement | tests/ structure, conftest.py |
| **Release** | Release prep | /release, version system |
| **Ecosystem** | Skills/hooks/workflows | /improve, governance |
| **Generation** | New commands/hooks/skills | Existing patterns, governance |

Identify affected: modules, APIs, commands, workflows, hooks, skills, docs, tests, config. Classify impact as Direct / Indirect / Repository-wide. Estimate complexity: Small / Medium / Large.

Ask user to confirm if ambiguous.

### Step 2.5: CLARIFY

If ambiguous: ask minimum questions. Do not generate multiple speculative prompts. List assumptions explicitly, keep them minimal and reversible.

### Step 3: GENERATE

Write prompt using this structure (include only relevant sections):

```markdown
# [Objective]
## Repository Context
## Current State
## Requirements
## Constraints
## Implementation Plan
## Integration Points (architecture, commands, hooks, workflows, skills, prompts, templates, config, docs, tests)
## Validation (build, lint, test, integration, docs, config, hooks)
## Documentation Updates
## Ecosystem Updates
## Success Criteria
## References
```

**Key rules:** Reference real paths and skills. Reference governance from docs/GOVERNANCE.md. Don't repeat hook-enforced rules. Don't duplicate architecture constraints — reference `guide.md`. Scale detail to complexity. Reuse before creating.

### Prompt Complexity

- Simple → concise
- Medium → standard implementation plan
- Large → detailed specification

### Step 4: REVIEW (Self-Audit)

Check: clarity, scoping, ecosystem leverage, redundancy, completeness, simplicity, architecture/repository/ecosystem consistency. Is this the smallest prompt that accomplishes the objective?

### Step 5: REFINE

Fix issues found in review. Repeat until all checks pass.

### Step 6: PRESENT

Show prompt in code block. Offer: edit, save to file, or use immediately with /project:cortex.

## Output

Save to `docs/audits/YYYY-MM-DD-prompt-{N}.md`:

```text
## Generated Prompt: [topic]
**Category:** [classification]
**Applies to:** [files/systems]

[prompt]

---
**Ecosystem leverage:** Skills, Workflows, Hooks, References
**Repository Impact:** Modules, Commands, Hooks, Workflows, Skills, Docs, Config, Tests

**Recommended Flow:** /project:review → /project:verify → /project:reflect
+ /project:release if release-related

**Confidence:** Repository understanding, Classification, Ecosystem coverage, Assumptions, Risks
```

## Philosophy

Generate the smallest, clearest, ecosystem-aware prompt that reuses existing systems, follows governance, integrates with architecture, minimizes duplication, identifies ecosystem updates.

## Completion Checklist

- [ ] Existing implementations reviewed
- [ ] Existing commands, workflows, hooks, skills, prompts, templates reviewed
- [ ] Existing documentation, tests, configuration reviewed
- [ ] No unnecessary duplication
- [ ] References only real repository artifacts

---

## Feedback Loop

**On entry:** Read `.claude/ecosystem/feedback.json`, filter last 10 entries where `command` matches this command name. If learnings exist, adapt behavior accordingly.

**On exit:** Append entry to `.claude/ecosystem/feedback.json`:
```json
{
  "timestamp": "<ISO-8601>",
  "command": "/project:prompt",
  "run_id": "<uuid>",
  "outcome": "success|failure|partial",
  "learnings": ["<what was discovered>"],
  "suggestions": ["<improvements for next run>"],
  "duration_ms": 0
}
```
