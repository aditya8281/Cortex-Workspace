# GUIDE.md — CORTEX Planning System

**Document:** Planning System Guide (Architecture Constitution)
**Authority:** Stage 6 — Master Versioned Implementation Roadmap
**Date:** 2026-06-27
**Revision:** v2.0 — Post Red Team Integration

---

## Purpose

This document is the **architecture constitution** for CORTEX. It governs how the planning system works — how versions, phases, and progress are structured, created, and maintained. It also records binding architecture decisions, capability domains, integration with external reference implementations, and the Red Team governance process.

---

## Planning Philosophy

The planning system is:

1. **Version-based.** Work is organized into versions. Each version represents one major milestone.
2. **Linear.** Versions are completed in order. No skipping.
3. **Incremental.** Each version builds on the previous. No wholesale rewrites.
4. **Complete.** Every approved capability appears in exactly one version.
5. **Executable.** Every phase contains enough detail to implement without additional planning.
6. **Agent-first.** The agent loop is the core system. Everything else depends on it.
7. **Migration-safe.** Every database change must have a verified rollback.
8. **Performance-gated.** Performance gates at every version, not just at the final.

---

## Architectural Principles

These principles govern all decisions in the CORTEX system. They are immutable unless formally amended through the ADR process.

### Core Principles

| # | Principle | Statement |
|---|-----------|-----------|
| 1 | **Local-first** | All data lives on the user's machine. No cloud dependency. |
| 2 | **Single-user** | No multi-tenancy. No user tables. Trust the host OS. |
| 3 | **Encrypted vaults** | Every user file is encrypted at rest with Fernet. |
| 4 | **Offline-capable** | The system works without network. No online APIs required. |
| 5 | **Streaming-native** | All LLM interactions stream tokens in real time. |
| 6 | **Plugin-safe** | External code runs in isolated contexts with explicit permissions. |
| 7 | **Autonomous** | The agent can act independently with user approval for destructive actions. |
| 8 | **Composable** | Every module has a single responsibility and clean interfaces. |
| 9 | **Observable** | Every significant action is logged and inspectable. |
| 10 | **Testable** | Every component can be tested in isolation with mocked dependencies. |

### Derived Principles (Post Red Team)

| # | Principle | Statement |
|---|-----------|-----------|
| 11 | **Agent-first** | The agent loop is the core system. Everything else depends on it. Build agent loop first, validate it works, then add capabilities around it. |
| 12 | **Migration-safe** | Every database change must have a verified rollback. No forward-only migrations. Every schema change is tested against both SQLite (dev) and PostgreSQL (prod). |
| 13 | **Performance-gated** | Performance gates at every version, not just at the final. Latency, memory, and throughput are measured and bounded per-version. |

---

## Directory Structure

```
.agents/plans/
├── GUIDE.md                    # This file (architecture constitution)
├── IMPLEMENTATION_STEPS.md     # Master roadmap navigation
├── ACTIVE_VERSION.md           # Currently active version pointer
├── FinalCompatibilities.md     # Cross-reference matrix
├── shared-phases.md            # Reusable phase definitions
├── Audit.md                    # Audit log
├── artifacts/                  # Stage 1-5 outputs (read-only reference)
│   ├── ai_philosophy.md
│   ├── architecture_decision_summary.md
│   ├── architecture_principles.md
│   ├── architecture_review.md
│   ├── capability_catalog.md
│   ├── capability_domains.md
│   ├── feature_decision_log.md
│   ├── red_team_report.md
│   └── ...
├── versions/
│   ├── v1.0/                   # Current state snapshot (non-executable)
│   ├── v1.01/                  # Repository restructure
│   ├── v1.02/                  # Backend architecture + agent loop
│   ├── v1.03/                  # Memory foundation
│   ├── v1.04/                  # Awareness layer
│   ├── v1.05/                  # Security layer
│   ├── v1.06/                  # Developer tools
│   ├── v1.07/                  # Interaction layer
│   ├── v1.08/                  # Planning system
│   ├── v1.09/                  # Learning system
│   ├── v1.10/                  — v1.14 (advanced intelligence)
│   ├── v2/                     # Architecture versions (reference)
│   ├── v3/ - v6/               # Future milestone versions
│   └── frontend-redesign-evolution.md
└── templates/                  # Phase and version templates
```

---

## reference architecture Integration

### What Is reference architecture

reference architecture is a reference implementation of a production-grade streaming agent loop. It consists of:

- **3,485 lines** of streaming agent loop code
- **60+ tool schemas** with dynamic loading
- **RAG-based tool selection** for intelligent capability routing
- **Context compaction** to manage long-running conversations
- **MCP (Model Context Protocol) integration** for external tool access
- **Memory persistence** across sessions
- **Multi-step reasoning** with tool use and self-correction

reference architecture represents the production standard that CORTEX is building toward. It is not code to be copied — it is an architectural reference that validates our design decisions and reveals gaps in our planning.

### How reference architecture Influenced the Planning System

Seven critical features from reference architecture were integrated into v1.02 and later versions:

| # | Feature | Impact | Target Version |
|---|---------|--------|----------------|
| 1 | **Streaming agent loop** | Core of the agent system — SSE streaming with tool execution | v1.02 |
| 2 | **Dynamic tool loading** | Tools loaded from schemas, not hardcoded | v1.02 |
| 3 | **RAG-based tool selection** | Vector similarity to select relevant tools per query | v1.03 |
| 4 | **Context compaction** | Summarize old context to stay within token limits | v1.02 |
| 5 | **MCP integration** | Model Context Protocol for external tool servers | v1.02 |
| 6 | **Memory persistence** | Save and restore conversation context | v1.03 |
| 7 | **Multi-step reasoning** | Chain tool calls with intermediate reasoning | v1.02 |

### Reference Document

Full audit of reference architecture against CORTEX planning: `REFERENCE_ARCHITECTURE_AUDIT.md` (in artifacts/ or root).

---

## Version Summary

The CORTEX system is built across 14 executable versions (v1.01 through v1.14), preceded by a snapshot (v1.0) and succeeded by major milestone versions (v2-v6).

### Executable Versions

| Version | Name | Duration | What It Delivers |
|---------|------|----------|------------------|
| **v1.0** | Snapshot | — | Current state baseline (non-executable) |
| **v1.01** | Foundation | 3-5 days | Repository restructure, project skeleton, CI/CD |
| **v1.02** | The Brain | 5-8 days | Streaming agent loop, tool policy, context compaction, MCP |
| **v1.03** | The Memory | 4-6 days | Embeddings pipeline, vector store, RAG retrieval, knowledge graph |
| **v1.04** | The Awareness | 4-6 days | File indexing, code intelligence, change tracking |
| **v1.05** | The Vault | 3-5 days | Fernet encryption, secure password cache, vault CLI |
| **v1.06** | The Developer | 3-5 days | Skills, hooks, commands, developer ecosystem |
| **v1.07** | The Interaction | 4-6 days | SSE streaming UI, chat interface, agent dashboard |
| **v1.08** | The Planning | 3-5 days | Autonomous planning, version management, progress tracking |
| **v1.09** | The Learning | 4-6 days | Preference learning, pattern recognition, outcome tracking |
| **v1.10** | The Scheduler | 4-6 days | Cron-based task scheduling, recurring agent actions |
| **v1.11** | The Researcher | 4-6 days | Web search, deep research, citation management |
| **v1.12** | The Integrator | 4-6 days | External service connectors, API gateway |
| **v1.13** | The Optimizer | 3-5 days | Performance tuning, caching strategy, monitoring |
| **v1.14** | The Polished | 4-6 days | UI polish, accessibility, documentation completeness |

### Milestone Versions (Reference)

| Version | Name | Focus |
|---------|------|-------|
| **v2** | The Architecture | Provider/MCP abstraction, plugin system, memory architecture |
| **v3** | The Desktop | Tauri shell, TUI, performance optimization |
| **v4** | The Automaton | Scheduler, MCP server, research, sessions |
| **v5** | The Workspace | Email, calendar, tasks, notes, documents, contacts |
| **v6** | The Ecosystem | Marketplace, graph intelligence, cross-encoder, polish |

---

## Architecture Decision Registry

All binding architecture decisions are recorded here. Once an ADR is marked **Implemented**, it is frozen — it cannot be contradicted by later work without a formal amendment.

| ADR | Decision | Status | Version |
|-----|----------|--------|---------|
| **AD-001** | Backend framework: FastAPI + sync SQLAlchemy 2.0 + Alembic | Implemented | v1.01 |
| **AD-002** | Database: PostgreSQL (prod) + SQLite (dev/test) + Alembic migrations | Implemented | v1.01 |
| **AD-003** | Frontend: Next.js 15 App Router + React 19 + TypeScript 5.8 + Tailwind 3.4 | Implemented | v1.01 |
| **AD-004** | Auth: JWT access (30min) + refresh (7-day) in httpOnly cookies + CSRF double-submit | Implemented | v1.01 |
| **AD-005** | Embeddings: ONNX (local) → Ollama (local) → mock (fallback). 768-dim in Qdrant | Planned | v1.03 |
| **AD-006** | RAG: HybridRetrievalV2 — vector + fulltext + graph via RRF + MMR | Planned | v1.03 |
| **AD-007** | Vault: Fernet encryption per-user. SecurePasswordCache. AES-256 at rest | Planned | v1.05 |
| **AD-008** | Agent: Streaming loop + tool policy + context compaction + multi-step reasoning | Implemented | v1.02 |
| **AD-009** | MCP: Model Context Protocol for external tool server integration | Implemented | v1.02 |
| **AD-010** | Memory: Qdrant (vector) + Neo4j (graph) + FTS5 (fulltext). Triple-store pattern | Planned | v1.03 |
| **AD-011** | Awareness: File indexing + code intelligence (Rust crate) + change tracking | Planned | v1.04 |
| **AD-012** | Learning: Preferences + patterns + outcomes. On-device ML with no cloud sync | Planned | v1.09 |

### ADR Rules

1. **No silent contradictions.** An implemented ADR cannot be contradicted by new code without a formal amendment.
2. **Amendments require review.** Changing an implemented ADR requires adversarial review (`/project:challenge`).
3. **New ADRs require justification.** Any new decision must reference which existing decisions it interacts with.
4. **Status tracking.** Statuses: `Planned` → `In Progress` → `Implemented` → `Frozen`.

---

## Capability Domain Map

CORTEX delivers 120 capabilities across 10 domains. Each domain contains 12 capabilities. Each capability is assigned to exactly one version.

| # | Domain | Capabilities | Range | Description |
|---|--------|-------------|-------|-------------|
| 1 | **Memory** | 12 | 1-12 | Storage, retrieval, knowledge graphs, embeddings, vector search |
| 2 | **Awareness** | 12 | 13-24 | File indexing, code intelligence, change tracking, context awareness |
| 3 | **Intelligence** | 12 | 25-36 | LLM integration, reasoning, tool selection, model management |
| 4 | **Agent** | 12 | 37-48 | Agent loop, autonomous actions, tool execution, multi-step reasoning |
| 5 | **Interaction** | 12 | 49-60 | Chat UI, streaming, SSE, dashboard, responsive design |
| 6 | **Security** | 12 | 61-72 | Encryption, auth, CSRF, vault, access control, audit logging |
| 7 | **Developer** | 12 | 73-84 | Skills, hooks, commands, CI/CD, testing, documentation |
| 8 | **Learning** | 12 | 85-96 | Preferences, patterns, outcomes, adaptation, feedback loops |
| 9 | **Planning** | 12 | 97-108 | Autonomous planning, version management, progress tracking, roadmaps |
| 10 | **Utility** | 12 | 109-120 | Scheduling, research, integrations, export, backup, health checks |

### Domain Dependency Order

Domains are delivered roughly in this order (some overlap across versions):

```
Memory → Awareness → Intelligence → Agent → Interaction
    ↓                                              ↓
Security → Developer → Learning → Planning → Utility
```

---

## Red Team Integration

### The Red Team Process

The CORTEX planning system underwent a formal Red Team review conducted by a **14-member council** of adversarial reviewers. The Red Team's purpose is to find flaws, gaps, inconsistencies, and risks in the planning system before implementation begins.

The Red Team process:

1. **Full audit** of all planning documents, capability assignments, version structure, and architecture decisions.
2. **Adversarial probing** — each reviewer attacks the plan from a different angle (security, performance, feasibility, scope, dependencies, etc.).
3. **Findings delivery** — structured reports with severity ratings and recommended fixes.
4. **Integration** — findings are addressed and integrated into the planning system.
5. **Validation** — re-review to confirm fixes are adequate.

### Key Findings and Resolution

The Red Team identified issues across multiple categories. All critical and high-severity findings have been addressed:

| Category | Key Finding | Resolution |
|----------|-------------|------------|
| **Scope** | Some versions were overloaded; others were under-scoped | Rebalanced durations and capability counts across versions |
| **Dependencies** | Missing dependency chains between versions | Explicit dependency graph added to each version OVERVIEW |
| **reference architecture gap** | Planning lacked reference to production agent implementations | reference architecture integration section added; 7 features mapped to versions |
| **Architecture drift** | No registry of binding decisions | AD-001 through AD-012 registered with status tracking |
| **Testing gaps** | No performance gates between versions | Derived principle: performance-gated at every version |
| **Migration risk** | No rollback strategy for schema changes | Derived principle: migration-safe; rollback required |
| **Agent priority** | Agent loop was scheduled too late in the roadmap | Agent loop (AD-008) moved to v1.02 as second executable version |

### Red Team Deliverables

Seven deliverable documents were produced during the Red Team review and are stored in `.agents/plans/artifacts/`:

| # | Document | Purpose |
|---|----------|---------|
| 1 | `architecture_review.md` | Full architectural review with findings |
| 2 | `architecture_decision_summary.md` | Summary of all architecture decisions |
| 3 | `capability_dependencies.md` | Dependency graph between capabilities |
| 4 | `feature_decision_log.md` | Log of all feature inclusion/exclusion decisions |
| 5 | `gap_analysis.md` | Gaps between planned capabilities and implementation |
| 6 | `planning_review.md` | Review of the planning system itself |
| 7 | `red_team_report.md` | Final Red Team report with all findings and resolutions |

These documents are **read-only reference** — they record historical decisions and should not be modified after the Red Team review closes.

---

## Enhanced Authority Hierarchy

When documents conflict, this order governs:

| Priority | Document | Purpose |
|----------|----------|---------|
| 1 | **CLAUDE.md** | Execution contract — what Claude does |
| 2 | **GUIDE.md** (this file) | Constitution — architecture principles, decisions, what to build |
| 3 | **AGENTS.md** | Agent behavior rules — security, API patterns |
| 4 | **IMPLEMENTATION_STEPS.md** | Implementation guide — execution order |
| 5 | **versions/vX/Phase-N.md** | Active phase plan — current work |
| 6 | **docs/** | Reference — detailed docs for specific domains |
| 7 | **REFERENCE_ARCHITECTURE_AUDIT.md** | Reference implementation audit — validates agent architecture |
| 8 | **artifacts/** (Red Team) | Validation documents — historical review records |

**Rule:** If a topic appears in multiple documents, the higher-priority document wins. Lower documents reference, not duplicate.

### Reference Documents

| Document | Location | Purpose |
|----------|----------|---------|
| Architecture | `docs/ARCHITECTURE.md` | System architecture details |
| Constitution | `.agents/plans/GUIDE.md` (this file) | Architecture principles, ADRs, domains |
| Governance | `docs/GOVERNANCE.md` | Project governance rules |
| Implementation Guide | `.agents/plans/IMPLEMENTATION_STEPS.md` | Development workflow details |
| API Reference | `docs/API.md` | API endpoint documentation |
| Database Schema | `docs/DATABASE.md` | Database schema documentation |
| Design System | `DESIGN.md` | Frontend design tokens and system |
| Implementation Guide | `.agents/plans/IMPLEMENTATION_STEPS.md` | Master roadmap navigation |
| reference architecture Audit | `REFERENCE_ARCHITECTURE_AUDIT.md` | Reference implementation integration plan |
| Phase Plans | `.agents/plans/versions/vX/Phase-N.md` | Per-version phase plans |
| Progress Tracking | `.agents/plans/versions/vX/PROGRESS.md` | Per-version progress |
| Red Team Reports | `.agents/plans/artifacts/` | Adversarial review deliverables |

---

## Version Philosophy

### What Is a Version

A version represents one major milestone in Cortex's evolution. After completing a version, Cortex has gained a clearly defined new capability or set of capabilities.

### Version Naming

Versions use the format `v1.XX` where XX is a two-digit number:

- `v1.0` — Current state (snapshot, non-executable)
- `v1.01` — Repository restructure
- `v1.02` — Backend architecture + agent loop
- `v1.03` — Memory foundation
- ... through `v1.14` — Advanced intelligence and polish

### Version Question

Every version answers one question: "What major capability or milestone does Cortex gain after completing this version?"

### Version Types

| Type | Description | Example |
|------|-------------|---------|
| Snapshot | Historical record of current state | v1.0 |
| Structural | Repository reorganization | v1.01 |
| Architectural | Infrastructure + agent core | v1.02 |
| Capability | New domain capabilities | v1.03–v1.14 |
| Milestone | Major system milestone | v2–v6 |

---

## Phase Philosophy

### What Is a Phase

A phase represents one logical implementation step within a version. A phase is large enough to be meaningful but small enough to be completable in a reasonable timeframe.

### Phase Naming

Phases use the format `P01.md`, `P02.md`, etc., within their version directory.

### Phase Contents

Every phase must include:

| Section | Purpose |
|---------|---------|
| Objective | What this phase achieves |
| Purpose | Why this phase exists |
| Architecture References | Which Stage 5 documents apply |
| Prerequisites | What must be done first |
| Dependencies | What this phase depends on |
| Implementation Tasks | Specific tasks to implement |
| Repository Changes | Files created, modified, moved |
| Migration Tasks | Migration steps if applicable |
| Backend Tasks | Backend-specific work |
| Frontend Tasks | Frontend-specific work |
| Documentation Tasks | Documentation updates |
| Developer Ecosystem Tasks | Skills, hooks, commands updates |
| Configuration Changes | Config file changes |
| Testing Strategy | How to test this phase |
| Validation Steps | How to verify completion |
| Definition of Done | Exact criteria for completion |
| Readiness for Next Phase | How to confirm ready for next phase |
| Estimated Complexity | Low/Medium/High with hours |
| Risks | Known risks and mitigations |

---

## Progress Tracking

### Progress File

Every version has a `PROGRESS.md` that tracks:

```markdown
# Version X.XX Progress

## Status: [Not Started | In Progress | Complete]

## Components
- [x] Component A — Complete (date)
- [ ] Component B — In Progress
- [ ] Component C — Not Started

## Capabilities Delivered
- [x] Capability X — Complete
- [ ] Capability Y — In Progress

## Metrics
- Files changed: X
- Tests added: X
- Coverage: X%
```

### Status Values

| Status | Meaning |
|--------|---------|
| Not Started | No work begun |
| In Progress | Active work underway |
| Complete | All phases done, all criteria met |

---

## Contribution Workflow

### Before Starting a Version

1. Read `IMPLEMENTATION_STEPS.md` for context
2. Read the version's `OVERVIEW.md` for scope
3. Read the current `PROGRESS.md` for status
4. Read prerequisite versions' `PROGRESS.md` for dependencies
5. Read this GUIDE.md for architecture principles and ADRs
6. Begin with `P01.md`

### During Implementation

1. Follow the phase exactly as written
2. Complete all implementation tasks
3. Run all validation steps
4. Verify definition of done
5. Update `PROGRESS.md`
6. Commit with clear message
7. Proceed to next phase

### After Completing a Version

1. Verify all phases complete
2. Verify all capabilities delivered
3. Run full test suite
4. Verify performance gates pass
5. Update `PROGRESS.md` to Complete
6. Proceed to next version

---

## How New Versions Are Created

New versions are created only when:

1. The current version is complete
2. All validation passes
3. All capabilities in the version are delivered
4. The version's progress shows Complete
5. Performance gates for the version pass

The version creator must:

1. Create the version directory
2. Write `OVERVIEW.md` with objective, scope, and dependencies
3. Write `PROGRESS.md` with initial status
4. Write each phase file with full detail
5. Update `IMPLEMENTATION_STEPS.md` with new version
6. Verify no ADR contradictions exist

---

## How New Phases Are Created

New phases are created only when:

1. The previous phase in the same version is complete
2. All prerequisites are met
3. All dependencies are resolved

The phase creator must:

1. Follow the phase template exactly
2. Include all required sections
3. Reference correct architecture documents
4. Define clear completion criteria
5. Define clear readiness for next phase
6. Reference applicable ADRs

---

## How Future Roadmap Updates Occur

Updates to the roadmap happen through:

1. **Phase completion updates** — Update PROGRESS.md after each phase
2. **Version completion updates** — Update IMPLEMENTATION_STEPS.md after each version
3. **Scope adjustments** — Only through formal review, never silently
4. **New version creation** — Only after current version is complete
5. **ADR amendments** — Only through adversarial review

### What Cannot Change Silently

- Version order
- Phase order within a version
- Capability assignments to versions
- Architecture decisions (ADRs)
- Completion criteria
- Red Team findings resolution status

### What Can Change

- Phase task details (if approach changes)
- Timeline estimates (based on actual effort)
- Risk assessments (based on new information)
- Implementation approaches (if better way found)

---

## Templates

Templates are in `.agents/plans/templates/`:

| Template | Purpose |
|----------|---------|
| `version-overview.md` | Template for version OVERVIEW.md |
| `phase-plan.md` | Template for phase P01.md etc. |
| `progress.md` | Template for version PROGRESS.md |

---

## Authority

This planning system is the single source of truth for all Cortex implementation. No implementation should begin without a corresponding phase file. No phase should be executed without its prerequisites being complete.

The planning system evolves only through the process described above. It does not evolve through informal drift or untracked changes.

Architecture decisions, once implemented, are frozen and cannot be contradicted without formal amendment. Red Team findings, once integrated, are binding on all subsequent work.

This document supersedes all previous versions of GUIDE.md.
