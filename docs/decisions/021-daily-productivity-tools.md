# ADR-021: Daily Productivity Tools Architecture

**Status:** Proposed
**Date:** 2026-06-24
**Deciders:** Adi + Claude Code
**Phase:** V4-V5

## Context

Odysseus has 10 productivity subsystems (~15,000 lines): task scheduler, skills, webhooks, email, calendar, notes, documents, contacts. The user wants all of them. Need to decide how they integrate with the agent system.

## Decision

- **Core (V4):** Task scheduler + skills + webhooks (foundation)
- **Plugins (V5):** Email, calendar, notes, documents, contacts
- Each is a separate module with its own routes, services, and models
- Agent tools expose productivity data to the agent system

## Consequences

### Positive
- Modular — each tool is independent
- Agent-accessible — all tools available to the agent via tool-calling
- Incremental — foundation first, full tools later

### Negative
- 10 modules to build and maintain
- Each needs its own data models, services, tests

## Related

- Odysseus reference repo (10 subsystems)
- V4-V5 phase plans
