# /project:prompt — Ecosystem-Aware Prompt Generator

Generate development prompts that integrate with the Cortex ecosystem. Not a text rewriter — an intelligent prompt architect that understands repo state and routes work through existing systems.

## Instructions

### Step 1: UNDERSTAND

Before generating anything, read the repository state:

```bash
# Current state
git status
git log --oneline -5
git branch --show-current

# Version context
cat .agents/plans/ACTIVE_VERSION.md
grep -r "in_progress\|active" .agents/plans/versions/*/progress.md
```

Read these files to understand the ecosystem:
- `docs/ARCHITECTURE.md` — system architecture
- `.agents/plans/guide.md` — constitution and principles
- `docs/WORKFLOWS.md` — development workflows
- `docs/GOVERNANCE.md` — governance rules
- `.agents/skills/` — available skills (list the directory)
- `.claude/commands/project/` — available commands (list the directory)
- `.claude/hooks/` — available hooks

This context ensures generated prompts reference real systems, not hypothetical ones.

### Step 2: CLASSIFY

The user provides a goal (e.g., "implement file watcher integration", "fix the auth bug", "audit the codebase"). Classify it into one of these categories:

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

### Step 3: GENERATE

Write the prompt using this structure:

```markdown
# [Objective]

## Context
[What this builds on — reference real files, real state, real phase plan]

## Constraints
[Architecture rules, governance — reference guide.md and CLAUDE.md, don't duplicate them]

## Approach
[How to do it — reference real skills, workflows, hooks that apply]

## Validation
[How to verify — reference real make targets, test commands]

## References
[Links to relevant docs, ADRs, existing patterns in the codebase]
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

### Step 4: REVIEW (Self-Audit)

Before presenting the prompt, audit it against these 6 checks:

1. **Clarity:** Would an agent reading this prompt know exactly what to do?
2. **Scoping:** Is the scope defined? Can it be done in one iteration?
3. **Ecosystem leverage:** Does it use existing systems or reinvent them?
4. **Redundancy:** Does it repeat rules already handled by the ecosystem?
5. **Completeness:** Are all integration points mentioned?
6. **Simplicity:** Can it be shorter without losing effectiveness?

### Step 5: REFINE

Fix any issues found in Step 4. Repeat until all 6 checks pass.

### Step 6: PRESENT

Show the final prompt in a code block. After the prompt, offer:

- Edit it based on feedback
- Save it to a file
- Use it immediately (if the user wants to proceed with /cortex or manually)

## Output

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
```
