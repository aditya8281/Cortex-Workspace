Last updated: 2026-06-28

# ADR-001: Agentic Development Ecosystem

**Status:** Accepted
**Date:** 2026-06-24
**Deciders:** Human (Adi) + Claude Code

## Context

Cortex has 60+ agent skills, solid CI, and clean governance docs. But there is no orchestrated development operating system — no formal workflows, no decision tracking, no automated validation beyond CI, no audit process, and no clear protocol for how multiple AI agents participate.

The repository has experienced:
- Documentation drift (5 competing doc systems, now consolidated)
- No decision tracking (architectural choices undocumented)
- No systematic bug discovery (ad-hoc only)
- No audit process (one audit done, not repeatable)
- No clear agent permission model
- No clarification rules (agents sometimes overreach or under-ask)

## Decision

We adopt a **convention-first, multi-agent** development ecosystem with:

1. **Four-layer validation:** Pre-commit → Local → CI → Post-merge audit
2. **Governance docs:** CLAUDE.md + AGENTS.md + docs/GOVERNANCE.md + docs/WORKFLOWS.md
3. **Decision tracking:** ADRs in docs/decisions/
4. **Audit tracking:** Periodic audits in docs/audits/
5. **Clarification rules:** Explicit rules for when agents must ask humans
6. **Permission model:** Read-only → Contributor → Reviewer → Architect

### What This Enables

- Any AI agent can participate by reading governance docs
- Decisions are documented and traceable
- Quality is enforced at multiple levels
- Technical debt is tracked and prioritized
- Architecture drift is detected early
- Agents know when to ask for help

### What This Does NOT Do

- No new tooling (convention-first, not tool-first)
- No runtime agent orchestration (agents self-govern via docs)
- No automated agent spawning (human decides when to use agents)
- No mandatory audit frequency (weekly is recommended, not enforced)

## Consequences

### Positive
- Clear rules for all participants
- Decisions are documented and reversible
- Quality gates prevent regressions
- Technical debt is visible and trackable
- Agents can work independently with clear boundaries

### Negative
- More documentation to maintain
- Some overhead for simple changes
- Agents must read more docs before starting work
- Clarification rules may slow down simple tasks

### Mitigations
- Clarification rules have explicit "may proceed without asking" cases
- Simple mechanical changes bypass most gates
- Documentation is kept concise and cross-referenced

## Alternatives Considered

### Option 1: Tool-first (rejected)
Build a CLI tool (`cortex audit`, `cortex validate`, `cortex review`) that agents call.
- **Pros:** Richer automation, easier to extend
- **Cons:** Requires building new tooling, more complex, tool maintenance burden
- **Why rejected:** Convention-first is simpler and works today with existing skills

### Option 2: Agent-agnostic framework (rejected)
Design a standard protocol that any agent implements via adapters.
- **Pros:** Maximum flexibility, future-proof
- **Cons:** Requires defining abstraction layer, more complex, premature
- **Why rejected:** premature abstraction — we don't yet know what other agents need

### Option 3: Claude Code only (rejected)
Design ecosystem specifically for Claude Code.
- **Pros:** Simpler, leverages Claude Code features directly
- **Cons:** Locks into one agent, doesn't scale
- **Why rejected:** User explicitly wants multi-agent support

## Related

- docs/GOVERNANCE.md — Governance rules
- docs/WORKFLOWS.md — Workflow definitions
- docs/ROADMAP.md — Development roadmap
