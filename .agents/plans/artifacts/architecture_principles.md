# Architecture Principles — CORTEX

**Document:** Binding Architecture Principles
**Authority:** Stage 5 — Repository & Architecture Restructure
**Date:** 2026-06-27

---

## Purpose

This document defines the binding architecture principles for Cortex. These principles are immutable — they govern every architectural decision. They are derived from the Stage 4 architecture decisions and the Stage 2 vision.

---

## The Twelve Principles

### 1. Domain-Driven Organization

**Principle:** The repository is organized around Cortex's 10 capability domains, not technologies.

**Rationale:** Technology-driven organization creates scattered responsibilities. Domain-driven organization creates clear ownership and natural boundaries.

**Enforcement:**
- Each domain has its own service directory
- Each domain has its own model file
- Each domain has its own API endpoint file
- Each domain has its own frontend feature directory

**Violation example:** Putting all models in one flat directory regardless of domain.

---

### 2. Dependency Direction

**Principle:** Dependencies flow strictly downward: API → Service → Agent → Intelligence → Infrastructure.

**Rationale:** Circular dependencies create coupling. Downward-only dependencies enable independent evolution.

**Enforcement:**
- Lower layers never import from higher layers
- Same-level communication uses events, not direct imports
- Dependency injection enforces boundaries

**Violation example:** A service importing from the API layer.

---

### 3. Event-Driven Communication

**Principle:** Cross-domain communication happens through events, not direct service calls.

**Rationale:** Direct calls create tight coupling. Events decouple domains while enabling cross-domain intelligence.

**Enforcement:**
- Services publish events on state changes
- Other services subscribe to events they care about
- No service calls another service's methods directly

**Violation example:** Memory service directly calling Learning service's methods.

---

### 4. Privacy as Foundation

**Principle:** Privacy is the foundation layer, not a feature. Every domain depends on it.

**Rationale:** Privacy cannot be bolted on. If privacy is a feature, it can be disabled. If privacy is architecture, it cannot be bypassed.

**Enforcement:**
- All data processing happens locally by default
- All data is encrypted at rest and in transit
- Consent is required before any data access
- Audit logging records all significant actions

**Violation example:** Adding a cloud service without privacy guarantees.

---

### 5. Memory-First Intelligence

**Principle:** Intelligence is built on memory, not computation. Cortex's primary capability is remembering and understanding.

**Rationale:** Computation is available everywhere. What makes Cortex unique is persistent, personal understanding.

**Enforcement:**
- Memory architecture is the highest priority
- All other domains connect to memory
- Memory is never deleted without explicit user action
- Cross-domain memory is a first-class capability

**Violation example:** Building a feature that ignores existing memory.

---

### 6. Layered Maturity

**Principle:** Each capability progresses through Foundation → Competent → Intelligent.

**Rationale:** Not all capabilities need to be intelligent immediately. A layered model allows Cortex to be useful at each level.

**Enforcement:**
- Foundation capabilities are built first
- Competent capabilities emerge from Foundation
- Intelligent capabilities emerge from Competent
- No capability skips levels

**Violation example:** Building an intelligent capability without Foundation first.

---

### 7. Simplicity Over Completeness

**Principle:** When facing a choice between simpler and more complete, choose simpler.

**Rationale:** Complexity is the enemy of maintainability. A simpler system that works for 80% of cases beats a complex system for 100%.

**Enforcement:**
- Each capability starts simple
- Complexity is added only when justified by user need
- Internal abstractions are minimized
- Code is readable over clever

**Violation example:** Building a complex abstraction for a problem that doesn't exist yet.

---

### 8. Architectural Evolution

**Principle:** The architecture evolves incrementally, not through wholesale redesign.

**Rationale:** The current architecture is sound. It needs evolution, not revolution.

**Enforcement:**
- Existing code is refactored, not rewritten
- New patterns are introduced gradually
- Architecture decision records document every change
- Technical debt is addressed incrementally

**Violation example:** Rewriting the entire backend to adopt a new framework.

---

### 9. Clear Ownership

**Principle:** Every file, every module, every domain has one clear owner.

**Rationale:** Without ownership, responsibilities scatter. With ownership, accountability exists.

**Enforcement:**
- Each domain has a domain owner
- Each file has a clear owner (domain or infrastructure)
- Code reviews require domain owner approval
- Ownership is documented in repository tree

**Violation example:** Multiple teams modifying the same service without coordination.

---

### 10. Discoverability

**Principle:** The repository structure communicates what Cortex does. A contributor should understand the project by browsing folders.

**Rationale:** If the structure doesn't communicate purpose, contributors waste time finding things.

**Enforcement:**
- Directory names describe purpose
- File names describe content
- README files explain non-obvious structure
- Code comments explain "why" over "what"

**Violation example:** Generic folder names like `utils/` or `helpers/` that don't communicate purpose.

---

### 11. Testability

**Principle:** Every component is testable in isolation. Tests are first-class citizens, not afterthoughts.

**Rationale:** Untested code is broken code waiting to be discovered.

**Enforcement:**
- Dependency injection enables isolated testing
- Mock external services in tests
- Test coverage tracked and enforced
- Tests run on every commit

**Violation example:** A service that cannot be tested without starting the full application.

---

### 12. Versioned Evolution

**Principle:** The system evolves through versioned phases. Each phase is independently valuable.

**Rationale:** Big-bang rewrites fail. Incremental evolution succeeds.

**Enforcement:**
- Six versions (V1-V6) with clear boundaries
- Each version delivers complete, working functionality
- Versions build on each other
- Progress is tracked per version

**Violation example:** Trying to build V6 features before V1 is complete.

---

## Principle Priority

When principles conflict, this priority governs:

1. **Privacy as Foundation** (principle 4) — always wins
2. **Memory-First Intelligence** (principle 5) — core identity
3. **Simplicity Over Completeness** (principle 7) — prevent complexity
4. **Dependency Direction** (principle 2) — prevent coupling
5. All other principles — evaluated case by case

---

## Principle Enforcement

Principles are enforced through:

1. **Architecture Decision Records** — Every decision references principles
2. **Code Reviews** — Reviewers check principle compliance
3. **Integrity System** — Automated principle checks
4. **Governance** — Quarterly principle review

---

## Relationship to Stage 4 Decisions

These principles are derived from the 12 architecture decisions in Stage 4:

| Principle | Derived From |
|-----------|-------------|
| Domain-Driven Organization | AD-001 |
| Dependency Direction | AD-001, AD-002 |
| Event-Driven Communication | AD-002 |
| Privacy as Foundation | AD-003 |
| Memory-First Intelligence | AD-004 |
| Layered Maturity | AD-005 |
| Simplicity Over Completeness | AD-011 |
| Architectural Evolution | AD-012 |
| Clear Ownership | AD-001, AD-008 |
| Discoverability | AD-008 |
| Testability | AD-011 |
| Versioned Evolution | AD-008 |

---

## Derived Core Principles

The following principles were established in Stage 2 (Vision & Identity Redefinition) as non-negotiable philosophical foundations. They predate the twelve architecture principles and inform them at a higher level of abstraction.

### Principle 1: Local-First by Default

Cortex runs on the user's machine. Not primarily locally. Not locally when possible. Locally by default. Cloud services, when they exist, are optional accelerators — never dependencies. If a cloud service becomes unavailable, Cortex continues to function with full capability.

**What this means for decisions:** Every feature must work without network access. Every data store must be local. Every computation must be possible on the user's hardware.

**What this means for architecture:** No hard dependencies on external services. Graceful degradation when external services are unavailable. Local databases as the primary data store.

---

### Principle 2: Privacy Before Convenience

Cortex knows intimate details about its user's work, habits, and knowledge. This knowledge is never shared. Not with the developer. Not with other users. Not with analytics services. Not with anyone. Privacy is not a setting that can be toggled. It is a structural guarantee embedded in the architecture.

**What this means for decisions:** When convenience and privacy conflict, privacy wins. When telemetry would be useful, it is not added. When sharing would improve the product, sharing does not happen.

**What this means for architecture:** No telemetry. No analytics. No phone-home. No external data transmission unless the user explicitly initiates it. Data encrypted at rest and in transit.

---

### Principle 3: Persistent Intelligence

Cortex does not forget. Every interaction, every index, every understanding persists across sessions, reboots, and years. Cortex's value is directly proportional to the duration it has been running. A Cortex installed yesterday is useful. A Cortex installed five years ago is irreplaceable.

**What this means for decisions:** Every piece of state must be durable. Every memory must survive process restarts. Backward compatibility is not optional — it is existential.

**What this means for architecture:** Database-backed state everywhere. No in-memory-only state for anything important. Migration systems that preserve accumulated understanding.

---

### Principle 4: Understand Before Acting

Cortex does not act first and ask questions later. It builds understanding. It gathers context. It analyzes. Then it acts with the full weight of its understanding behind it. Acting without understanding is not just incorrect — it is the antithesis of what Cortex is.

**What this means for decisions:** Features that act without context are rejected. Features that bypass understanding are rejected. The path from data to understanding to action must be visible and auditable at every step.

**What this means for architecture:** Every action must have a preceding understanding phase. Every recommendation must cite its evidence. Every automated decision must be explainable and reversible.

---

### Principle 5: Assist Instead of Replace

Cortex makes the human more capable. It does not make the human less necessary. Cortex suggests, recommends, prepares, and presents. The human decides. This is not a temporary limitation to be overcome as AI improves. It is a permanent design choice reflecting the belief that human judgment is irreplaceable.

**What this means for decisions:** Features that automate consequential decisions without human approval are rejected. Features that make the human feel unnecessary are rejected. The human must always feel more capable, not less capable, when Cortex is present.

**What this means for architecture:** Human-in-the-loop for all consequential actions. Undo capability for all state-changing operations. Clear attribution of which decisions were made by Cortex and which by the human.

---

### Principle 6: Human Control Always Exists

The human can always override Cortex. The human can always understand why Cortex did something. The human can always disable, modify, or ignore Cortex's suggestions. Cortex is a tool, not an authority. Its intelligence serves the human's judgment, never the reverse.

**What this means for decisions:** Features that cannot be overridden are rejected. Features that cannot be explained are rejected. Features that make it harder for the human to maintain control are rejected.

**What this means for architecture:** Every Cortex action is logged and queryable. Every Cortex suggestion includes its reasoning. Every automated process can be stopped. Every default can be changed.

---

### Principle 7: Architecture Before Implementation

The right structure enables decades of evolution. The wrong structure constrains months of work. Cortex's architecture must be designed for the 10-year horizon, not the next release. This means investing in abstraction, modularity, and extensibility before implementing features.

**What this means for decisions:** Features that require architectural compromises are architectural problems, not features. The architecture is fixed first. Features fit within it.

**What this means for architecture:** Clean interfaces between components. Minimal coupling between modules. Extension points that do not require modifying core code.

---

### Principle 8: Long-Term Maintainability

Cortex must be maintainable by a small team for years. Every line of code is a commitment to future understanding. Every dependency is a commitment to future compatibility. Every abstraction is a commitment to future flexibility.

**What this means for decisions:** Clever code is rejected in favor of clear code. Short-term shortcuts are rejected in favor of sustainable approaches. Features that add maintenance burden without proportional value are rejected.

**What this means for architecture:** Simple, readable code over clever, compact code. Comprehensive tests over rapid development. Documentation over tribal knowledge.

---

### Principle 9: Scalable Evolution

Cortex evolves. It does not revolutionize. Every change must build on what exists, preserve accumulated state, and extend capability without breaking continuity. The user who installed Cortex three years ago and the user who installs it today should share a coherent experience.

**What this means for decisions:** Breaking changes are rejected unless absolutely necessary and accompanied by migration paths. Features that require the user to start over are rejected. Features that render accumulated understanding obsolete are rejected.

**What this means for architecture:** Versioned APIs. Migration systems for data and configuration. Feature flags for gradual rollout. Backward compatibility as a first-class concern. Deprecation periods measured in months, not days.
