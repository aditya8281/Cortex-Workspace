# /project:prompt — Ecosystem-Aware Prompt Generator

Generate development prompts that integrate with the Cortex ecosystem. Not a text rewriter — an intelligent prompt architect that understands repo state and routes work through existing systems.

## Instructions

### Step 0: DISCOVER

Run `.agents/plans/shared-phases.md#repository-intelligence`.

Specifically identify:

- project layout
- major modules
- documentation locations
- commands
- hooks
- workflows
- skills
- prompts
- templates
- plans
- tests
- build system

Do not assume files exist. Adapt to the repository structure.

### Step 1: UNDERSTAND

Run `.agents/plans/shared-phases.md#planning-ecosystem-load`.

### Step 1.5: DISCOVER EXISTING IMPLEMENTATION

Before proposing any solution determine whether similar work already exists.

Review:

- existing implementations
- existing services
- utilities
- abstractions
- commands
- workflows
- hooks
- skills
- prompts
- templates
- documentation
- ADRs
- tests

Also determine whether the requested work should:

- extend an existing implementation
- replace an existing implementation
- deprecate an existing implementation
- remove obsolete implementations

Prefer evolution over duplication.

Prefer extending existing systems over creating duplicates.

### Step 2: CLASSIFY

The user provides a goal (e.g., "implement file watcher integration", "fix the auth bug", "audit the codebase").

Determine:

Primary Category

Optional Secondary Categories

A task may belong to multiple categories.

Example:

Primary:
Feature

Secondary:
Backend
Testing
Documentation
Ecosystem

| Category | When to Use | Ecosystem Leverage |
|----------|-------------|-------------------|
| **Planning** | Brainstorming or designing a feature | Routes through brainstorming skill, references guide.md principles |
| **Architecture** | Architectural decisions | Routes through /architecture or /challenge, references ADRs |
| **Feature** | Implementing new functionality | Routes through /cortex workflow, references phase plan |
| **Bug Fix** | Diagnosing and fixing bugs | Routes through TDD pattern, references test infrastructure |
| **Audit** | Repository or codebase audit | Routes through /audit, references hooks and automation |
| **Documentation** | Writing or updating docs | References docs/ structure, governance rules |
| **Refactor** | Restructuring code | Routes through /review + /challenge, references architecture |
| **Performance** | Optimization work | References benchmarks, profiling approach |
| **Frontend** | UI/UX work | References DESIGN.md, frontend architecture in CLAUDE.md |
| **Backend** | API or service work | References backend architecture, service patterns, auth model |
| **DevOps** | Infrastructure or deployment | References Makefile, docker-compose, CI pipeline |
| **Security** | Security review | Routes through AGENTS.md patterns, references docs/SECURITY.md |
| **Testing** | Test creation or improvement | References tests/ structure, conftest.py patterns |
| **Release** | Release preparation | Routes through /release, references version system |
| **Ecosystem** | Improving skills, hooks, workflows | Routes through /improve, references governance |
| **Generation** | Creating new commands, hooks, skills | References existing patterns, governance rules |

Ask the user to confirm the classification if ambiguous.

Determine repository impact.

Identify:

- affected modules
- affected APIs
- affected commands
- affected workflows
- affected hooks
- affected skills
- affected documentation
- affected tests
- affected configuration

Also classify impact as:

- Direct
- Indirect
- Repository-wide

Estimate implementation complexity:

- Small
- Medium
- Large

Include these in the generated prompt where relevant.

### Step 2.5: CLARIFY

If the user's goal is ambiguous:

- Ask only the minimum number of questions required.
- Do not generate multiple speculative prompts.
- Clearly state what information is missing.

If reasonable assumptions are made:

- List them explicitly in the final output.
- Keep assumptions minimal and reversible.

### Step 3: GENERATE

Write the prompt using this structure:

```markdown
# [Objective]

## Repository Context

## Current State

## Requirements

## Constraints

## Implementation Plan

## Integration Points

Include:

- architecture
- commands
- hooks
- workflows
- skills
- prompts
- templates
- configuration
- documentation
- tests

## Validation

Validation should include:

- build verification
- linting
- testing
- integration verification
- documentation verification
- configuration verification
- hook verification (where applicable)

## Documentation Updates

## Ecosystem Updates

## Success Criteria

A task is complete only when:

- implementation is complete
- tests pass
- documentation is updated
- configuration is updated if needed
- ecosystem updates are completed
- repository consistency is maintained

## References
```

**Key rules for generated prompts:**
- Reference real file paths that exist in the repository
- Reference real skills from `.agents/skills/` that apply to this work
- Reference real workflows from `docs/WORKFLOWS.md`
- Reference real governance from `docs/GOVERNANCE.md`
- Do not repeat rules already enforced by hooks (the on-change hook handles lint)
- Do not duplicate architecture constraints — reference `guide.md` instead
- Be concise for simple tasks, detailed for complex ones
- Scale detail to the actual complexity of the work
- Reuse existing implementations before creating new ones.
- Prefer extending existing commands, workflows, hooks and skills.
- Mention documentation updates if implementation changes behavior.
- Mention configuration updates if required.
- Mention testing expectations.
- Mention ecosystem updates where applicable.

### Prompt Complexity

Automatically scale detail based on task complexity.

- Simple → concise prompt.
- Medium → standard implementation plan.
- Large → detailed implementation specification.

Do not generate unnecessarily large prompts for simple tasks.

### Step 4: REVIEW (Self-Audit)

Before presenting the prompt, audit it against these 6 checks:

1. **Clarity:** Would an agent reading this prompt know exactly what to do?
2. **Scoping:** Is the scope defined? Can it be done in one iteration?
3. **Ecosystem leverage:** Does it use existing systems or reinvent them?
4. **Redundancy:** Does it repeat rules already handled by the ecosystem?
5. **Completeness:** Are all integration points mentioned?
6. **Simplicity:** Can it be shorter without losing effectiveness?
7. Architecture consistency
8. Repository consistency
9. Documentation completeness
10. Reuse of existing systems
11. Scalability
12. Future maintainability
13. Agent clarity
14. Determinism
15. Repository consistency
16. Ecosystem consistency
17. Is this the smallest prompt that accomplishes the objective?

### Step 5: REFINE

Fix issues found during review.

Repeat the review until every check passes.

If important repository information is missing, ask clarifying questions instead of generating a weak prompt.
### Step 6: PRESENT

Show the final prompt in a code block. After the prompt, offer:

- Edit it based on feedback
- Save it to a file
- Use it immediately (if the user wants to proceed with /cortex or manually)

## Output 

Save prompt to docs/audits/YYYY-MM-DD-prompt-{N}.md

Where:

* `YYYY-MM-DD` is today's date.
* `{N}` is the prompt number for that day.

```
## Generated Prompt: [topic]

**Category:** [classification]
**Applies to:** [files/systems affected]

[The prompt in a code block]

---
**Ecosystem leverage:**
- Skills: [which skills this prompt uses]
- Workflows: [which workflow stages this follows]
- Hooks: [which hooks will run during execution]
- References: [key docs/files referenced]

**Repository Impact**

- Modules:
- Commands:
- Hooks:
- Workflows:
- Skills:
- Documentation:
- Configuration:
- Tests:

---

**Recommended Command Flow**

**Recommended Command Flow**

Before implementation:

- Commands relevant to planning

During implementation:

- Commands relevant to execution

After implementation:

- /project:review
- /project:verify
- /project:reflect

If release-related:

- /project:release

---

**Confidence**

- Repository understanding:
- Classification confidence:
- Ecosystem coverage:
- Assumptions made:
- Potential risks:
```

## Philosophy

This command should not simply generate prompts.

Its objective is to generate the smallest, clearest, ecosystem-aware prompt that:

- reuses existing systems
- follows project governance
- integrates with current architecture
- minimizes duplication
- identifies ecosystem updates
- produces implementation-ready instructions

## Completion Checklist

Before presenting the prompt, confirm:

- Existing implementations reviewed.
- Existing commands reviewed.
- Existing workflows reviewed.
- Existing hooks reviewed.
- Existing skills reviewed.
- Existing prompts reviewed.
- Existing templates reviewed.
- Existing documentation reviewed.
- Existing tests reviewed.
- Existing configuration reviewed.
- No unnecessary duplication introduced.
- Prompt references only real repository artifacts.
