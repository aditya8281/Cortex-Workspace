# Cortex Roadmap Audit — 2026-06-20

> Comprehensive review of project state, plan coverage, and roadmap restructuring rationale.

---

## Current State Summary

**Phases Complete:** 0-A (Prerequisites), 0-B (Architecture), 1 (Memory), 2 (Indexing), 3 (Agents) + UI Refactor
**Phases Not Started:** 4 (Intelligence), 5 (Desktop), 6 (Learning)
**Commits:** 20+ commits covering infrastructure, features, and UI redesign
**Migrations:** 14 Alembic migrations (a through n)
**Tests:** Root-level integration tests (8 files) + backend tests (4 files) + frontend vitest (2 files)

---

## What Works Today

| Feature | Status | Quality |
|---------|--------|---------|
| Multi-user auth (JWT cookies, Argon2, refresh rotation) | ✅ Working | Production-grade |
| Encrypted vault (Fernet, separate password, file ops) | ✅ Working | Production-grade |
| Profile management (avatar, GitHub, developer profile) | ✅ Working | Good |
| Memory/Knowledge entries (CRUD, vector search, categories) | ✅ Working | Good |
| Repository indexing (hash-based incremental, code chunking) | ✅ Working | Functional |
| Knowledge graph (nodes, edges, graph build/query) | ✅ Working | Functional |
| Unified search (code + memory merge, graph enrichment) | ✅ Working | Functional |
| Agent system (planner, executor, runs, steps, feedback) | ✅ Working | Structural only |
| System metrics (CPU, RAM, GPU, processes, logs) | ✅ Working | Good |
| Notifications (CRUD, read status) | ✅ Working | Basic |
| WebSocket system metrics push | ✅ Working | Good |
| Dashboard with metrics, processes, activity, insights | ✅ Working | Good |
| All pages wrapped in DashboardShell | ✅ Working | Good |
| Warmer dark theme with glass panels | ✅ Working | Good |
| Command palette (Cmd+K) | ✅ Working | Good |

---

## Critical Gaps Identified

### Gap 1: No LLM Integration (CRITICAL)

**Impact:** Without an LLM, the entire intelligence layer is hollow.

- Agent executor falls back to keyword routing (not real reasoning)
- Search "AI Answer" concatenates titles (not real synthesis)
- No conversational chat experience possible
- Context builder can't generate insights
- No code explanation, summarization, or generation

**Current state:** `LLMProvider` is an abstract interface with zero implementations.

**What's needed:**
- llama.cpp (local CPU/GPU inference)
- Ollama integration (model management + inference)
- Model download, management, and selection
- Hardware-aware model recommendations
- Quantization selection (Q4_K_M, Q5_K_M, Q8_0, etc.)

### Gap 2: No Local Model Management

**Impact:** Users can't discover, download, or manage local LLMs.

- No model browser or marketplace
- No hardware detection for recommendations
- No download queue with pause/resume
- No model capability descriptions (coding, reasoning, vision, etc.)
- No quantization selection UI
- No model benchmarking or compatibility checks

### Gap 3: Naive Indexing Strategy

**Impact:** Wasted resources indexing irrelevant files, no real-time sync.

- Indexes ALL files in a repo (including node_modules, .git, build artifacts)
- No exclusion rules for caches, temp files, binaries, virtual environments
- No real-time file watching or automatic re-indexing
- No prioritization (indexes everything equally)
- No user-controlled indexing locations
- Rust file watcher exists but isn't integrated

### Gap 4: Limited Retrieval Quality

**Impact:** Search results may miss relevant content or return noise.

- No hybrid retrieval (vector + keyword + graph combined)
- No reranking of results
- No context compression (passing full documents to LLM)
- No multi-level retrieval (file → chunk → symbol)
- Graph enrichment is basic (calls/imports only)
- No memory integration in retrieval (code + memory should cross-pollinate)

### Gap 5: No Agent Observability

**Impact:** Can't monitor agent performance, tool success, or resource usage.

- No dashboards for agent performance metrics
- No token usage tracking
- No tool success/failure rates
- No workflow completion metrics
- No retrieval quality metrics
- No model performance tracking
- No indexing health monitoring
- No synchronization status display

### Gap 6: Frontend Architecture Issues

**Impact:** Inconsistent patterns, potential auth bypass, dead weight.

- Two parallel API client systems (monolithic `cortexApi.ts` + modular `src/shared/api/`)
- No Next.js middleware for auth (client-side useEffect redirect = flash of protected content)
- Three.js installed but unused (~2MB dead weight)
- Notifications panel is a TODO stub
- `agentApi.list()` return type mismatch

### Gap 7: Rust Crates Not Integrated

**Impact:** Code intelligence and file watching are orphaned.

- `cortex-code-intel`: Only Python parsing, not called from Python backend
- `cortex-file-watcher`: Prints to stdout, no IPC, no integration
- No Cargo build in CI

---

## Roadmap Restructuring Rationale

### Why the original 6-phase plan needs restructuring:

1. **Phase 4 (Intelligence) assumes LLM exists but never implements it.** The ContextBuilder and ConversationMemory are useless without a brain. LLM integration must come first.

2. **No phase addresses local model management.** For a local-first AI OS, the ability to discover, download, and manage local models is foundational. Users need to understand which models are best for coding, reasoning, agents, vision, embeddings, RAG, tool use, or general chat.

3. **Indexing needs intelligence before Desktop.** Smart indexing with exclusion rules, real-time sync, and prioritization should happen before desktop packaging, because desktop users will have much larger file systems to index.

4. **Observability is scattered.** No dedicated phase for monitoring agent performance, retrieval quality, or system health.

5. **Desktop (Phase 5) is premature.** The web app needs LLM integration, smart indexing, and conversation memory before desktop packaging makes sense. Desktop without a brain is just a wrapped web app.

6. **Phase 6 (Learning) is too broad.** Pattern recognition, correction tracking, long-term memory, and proactive assistance should be split into focused phases.

### New 10-phase structure:

| Phase | Name | Rationale |
|-------|------|-----------|
| 4A | LLM Integration & Local Models | Without a brain, nothing else matters |
| 4B | Smart Indexing & Retrieval | Understanding the machine is the core value |
| 5 | Conversation & Context | Persistent memory makes Cortex a companion |
| 6 | Agent Intelligence | Multi-step reasoning, tool chaining, workflows |
| 7 | Desktop Preparation | Service boundaries, filesystem, native access |
| 8 | Learning Loop | Pattern recognition, corrections, proactive assist |
| 9 | Observability & Monitoring | See what's happening, measure quality |
| 10 | Production Hardening | Reliability, security, performance, packaging |

---

## Frontend Improvement Opportunities

### Design System Enhancements
- Unify the two API client systems (monolithic + modular)
- Add Next.js middleware for auth (prevent flash of protected content)
- Remove Three.js dead weight
- Complete notifications panel
- Add loading states and skeleton screens consistently
- Improve error states and empty states
- Add keyboard shortcuts for power users
- Command palette: add actions beyond navigation (create memory, run agent, etc.)

### New Frontend Features
- Local model browser and manager UI
- Model download progress with pause/resume
- Hardware-aware model recommendations
- Agent performance dashboard
- Indexing health dashboard
- Real-time sync status indicator
- System health overview
- Conversation history with search
- Context panel showing what the AI knows

---

*This audit was conducted on 2026-06-20 after completing Phases 0-A through 3 plus UI Refactor.*
