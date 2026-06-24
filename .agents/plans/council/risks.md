# CORTEX Risks — Evidence-Based

**Date:** 2026-06-25
**Purpose:** Technical and strategic risks that could derail Cortex.

---

## 1. Agent Loop Replacement — Breakage Cascade (Critical)

**Risk:** Replacing Planner→Executor with unified agent loop breaks the agent system, which is the central nervous system of Cortex. Every agent-related feature depends on it.

**Evidence:**
- run_manager.py orchestrates plan→execute→record — tightly coupled to two-agent pattern
- background.py depends on executor's SSE streaming
- Agent API endpoints assume plan+execute separation
- Frontend agent module renders plan steps and execution results separately
- 14 agent workflow tests depend on current architecture

**Impact:** If the replacement breaks, no agent functionality works. Chat, background tasks, agent runs — all broken.

**Mitigation:**
- Implement behind feature flag (old path + new path)
- Keep planner.py as fallback during transition
- Test against all 341 existing tests
- Gradual migration: new loop handles new requests, old loop handles existing runs

---

## 2. Vector Store Abstraction — Search Regression (High)

**Risk:** Abstracting Qdrant behind a Protocol could regress search quality or performance.

**Evidence:**
- hybrid_retrieval.py directly uses Qdrant client
- 11 vector_db tests verify Qdrant-specific behavior
- Payload filtering uses Qdrant-specific syntax
- Collection management is Qdrant-specific

**Impact:** Search quality regression is user-visible and damages trust.

**Mitigation:**
- Phase 2 creates Protocol + Qdrant implementation only
- Desktop implementation (turbovec) in Phase 6
- No behavior change in Phase 2 — same Qdrant, same queries
- Search quality regression tests before and after

---

## 3. Context Compaction Quality — Agent Degradation (High)

**Risk:** Poor compaction destroys context that the agent needs, causing it to repeat work, lose track of goals, or make incorrect decisions.

**Evidence:**
- Cortex has no compaction — no baseline to compare against
- Odysseus's compaction uses LLM calls — quality depends on LLM capability
- Token estimation is rough (`len(text) // 4`) — compaction timing could be wrong
- No structured summary format exists in Cortex

**Impact:** Agent makes mistakes in long conversations, loses user context.

**Mitigation:**
- Use cheaper/faster model for compaction (not the main agent model)
- Log compaction events for debugging
- Allow manual override ("remind me about X")
- Start with simple truncation, add structured summary in second pass

---

## 4. Scope Creep — Daily Productivity Overload (High)

**Risk:** Adding email, calendar, tasks, notes, documents, contacts, research, skills, webhooks, task scheduler simultaneously overwhelms the codebase.

**Evidence:**
- ~15,000 lines of Odysseus daily productivity code to adapt
- 10 new subsystems, 12+ new models, 13+ new migrations
- Each subsystem has its own API routes, services, and database tables
- Cortex currently has 26 services — adding 10 more is a 40% increase

**Impact:** Quality degrades across all subsystems. Testing becomes impossible. Maintenance burden doubles.

**Mitigation:**
- Strict phase ordering: agent intelligence first (Phase 2-3), daily tools foundation (Phase 4), full daily tools (Phase 5+)
- Each subsystem gets its own spec → plan → implement cycle
- Never implement more than 2 new subsystems simultaneously
- User explicitly requested all daily tools — but sequencing matters

---

## 5. MCP Integration Complexity (Medium)

**Risk:** MCP protocol is still evolving. Implementing MCP client + server + lifecycle management is complex and could become a maintenance burden.

**Evidence:**
- Odysseus has McpManager (complex lifecycle)
- Continue has MCPManagerSingleton (simpler)
- MCP spec has stdio + SSE transports — both need implementation
- MCP ecosystem is fragmented (different server implementations)

**Impact:** MCP integration could become a time sink with limited return if the ecosystem doesn't stabilize.

**Mitigation:**
- Start with MCP client only (connect to external servers)
- Defer MCP server (expose Cortex tools) to later
- Use Strands's MCPTool wrapper pattern (simpler than full manager)
- Monitor MCP spec stability before investing heavily

---

## 6. Token Estimation Inaccuracy (Medium)

**Risk:** `len(text) // 4` is a rough approximation. Compaction timing, context budget, and token limits will be wrong.

**Evidence:**
- conversation_service.py uses character-based estimation
- Different tokenizers produce different counts (tiktoken vs cl100k vs o200k)
- Embedding models have their own token limits
- LLM context windows are token-based, not character-based

**Impact:** Context overflow (LLM truncation) or waste (underutilized context window).

**Mitigation:**
- Install tiktoken for accurate counting
- Use tiktoken in compaction threshold calculation
- Add token count to API responses for debugging
- Budget 10% safety margin on all token calculations

---

## 7. Frontend Duplication Divergence (Medium)

**Risk:** Two API client layers (cortexApi.ts 536 lines + modular api/ 900 lines) could diverge, causing inconsistent behavior.

**Evidence:**
- cortexApi.ts is used by some pages, modular api/ by others
- Both implement CSRF handling independently
- Both implement auto-refresh independently
- No shared base between them

**Impact:** Different pages behave differently for same operations. Bugs fixed in one client not fixed in the other.

**Mitigation:**
- Deprecate cortexApi.ts — migrate all consumers to modular api/
- Add deprecation warning to cortexApi.ts
- Consolidate CSRF and auto-refresh into shared client.ts
- Timeline: complete before adding new API consumers

---

## 8. Test Coverage Gaps — Regression Risk (Medium)

**Risk:** Frontend (10/48 files tested), CLI (0/15 tested), Rust crates (0 tested) could regress silently.

**Evidence:**
- Only Button has UI component tests
- No CLI tests exist
- No Rust tests exist
- 4 frontend pages lack test files

**Impact:** Regressions in untested areas discovered only by users.

**Mitigation:**
- Prioritize tests for new subsystems (agent loop, compaction, tools)
- Add CLI tests as commands are implemented
- Add integration tests for frontend API client layer
- Rust crates are scaffolding — low priority for testing

---

## 9. Documentation Drift (Low)

**Risk:** CLAUDE.md references middleware/ directory that doesn't exist. ROADMAP.md phases don't match actual implementation state. Docs diverge from code.

**Evidence:**
- CLAUDE.md line ~30: `├── middleware/` — no such directory
- ROADMAP.md says Phase 6.5 complete — unclear what that means
- Architecture docs reference patterns that may not match current code

**Impact:** New developers (human or AI) get confused by inaccurate docs.

**Mitigation:**
- Audit all documentation against current codebase
- Fix CLAUDE.md middleware reference
- Update ROADMAP.md to match actual state
- Add documentation freshness checks to /project:health

---

## 10. Schema Debt Accumulation (Low)

**Risk:** model_variants has 4 duplicate columns overlapping with quantizations. More debt could accumulate as new models are added.

**Evidence:**
- Migration c00000000005 documents the duplication
- No cleanup migration has been created
- New models (ScheduledTask, EmailAccount, etc.) will add more tables

**Impact:** Data inconsistency, confusion about which column to use.

**Mitigation:**
- Create cleanup migration for model_variants before adding new models
- Document schema debt in DATABASE.md
- Add schema review to /project:architecture

---

## 11. Phase 2 Bottleneck — All Workstreams Blocked (Strategic)

**Risk:** Phase 2 (Service Abstraction) is the single critical bottleneck. All 4 workstreams (Memory, Indexing, Platform, Agent) depend on it. Delay cascades everywhere.

**Evidence:**
- Phase impact analysis shows: MI-1, II-1, PI-1, AI-1 all depend on Phase 2
- Phase 2 has 8 implementation items (provider abstraction, tool system, agent loop, compaction, security, plugins, config)
- Phase 2 is the most complex phase (new abstractions + refactoring)

**Impact:** Every week Phase 2 slips delays all workstreams by a week.

**Mitigation:**
- Start Phase 2 immediately after daemon foundation
- Break Phase 2 into smaller deliverables (provider Protocol first, then tool system, then agent loop)
- Parallelize independent items (compaction + security can run in parallel with provider abstraction)
- Set hard deadline for Phase 2 completion

---

## Summary: Risk Matrix

| Risk | Likelihood | Impact | Severity | Mitigation Owner |
|------|-----------|--------|----------|-----------------|
| Agent loop breakage | High | Critical | **Critical** | Implementation plan |
| Vector store regression | Medium | High | **High** | Phase 2 design |
| Compaction quality | Medium | High | **High** | Implementation plan |
| Scope creep (daily tools) | High | High | **High** | Phase ordering |
| MCP complexity | Medium | Medium | **Medium** | Implementation plan |
| Token estimation | High | Medium | **Medium** | tiktoken adoption |
| Frontend duplication | High | Medium | **Medium** | Migration plan |
| Test coverage gaps | Medium | Medium | **Medium** | Test priority |
| Documentation drift | High | Low | **Low** | /project:health |
| Schema debt | Low | Low | **Low** | Cleanup migration |
| Phase 2 bottleneck | High | High | **High** | Phase decomposition |
