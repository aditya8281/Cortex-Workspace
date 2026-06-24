# CORTEX Governance Rules

This document defines the rules of engagement for all participants (human and agent) in the Cortex development process.

---

## Single Source of Truth

| Topic | Source of Truth | Location |
|-------|----------------|----------|
| Agent behavior | CLAUDE.md | `/CLAUDE.md` |
| Security patterns | AGENTS.md | `/AGENTS.md` |
| System architecture | docs/ARCHITECTURE.md | `/docs/ARCHITECTURE.md` |
| Development roadmap | docs/ROADMAP.md | `/docs/ROADMAP.md` |
| API reference | docs/API.md | `/docs/API.md` |
| Database schema | docs/DATABASE.md | `/docs/DATABASE.md` |
| Security patterns | docs/SECURITY.md | `/docs/SECURITY.md` |
| Ecosystem governance | docs/GOVERNANCE.md | `/docs/GOVERNANCE.md` (this file) |
| Workflow definitions | docs/WORKFLOWS.md | `/docs/WORKFLOWS.md` |
| Design system | DESIGN.md | `/DESIGN.md` |
| Architectural decisions | docs/decisions/ | `/docs/decisions/` |
| Audit history | docs/audits/ | `/docs/audits/` |
| Hook system | .claude/hooks/ | `/.claude/hooks/` |
| Automation scripts | scripts/automation/ | `/scripts/automation/` |
| Developer guide | docs/DEVELOPER_GUIDE.md | `/docs/DEVELOPER_GUIDE.md` |

**Rule:** If a topic appears in multiple files, the source of truth wins. Other files must reference it, not duplicate it.

---

## Agent Permission Model

| Level | Capabilities | Human Approval Required |
|-------|-------------|------------------------|
| **Read-only** | Explore code, search, analyze | No |
| **Contributor** | Create branches, commit code | For merge |
| **Reviewer** | Review PRs, approve changes | For final merge |
| **Architect** | Create ADRs, modify governance | Always |

**Default:** Agents start at **Read-only**. Permission upgrades require human approval.

**Violation:** If an agent exceeds its permission level, the action must be reverted and the agent must request upgrade.

---

## Clarification Rules

### Agent MUST Ask Human

| Situation | Reason |
|-----------|--------|
| Irreversible decisions | Schema migrations, breaking API changes, security policy changes |
| Multiple valid paths | Architecture choices with trade-offs, design alternatives |
| Scope ambiguity | Unclear requirements, missing specifications |
| Resource constraints | Time/token budget decisions, priority conflicts |
| Security implications | New auth patterns, data handling changes |
| Breaking changes | API modifications, schema changes, dependency upgrades |
| Cross-domain impact | Changes affecting >2 subsystems |
| New patterns | Introducing new technologies or approaches not in current stack |

### Agent MAY Proceed Without Asking

| Situation | Reason |
|-----------|--------|
| Clear specifications | Task is well-defined with explicit acceptance criteria |
| Existing patterns | Following established codebase patterns |
| Mechanical changes | Typo fixes, formatting, import organization |
| Test updates | Updating tests for existing functionality |
| Documentation fixes | Correcting errors, updating examples |
| Dependency updates | Minor version bumps without breaking changes |

---

## Skill Governance

### Skill-First Rule

Before performing any significant task, agents must determine whether an existing skill can improve the process.

**Workflow:** Context → Find Skill → Use Skill → Brainstorm → Plan → Implement → Test → Validate → Review → Complete

**NOT:** Context → Implement Immediately

### Mandatory Skill Discovery

At the beginning of every major task:

1. Identify the task domain
2. Search for relevant skills
3. Evaluate available skills
4. Select the best skill or skill combination
5. Apply those skills before continuing

### Skill Gap Detection

During execution, agents must continuously evaluate:

- Is this process repetitive?
- Is this process likely to happen again?
- Is this process Cortex-specific?
- Is this process difficult enough to benefit from standardization?
- Is this process valuable enough to reuse?

If yes: Create a Skill Improvement Candidate.

### Skill Creation Workflow

Whenever a reusable workflow is identified:

1. Extract the process
2. Document the process
3. Create a dedicated skill
4. Add examples
5. Add validation steps
6. Integrate it into existing workflows

Creating skills should become a normal part of Cortex development.

### Cortex-Specific Skills

Actively build a library of Cortex-specific skills:

- Cortex Architecture Audit
- Cortex Repository Health Review
- Cortex Planning Consistency Audit
- Cortex Documentation Consistency Audit
- Cortex Memory Review
- Cortex Retrieval Review
- Cortex Model Marketplace Review
- Cortex Agent Review
- Cortex Desktop Readiness Audit
- Cortex Release Readiness Audit
- Cortex Frontend/Backend Contract Audit

Whenever a Cortex-specific workflow becomes mature and reusable, convert it into a dedicated skill.

### Skill Evolution

Skills must not remain static. When a skill is used:

- Review effectiveness
- Review output quality
- Review missing steps
- Review friction points
- Improve the skill

Skills should evolve alongside Cortex.

### Long-Term Objective

The Cortex repository should gradually evolve into a skill-driven engineering system. Over time, more work should move from ad-hoc manual execution to reusable, documented, validated skills.

Success means future agents spend less time reinventing workflows and more time executing proven processes. Whenever a better workflow is discovered, the agent should improve the ecosystem itself rather than only completing the immediate task.

---

## Branching Rules

### Mandatory Branch-Then-Merge

Every significant change must go through a feature branch. Never commit directly to `main`.

**Rule:** `main` branch must always be in a working state. All changes go through: `main` → feature branch → work → verify → merge back to `main`.

**Branch naming:**
- `feat/<topic>` — new features
- `fix/<topic>` — bug fixes
- `docs/<topic>` — documentation changes
- `refactor/<topic>` — code refactoring

**Branch lifecycle:**
1. Create branch from `main`
2. Make changes, commit with descriptive messages
3. Run relevant hooks and tests on the branch
4. When ready, run full verification (`make hooks-merge`, `make test`, `make lint`)
5. Merge to `main` with `--no-ff` (merge commit, not fast-forward)
6. Delete the feature branch after merge

**Parallel branch limit:** Minimize parallel branches. Finish one before starting the next. Maximum 2-3 active branches at any time to reduce merge conflicts.

**Main branch protection:**
- All hooks must pass before merge
- All tests must pass
- No direct commits to `main`
- No merge if main is broken

---

## Code Quality Standards

### Mandatory Before Every Commit

1. `make lint` passes (ruff + mypy)
2. `make format` applied (ruff format)
3. No secrets in code (detect-secrets)
4. No large files added (>500KB)

### Mandatory Before Every PR

1. All tests pass (`make test` + `cd frontend && npm test`)
2. Frontend builds (`cd frontend && npm run build`)
3. No regressions (existing tests still pass)
4. Documentation updated (if applicable)
5. ADR created (if architectural decision made)

### Mandatory Before Merge

1. CI passes (GitHub Actions)
2. Human review approved
3. No unresolved conflicts
4. No revert of previous reverts (circular)

---

## Documentation Standards

### When to Update Documentation

| Change Type | Docs to Update |
|-------------|---------------|
| New API endpoint | docs/API.md |
| New database table | docs/DATABASE.md |
| New security pattern | docs/SECURITY.md |
| Architecture change | docs/ARCHITECTURE.md |
| Roadmap change | docs/ROADMAP.md |
| New decision | docs/decisions/NNN-name.md |
| Bug found | docs/audits/YYYY-MM-DD-report.md |
| Workflow change | docs/WORKFLOWS.md |
| Governance change | docs/GOVERNANCE.md |

### Documentation Format

- Use Markdown with consistent heading levels
- Include "Last updated" date at top of each doc
- Use tables for structured data
- Use code blocks for commands and examples
- Cross-reference related docs with relative links

---

## Decision Tracking Rules

### When to Create an ADR

- New technology choice
- Architecture pattern change
- Security policy change
- API design decision
- Database schema philosophy change
- Testing strategy change
- Deployment approach change

### ADR Format

```markdown
# ADR-NNN: Title

**Status:** Proposed | Accepted | Deprecated | Superseded by ADR-XXX
**Date:** YYYY-MM-DD
**Deciders:** List of people/agents involved

## Context

What is the issue we're facing?

## Decision

What did we decide?

## Consequences

What are the implications?

## Alternatives Considered

What else did we evaluate?
```

### ADR Rules

1. ADRs are immutable once accepted
2. ADRs can be superseded, not modified
3. ADRs must reference related ADRs
4. ADRs must include alternatives considered
5. ADRs must be created before implementation

---

## Audit Rules

### When to Run Audits

| Trigger | Frequency |
|---------|-----------|
| Scheduled | Weekly (automated) |
| Before release | Manual |
| After major changes | Manual |
| On request | Manual |

### Audit Scope

- Architecture drift detection
- Documentation drift detection
- Technical debt identification
- Dead code detection
- Duplicate code detection
- Incomplete feature detection
- Placeholder detection (TBD, TODO, FIXME)
- Security vulnerability scanning
- Test coverage analysis

### Audit Reporting

Findings are reported in `docs/audits/YYYY-MM-DD-report.md` with:
- Summary (counts by severity)
- Individual findings with file/line references
- Recommended fixes
- Status tracking (Open → In Progress → Fixed)
