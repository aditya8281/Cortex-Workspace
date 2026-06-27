# Architecture Decision Summary — CORTEX

**Document:** Final Decisions from the Architecture Council
**Authority:** Stage 4 — Master Consolidation & Final Specification
**Date:** 2026-06-27

---

## Purpose

This document records the final architectural decisions made during Stage 4 consolidation. These decisions are binding — they define the architectural direction for all future implementation.

---

## Decision Methodology

Every architectural decision was evaluated against:

1. **Nine non-negotiable principles** (local-first, privacy, persistence, understanding, assistance, human control, architecture before implementation, maintainability, scalable evolution)
2. **Vision alignment** (does this strengthen persistent intelligence?)
3. **Complexity cost** (does this justify its complexity?)
4. **Reversibility** (can this be changed later if needed?)

---

## Decisions

### AD-001: Domain-Driven Architecture

**Decision:** Cortex's capabilities are organized into 10 permanent domains with clear boundaries.

**Rationale:** The current monolithic backend lacks clear boundaries. Without domains, features bleed into each other, creating coupling and making maintenance difficult. Domain-driven design provides natural boundaries that prevent architecture degradation.

**Consequences:**
- Each domain has its own models, services, and API endpoints
- Domains communicate through defined interfaces
- New capabilities are added to existing domains, not created as new domains
- The domain model is conceptual (not necessarily matching folder structure exactly)

**Status:** APPROVED

---

### AD-002: Event-Driven Communication

**Decision:** Domains communicate through an event bus, not direct service calls.

**Rationale:** Direct service calls create tight coupling. When Domain A calls Domain B's service directly, changes in B break A. An event bus decouples domains — A publishes events, B subscribes. This enables independent evolution.

**Consequences:**
- Cross-domain communication is asynchronous by default
- Domains can be developed and tested independently
- Event schemas must be versioned carefully
- Debugging requires event tracing infrastructure

**Status:** APPROVED

---

### AD-003: Privacy as Architecture

**Decision:** Privacy is not a feature — it is the foundation layer. Every domain depends on it.

**Rationale:** Privacy cannot be bolted on after the fact. If privacy is a feature, it can be disabled. If privacy is architecture, it cannot be bypassed. Every domain operates within privacy constraints by design.

**Consequences:**
- All data processing happens locally by default
- All data is encrypted at rest and in transit
- Consent is required before any data access
- Audit logging records all significant actions
- No telemetry without explicit opt-in

**Status:** APPROVED

---

### AD-004: Memory-First Intelligence

**Decision:** Intelligence is built on memory, not computation. Cortex's primary capability is remembering and understanding.

**Rationale:** Computation is available everywhere. What makes Cortex unique is persistent, personal understanding. Without memory, Cortex is just another AI tool. With memory, it becomes a companion.

**Consequences:**
- Memory architecture is the highest priority
- All other domains connect to memory
- Memory is never deleted without explicit user action
- Memory consolidation is a background process
- Cross-domain memory is a first-class capability

**Status:** APPROVED

---

### AD-005: Layered Maturity Model

**Decision:** Each capability progresses through three levels: Foundation, Competent, Intelligent.

**Rationale:** Not all capabilities need to be intelligent immediately. A layered model allows Cortex to be useful at Foundation level while growing toward Intelligent. This prevents over-engineering early capabilities.

**Consequences:**
- Foundation capabilities are built first
- Competent capabilities emerge from Foundation
- Intelligent capabilities emerge from Competent
- Each level adds meaningful value
- No capability skips levels

**Status:** APPROVED

---

### AD-006: Multi-Modal Interaction

**Decision:** Cortex communicates through multiple modalities: conversational, visual, command-line, API, voice, ambient.

**Rationale:** Different tasks require different interaction modes. Coding is visual. Quick commands are textual. Complex workflows are conversational. Ambient presence requires subtlety. One mode cannot serve all needs.

**Consequences:**
- Conversational interface remains primary
- CLI is completed for power users
- GUI provides visual interfaces for visual tasks
- API enables programmatic integration
- Voice is added when technology matures
- Ambient intelligence emerges from awareness + proactive assistance

**Status:** APPROVED

---

### AD-007: Learning Without Surveillance

**Decision:** Cortex learns from interaction without surveilling the user. Learning happens on-device, with consent, using local data only.

**Rationale:** Learning requires data. Surveillance also requires data. The difference is consent, scope, and purpose. Cortex learns from what the user explicitly shares and what it can observe on the user's machine — never from external sources, never without consent.

**Consequences:**
- Preference learning requires user feedback
- Workflow learning requires observation of user actions
- Habit learning requires temporal patterns
- All learning data stays on-device
- Learning can be paused or reset at any time

**Status:** APPROVED

---

### AD-008: Gradual Capability Expansion

**Decision:** New capabilities are added incrementally, not all at once. Each phase builds on the previous.

**Rationale:** Building all 120 capabilities simultaneously is impossible. A phased approach allows Cortex to be useful at each phase while growing toward the complete vision. This also allows learning from each phase to inform the next.

**Consequences:**
- Phase 1: Foundation (25 capabilities)
- Phase 2: Core Memory + Awareness (18 capabilities)
- Phase 3: Learning + Execution (18 capabilities)
- Phase 4: Interaction + Developer (29 capabilities)
- Phase 5: Advanced Integration (29 capabilities)
- Phase 6: Intelligence (7 capabilities)

**Status:** APPROVED

---

### AD-009: Rejection of Community Features

**Decision:** Community features (multi-user, social, marketplace) are permanently rejected.

**Rationale:** Cortex is a personal intelligence. Community features compromise the personal intelligence principle. They create dependencies on other users, introduce social dynamics that distract from personal intelligence, and compromise privacy.

**Consequences:**
- Cortex is always single-user
- No sharing, no social features, no community
- Marketplace is rejected (extension system only)
- Analytics dashboard is rejected (vanity metrics)
- Cross-device sync is personal, not social

**Status:** APPROVED

---

### AD-010: Rejection of Cloud Dependency

**Decision:** Core capabilities must work without network access. Cloud services may be optional integrations but never required.

**Rationale:** Local-first is a non-negotiable principle. If core capabilities require the cloud, Cortex is not local-first. Optional cloud integration (e.g., email, calendar) is acceptable if the capability degrades gracefully without network.

**Consequences:**
- All memory, cognition, and learning work offline
- Cloud integrations (email, calendar) have offline fallbacks
- No telemetry without explicit opt-in
- No cloud-based model inference required
- Local model management is first-class

**Status:** APPROVED

---

### AD-011: Simplicity Over Completeness

**Decision:** When facing a choice between a simpler approach and a more complete approach, choose simpler.

**Rationale:** Complexity is the enemy of maintainability. A simpler system that works for 80% of cases is better than a complex system that works for 100%. The remaining 20% can be addressed through extensions or future work.

**Consequences:**
- Each capability starts simple
- Complexity is added only when justified by user need
- Internal abstractions are minimized
- Code is readable over clever
- Documentation explains the "why" over the "what"

**Status:** APPROVED

---

### AD-012: Architectural Evolution Over Revolution

**Decision:** The architecture evolves incrementally, not through wholesale redesign.

**Rationale:** The current architecture (FastAPI + SQLAlchemy + Next.js) is sound. It does not need replacement — it needs evolution. Bounded contexts, event bus, and service interfaces can be added without rewriting everything.

**Consequences:**
- Existing code is refactored, not rewritten
- New patterns are introduced gradually
- Architecture decision records document every change
- The architecture is reviewed regularly
- Technical debt is addressed incrementally

**Status:** APPROVED

---

## Summary of Decisions

| # | Decision | Status |
|---|----------|--------|
| AD-001 | Domain-Driven Architecture | APPROVED |
| AD-002 | Event-Driven Communication | APPROVED |
| AD-003 | Privacy as Architecture | APPROVED |
| AD-004 | Memory-First Intelligence | APPROVED |
| AD-005 | Layered Maturity Model | APPROVED |
| AD-006 | Multi-Modal Interaction | APPROVED |
| AD-007 | Learning Without Surveillance | APPROVED |
| AD-008 | Gradual Capability Expansion | APPROVED |
| AD-009 | Rejection of Community Features | APPROVED |
| AD-010 | Rejection of Cloud Dependency | APPROVED |
| AD-011 | Simplicity Over Completeness | APPROVED |
| AD-012 | Architectural Evolution Over Revolution | APPROVED |

**Total decisions:** 12
**All approved:** Yes
**All consistent with vision:** Yes
**All consistent with principles:** Yes

---

## Open Architectural Questions

These questions were identified but not resolved. They should be addressed during implementation planning:

1. **Event bus implementation:** In-memory vs Redis pub/sub vs custom?
2. **Domain boundary enforcement:** How strict are domain boundaries at the code level?
3. **Configuration storage:** Database vs file system vs hybrid?
4. **Background task scheduling:** Celery vs custom scheduler vs asyncio?
5. **Extension system scope:** What can extensions access? What can they not?

---

## Decision Authority

These decisions are made by the Architecture Council during Stage 4. They can only be changed through formal revision, not informal drift. Any proposed change must be evaluated against the nine non-negotiable principles and documented as a new ADR.
