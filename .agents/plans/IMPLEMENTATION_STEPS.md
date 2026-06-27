# IMPLEMENTATION_STEPS.md — CORTEX Master Roadmap

**Document:** Master Implementation Roadmap (Post-Red Team Enhancement)
**Authority:** Stage 6 — Master Versioned Implementation Roadmap + Stage 9 — Red Team Review
**Date:** 2026-06-27
**Version:** 2.0 (Enhanced with Red Team Findings)

---

## Purpose

This document is the navigation layer for the entire Cortex implementation roadmap. It explains where we are, where we're going, and how versions relate to each other. It integrates Red Team findings, architecture feature traceability, and enhanced implementation rules. It does not duplicate phase details — those live in the version directories.

---

## Current Repository State

The current repository contains:

- **Backend:** FastAPI + SQLAlchemy 2.0 + Alembic + PostgreSQL 16
- **Frontend:** Next.js 15 App Router + React 19 + TypeScript 5.8 + Tailwind 3.4
- **Code Intelligence:** Rust crate (cortexCode)
- **CLI:** TypeScript CLI tool
- **Agent System:** Single async generator loop, 15+ tools
- **Integrity System:** 10 engines, 40+ files, 95 tests
- **Developer Ecosystem:** 142 skills, 18 commands, 16 hooks
- **Storage:** PostgreSQL 16 + Redis 7 + Qdrant (embedded)
- **Embeddings:** ONNX Runtime BGE-M3 (768-dim)

### What Works

- Agent loop with tool execution
- Basic memory (conversations, documents, knowledge graph)
- Basic awareness (filesystem, repository, document indexing)
- Basic search (vector + fulltext + graph via RRF + MMR)
- Authentication (JWT + CSRF)
- Encryption (Fernet vault)
- Streaming (SSE)
- Desktop daemon
- Code intelligence (Rust crate)
- 142 skills, 18 commands, 16 hooks

### What's Missing

- 97 of 120 capabilities have zero implementation
- 28 capabilities are incomplete
- No event-driven architecture
- No domain-driven service organization
- No frontend feature modules
- No learning system
- No planning system
- No workflow orchestration
- No voice interaction
- No utility platform (calendar, email, tasks, notes)

---

## Target Vision

Cortex is a persistent machine intelligence layer — a brain for your personal computer. It remembers, understands, learns, and assists across every dimension of digital work. Local-first, privacy-by-architecture, compound intelligence over years.

**The 10 domains:**
1. Memory — The persistent brain
2. Awareness — The senses
3. Cognition — The thinking
4. Execution — The hands
5. Learning — The adaptation
6. Interaction — The voice
7. Developer — The craft
8. Utility — Daily life
9. Integration — The connections
10. Privacy & Security — The shield

**120 approved capabilities** across these domains, progressing through Foundation → Competent → Intelligent maturity levels.

---

## Red Team Integration

### What the Red Team Found

A 14-member independent review council (Stage 9 — Red Team Review) conducted a ruthless audit of the roadmap against the reference architecture integration plan. The verdict: **"The roadmap will NOT naturally evolve into the complete vision without major replanning."**

The 7 Red Team deliverables are:

| # | Document | Key Finding |
|---|----------|-------------|
| 1 | `artifacts/planning_review.md` | 14 critical findings. reference architecture integration plan absent from roadmap. Agent loop underspecified. Context management primitive. Tool system undersized. MCP integration missing. |
| 2 | `artifacts/final_recommendations.md` | Answer: NO — 3 must-do, 4 should-do, 3 nice-to-have changes required. |
| 3 | `artifacts/missing_features.md` | 22 reference architecture features not in roadmap. 7 critical, 12 important, 3 nice-to-have. 19 of 22 not adequately planned. |
| 4 | `artifacts/roadmap_refinements.md` | 9 specific refinements: v1.02 restructure, v1.01 additions, v1.13 split, integration tests, migration rollback, DoD strengthening, performance gates, dependency visualization, feature traceability. |
| 5 | `artifacts/implementation_order_improvements.md` | Verified dependency chain. Recommended Option A (minimal changes). v1.07→v1.06 dependency flagged as questionable. |
| 6 | `artifacts/future_risks.md` | 10 risks identified. Two RED: agent loop rewrite (80%/critical) and security vulnerabilities in agent loop (60%/critical). |
| 7 | `artifacts/planning_improvements.md` | 7 improvements with priorities. Top: restructure v1.02 with agent hardening. |

### How Red Team Findings Were Addressed

| Finding | Response | Version Affected |
|---------|----------|-----------------|
| 7 critical reference architecture features missing from agent foundation | **v1.02 restructured** from 5 to 8 phases. Added: Agent System Hardening (P03), MCP Integration (P04), Tool Infrastructure (P05), Observability Foundation (P07). | v1.02 |
| Frontend lacks feature-module architecture | **v1.01 expanded** with P07 (Frontend Feature Module Scaffolding) and P08 (Testing Infrastructure). | v1.01 |
| No testing infrastructure | **v1.01 expanded** with P08 (Testing Infrastructure): fixture factories, integration harnesses, CI pipeline, meta-tests. | v1.01 |
| No migration rollback strategy | **All P01 phases** now require migration rollback verification. | All versions |
| Definition of Done too generic | **Enhanced DoD** includes integration tests, security scan, performance comparison, reference architecture cross-reference. | All phases |
| No performance baselines | **v1.01 captures performance baseline**. v1.02+ includes performance gates. | v1.01+ |
| No architecture feature traceability | **reference architecture Feature Matrix** added to this document. | This document |

### What's Still Pending

| Item | Priority | Recommended Version | Status |
|------|----------|-------------------|--------|
| Domain-specific rules (G2) | Medium | v1.02 P02 (add to context providers) | Not planned |
| MemoryProvider Protocol (G3) | Low | v1.02 P02 (add alongside other Protocols) | Not planned |
| Teacher escalation (G1) | Low | v1.10 (add to session manager) | Not planned |
| UI control tool (G4) | Low | v1.14+ (defer until Tauri stable) | Not planned |
| Model serving cookbook (G5) | Low | v1.14+ or defer (documentation only) | Not planned |
| Docker GPU support (G6) | Low | v1.14+ Phase-3 | Not planned |
| Systemd service file (G7) | Low | v1.08 (alongside desktop work) | Not planned |
| Cross-version integration tests in v1.06 | Medium | v1.06 P06 (dedicated phase) | Not planned |

---

## ASCII Dependency Graph

```
                         v1.01 (Repository Restructure)
                                    │
                         v1.02 (Backend Architecture + Agent Hardening)
                          ┌────┬────┼────┬────┐
                          │    │    │    │    │
                       v1.03  v1.04  v1.05  v1.09
                       (Mem)  (Awr)  (Pri)  (Lrn)
                          │    │      │      │
                       v1.07  v1.08   │    v1.10
                       (MemE) (AwrE)  │    (Plan)
                          │    │      │      │
                          │    ├──v1.11──────┤
                          │    │ (Interact)  │
                          ├──v1.12──────────┤
                          │ (Developer)     │
                          │    │            │
                       v1.06  │         v1.14
                       (Cog)──┘    (Advanced Intel)
```

**Detailed dependency arrows:**

```
v1.01 ──> v1.02
v1.02 ──> v1.03 (Memory Foundation)
v1.02 ──> v1.04 (Awareness Foundation)
v1.02 ──> v1.05 (Privacy & Trust)
v1.02 ──> v1.09 (Learning Foundation)
v1.03 ──> v1.06 (Cognition Core)  [also needs v1.04]
v1.03 ──> v1.07 (Memory Evolution)
v1.04 ──> v1.06 (Cognition Core)  [also needs v1.03]
v1.04 ──> v1.08 (Awareness Expansion)
v1.06 ──> v1.09 (Learning Foundation)
v1.06 ──> v1.10 (Planning & Orchestration)  [also needs v1.09]
v1.06 ──> v1.11 (Interaction)  [also needs v1.08]
v1.06 ──> v1.12 (Developer Intelligence)  [also needs v1.03]
v1.08 ──> v1.11 (Interaction)  [also needs v1.06]
v1.08 ──> v1.13 (Utility & Integration)  [also needs v1.09]
v1.09 ──> v1.10 (Planning & Orchestration)  [also needs v1.06]
v1.09 ──> v1.13 (Utility & Integration)  [also needs v1.08]
v1.10 ──> v1.14 (Advanced Intelligence)  [also needs v1.11]
v1.11 ──> v1.14 (Advanced Intelligence)  [also needs v1.10]
```

**Critical Path (longest dependency chain):**

```
v1.01 → v1.02 → v1.03 → v1.06 → v1.09 → v1.10 → v1.14
```

**Critical Path Duration:** ~78 days (minimum, single-track)

This chain determines the minimum time to full intelligence. Delays in any version on this chain delay the entire project. The chain passes through: Repository Restructure → Backend Architecture → Memory Foundation → Cognition Core → Learning Foundation → Planning & Orchestration → Advanced Intelligence.

---

## Parallel Development Tracks

Multiple versions can be developed simultaneously after v1.02 completes:

```
TRACK A (Memory):     v1.03 ──────────────> v1.07
TRACK B (Awareness):  v1.04 ──────────────> v1.08
TRACK C (Privacy):    v1.05
TRACK D (Learning):   v1.09 (after v1.06)
TRACK E (Interaction):v1.11 (after v1.08, v1.06)
TRACK F (Developer):  v1.12 (after v1.06, v1.03)
TRACK G (Utility):    v1.13 (after v1.08, v1.09)
```

**Parallel opportunity matrix:**

| Track A | Track B | Track C | Condition |
|---------|---------|---------|-----------|
| v1.03 (Memory) | v1.04 (Awareness) | v1.05 (Privacy) | All three depend on v1.02 only |
| v1.07 (Memory Evo) | v1.08 (Awareness Exp) | — | Both depend on v1.03/v1.04 respectively |
| v1.11 (Interaction) | v1.12 (Developer) | v1.13 (Utility) | All depend on v1.06/v1.08 + earlier |

**Maximum parallelism:** After v1.02 completes, up to 3 teams can work simultaneously on Tracks A, B, and C. After v1.06 completes, up to 4 teams can work on Tracks D, E, F, G.

---

## Version Sequence

### Overview

| Version | Name | Type | Phases | Capabilities | Estimated Duration |
|---------|------|------|--------|-------------|-------------------|
| v1.0 | Current State | Snapshot | 0 | 0 | — |
| v1.01 | Repository Restructure | Structural | 8 | 0 | 12-20 days |
| v1.02 | Backend Architecture + Agent Hardening | Architectural | 8 | 8 | 25-35 days |
| v1.03 | Memory Foundation | Capability | 5 | 7 | 5-7 days |
| v1.04 | Awareness Foundation | Capability | 4 | 6 | 4-5 days |
| v1.05 | Privacy & Trust | Capability | 4 | 9 | 4-5 days |
| v1.06 | Cognition & Execution Core | Capability | 5 | 8 | 6-7 days |
| v1.07 | Memory Evolution | Capability | 4 | 6 | 5-6 days |
| v1.08 | Awareness Expansion | Capability | 5 | 10 | 6-7 days |
| v1.09 | Learning Foundation | Capability | 5 | 10 | 7-8 days |
| v1.10 | Planning & Orchestration | Capability | 5 | 13 | 7-8 days |
| v1.11 | Interaction & Communication | Capability | 5 | 12 | 7-8 days |
| v1.12 | Developer Intelligence | Capability | 6 | 15 | 8-9 days |
| v1.13 | Utility & Integration | Capability | 6 | 19 | 10-12 days |
| v1.14 | Advanced Intelligence | Capability | 4 | 4 | 5-6 days |
| **Total** | | | **76** | **120** | **~104-135 days** |

### Phase Counts by Version

| Version | Phases | IDs |
|---------|--------|-----|
| v1.01 | 8 | P01-P08 |
| v1.02 | 8 | P01-P08 |
| v1.03 | 5 | P01-P05 |
| v1.04 | 4 | P01-P04 |
| v1.05 | 4 | P01-P04 |
| v1.06 | 5 | P01-P05 |
| v1.07 | 4 | P01-P04 |
| v1.08 | 5 | P01-P05 |
| v1.09 | 5 | P01-P05 |
| v1.10 | 5 | P01-P05 |
| v1.11 | 5 | P01-P05 |
| v1.12 | 6 | P01-P06 |
| v1.13 | 6 | P01-P06 |
| v1.14 | 4 | P01-P04 |

---

### Version Details

#### v1.0: Current State
**Question:** Where are we today?
**Type:** Historical snapshot (non-executable)
**What it documents:** Current repository, architecture, features, debt
**Location:** `.agents/plans/versions/v1.0/`

#### v1.01: Repository Restructure
**Question:** Can we navigate the codebase?
**Type:** Structural migration (no capability changes)
**What it does:** Domain-driven reorganization of backend services, frontend components, documentation, planning. Includes frontend feature module scaffolding and testing infrastructure (Red Team additions).
**Capabilities:** 0 (pure structure)
**Phases:** 8 — P01 Backend Services, P02 Backend Models, P03 Import Migration, P04 Frontend Modules, P05 Documentation, P06 Planning, P07 Frontend Feature Module Scaffolding*, P08 Testing Infrastructure*
**Duration:** 12-20 days
**Location:** `.agents/plans/versions/v1.01/`
**Red Team additions:** P07 (Frontend Feature Module Scaffolding), P08 (Testing Infrastructure — fixture factories, integration harnesses, CI pipeline, meta-tests)

#### v1.02: Backend Architecture + Agent Hardening
**Question:** Does the architecture support domain evolution AND is the agent system production-ready?
**Type:** Architectural improvement (expanded per Red Team)
**What it does:** API domain reorganization, event system, core infrastructure, import migration. **Plus:** Agent system hardening from proven patterns from reference implementations (streaming loop, compaction, tool schemas, intent classification, stall detection, completion verification, detached runs, MCP integration, tool infrastructure, observability).
**Capabilities:** 0 (architecture only)
**Phases:** 8 — P01 API Domain Reorganization, P02 Service Boundaries + Event Bus, P03 Agent System Hardening*, P04 MCP Integration*, P05 Tool Infrastructure*, P06 Database Schema Updates, P07 Observability Foundation*, P08 Integration & Testing
**Duration:** 25-35 days
**Location:** `.agents/plans/versions/v1.02/`
**Red Team additions:** P03 (Agent System Hardening), P04 (MCP Integration), P05 (Tool Infrastructure), P07 (Observability Foundation). This is the single most important change from the Red Team review — without these, every subsequent capability is built on a weak foundation.

#### v1.03: Memory Foundation
**Question:** Can Cortex remember?
**Type:** Capability delivery
**What it does:** Episodic memory, semantic memory, working memory, memory graph, memory search, forgetting, temporal memory
**Capabilities:** M1, M2, M4, M6, M7, M10, M12 (7)
**Phases:** 5
**Duration:** 5-7 days
**Location:** `.agents/plans/versions/v1.03/`

#### v1.04: Awareness Foundation
**Question:** Can Cortex perceive its environment?
**Type:** Capability delivery
**What it does:** Filesystem, repository, project, device, environment, system health awareness
**Capabilities:** A1, A2, A3, A9, A14, A15 (6)
**Phases:** 4
**Duration:** 4-5 days
**Location:** `.agents/plans/versions/v1.04/`

#### v1.05: Privacy & Trust
**Question:** Can Cortex be trusted?
**Type:** Capability delivery
**What it does:** Local processing, encryption, access control, audit, sovereignty, transparency, consent, data export
**Capabilities:** P1, P2, P3, P4, P5, P6, P7, P8, X5 (9)
**Phases:** 4
**Duration:** 4-5 days
**Location:** `.agents/plans/versions/v1.05/`

#### v1.06: Cognition & Execution Core
**Question:** Can Cortex think and act?
**Type:** Capability delivery
**What it does:** Reasoning, confidence estimation, problem solving, error analysis, automation, permissions, recovery, execution history
**Capabilities:** C4, C6, C9, C10, E2, E5, E6, E10 (8)
**Phases:** 5
**Duration:** 6-7 days
**Location:** `.agents/plans/versions/v1.06/`

#### v1.07: Memory Evolution
**Question:** Does memory deepen understanding?
**Type:** Capability delivery
**What it does:** Procedural memory, consolidation, knowledge evolution, context retrieval, confidence-weighted memory, cross-domain memory
**Capabilities:** M3, M5, M8, M9, M11, M13 (6)
**Phases:** 4
**Duration:** 5-6 days
**Location:** `.agents/plans/versions/v1.07/`

#### v1.08: Awareness Expansion
**Question:** Does awareness extend beyond files?
**Type:** Capability delivery
**What it does:** Desktop, terminal, browser, clipboard, running applications, notification, calendar, email, workspace, temporal awareness
**Capabilities:** A4, A5, A6, A7, A8, A10, A11, A12, A13, A16 (10)
**Phases:** 5
**Duration:** 6-7 days
**Location:** `.agents/plans/versions/v1.08/`

#### v1.09: Learning Foundation
**Question:** Can Cortex adapt?
**Type:** Capability delivery
**What it does:** Preference, workflow, habit learning. Feedback, behavior adaptation, personalization, knowledge refinement, improvement, pattern recognition, anomaly detection
**Capabilities:** L1, L2, L3, L4, L5, L6, L7, L8, L9, L10 (10)
**Phases:** 5
**Duration:** 7-8 days
**Location:** `.agents/plans/versions/v1.09/`

#### v1.10: Planning & Orchestration
**Question:** Can Cortex plan and orchestrate?
**Type:** Capability delivery
**What it does:** Planning, task decomposition, reflection, hypothesis, decision support, goal management, workflow orchestration, scheduling, parallel execution, background tasks, verification, rollback, batch operations
**Capabilities:** C1, C2, C3, C5, C7, C8, E3, E4, E7, E8, E9, E11, E12 (13)
**Phases:** 5
**Duration:** 7-8 days
**Location:** `.agents/plans/versions/v1.10/`

#### v1.11: Interaction & Communication
**Question:** Can Cortex communicate naturally?
**Type:** Capability delivery
**What it does:** Voice, command palette, GUI, CLI, API, GUI redesign, interaction refinement, proactive assistance, contextual suggestions, multi-modal, ambient intelligence, summarization
**Capabilities:** I1, I2, I3, I4, I5, I6, I7, I8, I9, I10, I11, I12 (12)
**Phases:** 5
**Duration:** 7-8 days
**Location:** `.agents/plans/versions/v1.11/`

#### v1.12: Developer Intelligence
**Question:** Does Cortex understand code deeply?
**Type:** Capability delivery
**What it does:** Code understanding, repository intelligence, code review, test generation, documentation generation, refactoring, debugging, performance analysis, architecture guidance, dependency analysis, security analysis, migration assistance, code generation, CI/CD understanding, git intelligence
**Capabilities:** D1, D2, D3, D4, D5, D6, D7, D8, D9, D10, D11, D12, D13, D14, D15 (15)
**Phases:** 6
**Duration:** 8-9 days
**Location:** `.agents/plans/versions/v1.12/`

#### v1.13: Utility & Integration
**Question:** Is Cortex a complete life assistant?
**Type:** Capability delivery
**What it does:** Calendar, email, task management, notes, contacts, workspace management, dashboard, daily briefing, weekly review, habit tracking, focus management, tool integration, service integration, protocol support, extension system, cross-device sync, differential privacy, secure enclaves
**Capabilities:** U1-U12, X1, X2, X3, X4, X6, P9, P10 (19)
**Phases:** 6
**Duration:** 10-12 days
**Location:** `.agents/plans/versions/v1.13/`
**Note:** This version carries 19 capabilities — the highest of any version. The Red Team recommended splitting it. If quality degrades, split into v1.13a (Calendar/Tasks/Notes, 8 capabilities) and v1.13b (Contacts/Extensions/Sync/Dashboard, 11 capabilities).

#### v1.14: Advanced Intelligence
**Question:** Is Cortex truly intelligent?
**Type:** Capability delivery
**What it does:** Strategy generation, self-evaluation, analogy recognition, causal reasoning
**Capabilities:** C11, C12, C13, C14 (4)
**Phases:** 4
**Duration:** 5-6 days
**Location:** `.agents/plans/versions/v1.14/`

---

## reference architecture Feature Traceability Matrix

This matrix maps every reference architecture feature to its implementing version and phase. It ensures no critical feature is missed. Source: `artifacts/missing_features.md` + `FinalCompatibilities.md`.

| reference architecture Feature | Architecture Section | Implementing Version | Phase | Status |
|-----------------|-----------------|---------------------|-------|--------|
| Streaming Agent Loop | 3.Critical.1 | v1.02 | P03 (Agent System Hardening) | Planned |
| Context Compaction (85% threshold) | 3.Critical.2 | v1.02 | P03 (Agent System Hardening) | Planned |
| Tool Schemas (OpenAI-compatible JSON Schema) | 3.Critical.3 | v1.02 | P05 (Tool Infrastructure) | Planned |
| RAG-based Tool Selection | 3.Critical.4 | v1.02 | P05 (Tool Infrastructure) | Planned |
| Prompt Security (UNTRUSTED_SOURCE_DATA) | 3.Critical.5 | v1.02 | P03 (Agent System Hardening) | Planned |
| MCP Integration (stdio + SSE) | 3.Critical.6 | v1.02 | P04 (MCP Integration) | Planned |
| Detached Agent Runs | 3.Critical.7 | v1.02 | P03 (Agent System Hardening) | Planned |
| Tool Registration & Discovery | 4.Service.1 | v1.02 | P05 (Tool Infrastructure) | Planned |
| Intent Classification (casual/admin/agent/continuation) | 4.Pattern.12 | v1.02 | P03 (Agent System Hardening) | Planned |
| Per-turn Tool Policy Composition | 4.Pattern.11 | v1.02 | P03 (Agent System Hardening) | Planned |
| Completion Verification (fresh-context subagent) | 5.Observability.2 | v1.02 | P03 (Agent System Hardening) | Planned |
| Stall Detection (loop-breaker) | 5.Observability.3 | v1.02 | P03 (Agent System Hardening) | Planned |
| Observability Metrics (TPS, tokens, context %) | 5.Observability.1 | v1.02 | P07 (Observability Foundation) | Planned |
| Session Search (conversation embedding) | 6.Features.1 | v1.03 | P04 or P05 | Planned |
| Skills Runtime System | 7.1.Tier3.1 | v1.12 | TBD | Not Planned |
| Webhook System (CRUD + HMAC) | 4.5.Daily.1 | v1.13 | TBD | Not Planned |
| Agent-to-Agent Sessions | 4.5.Daily.2 | v1.10 | TBD | Not Planned |
| Housekeeping Tasks (7 built-in) | 7.1.Tier3.2 | v1.10 | TBD | Not Planned |
| Contacts System (CardDAV) | 4.5.Daily.3 | v1.13 | TBD | Not Planned |
| Deep Research Engine | 4.5.Daily.4 | v1.14 | TBD | Not Planned |

### Traceability Summary

| Category | Count | Planned | Not Planned |
|----------|-------|---------|-------------|
| Critical (Section 3) | 7 | 7 | 0 |
| Service/Pattern (Section 4) | 2 | 2 | 0 |
| Observability (Section 5) | 3 | 3 | 0 |
| Features (Section 6) | 1 | 1 | 0 |
| Daily Tools (Section 4.5) | 3 | 0 | 3 |
| Tier 3 (Section 7.1) | 2 | 0 | 2 |
| **Total** | **18** | **13** | **5** |

**All 7 critical reference architecture features are planned in v1.02.** The 5 unimplemented features are lower-priority items assigned to later versions without dedicated phase plans.

---

## Enhanced Version Dependency Table

| Version | Inputs (Depends On) | Outputs (Provides To) | Critical Path? |
|---------|---------------------|----------------------|----------------|
| v1.01 | None | v1.02 (restructured codebase) | YES — all versions depend on this chain |
| v1.02 | v1.01 | v1.03, v1.04, v1.05, v1.09 (architecture + hardened agent) | YES |
| v1.03 | v1.02 | v1.06, v1.07 (episodic + semantic + working memory, memory graph) | YES — via v1.06 |
| v1.04 | v1.02 | v1.06, v1.08 (filesystem, repo, project, device awareness) | No — parallel track |
| v1.05 | v1.02 | v1.11 (encryption, RBAC, audit, sovereignty) | No — parallel track |
| v1.06 | v1.03 + v1.04 | v1.09, v1.10, v1.11, v1.12, v1.14 (reasoning, confidence, problem solving) | YES |
| v1.07 | v1.03 | v1.14 (consolidation, evolution, cross-domain memory) | No — parallel track |
| v1.08 | v1.04 | v1.11, v1.13 (desktop, terminal, browser, calendar, email awareness) | No — parallel track |
| v1.09 | v1.02 + v1.06 | v1.10, v1.13 (preference, workflow, habit learning) | YES — via v1.10 |
| v1.10 | v1.09 + v1.06 | v1.14 (planning, decomposition, scheduling, orchestration) | YES |
| v1.11 | v1.06 + v1.08 | v1.14 (voice, command palette, proactive, multi-modal) | No — parallel track |
| v1.12 | v1.06 + v1.03 | None (terminal — no downstream versions) | No — parallel track |
| v1.13 | v1.08 + v1.09 | None (terminal — no downstream versions) | No — parallel track |
| v1.14 | v1.10 + v1.11 | None (final version) | YES — final milestone |

### Critical Path Analysis

The longest dependency chain determines minimum time to full intelligence:

```
v1.01 → v1.02 → v1.03 → v1.06 → v1.09 → v1.10 → v1.14
  15d    30d     6d      6.5d    7.5d     7.5d     5.5d
                                        Total: ~78 days
```

**Why this is the critical path:**
1. v1.03 (Memory Foundation) feeds into v1.06 (Cognition) — you can't think without memory
2. v1.06 (Cognition) feeds into v1.09 (Learning) — you can't learn without cognition
3. v1.09 (Learning) feeds into v1.10 (Planning) — you can't plan without learning
4. v1.10 (Planning) feeds into v1.14 (Advanced Intelligence) — you can't strategize without planning

**Non-critical parallel tracks that can accelerate delivery:**
- Track B (v1.04 → v1.08): Awareness runs in parallel with Track A
- Track C (v1.05): Privacy runs in parallel with Tracks A and B
- Tracks E/F/G (v1.11, v1.12, v1.13): Run in parallel after v1.06 completes

---

## reference architecture Feature Mapping by Version

### v1.02 — Agent Intelligence Foundation (15 features)

The restructured v1.02 absorbs all 7 critical and 8 important reference architecture features that were previously missing:

| Feature | Source | Phase | Effort |
|---------|--------|-------|--------|
| Streaming agent loop (3,485-line equivalent) | reference architecture 3.Critical.1 | P03 | High (3-5 days) |
| Context compaction (auto at 85%) | reference architecture 3.Critical.2 | P03 | High (2-3 days) |
| Prompt security (UNTRUSTED_SOURCE_DATA) | reference architecture 3.Critical.5 | P03 | Low (1 day) |
| Intent classification (4-way routing) | reference architecture 4.Pattern.12 | P03 | Low (1 day) |
| Per-turn tool policy | reference architecture 4.Pattern.11 | P03 | Medium (1-2 days) |
| Completion verification subagent | reference architecture 5.Observability.2 | P03 | Medium (1-2 days) |
| Stall detection (loop-breaker) | reference architecture 5.Observability.3 | P03 | Low (1 day) |
| Detached agent runs with persistence | reference architecture 3.Critical.7 | P03 | Medium (2-3 days) |
| MCP client (stdio + SSE) | reference architecture 3.Critical.6 | P04 | High (3-4 days) |
| Tool wrapping for MCP tools | reference architecture 3.Critical.6 | P04 | Medium (1-2 days) |
| Tool schemas (OpenAI-compatible JSON Schema) | reference architecture 3.Critical.3 | P05 | Medium (1-2 days) |
| RAG-based tool selection (for 15+ tools) | reference architecture 3.Critical.4 | P05 | Medium (2-3 days) |
| Tool registration & discovery | reference architecture 4.Service.1 | P05 | Medium (1-2 days) |
| Observability metrics (TPS, tokens, context %) | reference architecture 5.Observability.1 | P07 | Medium (2 days) |
| tiktoken integration (accurate counting) | reference architecture 3.Critical | P03 | Low (0.5 days) |

### v1.03 — Memory + Session Search (7+1 features)

| Feature | Source | Capabilities |
|---------|--------|-------------|
| Episodic memory | Memory Foundation | M1 |
| Semantic memory | Memory Foundation | M2 |
| Working memory | Memory Foundation | M4 |
| Memory graph | Memory Foundation | M6 |
| Forgetting mechanism | Memory Foundation | M7 |
| Memory search | Memory Foundation | M10 |
| Temporal memory | Memory Foundation | M12 |
| Session search (conversation embedding) | reference architecture 6.Features.1 | Integrated into P04/P05 |

### v1.09-v1.14 — Remaining reference architecture Features

| Feature | reference architecture Source | Version |
|---------|----------------|---------|
| Housekeeping tasks (7 built-in) | 7.1.Tier3.2 | v1.10 |
| Agent-to-agent sessions | 4.5.Daily.2 | v1.10 |
| Skills runtime system | 7.1.Tier3.1 | v1.12 |
| Webhook system (CRUD + HMAC) | 4.5.Daily.1 | v1.13 |
| Contacts system (CardDAV) | 4.5.Daily.3 | v1.13 |
| Deep research engine | 4.5.Daily.4 | v1.14 |

---

## High-Level Implementation Order

### Stage 1: Foundation (v1.01 + v1.02)
Build the structure and architecture that everything else depends on. The Red Team expanded v1.01 to 8 phases and v1.02 to 8 phases — this is the longest and most critical stage.

**v1.01 (12-20 days):** Repository restructure + frontend scaffolding + testing infrastructure
**v1.02 (25-35 days):** Backend architecture + agent hardening + MCP + tool infrastructure + observability

### Stage 2: Core Memory + Awareness + Privacy (v1.03 + v1.04 + v1.05)
Build the three foundation domains in parallel. All three depend only on v1.02.

**v1.03 (5-7 days):** Episodic, semantic, working memory. Memory graph. Search. Forgetting. Session search.
**v1.04 (4-5 days):** Filesystem, repository, project, device, environment, system health awareness.
**v1.05 (4-5 days):** Local processing, encryption, RBAC, audit, sovereignty, transparency, consent, export.

### Stage 3: Cognition + Memory Evolution + Awareness Expansion (v1.06 + v1.07 + v1.08)
Build thinking, deepen memory, extend awareness. v1.06 requires both v1.03 and v1.04. v1.07 and v1.08 can run in parallel.

**v1.06 (6-7 days):** Reasoning, confidence estimation, problem solving, error analysis, automation, recovery.
**v1.07 (5-6 days):** Procedural memory, consolidation, knowledge evolution, cross-domain memory.
**v1.08 (6-7 days):** Desktop, terminal, browser, clipboard, calendar, email, workspace, notification awareness.

### Stage 4: Learning (v1.09)
Build adaptation and personalization. Depends on v1.06 (cognition).

**v1.09 (7-8 days):** Preference, workflow, habit learning. Behavior adaptation. Pattern recognition. Anomaly detection.

### Stage 5: Planning + Orchestration (v1.10)
Build task decomposition, scheduling, and autonomous operation. Depends on v1.09 (learning) + v1.06 (cognition).

**v1.10 (7-8 days):** Planning, decomposition, decision support, goal management, scheduling, parallel execution, rollback.

### Stage 6: Communication + Developer + Utility (v1.11 + v1.12 + v1.13)
Build the interaction layer, developer platform, and utility platform. All three can run in parallel.

**v1.11 (7-8 days):** Voice, command palette, proactive assistance, multi-modal, ambient intelligence.
**v1.12 (8-9 days):** Code understanding, review, generation, debugging, architecture guidance, security analysis.
**v1.13 (10-12 days):** Calendar, email, tasks, notes, contacts, dashboard, extensions, sync.

### Stage 7: Advanced Intelligence (v1.14)
Build the final intelligence capabilities. Depends on v1.10 (planning) + v1.11 (interaction).

**v1.14 (5-6 days):** Strategy generation, self-evaluation, analogy recognition, causal reasoning.

---

## Major Milestones

| After Version | Milestone | User Experience | Cumulative Capabilities |
|--------------|-----------|-----------------|------------------------|
| v1.01 | Navigable codebase | Contributors can find anything | 0 |
| v1.02 | Production-ready agent + architecture | Agent streams, compacts, uses tools with schemas, connects via MCP | 0 |
| v1.03 | Cortex remembers | Persistent episodic + semantic memory | 7 |
| v1.04 | Cortex perceives | Knows files, repos, projects, hardware | 13 |
| v1.05 | Cortex is trusted | Local-first, encrypted, auditable | 22 |
| v1.06 | Cortex thinks | Reasoning, confidence, problem solving | 30 |
| v1.07 | Memory deepens | Consolidation, evolution, cross-domain | 36 |
| v1.08 | Awareness extends | Desktop, terminal, calendar, email | 46 |
| v1.09 | Cortex adapts | Learns preferences, workflows, habits | 56 |
| v1.10 | Cortex plans | Task decomposition, scheduling, orchestration | 69 |
| v1.11 | Cortex communicates | Voice, proactive, multi-modal | 81 |
| v1.12 | Cortex codes | Deep code understanding, review, generation | 96 |
| v1.13 | Cortex manages life | Calendar, email, tasks, dashboard | 115 |
| v1.14 | Cortex is intelligent | Strategy, self-evaluation, analogy, causation | 120 |

---

## Implementation Rules

These rules apply to ALL versions and phases. They incorporate Red Team recommendations.

### 1. Read Before Write

Before starting ANY phase:

1. Read the active version's `OVERVIEW.md` for scope
2. Read the current `PROGRESS.md` for status
3. Read prerequisite versions' `PROGRESS.md` for dependency verification
4. Read the specific phase file for implementation details
5. Read this document for cross-version context
6. Read `.agents/plans/GUIDE.md` for architecture constraints

### 2. TDD When Applicable

Write failing test → implement → verify pass → commit. Every new subsystem follows this cycle. 341 existing tests are the safety net. Never reduce the test count.

### 3. Commit After Each Logical Unit

Small, focused commits. Each commit is self-contained and testable. `make lint` + `make format` after each commit. Standard one-line git messages in conventional format. No co-authored-by tags.

### 4. Follow Architecture

File placement rules from CLAUDE.md apply always. Ownership checks on ALL user-scoped endpoints. API conventions: specific routes before parameterized, `response_model=` on all decorators.

### 5. Migration Rollback Requirement (Red Team)

**Every P01 phase** that creates or modifies database migrations MUST include:

```yaml
Rollback Verification:
  - [ ] Migration applies cleanly to fresh database
  - [ ] Migration rolls back cleanly with `alembic downgrade -1`
  - [ ] No data loss on rollback (verified by test)
  - [ ] Full test suite passes after rollback
  - [ ] Rollback command documented in phase file
```

### 6. Strengthened Definition of Done (Red Team)

Every phase completion requires ALL of the following:

```yaml
Definition of Done:
  - [ ] All implementation tasks complete
  - [ ] Unit tests passing (pytest / vitest)
  - [ ] Integration tests passing
  - [ ] No lint errors (ruff / eslint)
  - [ ] No type errors (mypy / tsc)
  - [ ] Migration applies and rolls back cleanly (if applicable)
  - [ ] Documentation updated (if applicable)
  - [ ] Performance within 10% of baseline (v1.02+)
  - [ ] Security scan clean — no new vulnerabilities (v1.02+)
  - [ ] Cross-reference with reference architecture features complete (v1.02+)
  - [ ] Progress updated in `PROGRESS.md`
  - [ ] Committed with clear message
```

### 7. Performance Gates (Red Team)

Starting from v1.02, every phase must meet these performance criteria:

| Metric | Gate | Applies To |
|--------|------|-----------|
| API response time (p95) | < 200ms for CRUD | v1.02+ |
| Embedding speed | >= 100 chunks/second | v1.03+ |
| Agent first-token latency | < 500ms | v1.02+ |
| Backend memory usage | < 512MB | v1.02+ |
| Test suite runtime | < 5 minutes | v1.01+ |
| Context compaction time | < 2 seconds | v1.02+ |
| MCP tool discovery | < 1 second | v1.02+ |

### 8. Cross-Version Integration Test Requirement (Red Team)

Starting from v1.06 (first version with multiple domains interacting):

- Every version's final phase MUST include at least 3 cross-domain integration tests
- v1.06 specifically needs a dedicated integration phase: Memory + Cognition, Awareness + Cognition, end-to-end agent flows
- Regression test suite must expand with each version
- Performance comparison against baseline in every final phase

### 9. reference architecture Feature Verification Requirement (Red Team)

For every version that implements reference architecture features:

- Cross-reference completed features against this document's reference architecture Feature Traceability Matrix
- Mark completed features as ✅ in `PROGRESS.md`
- Verify no reference architecture feature was missed during implementation
- Report any newly discovered gaps to this document

### 10. Branching Is Mandatory

Feature branch before any significant change. Never commit directly to `main`. Branch naming: `feat/<topic>`, `fix/<topic>`, `docs/<topic>`. Merge after verification.

### 11. One Phase at a Time

Phases are capability milestones, not calendar commitments. Each phase is complete when all deliverables are achieved. No rushing to the next phase.

### 12. Scope Is Guarded

Each subsystem gets its own spec → plan → implement cycle. Never implement more than 2 new subsystems simultaneously. Daily productivity tools are sequenced: foundation first, full tools later.

---

## Version Summary with Red Team Impact

| Version | Name | Original Duration | Revised Duration | Delta | Reason for Change |
|---------|------|-------------------|-----------------|-------|-------------------|
| v1.01 | Repository Restructure | 11-18 days | 12-20 days | +1-2d | Added P07 (Frontend Modules) + P08 (Testing Infrastructure) |
| v1.02 | Backend Architecture | 17-25 days | 25-35 days | +8-10d | Added P03 (Agent Hardening) + P04 (MCP) + P05 (Tools) + P07 (Observability) |
| v1.03 | Memory Foundation | 5-7 days | 5-7 days | — | No change |
| v1.04 | Awareness Foundation | 4-5 days | 4-5 days | — | No change |
| v1.05 | Privacy & Trust | 4-5 days | 4-5 days | — | No change |
| v1.06 | Cognition Core | 6-7 days | 6-7 days | — | No change |
| v1.07 | Memory Evolution | 5-6 days | 5-6 days | — | No change |
| v1.08 | Awareness Expansion | 6-7 days | 6-7 days | — | No change |
| v1.09 | Learning Foundation | 7-8 days | 7-8 days | — | No change |
| v1.10 | Planning & Orchestration | 7-8 days | 7-8 days | — | No change |
| v1.11 | Interaction | 7-8 days | 7-8 days | — | No change |
| v1.12 | Developer Intelligence | 8-9 days | 8-9 days | — | No change |
| v1.13 | Utility & Integration | 10-12 days | 10-12 days | — | No change (split recommended if quality degrades) |
| v1.14 | Advanced Intelligence | 5-6 days | 5-6 days | — | No change |
| **Total** | | **~90-102 days** | **~104-135 days** | **+14-33d** | Front-loaded investment in v1.01/v1.02 |

**Key insight:** The Red Team's changes are front-loaded. v1.01 and v1.02 absorb the additional work (~10-12 days extra). This investment pays off by ensuring every subsequent version builds on a solid foundation. The critical path grows from ~78 days to ~88 days, but the risk of agent system failure drops dramatically.

---

## How to Use This Document

1. **Find where you are:** Check `PROGRESS.md` in the current version directory
2. **Find what's next:** Look at the version sequence above
3. **Find dependencies:** Check the Enhanced Version Dependency Table
4. **Find details:** Read the specific version's `OVERVIEW.md` and phase files
5. **Find reference architecture coverage:** Check the reference architecture Feature Traceability Matrix
6. **Find context:** Read this document for big picture
7. **Check Red Team status:** Review "What's Still Pending" section

---

## Reference Documents

| Document | Location | Purpose |
|----------|----------|---------|
| Planning Guide | `.agents/plans/GUIDE.md` | How the planning system works |
| Architecture Constitution | `.agents/plans/GUIDE.md` | 10 principles, what to keep/reject |
| Architecture Decisions | `.agents/plans/artifacts/architecture_decision_summary.md` | Binding decisions |
| Capability Model | `.agents/plans/artifacts/capability_model.md` | 120 capabilities |
| Capability Dependencies | `.agents/plans/artifacts/capability_dependencies.md` | Implementation order |
| Implementation Priority | `.agents/plans/artifacts/implementation_priority.md` | Priority tiers |
| Repository Architecture | `.agents/plans/artifacts/repository_architecture.md` | Target architecture |
| Migration Map | `.agents/plans/artifacts/migration_map.md` | Current→Target mapping |
| Migration Strategy | `.agents/plans/artifacts/migration_strategy.md` | Migration phases |
| Final Product Specification | `.agents/plans/artifacts/final_product_specification.md` | What Cortex is |
| reference architecture Cross-Reference | `.agents/plans/FinalCompatibilities.md` | reference architecture→Cortex version mapping (62 items) |
| **Red Team Deliverables** | | |
| Planning Review | `.agents/plans/artifacts/planning_review.md` | 14 critical findings |
| Final Recommendations | `.agents/plans/artifacts/final_recommendations.md` | Must-do/should-do changes |
| Missing Features | `.agents/plans/artifacts/missing_features.md` | 22 reference architecture gaps identified |
| Roadmap Refinements | `.agents/plans/artifacts/planning_review.md` (merged) | 9 specific refinements |
| Implementation Order | `.agents/plans/artifacts/planning_review.md` (merged) | Dependency chain verification |
| Future Risks | `.agents/plans/artifacts/future_risks.md` | 10 risks with heat map |
| Planning Improvements | `.agents/plans/artifacts/planning_review.md` (merged) | 7 improvement priorities |

---

## Red Team Implementation Order Analysis

Source: `artifacts/implementation_order_improvements.md` (archived after merge)

### Current Order Issues

**Issue 1: Agent Loop Should Be Built Before Memory**
Current v1.03 (Memory) before v1.06 (Cognition/Execution). Memory systems are designed without knowing how the agent loop will use them. **Verdict:** CORRECT after v1.02 restructuring. The dependency chain v1.02 → v1.03 is correct.

**Issue 2: Privacy Before Agent Loop**
v1.05 (Privacy) after v1.03 (Memory) but before v1.06 (Cognition). Privacy architecture should wrap the agent loop from the start. **Verdict:** Partially correct. Prompt security in v1.02, full privacy in v1.05.

**Issue 3: Learning Before Planning**
v1.09 (Learning) before v1.10 (Planning). **Verdict:** CORRECT. Keep as-is. Learning provides preference/pattern data that planning uses. The dependency is one-directional: Learning → Planning.

**Issue 4: Developer Intelligence Too Late**
v1.12 (Developer Intelligence) near the end. Would be helpful during v1.03-v1.11 implementation. **Verdict:** WORTH CONSIDERING but not critical. The team can use existing tools during development.

**Issue 5: Utility Platform at the End**
v1.13 (Utility) near the end. Calendar, tasks, notes are high-value user features. **Verdict:** PARTIALLY CORRECT. Consider moving basic utility (tasks, notes) earlier.

### Revised Implementation Order

#### Option A: Minimal Changes (Recommended)

```
v1.01  Repository Restructure     (12-20 days)
v1.02  Backend Architecture       (25-35 days) -- EXPANDED with reference architecture features
v1.03  Memory Foundation          (11-18 days) -- unchanged
v1.04  Awareness Foundation       (10-16 days) -- unchanged
v1.05  Privacy and Trust          (10-16 days) -- unchanged
v1.06  Cognition Core             (13-20 days) -- unchanged
v1.07  Memory Evolution           (10-16 days) -- unchanged
v1.08  Awareness Expansion        (14-22 days) -- unchanged
v1.09  Learning Foundation        (13-20 days) -- unchanged
v1.10  Planning and Orchestration (16-24 days) -- unchanged
v1.11  Interaction                (14-22 days) -- unchanged
v1.12  Developer Intelligence     (16-24 days) -- unchanged
v1.13  Utility and Integration    (20-30 days) -- SLIMMED from 19 to 12 capabilities
v1.14  Advanced Intelligence      (10-16 days) -- unchanged
```

**Total:** 184-295 days (was 172-278)

#### Option B: Aggressive Restructuring

Move utility earlier, split large versions:

```
v1.01  Repository Restructure     (12-20 days)
v1.02  Backend Architecture       (25-35 days)
v1.03  Memory Foundation          (11-18 days)
v1.04  Awareness Foundation       (10-16 days)
v1.05  Privacy and Trust          (10-16 days)
v1.06  Cognition Core             (13-20 days)
v1.07  Memory Evolution           (10-16 days)
v1.08  Awareness + Basic Utility  (18-28 days) -- merge Calendar/Tasks from v1.13
v1.09  Learning Foundation        (13-20 days)
v1.10  Planning and Orchestration (16-24 days)
v1.11  Interaction                (14-22 days)
v1.12  Developer Intelligence     (16-24 days)
v1.13  Integration Platform       (14-22 days) -- slimmed to Integration only
v1.14  Advanced Intelligence      (10-16 days)
```

**Total:** 192-305 days. More balanced load per version.

**Recommendation:** Option A is safer. The current order is mostly correct. The main issue is v1.02 underspecification, not ordering.

### Dependency Chain Verification

#### Critical Path (must be sequential)

```
v1.01 -> v1.02 -> v1.03 -> v1.07 -> v1.06 -> v1.09 -> v1.10 -> v1.14
```

- v1.01 (restructure) must come first — correct
- v1.02 (architecture) must come before capabilities — correct
- v1.03 (memory) must come before v1.07 (memory evolution) — correct
- v1.07 (memory evolution) before v1.06 (cognition) — DEBATABLE. Basic memory should suffice for cognition.
- v1.06 (cognition) before v1.09 (learning) — correct. Learning needs cognition to evaluate.
- v1.09 (learning) before v1.10 (planning) — correct. Planning benefits from learned patterns.
- v1.10 (planning) before v1.14 (advanced) — correct.

**Issue:** v1.07 → v1.06 dependency is questionable. Consider swapping or making them parallel.

#### Parallel Tracks (can run concurrently)

```
Track A: v1.03 -> v1.07 (Memory)
Track B: v1.04 -> v1.08 (Awareness)
Track C: v1.05 (Privacy)
Track D: v1.11 (Interaction)
Track E: v1.12 (Developer Intelligence)
Track F: v1.13 (Utility/Integration)
```

All tracks converge at v1.06 (Cognition Core) or v1.10 (Planning).

v1.11 (Interaction) depends on v1.05 (Privacy) and v1.08 (Awareness). If both are done, v1.11 can proceed independently. Yes, parallel is correct.

---

## Red Team Roadmap Refinements

Source: `artifacts/roadmap_refinements.md` (archived after merge)

### Refinement 1: v1.02 Must Be Restructured

v1.02 currently plans service boundaries and event bus but ignores the 7 critical reference architecture features. The restructured v1.02 has 8 phases: P01 API Domain Reorganization, P02 Service Boundaries + Event Bus (merged), P03 Agent System Hardening (NEW), P04 MCP Integration (NEW), P05 Tool Infrastructure (NEW), P06 Database Schema Updates, P07 Observability Foundation (NEW), P08 Integration & Testing.

**Revised duration:** 25-35 days (was 17-25).

### Refinement 2: v1.01 Should Add Frontend Modules and Testing

Add P07: Frontend Feature Module Scaffolding (create `frontend/src/features/`, feature module template, migrate existing components). Add P08: Testing Infrastructure (pytest fixtures factory, integration test framework, agent system test harness, frontend test setup, performance baseline capture, CI pipeline test integration).

**Revised duration:** 12-20 days (was 11-18).

### Refinement 3: Split v1.13

v1.13 has 19 capabilities (the most of any version). Split into v1.13 (Calendar, Tasks, Notes, Documents — 8 capabilities) and v1.14 (Contacts, Email, Extensions, Sync, Dashboard, Workspace, Webhooks — 11 capabilities). Old v1.14 (Advanced Intelligence with 4 capabilities) absorbed into v1.15 or merged.

**Alternative:** Move Calendar/Tasks to v1.08, Notes to v1.11. Reduces v1.13 to 16 capabilities.

### Refinement 4: Add Cross-Version Integration Tests

Add to every version's final phase: cross-domain integration tests (at least 3 per version), regression test suite expansion, performance comparison against baseline. Add to v1.06: dedicated integration test phase (P06) for Memory + Cognition, Awareness + Cognition, and end-to-end agent flow tests.

### Refinement 5: Add Migration Rollback to Every P01

Add validation step: "Verify migration rolls back cleanly." Add validation step: "Verify no data loss on rollback." Document rollback command: `alembic downgrade -1`.

### Refinement 6: Strengthen Definition of Done

Current DoD is generic ("All tests passing"). Improved DoD: all implementation tasks complete, unit tests passing, integration tests passing, no lint errors, no type errors, migration applies and rolls back cleanly, documentation updated, performance within 10% of baseline, security scan clean, cross-reference with reference architecture features complete.

### Refinement 7: Add Performance Gates

Starting from v1.02: API response time p95 < 200ms for CRUD, embedding speed ≥ 100 chunks/second, agent first-token latency < 500ms, backend memory usage < 512MB, test suite < 5 minutes.

### Refinement 8: Version Dependency Visualization

Add to IMPLEMENTATION_STEPS.md: ASCII dependency graph showing version relationships, critical path highlighted, parallel tracks highlighted. (Already present in this document.)

### Refinement 9: Add reference architecture Feature Traceability

Add to IMPLEMENTATION_STEPS.md: reference architecture feature matrix showing which version implements each feature, cross-reference with reference architecture sections. (Already present in this document.)
