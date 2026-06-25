# ADR-011: Multi-Agent Governance Ecosystem

**Status:** Accepted
**Date:** 2026-06-24
**Deciders:** Adi + Claude Code

## Context

Multiple AI agents (Claude Code, future agents) participate in development. Without governance rules, agents may overreach, under-ask, or contradict each other.

## Decision

Adopt a convention-first governance system:
- 12 mandatory rules (docs/GOVERNANCE.md)
- 11 hooks (Claude Code hooks, governance hooks)
- 10 workflows (docs/WORKFLOWS.md)
- Strategic commands ecosystem (.claude/commands/project/) — 17 commands and growing
- Authority hierarchy: CLAUDE.md > guide.md > AGENTS.md > versions/ > docs/

## Consequences

### Positive
- Any AI agent can participate by reading governance docs
- Quality gates prevent regressions
- Technical debt is visible and trackable
- Architecture drift detected early

### Negative
- More documentation to maintain
- Some overhead for simple changes
- Agents must read more docs before starting

## Related

- `CLAUDE.md` — Execution contract
- `guide.md` — Constitution
- `AGENTS.md` — Agent behavior rules
- `docs/GOVERNANCE.md` — Governance rules
- `docs/WORKFLOWS.md` — Workflow definitions
- Integrity System: `/project:integrity` command and `cortex-integrity` skill as governance ecosystem additions
