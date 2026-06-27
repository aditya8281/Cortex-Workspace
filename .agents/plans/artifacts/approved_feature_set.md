# Approved Feature Set — CORTEX

**Document:** Consolidated Approved Features
**Authority:** Stage 4 — Master Consolidation & Final Specification
**Date:** 2026-06-27

---

## Purpose

Every feature, capability, and idea from all three stages has been evaluated. This document lists every approved feature, its consolidation decision, and its domain assignment. Features not listed here were either merged into listed features, rejected, or archived.

---

## Consolidation Statistics

| Source | Count | Approved | Merged | Rejected |
|--------|-------|----------|--------|----------|
| Current features (Stage 1) | 43 | 38 | 5 | 0 |
| Planned features (Stage 2) | 44 | 28 | 12 | 4 |
| Stage 3 capabilities | 110 | 66 | 31 | 13 |
| **Total evaluated** | **197** | **132 unique** | — | **17** |

**Note:** The 132 unique approved features overlap significantly. After deduplication and merging, the final approved feature count is 110 capabilities across 10 domains.

---

## Domain 1: Memory (13 capabilities)

| # | Feature | Source | Decision | Priority |
|---|---------|--------|----------|----------|
| M1 | Episodic Memory | Stage 3 | NEW | Foundation |
| M2 | Semantic Memory | Stage 1 (Knowledge Graph) + Stage 3 | IMPROVE | Foundation |
| M3 | Procedural Memory | Stage 3 | NEW | Core |
| M4 | Working Memory | Stage 1 (Conversation Context) + Stage 3 | IMPROVE | Foundation |
| M5 | Memory Consolidation | Stage 3 | NEW | Core |
| M6 | Memory Graph | Stage 1 (Knowledge Graph) + Stage 2 (V2) + Stage 3 | IMPROVE | Foundation |
| M7 | Forgetting | Stage 1 (Memory Decay) + Stage 3 | IMPROVE | Enhancement |
| M8 | Knowledge Evolution | Stage 3 | NEW | Core |
| M9 | Context Retrieval | Stage 1 (HybridRetrievalV2) + Stage 3 | IMPROVE | Core |
| M10 | Memory Search | Stage 1 (Unified Search) + Stage 3 | IMPROVE | Foundation |
| M11 | Confidence-Weighted Memory | Stage 3 | NEW | Enhancement |
| M12 | Temporal Memory | Stage 3 | NEW | Enhancement |
| M13 | Cross-Domain Memory | Stage 3 | NEW | Core |

**Merged from:**
- Knowledge Graph (B17) → merged into M2/M6
- Unified Search (B18) → merged into M10
- Long-term Memory (B12) → merged into M2
- Memory Decay (B13) → merged into M7
- Memory Architecture v2 (P05) → merged into M1-M6
- Vector Store Abstraction (P08) → merged into M6/M10
- Graph Intelligence v2 (P41) → merged into M6
- Cross-encoder Reranking (P42) → merged into M9/M10

---

## Domain 2: Awareness (16 capabilities)

| # | Feature | Source | Decision | Priority |
|---|---------|--------|----------|----------|
| A1 | Filesystem Awareness | Stage 1 (Document Indexing) + Stage 2 (P23) + Stage 3 | IMPROVE | Foundation |
| A2 | Repository Awareness | Stage 1 (Repository Management) + Stage 3 | IMPROVE | Foundation |
| A3 | Project Awareness | Stage 3 | NEW | Foundation |
| A4 | Desktop Awareness | Stage 3 | NEW | Core |
| A5 | Terminal Awareness | Stage 3 | NEW | Core |
| A6 | Browser Awareness | Stage 3 | NEW | Enhancement |
| A7 | Clipboard Awareness | Stage 3 | NEW | Enhancement |
| A8 | Running Applications | Stage 3 | NEW | Core |
| A9 | Device Awareness | Stage 1 (Hardware Detection) + Stage 3 | IMPROVE | Core |
| A10 | Notification Awareness | Stage 1 (Notification System) + Stage 3 | IMPROVE | Core |
| A11 | Calendar Awareness | Stage 3 | NEW | Core |
| A12 | Email Awareness | Stage 3 | NEW | Core |
| A13 | Workspace Awareness | Stage 3 | NEW | Foundation |
| A14 | Environment Awareness | Stage 3 | NEW | Core |
| A15 | System Health Awareness | Stage 1 (Health Checks) + Stage 3 | IMPROVE | Core |
| A16 | Temporal Awareness | Stage 3 | NEW | Enhancement |

**Merged from:**
- Document Indexing (B19) → merged into A1
- Repository Management (B20) → merged into A2
- Hardware Detection (B22) → merged into A9
- Notification System (B26) → merged into A10
- Health Checks (B03) → merged into A15
- File Watching (P23) → merged into A1

---

## Domain 3: Cognition (14 capabilities)

| # | Feature | Source | Decision | Priority |
|---|---------|--------|----------|----------|
| C1 | Planning | Stage 3 | NEW | Core |
| C2 | Task Decomposition | Stage 3 | NEW | Core |
| C3 | Reflection | Stage 3 | NEW | Core |
| C4 | Reasoning | Stage 1 (Agent Loop) + Stage 3 | IMPROVE | Foundation |
| C5 | Hypothesis Generation | Stage 3 | NEW | Enhancement |
| C6 | Confidence Estimation | Stage 3 | NEW | Foundation |
| C7 | Decision Support | Stage 3 | NEW | Core |
| C8 | Goal Management | Stage 3 | NEW | Enhancement |
| C9 | Problem Solving | Stage 1 (Agent Loop) + Stage 3 | IMPROVE | Core |
| C10 | Error Analysis | Stage 3 | NEW | Core |
| C11 | Strategy Generation | Stage 3 | NEW | Enhancement |
| C12 | Self-Evaluation | Stage 3 | NEW | Enhancement |
| C13 | Analogy Recognition | Stage 3 | NEW | Enhancement |
| C14 | Causal Reasoning | Stage 3 | NEW | Enhancement |

**Merged from:**
- Agent Loop (B31) → merged into C4/C9
- Research Agent (P27) → MERGED into C1/C4 (narrowed: research as cognition, not autonomous agent)

---

## Domain 4: Execution (12 capabilities)

| # | Feature | Source | Decision | Priority |
|---|---------|--------|----------|----------|
| E1 | Tool Execution | Stage 1 (Agent Tools) + Stage 3 | IMPROVE | Foundation |
| E2 | Automation | Stage 3 | NEW | Core |
| E3 | Workflow Orchestration | Stage 2 (P31) + Stage 3 | IMPROVE | Core |
| E4 | Scheduling | Stage 2 (P25) + Stage 3 | NEW | Core |
| E5 | Permission Management | Stage 1 (Ownership Checks) + Stage 3 | IMPROVE | Foundation |
| E6 | Recovery | Stage 3 | NEW | Core |
| E7 | Parallel Execution | Stage 3 | NEW | Enhancement |
| E8 | Background Tasks | Stage 2 (P30) + Stage 3 | IMPROVE | Core |
| E9 | Action Verification | Stage 3 | NEW | Core |
| E10 | Execution History | Stage 3 | NEW | Core |
| E11 | Rollback | Stage 3 | NEW | Core |
| E12 | Batch Operations | Stage 3 | NEW | Enhancement |

**Merged from:**
- Agent Tools 15+ (B32) → merged into E1
- Ownership Checks → merged into E5
- Workflow Engine (P31) → merged into E3
- Scheduler (P25) → merged into E4
- Background Intelligence (P30) → merged into E8
- Task Queue (P29) → merged into E3/E8

---

## Domain 5: Learning (10 capabilities)

| # | Feature | Source | Decision | Priority |
|---|---------|--------|----------|----------|
| L1 | Preference Learning | Stage 3 | NEW | Core |
| L2 | Workflow Learning | Stage 3 | NEW | Core |
| L3 | Habit Learning | Stage 3 | NEW | Enhancement |
| L4 | Behavior Adaptation | Stage 3 | NEW | Core |
| L5 | Feedback Learning | Stage 3 | NEW | Core |
| L6 | Personalization | Stage 3 | NEW | Enhancement |
| L7 | Knowledge Refinement | Stage 3 | NEW | Core |
| L8 | Continuous Improvement | Stage 3 | NEW | Core |
| L9 | Pattern Recognition | Stage 3 | NEW | Core |
| L10 | Anomaly Detection | Stage 3 | NEW | Enhancement |

**All new.** No current implementation covers learning. This domain is entirely forward-looking.

---

## Domain 6: Interaction (12 capabilities)

| # | Feature | Source | Decision | Priority |
|---|---------|--------|----------|----------|
| I1 | Conversational Interface | Stage 1 (SSE Streaming) + Stage 3 | IMPROVE | Foundation |
| I2 | Voice Interface | Stage 3 | NEW | Enhancement |
| I3 | Command Palette | Stage 2 (P22) + Stage 3 | NEW | Core |
| I4 | GUI | Stage 1 (Next.js Frontend) + Stage 3 | IMPROVE | Core |
| I5 | CLI | Stage 2 (P11) + Stage 3 | IMPROVE | Foundation |
| I6 | API | Stage 1 (136 endpoints) + Stage 3 | IMPROVE | Foundation |
| I7 | Notifications | Stage 1 (Notification System) + Stage 2 (P10/P20) + Stage 3 | IMPROVE | Core |
| I8 | Proactive Assistance | Stage 3 | NEW | Core |
| I9 | Contextual Suggestions | Stage 3 | NEW | Core |
| I10 | Multi-Modal Interaction | Stage 3 | NEW | Enhancement |
| I11 | Ambient Intelligence | Stage 2 (P21) + Stage 3 | NEW | Core |
| I12 | Summarization | Stage 3 | NEW | Core |

**Merged from:**
- SSE Streaming (B16) → merged into I1
- Next.js Frontend → merged into I4
- CLI v2 (P11) → merged into I5
- 136 API Endpoints → merged into I6
- Notification Engine (P10) → merged into I7
- Desktop Notifications (P20) → merged into I7
- System Tray (P21) → merged into I11
- Global Hotkeys (P22) → merged into I3

---

## Domain 7: Developer (15 capabilities)

| # | Feature | Source | Decision | Priority |
|---|---------|--------|----------|----------|
| D1 | Code Understanding | Stage 1 (Rust Code Intel) + Stage 3 | IMPROVE | Foundation |
| D2 | Repository Intelligence | Stage 1 (Repository Management) + Stage 3 | IMPROVE | Foundation |
| D3 | Code Review | Stage 3 | NEW | Core |
| D4 | Documentation Generation | Stage 3 | NEW | Core |
| D5 | Test Generation | Stage 3 | NEW | Core |
| D6 | Refactoring Assistance | Stage 3 | NEW | Enhancement |
| D7 | Debugging Support | Stage 3 | NEW | Core |
| D8 | Architecture Guidance | Stage 3 | NEW | Core |
| D9 | Dependency Analysis | Stage 3 | NEW | Core |
| D10 | Performance Analysis | Stage 3 | NEW | Enhancement |
| D11 | Security Analysis | Stage 3 | NEW | Core |
| D12 | Migration Assistance | Stage 3 | NEW | Enhancement |
| D13 | Code Generation | Stage 1 (Agent Tools) + Stage 3 | IMPROVE | Core |
| D14 | Git Intelligence | Stage 1 (GitHub Proxy) + Stage 3 | IMPROVE | Core |
| D15 | CI/CD Understanding | Stage 3 | NEW | Enhancement |

**Merged from:**
- Rust Code Intel (scaffolded) → merged into D1
- Repository Management → merged into D2
- GitHub Proxy (B30) → merged into D14
- Agent Tools for code → merged into D13

---

## Domain 8: Utility (12 capabilities)

| # | Feature | Source | Decision | Priority |
|---|---------|--------|----------|----------|
| U1 | Calendar Management | Stage 2 (P33) + Stage 3 | NEW | Core |
| U2 | Email Management | Stage 2 (P32) + Stage 3 | NEW | Core |
| U3 | Task Management | Stage 2 (P34) + Stage 3 | NEW | Core |
| U4 | Notes & Knowledge Management | Stage 2 (P35) + Stage 3 | NEW | Core |
| U5 | Document Management | Stage 2 (P36) + Stage 3 | NEW | Core |
| U6 | Contact Management | Stage 2 (P37) + Stage 3 | POSTPONE | Enhancement |
| U7 | Digital Workspace Management | Stage 3 | NEW | Enhancement |
| U8 | Personal Dashboard | Stage 2 (P38) + Stage 3 | NEW | Core |
| U9 | Daily Briefing | Stage 3 | NEW | Core |
| U10 | Weekly Review | Stage 3 | NEW | Enhancement |
| U11 | Habit Tracking | Stage 3 | NEW | Enhancement |
| U12 | Focus Management | Stage 3 | NEW | Enhancement |

**Merged from:**
- Email Integration (P32) → merged into U2
- Calendar Integration (P33) → merged into U1
- Task Management (P34) → merged into U3
- Notes System (P35) → merged into U4
- Document Management (P36) → merged into U5
- Contacts (P37) → POSTPONE to later phases
- Workspace Dashboard (P38) → merged into U8

---

## Domain 9: Integration (6 capabilities)

| # | Feature | Source | Decision | Priority |
|---|---------|--------|----------|----------|
| X1 | Tool Integration | Stage 3 | NEW | Foundation |
| X2 | Service Integration | Stage 3 | NEW | Core |
| X3 | Protocol Support | Stage 2 (P02/P26) + Stage 3 | IMPROVE | Foundation |
| X4 | Extension System | Stage 2 (P03) + Stage 3 | IMPROVE | Enhancement |
| X5 | Data Import/Export | Stage 3 | NEW | Foundation |
| X6 | Cross-Device Synchronization | Stage 1 (Sync System) + Stage 3 | IMPROVE | Enhancement |

**Merged from:**
- MCP Integration (P02) → merged into X3
- Plugin System (P03) → merged into X4
- MCP Server Mode (P26) → merged into X3
- Sync System (B29) → merged into X6

---

## Domain 10: Privacy & Security (10 capabilities)

| # | Feature | Source | Decision | Priority |
|---|---------|--------|----------|----------|
| P1 | Local Processing | Stage 1 (Daemon) + Stage 3 | IMPROVE | Foundation |
| P2 | Encryption at Rest | Stage 1 (Vault) + Stage 3 | IMPROVE | Foundation |
| P3 | Encryption in Transit | Stage 1 (HTTPS) + Stage 3 | IMPROVE | Foundation |
| P4 | Access Control | Stage 1 (Auth) + Stage 3 | IMPROVE | Foundation |
| P5 | Audit Logging | Stage 3 | NEW | Foundation |
| P6 | Data Sovereignty | Stage 3 | NEW | Foundation |
| P7 | Transparency | Stage 3 | NEW | Foundation |
| P8 | Consent Management | Stage 3 | NEW | Core |
| P9 | Differential Privacy | Stage 3 | NEW | Enhancement |
| P10 | Secure Enclaves | Stage 3 | NEW | Enhancement |

**Merged from:**
- JWT Auth + CSRF → merged into P4
- Fernet Vault → merged into P2
- HTTPS Redirect → merged into P3
- Ownership Checks → merged into P4
- Daemon Lifecycle → merged into P1

---

## Infrastructure Features (Cross-Cutting)

These features span multiple domains and are not assigned to a single domain:

| # | Feature | Source | Decision | Purpose |
|---|---------|--------|----------|---------|
| INF1 | Daemon Lifecycle | Stage 1 | KEEP | Local-first operation |
| INF2 | Health System (3-level) | Stage 1 | KEEP | Reliability |
| INF3 | Middleware Stack | Stage 1 | KEEP | Security, performance |
| INF4 | Alembic Migrations | Stage 1 | KEEP | Schema evolution |
| INF5 | Integrity System (10 engines) | Stage 1 | KEEP | Quality enforcement |
| INF6 | Skills Ecosystem (142) | Stage 1 | KEEP | Developer extensibility |
| INF7 | Commands Ecosystem (18) | Stage 1 | KEEP | Workflow orchestration |
| INF8 | Hooks System (16) | Stage 1 | KEEP | Automated quality |
| INF9 | Test Suite (1188+) | Stage 1 | KEEP | Reliability |
| INF10 | Desktop Shell | Stage 2 (P16) | NEW | Native desktop experience |
| INF11 | Offline Mode | Stage 2 (P19) | NEW | Local-first guarantee |
| INF12 | Session Management | Stage 2 (P28) | KEEP | Continuity |
| INF13 | Event Bus | Stage 2 (P04) | NEW | Decoupled architecture |
| INF14 | Service Interfaces | Stage 2 (P06) | NEW | Abstraction layer |
| INF15 | Bounded Contexts | Stage 2 (P07) | NEW | Architecture evolution |
| INF16 | Configuration System | Stage 2 (P09) | NEW | Flexibility |

---

## Rejected Features (Final)

| Feature | Source | Reason |
|---------|--------|--------|
| Community Features | Stage 2 (V6) | Violates personal intelligence principle |
| Analytics Dashboard | Stage 2 (V6) | Vanity metric, not user value |
| Social Intelligence | Stage 3 | Crosses privacy boundary |
| Emotional Intelligence | Stage 3 | Technically unreliable, ethically questionable |
| Multi-User Intelligence | Stage 3 | Violates personal intelligence identity |
| Cloud Acceleration | Stage 3 | Creates dependency |
| Automatic Code Execution | Stage 3 | Violates human control |
| Sentience Simulation | Stage 3 | Deception erodes trust |
| Competitive Intelligence | Stage 3 | Business function, not personal |
| Financial Trading | Stage 3 | Irreversible harm |
| Autonomous Research | Stage 3 | Resource consumption without value |
| Game AI | Stage 3 | Entertainment, not intelligence |

---

## Summary

| Domain | Capabilities | Foundation | Core | Enhancement |
|--------|-------------|------------|------|-------------|
| Memory | 13 | 5 | 4 | 4 |
| Awareness | 16 | 3 | 10 | 3 |
| Cognition | 14 | 2 | 7 | 5 |
| Execution | 12 | 2 | 7 | 3 |
| Learning | 10 | 0 | 6 | 4 |
| Interaction | 12 | 3 | 6 | 3 |
| Developer | 15 | 2 | 8 | 5 |
| Utility | 12 | 0 | 6 | 6 |
| Integration | 6 | 3 | 1 | 2 |
| Privacy & Security | 10 | 7 | 1 | 2 |
| Infrastructure | 16 | 10 | 4 | 2 |
| **Total** | **126** | **37** | **60** | **39** |
