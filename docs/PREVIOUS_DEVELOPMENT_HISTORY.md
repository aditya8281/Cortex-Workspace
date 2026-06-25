# PREVIOUS DEVELOPMENT HISTORY

**Created:** 2026-06-25
**Purpose:** Preserves all pre-V1 development history, planning artifacts, and lessons learned. This file is archival — it is not referenced by any active document.

---

## 1. Original Development Phases (Phase 1–6)

The original Cortex development followed a phase-based approach (Phase 1–10). Phases 1–6 built the existing codebase. Phase 6.5 established the governance ecosystem. Phases 7–10 were planned but never started.

### Phase 1: Identity + Secure Storage ✅ Complete

- Multi-user authentication with JWT and refresh tokens
- Encrypted private vault per user (separate password)
- Profile management and GitHub account linking
- Admin user management
- Cookie-based authentication with automatic refresh
- Spring-physics animations, command palette, glass morphism UI

### Phase 2: Indexing & Knowledge Graph ✅ Complete

- Incremental indexer (hash-based change detection)
- Knowledge graph (graph_nodes, graph_edges)
- Cross-file search (vector + graph enrichment)
- Unified search API
- Repository management API (CRUD + indexing triggers)
- Background tasks: index_repo, build_graph

### Phase 3: Unified Search & Agents ✅ Complete

- Agent system (base agent, planner, executor)
- Agent run manager with step tracking
- Agent CRUD API + run/step/feedback API
- Frontend: Agent chat interface, Agents management page

### Phase 4A: LLM Integration & Local Models 🟡 Partial

- LLM manager with provider abstraction (llama.cpp, Ollama) ✅
- Model catalog with providers, variants, capabilities, benchmarks ✅
- Hardware detection and quantization recommendations ✅
- Model download manager with progress tracking ✅
- User model settings (persisted per-user) ✅
- Frontend: Models page with catalogue, installed models, download queue ✅
- Conversation-to-memory pipeline ✅
- Long-term memory with decay ✅

### Phase 4B: Smart Indexing & Retrieval 🟡 Partial

- Semantic chunker with language-aware splitting ✅
- Indexing configuration (include/exclude paths, file types) ✅
- Full-text search (PostgreSQL ts_vector) ✅
- Hybrid retrieval (vector + keyword + graph) ✅
- Document indexer for non-code files ✅
- Retrieval quality metrics ✅
- File watcher v2 with sync state persistence ✅
- Batch indexer for bulk operations ✅

### Phase 5: Conversation & Context 🟡 Partial

- Conversation model with message history and token tracking ✅
- Conversation-to-memory pipeline ✅
- Long-term memory model with decay, confidence, and access tracking ✅
- SSE streaming for real-time agent responses ✅
- Conversation service with context building ✅

### Phase 6: Agent Intelligence 🟡 Partial

- Agent SSE streaming ✅
- Expanded tool registry ✅
- RAG pipeline integration ✅
- Entity extraction service ✅
- Search clustering and recommendations ✅

### Phase 6.5: Agentic Ecosystem ✅ Complete

- Governance docs (docs/GOVERNANCE.md)
- Workflow definitions (docs/WORKFLOWS.md)
- Decision tracking (docs/decisions/)
- Audit tracking (docs/audits/)
- Enhanced CLAUDE.md with ecosystem integration
- Enhanced AGENTS.md with workflow and skill rules
- ADR for ecosystem design (docs/decisions/001-agentic-ecosystem.md)
- 66+ agent skills (.claude/skills/)
- 7 strategic commands (.claude/commands/project/)
- 11 governance hooks (.claude/hooks/)
- Automation framework (scripts/automation/)
- Claude Code integration (settings.local.json, hooks)

---

## 2. Planned But Never Started Phases

### Phase 7: Desktop Preparation (⬜ Not started)

Would have covered:
- Service abstraction layer
- Filesystem abstraction
- Tauri readiness
- Provider protocol interfaces

### Phase 8: Learning Loop (⬜ Not started)

Would have covered:
- Pattern recognition
- Correction tracking
- Proactive assistant behavior

### Phase 9: Observability & Monitoring (⬜ Not started)

Would have covered:
- Dashboards
- Metrics
- Health monitoring
- Distributed tracing

### Phase 10: Production Hardening (⬜ Not started)

Would have covered:
- Test coverage expansion
- Security hardening
- Performance optimization
- Docker/CI/CD improvements

---

## 3. The Desktop-First Reorientation (2026-06-25)

### Strategic Pivot

On 2026-06-25, Cortex pivoted from a browser-first web application to a desktop-first daemon-centric intelligence platform. This was captured in:

- `docs/superpowers/specs/2026-06-25-cortex-reorientation-design.md` — Design spec (491 lines)
- `.agents/plans/2026-06-25-desktop-reorientation.md` — Implementation plan (1,897 lines)

### What Changed

The reorientation redefined CORTEX as:

> "A persistent intelligence daemon that maintains understanding over time. Not primarily a chatbot, web application, or model wrapper — conversational interaction is one interface among many."

**Three pillars:**
1. **Persistent understanding** — builds and maintains a coherent model of your digital life
2. **Native integration** — lives on your machine, integrates with how you work
3. **User sovereignty** — everything runs locally, no telemetry, no cloud dependency

### What This Superseded

The reorientation replaced the Phase 7–10 plans with a V1–V6 version system:

| Old (Never Started) | New (V1–V6 System) |
|---------------------|---------------------|
| Phase 7: Desktop Preparation | V1–V3: Daemon + Architecture + Desktop |
| Phase 8: Learning Loop | V4–V5: Automaton + Workspace |
| Phase 9: Observability | V4–V6: Distributed across versions |
| Phase 10: Production Hardening | V6: Ecosystem + Polish |

### The V1–V6 Version System

| Version | Name | Duration | Focus |
|---------|------|----------|-------|
| **V1** | The Brain Works | 11–18 days | Daemon lifecycle, agent loop, CLI |
| **V2** | The Architecture | 17–25 days | Provider abstraction, MCP, plugins |
| **V3** | The Desktop | 22–31 days | Tauri shell, TUI, performance |
| **V4** | The Automaton | 21–30 days | Scheduler, MCP server, research |
| **V5** | The Workspace | 27–38 days | Email, calendar, tasks, notes |
| **V6** | The Ecosystem | 27–38 days | Marketplace, graph intelligence, polish |

Active version tracking: `.agents/plans/ACTIVE_VERSION.md`

---

## 4. The Architecture Council (2026-06-25)

A comprehensive multi-review analysis was conducted to validate the Cortex architecture against 10 reference repositories. This produced 22 files across 3 phases:

### Phase 1: Reference Repository Analysis

10 reference repos were analyzed across 4 batches:

| Batch | Repos | Domain |
|-------|-------|--------|
| 1 | Mem0, Graphiti, Zep | Memory, knowledge graphs |
| 2 | LlamaIndex, sist2, turbovec | Indexing, retrieval, vector storage |
| 3 | Open WebUI, AnythingLLM, ollama-catalog | Platform architecture |
| 4 | Continue, Odysseus, Strands | Agent orchestration |

**Findings:** 73 gaps identified, all mapped to version plans via FinalCompatibilities.md.

### Phase 2: Architecture Reviews

Three independent reviews:

1. **Architecture Review** — Validated against guide.md's 10 principles. Found 12 confirmed decisions, 7 to revisit, 5 needing new ADRs.

2. **Challenge Review** — Adversarial review of version boundaries, ordering, and key decisions. Identified decision debt (agent system, tool registry, embedding, vector store, background tasks).

3. **Reflection Review** — Improvement, simplification, and automation opportunities. Found potential for shared utilities, config-driven testing, and pipeline composition.

### Phase 3: Audit Files

5 audit documents were generated:

| File | Lines | Content |
|------|-------|---------|
| Audit.md | 250 | Master plan audit — verdict: "ready for implementation" |
| FinalCompatibilities.md | 227 | 62 ODYSSEUS items mapped to version plans |
| archive-candidates.md | 116 | 27 files recommended for archival |
| implementation_steps.md | 528 | Definitive contributor guide |
| governance-audit.md | 219 | Governance activation audit |

### Architecture Decisions Documented

13 confirmed decisions, 7 to revisit, 5 new ADRs created (see `docs/decisions/`):

**Confirmed:** PostgreSQL, two-password auth, Fernet vault, hybrid retrieval, Next.js 15, embedding fallback, arq tasks, Docker Compose, TDD/SQLite tests, multi-agent governance, Warm Neural Dark, code-aware knowledge graph.

**Revisiting:** Pluggable embedding provider, event-driven runner.

**New:** MCP integration, plugin architecture, desktop mode strategy, token estimation, daily productivity tools.

---

## 5. The Governance Activation (2026-06-25)

### Problem

Cortex had comprehensive governance documentation (GOVERNANCE.md, WORKFLOWS.md, DEVELOPER_GUIDE.md) but none of it was enforced by the platform. Claude Code had no awareness of Cortex-specific processes.

### Solution

1. **CLAUDE.md rewritten** as execution contract (not just a reference doc)
2. **Entry Protocol** — 4-step process Claude follows on every session entry
3. **Authority Hierarchy** — 6-level priority for document conflicts
4. **ACTIVE_VERSION.md** — single source of truth for current development state
5. **Claude Code hooks** — pre-commit-gate.py wired into settings.local.json
6. **Cortex-specific skills** — cortex-architecture-audit, cortex-health-review, cortex-status
7. **Automation framework** — 4 new phases (release, documentation, skills, status)

### Key Insight

Governance docs are worthless if the platform doesn't enforce them. The fix was to wire governance into Claude Code's hook system so checks run automatically at checkpoints (push/merge), not on every tool call.

### Commits

- `be123ba` — "docs: governance activation audit — CLAUDE.md rewritten as control plane"
- `6d79034` — "fix: resolve 4 critical governance gaps"
- `f882776` — "docs: archive 22 superseded files, extract 20 ADRs, delete .impeccable cache"

---

## 6. The Strategic Command System (2026-06-24)

Seven slash commands were designed and implemented for continuous improvement:

| Command | Purpose |
|---------|---------|
| `/project:reflect` | Structured reflection on completed work |
| `/project:review` | Code quality analysis |
| `/project:challenge` | Adversarial review of decisions |
| `/project:health` | Repository health check |
| `/project:architecture` | Architecture alignment check |
| `/project:ideas` | Innovation discovery |
| `/project:improve` | Ecosystem improvement suggestions |

These are implemented in `.claude/commands/project/` and remain active.

---

## 7. Key Lessons Learned

### Architecture

1. **Single source of truth wins.** When 5 documentation systems compete, nothing is true. CLAUDE.md as execution contract resolved this.
2. **Governance without enforcement is theater.** Hooks in settings.local.json make governance real.
3. **Constitution first, plans second.** guide.md defines what to build; version plans define how.
4. **Desktop-first is the right direction.** The original Phase 1–10 system assumed browser-first. The reorientation corrected this.

### Development

1. **TDD saves time.** 341+ existing tests provide a safety net for every change.
2. **Agent system needs replacement.** The Planner→Executor two-agent pattern adds latency and complexity. A single streaming loop is the right architecture.
3. **Tool registry needs schemas.** Hand-maintained TOOL_REGISTRY dict degrades LLM function-calling. @tool decorator is the answer.
4. **Embedding providers must be pluggable.** Hardcoded fallback chain can't be extended.
5. **Vector store must be abstracted.** Qdrant-only locks out desktop mode.

### Process

1. **One question at a time** in brainstorming. Don't overwhelm.
2. **Small focused commits** beat large batches.
3. **Cross-reference everything.** FinalCompatibilities.md prevents items from falling through cracks.
4. **Archive, don't delete.** Historical context is valuable even when superseded.
5. **Progress tracking must be atomic.** Component-level tracking in progress.md catches stale status.

---

## 8. Original Phase Plan Files (Now Archived)

These files were superseded by the V1–V6 version system and archived to `.agents/plans/_archive/`:

| Original File | Replaced By |
|---------------|-------------|
| `00-INDEX.md` | `guide.md` + `versions/` structure |
| `01-PHASE-1-FOUNDATION.md` | `versions/v1/Phase-1.md` |
| `02-PHASE-2-AGENT.md` | `versions/v1/Phase-2.md` |
| `03-PHASE-3-MEMORY.md` | `versions/v2/Phase-3.md` |
| `04-PHASE-4-DESKTOP.md` | `versions/v3/Phase-1.md` |
| `05-PHASE-5-DAILY.md` | `versions/v5/Phase-1.md` |
| `06-PHASE-6-PRODUCTION.md` | `versions/v6/Phase-3.md` |
| `07-ARCHITECTURE.md` | `guide.md` |
| `08-PRODUCTION-READINESS.md` | `versions/v6/Phase-3.md` |

Council discovery docs (archived):
- `council/architecture-decisions.md` → findings in `guide.md` + `docs/decisions/`
- `council/contradictions.md` → resolved in governance activation
- `council/current-state.md` → superseded by progress tracking
- `council/opportunities.md` → captured in version plans
- `council/risks.md` → mitigated in version plans
- `council/strengths.md` → captured in guide.md
- `council/weaknesses.md` → addressed in version plans

Reference consolidation (archived):
- `reference-repo-consolidation/` (12 files) → findings in `FinalCompatibilities.md`
- `CORTEX_REFERENCE_CONSOLIDATION_MASTER_PLAN.md` → superseded
- `ODYSSEUS_INTEGRATION_PLAN.md` → superseded
- `archive-candidates.md` → served its purpose

---

## 9. Codebase Statistics at Time of Archive

| Metric | Value |
|--------|-------|
| Backend test files | 42 |
| Migration files | 8 |
| Backend services | 45+ |
| Backend routes | 20+ |
| Frontend components | Multiple |
| Skills | 69 |
| ADRs | 21 |
| Governance hooks | 11 |
| Slash commands | 7 |
| Automation phases | 8 |
| Planning documents (active) | 15 |
| Planning documents (archived) | 22+ |

---

*This document preserves the complete development history of Cortex prior to the V1 version system. All information here is historical context — the authoritative planning documents are in the active V1–V6 version system.*
