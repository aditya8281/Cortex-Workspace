# Final Product Specification — CORTEX

**Document:** Unified Product Specification
**Authority:** Stage 4 — Master Consolidation & Final Specification
**Date:** 2026-06-27
**Status:** Definitive — all future implementation references this document

---

## Purpose

This document is the single source of truth for what Cortex is, what it can do, and what it will become. It merges three sources:

1. **Current repository** — 43 implemented features, 136 API endpoints, 72 services, agent system, integrity system
2. **Previous plans** — V1-V6 roadmap, 44 planned components, architecture evolution
3. **Future capability exploration** — 110 discovered capabilities across 10 domains

Nothing valuable has been lost. Nothing exists twice. Nothing contradicts. Every feature competed against the vision. Only the strongest survived.

---

## What Cortex Is

**One sentence:** Cortex gives your machine a brain — one that knows you, grows with you, and never shares your secrets.

**What it is:**
- A persistent machine intelligence layer
- A brain for your personal computer
- A trusted digital companion
- A local-first intelligence system
- A system that compounds understanding over years

**What it is NOT:**
- NOT a chatbot
- NOT a coding assistant
- NOT a cloud service
- NOT a platform
- NOT a replacement for human judgment

---

## Identity Characteristics

Cortex is **quiet.** It does not demand attention. It works in the background, building understanding, waiting to be useful.

Cortex is **patient.** It does not need to demonstrate value every session. It compounds value over months and years.

Cortex is **honest.** It says when it does not know. It explains its reasoning. It does not fabricate confidence.

Cortex is **local.** Its intelligence lives on your machine. No telemetry. No cloud dependency. No external service determines what Cortex knows.

Cortex is **yours.** Your data, your understanding, your intelligence. Cortex does not share your information with anyone.

Cortex is **humble.** It claims to understand your machine, your work, and your preferences — and to be genuinely useful within that scope.

---

## Nine Non-Negotiable Principles

1. **Local-first by default** — Core capabilities work without network access
2. **Privacy before convenience** — Architectural privacy guarantees, not promises
3. **Persistent intelligence** — Knowledge compounds across sessions, months, years
4. **Understand before acting** — Context and intent precede execution
5. **Assist instead of replace** — Augment human capability, never substitute it
6. **Human control always exists** — Every action is explainable and reversible
7. **Architecture before implementation** — Design precedes code
8. **Long-term maintainability** — Simplicity and clarity over cleverness
9. **Scalable evolution** — Grow through accumulation, not overhaul

---

## Mission

Build the first persistent intelligence layer that lives on a personal machine, understands its user over years, and serves as a trusted companion across every dimension of digital work.

---

## Product Values

1. **Depth over breadth** — Deep understanding of one person's work beats shallow understanding of many things
2. **Persistence over novelty** — Accumulated knowledge over years beats impressive single-session capabilities
3. **Privacy over convenience** — Architectural privacy guarantees beat cloud-accelerated features
4. **Understanding over action** — Understanding intent beats executing tasks quickly
5. **Trust over capability** — A less capable trusted system beats a more capable untrusted one

---

## What Cortex Refuses

1. **Cloud dependency** — Core capabilities must work without network access
2. **Data sharing** — User data never leaves the machine without explicit permission
3. **Complexity accumulation** — Every new capability must justify its complexity cost
4. **Human replacement** — Cortex assists. Cortex does not replace.
5. **Opacity** — Every action must be explainable and reversible

---

## Ten Permanent Domains

Cortex's capabilities are organized into 10 permanent domains. These are conceptual groupings, not code structure.

### Domain 1: Memory
**Purpose:** The persistent brain. Remember, connect, retrieve knowledge over years.
**Key Insight:** Memory is not storage — it is understanding.
**Current State:** Basic CRUD + search + knowledge graph + long-term memory + decay
**Target State:** Episodic, semantic, procedural, working memory with graph structure, consolidation, forgetting, evolution, cross-domain connections, temporal awareness, confidence weighting

### Domain 2: Awareness
**Purpose:** The senses. Perceive the user's digital environment.
**Key Insight:** Awareness is not surveillance — it is context.
**Current State:** Basic filesystem awareness via document indexing, repository management, model awareness
**Target State:** Full filesystem, repository, project, desktop, terminal, browser, clipboard, device, calendar, email, workspace, environment, system health, temporal, notification, running application awareness

### Domain 3: Cognition
**Purpose:** The thinking. Process information and generate insights.
**Key Insight:** Cognition is not computation — it is understanding.
**Current State:** Single agent loop with 15+ tools, stall detection, basic reasoning
**Target State:** Planning, task decomposition, reflection, reasoning, hypothesis generation, confidence estimation, decision support, goal management, problem solving, error analysis, strategy, self-evaluation, analogy, causal reasoning

### Domain 4: Execution
**Purpose:** The hands. Act on the world through tools and automation.
**Key Insight:** Execution is not automation — it is capability.
**Current State:** Agent tools (15+), basic tool execution
**Target State:** Automation, workflow orchestration, scheduling, permission management, recovery, parallel execution, background tasks, action verification, execution history, rollback, batch operations

### Domain 5: Learning
**Purpose:** The adaptation. Improve over time through experience.
**Key Insight:** Learning is not training — it is adaptation.
**Current State:** Memory decay (basic), conversation context
**Target State:** Preference, workflow, habit learning; behavior adaptation; feedback learning; personalization; knowledge refinement; continuous improvement; pattern recognition; anomaly detection

### Domain 6: Interaction
**Purpose:** The voice. Communicate with the user through multiple modalities.
**Key Insight:** Interaction is not interface — it is communication.
**Current State:** Conversational interface (SSE streaming), notifications, settings
**Target State:** Voice, command palette, GUI, CLI, API, proactive assistance, contextual suggestions, multi-modal, ambient intelligence, summarization

### Domain 7: Developer
**Purpose:** The craft. Serve developers with specialized intelligence.
**Key Insight:** Developer experience is not code generation — it is understanding.
**Current State:** Code indexing, repository management, Rust code intelligence (scaffolded), 142 skills, 18 commands, 16 hooks
**Target State:** Code understanding, repository intelligence, code review, documentation generation, test generation, refactoring, debugging, architecture guidance, dependency analysis, performance analysis, security analysis, migration, code generation, git intelligence, CI/CD

### Domain 8: Utility
**Purpose:** Daily life. Assist with everyday digital tasks beyond coding.
**Key Insight:** Utility is not features — it is assistance.
**Current State:** Notifications, settings, profile management
**Target State:** Calendar, email, task management, notes, documents, contacts, workspace management, dashboard, daily briefing, weekly review, habit tracking, focus management

### Domain 9: Integration
**Purpose:** The connections. Connect with external tools and services.
**Key Insight:** Integration is not connectivity — it is understanding.
**Current State:** GitHub proxy, sync system, MCP-ready architecture
**Target State:** Tool integration, service integration, protocol support (MCP, REST, WebSocket, SSH), extension system, data import/export, cross-device synchronization

### Domain 10: Privacy & Security
**Purpose:** The shield. Protect user data and maintain trust.
**Key Insight:** Privacy is not policy — it is architecture.
**Current State:** JWT auth, CSRF protection, Fernet encryption vault, ownership checks, middleware stack (CORS, rate limiting, request size limiting, HTTPS redirect)
**Target State:** Local processing, encryption at rest/in transit, access control, audit logging, data sovereignty, transparency, consent management, differential privacy, secure enclaves

---

## How All Capabilities Fit Together

```
┌───────────────────────────────────────────────────────────────┐
│                    INTERACTION                                │
│  Conversational · Voice · Command Palette · GUI · CLI · API  │
│  Proactive Assistance · Ambient Intelligence · Summarization  │
├──────────────────────┬────────────────────────────────────────┤
│     UTILITY          │          DEVELOPER                     │
│  Calendar · Email    │  Code Understanding · Repo Intelligence│
│  Tasks · Notes       │  Code Review · Debugging · Generation  │
│  Dashboard · Briefing│  Architecture · Git · CI/CD            │
├──────────────────────┴────────────────────────────────────────┤
│                    COGNITION     │      EXECUTION              │
│  Planning · Reasoning            │  Tool Execution · Automation │
│  Decision Support · Reflection   │  Workflows · Scheduling     │
│  Problem Solving · Error Analysis│  Recovery · Rollback         │
├──────────────────────┬──────────┴─────────────────────────────┤
│     LEARNING         │          INTEGRATION                   │
│  Preferences · Habits │  Tool · Service · Protocol            │
│  Feedback · Patterns  │  Extensions · Import/Export · Sync    │
├──────────────────────┴───────────────────────────────────────┤
│                    AWARENESS     │      MEMORY                 │
│  Filesystem · Repository · Proj │  Episodic · Semantic · Graph│
│  Desktop · Calendar · Email      │  Working · Search · Evolution│
├─────────────────────────────────┴────────────────────────────┤
│                    PRIVACY & SECURITY (Foundation)            │
│  Local Processing · Encryption · Access Control · Audit       │
│  Data Sovereignty · Transparency · Consent · Secure Enclaves  │
└───────────────────────────────────────────────────────────────┘
```

**Flow:** Privacy & Security → Awareness + Memory → Cognition + Learning + Integration → Execution → Utility + Developer → Interaction

Each layer builds on the layers below. Privacy is the foundation. Awareness and Memory provide perception. Cognition, Learning, and Integration provide processing. Execution provides action. Utility and Developer provide service. Interaction provides communication.

---

## Technical Foundation

**Backend:** FastAPI + sync SQLAlchemy 2.0 + Alembic + PostgreSQL 16
**Frontend:** Next.js 15 App Router + React 19 + TypeScript 5.8 + Tailwind 3.4
**Code Intelligence:** Rust (cortexCode crate)
**Storage:** PostgreSQL 16 + Redis 7 + Qdrant (embedded)
**Embeddings:** ONNX Runtime BGE-M3 (768-dim)
**RAG:** HybridRetrievalV2 (vector + fulltext + graph via RRF + MMR)
**Encryption:** Fernet (vault) + JWT/Argon2 (auth)
**Agent System:** Single async generator loop, max 25 iterations, 15+ tools
**Integrity System:** 10 engines, 40+ files, 95 tests
**Developer Ecosystem:** 142 skills, 18 commands, 16 hooks

---

## Rejected Capabilities (Final)

These capabilities were considered and permanently rejected:

1. **Social Intelligence** — Crosses privacy boundary into surveillance
2. **Emotional Intelligence** — Technically unreliable and ethically questionable
3. **Multi-User Intelligence** — Violates personal intelligence identity
4. **Cloud Acceleration** — Creates dependency; core must work locally
5. **Automatic Code Execution** — Violates human control principle
6. **Sentience Simulation** — Deception erodes trust
7. **Competitive Intelligence** — Business function, not personal intelligence
8. **Financial Trading** — Irreversible harm from mistakes
9. **Autonomous Research** — Resource consumption without guaranteed value
10. **Game AI** — Entertainment, not intelligence
11. **Community Features (V6)** — Violates personal intelligence principle
12. **Analytics Dashboard (V6)** — Vanity metric, not user value

---

## Open Questions (Carried Forward)

These questions were identified during brainstorming and remain unresolved. They should be addressed during implementation planning:

1. Where does Cortex end and the user begin?
2. What happens when Cortex disagrees with the user?
3. What should Cortex forget?
4. How proactive is too proactive?
5. How does Cortex handle user frustration?
6. How does Cortex handle preference conflicts?
7. What is the right default for data retention?
8. How does Cortex handle data portability?
9. How does Cortex scale with time (data accumulation)?
10. Should Cortex warn users about unhealthy patterns?

---

## Specification Authority

This document is the definitive product specification. After Stage 4:

- All future implementation must reference this specification
- No capability may be added without evaluating it against this specification
- No contradiction with this specification is permitted
- The specification evolves only through formal revision, not informal drift

**Next Stage:** Stage 5 — Implementation Roadmap (derives implementation plan from this specification)
