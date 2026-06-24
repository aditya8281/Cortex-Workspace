# CORTEX Contradictions — Evidence-Based

**Date:** 2026-06-25
**Purpose:** Places where Cortex's documentation, code, and plans contradict each other.

---

## 1. Documentation vs Code Contradictions

### 1.1 Middleware Directory
- **CLAUDE.md says:** `├── middleware/ # CORS, rate limiting, CSRF, request logging`
- **Code has:** No `middleware/` directory. All middleware lives in `core/` files: `core/middleware.py`, `core/csrf.py`, `core/rate_limit.py`, `core/https_redirect.py`.
- **Impact:** New developers (human or AI) look for a directory that doesn't exist.
- **Resolution:** Either move files to `middleware/` or update CLAUDE.md.

### 1.2 Tool Count
- **CLAUDE.md says:** "5 tools with no parameter schemas" (in the agent section summary).
- **tools.py has:** 5 tools registered in TOOL_REGISTRY: `exec_command`, `git_log`, `git_diff`, `web_fetch`, `ask_user`.
- **But also:** `write_file` exists as a method on ExecutorAgent and is in `_REQUIRES_APPROVAL`, but is NOT in TOOL_REGISTRY. `_REQUIRES_APPROVAL` includes `write_file` but the approval check is dead code for that tool since it's never registered.
- **Impact:** Confusion about actual tool count and which tools require approval.
- **Resolution:** Either register `write_file` in TOOL_REGISTRY or remove it from `_REQUIRES_APPROVAL`.

### 1.3 CLAUDE.md Architecture Diagram vs Actual Structure
- **CLAUDE.md says:** Backend structure includes `├── middleware/` and implies `services/` has specific subdirectories.
- **Actual structure:** No `middleware/` directory. `services/` has `llm/` subdirectory but no other subdirectories matching the diagram.
- **Impact:** Architecture diagram doesn't match reality.
- **Resolution:** Update diagram to match actual structure.

### 1.4 DATABASE.md Table Count
- **DATABASE.md says:** "33 tables" in the header.
- **DATABASE.md also says:** Lists tables with migration prefixes. Count of listed tables should be verified against actual models.
- **Code has:** 33 SQLAlchemy model classes across 17 model files.
- **Impact:** Minor — count appears accurate but should be verified.
- **Resolution:** Verify count matches.

### 1.5 ROADMAP.md Phase Status
- **ROADMAP.md says:** Phases 1-3 complete, 4A-6 partial, 6.5 complete.
- **What "complete" means:** Unclear. Phase 1 (Foundation) — is the daemon foundation done? The desktop-first reorientation plan defines Phase 1 as "Daemon Foundation" which is NOT implemented yet.
- **Contradiction:** ROADMAP.md's Phase 1-3 completion refers to the original web-first roadmap. The desktop-first reorientation has a DIFFERENT Phase 1-7 numbering. These two phase systems overlap and confuse.
- **Impact:** Anyone reading ROADMAP.md thinks Phase 1-3 are done. The daemon-first plan says Phase 1 (Daemon Foundation) hasn't started.
- **Resolution:** Clarify which phase system ROADMAP.md refers to. Add cross-reference to daemon-first plan.

---

## 2. Plan vs Plan Contradictions

### 2.1 Two Competing Phase Systems
- **ROADMAP.md:** 10 phases (1-6 complete/partial, 6.5 complete, 7-10 upcoming). Original web-first roadmap.
- **Desktop-First Reorientation:** 7 phases (Daemon Foundation → Web UI Transition). New daemon-centric roadmap.
- **Reference Repo Master Plan:** 4 tiers (Phase 2 → Phase 3 → Phase 4 → Phase 5+). Workstream-based.
- **Contradiction:** Three different phase numbering systems exist. Phase 2 in one plan ≠ Phase 2 in another.
- **Impact:** Confusing for anyone trying to understand what's next.
- **Resolution:** Establish single phase system. ROADMAP.md should reference the daemon-first plan as the authoritative roadmap.

### 2.2 "Phase 2" Means Different Things
- **Desktop-First Plan Phase 2:** Service Abstraction (2 tasks: Protocol definitions, Service Registry).
- **Master Plan Tier 1:** "Phase 2 — Service Abstraction" (8 items: provider abstraction, tool system, agent loop, compaction, security, plugins, config).
- **Reference Repo Phase Impact:** Phase 2 unblocks MI-1, II-1, PI-1, AI-1.
- **Contradiction:** The desktop-first plan's Phase 2 has 2 tasks. The master plan's Phase 2 has 8 items. These are not the same scope.
- **Impact:** Implementation planning is ambiguous — which Phase 2 scope is authoritative?
- **Resolution:** Merge the two Phase 2 scopes into one authoritative plan.

### 2.3 Agent System Replacement Timing
- **Desktop-First Plan:** Phase 2 is "Service Abstraction" — defines DatabaseProvider, VectorStoreProvider, CacheProvider. Agent system is NOT mentioned.
- **Master Plan:** Agent system rebuild (R5) is Priority 1 in "Critical — Do First."
- **Action Items:** AI-13 (Agent System Foundation) depends on "Daemon Phase 2 complete" and "AI-4 (provider abstraction)."
- **Contradiction:** The desktop-first plan doesn't mention agent system rebuild at all. The master plan says it's the highest priority. When does it actually happen?
- **Impact:** The most critical improvement (agent loop) has no clear home in any phase plan.
- **Resolution:** Add agent system rebuild to the daemon-first plan, likely as part of Phase 2 or a new Phase 2.5.

### 2.4 Memory Consolidation Timing
- **Master Plan:** M1 (Memory Consolidation Pipeline) is Priority 7 in "Critical — Do First."
- **Phase Impact Analysis:** MI-1 depends on Phase 2 (Service Abstraction).
- **Action Items:** AI-5 (MI-1) depends on "AI-3 spec approved, Daemon Phase 2 complete, AI-4 (needs abstracted LLM)."
- **Contradiction:** M1 is listed as "Critical — Do First" but has 3 dependencies. It can't actually start immediately.
- **Impact:** Misleading priority ordering.
- **Resolution:** Clarify that "Critical" means "critical importance" not "start immediately." Dependencies determine actual start time.

---

## 3. Code vs Code Contradictions

### 3.1 Tool Approval Dead Code
- **tools.py `_REQUIRES_APPROVAL`:** Includes `write_file`.
- **TOOL_REGISTRY:** Does NOT include `write_file`. Only includes: `exec_command`, `git_log`, `git_diff`, `web_fetch`, `ask_user`.
- **executor.py:** Has `write_file` as a method. Calls it directly, not through TOOL_REGISTRY.
- **Contradiction:** `_REQUIRES_APPROVAL` checks for `write_file` but the tool is never looked up in TOOL_REGISTRY. The approval check is dead code for `write_file`.
- **Impact:** `write_file` bypasses approval entirely because it's called as a method, not through the registry.
- **Resolution:** Either register `write_file` in TOOL_REGISTRY or remove from `_REQUIRES_APPROVAL`.

### 3.2 SSRF Protection Inconsistency
- **tools.py:** Has `_is_private_url()` for SSRF protection on `web_fetch`.
- **But:** `exec_command` can run `curl` or `wget` to internal URLs, bypassing the SSRF check.
- **Contradiction:** SSRF protection exists for one tool but can be bypassed via another tool.
- **Impact:** Security gap — agent can reach internal services via exec_command + curl.
- **Resolution:** Add URL filtering to exec_command output, or block curl/wget in exec_command.

### 3.3 Command Blocking Bypass
- **tools.py `BLOCKED_PATTERNS`:** Blocks `pip install`, `npm install`.
- **But:** `python -m pip install`, `pip3 install`, `npx pip install` are not blocked.
- **Contradiction:** Security controls can be trivially bypassed.
- **Impact:** Agent can install packages despite blocking rules.
- **Resolution:** Block broader patterns or use allowlist approach.

### 3.4 Embedding Service Sync/Async Mismatch
- **embedding_service.py:** Uses `ThreadPoolExecutor` + `asyncio.run()` to call synchronous embedding functions.
- **But:** If called from within an existing async context (e.g., arq worker), `asyncio.run()` will fail because there's already an event loop running.
- **Contradiction:** Embedding service works in sync contexts but may fail in async contexts.
- **Impact:** Potential runtime error in arq workers.
- **Resolution:** Use `loop.run_in_executor()` instead of `asyncio.run()` when event loop exists.

### 3.5 Token Estimation vs Actual Tokens
- **conversation_service.py:** Uses `len(text) // 4` for token estimation.
- **Compaction (proposed):** Will use token count to trigger at 85% of context window.
- **Contradiction:** If token estimation is wrong, compaction triggers at wrong time. `len("hello") // 4 = 1` but tiktoken produces 1 token for "hello". For Chinese text, `len("你好") // 4 = 0` but tiktoken produces 1-2 tokens.
- **Impact:** Compaction could trigger too early (wasting context) or too late (overflow).
- **Resolution:** Install tiktoken before implementing compaction.

---

## 4. Vision vs Implementation Contradictions

### 4.1 "Local-First" vs Docker Requirement
- **Vision (reorientation design):** "Local-first persistent intelligence layer. Runs on your machine."
- **Reality:** Requires Docker (PostgreSQL + Redis + Qdrant) to run. Docker is not "local-first" — it's "Docker-first."
- **Contradiction:** Vision says local-first, implementation requires containerization.
- **Impact:** Desktop mode can't exist until embedded alternatives are available.
- **Resolution:** Phase 2 (vector store abstraction) + Phase 6 (embedded databases) resolve this. But until then, the contradiction stands.

### 4.2 "Daemon-First" vs Current Architecture
- **Vision (reorientation design):** "Daemon-first, surface-second. Intelligence works without UI."
- **Reality:** Current architecture is web-first. FastAPI serves both API and frontend. No daemon concept exists. No PID management. No health monitoring. No sleep/wake.
- **Contradiction:** Vision says daemon-first, code is web-first.
- **Impact:** The entire daemon-first transition hasn't started.
- **Resolution:** Desktop-First Implementation Plan (1,898 lines) defines the path. But it hasn't been executed yet.

### 4.3 "CLI as Primary Interface" vs CLI Stubs
- **Vision (reorientation design):** "CLI as primary automation interface. Programmable surface."
- **Reality:** 15 CLI stubs, zero functionality. 158 lines total.
- **Contradiction:** Vision says CLI is primary, CLI doesn't work.
- **Impact:** No automation possible without the web UI.
- **Resolution:** CLI implementation (AD18) in Phase 4.

### 4.4 "Agent System" vs Agent Reality
- **CLAUDE.md says:** "Autonomous agents" as a core capability.
- **README.md says:** "Reasoning and agency" as a pillar.
- **Reality:** 5 tools, no schemas, no compaction, no security, max 10 iterations, Planner→Executor (the weakest agent model across all references).
- **Contradiction:** Marketing says "autonomous agents," code has a fragile prototype.
- **Impact:** User expectations don't match reality.
- **Resolution:** Agent system rebuild (R5) in Phase 2-3.

### 4.5 "486+ Tests" vs Actual Count
- **CLAUDE.md says:** "486+ tests (pytest + vitest)."
- **Actual count:** 341 test functions across 42 test files (backend only). Frontend tests not counted in this number.
- **Contradiction:** Documentation overstates test count.
- **Impact:** Misleading quality signal.
- **Resolution:** Update CLAUDE.md with accurate count. Run full count including frontend.

---

## 5. Cross-Reference Contradictions

### 5.1 Recommendation Priority vs Dependency Order
- **Master Plan:** Lists R5 (Agent System) as Priority 1, "Critical — Do First."
- **Dependencies:** R5 depends on Phase 2 (Service Abstraction). Phase 2 depends on Daemon Foundation (Phase 1).
- **Contradiction:** "Do First" doesn't mean "start first." It means "most important when you can start."
- **Impact:** Misleading urgency — someone might try to implement R5 before Phase 1-2.
- **Resolution:** Clarify that priority ranking is about importance, not sequence. Dependencies determine sequence.

### 5.2 Odysseus Daily Tools — DEFER vs ADOPT
- **Odysseus Integration Plan (original):** Listed email, calendar, tasks, notes, documents, contacts as DEFER.
- **User correction:** "all the tools like email tasks calender and all that daily tasks for user are also included from odysseus or not i need them too"
- **Master Plan:** All daily tools listed as ADOPT.
- **Contradiction:** Original plan deferred them, user required them, master plan adopted them. The classification changed mid-stream.
- **Impact:** Scope expanded significantly. Implementation sequencing unclear.
- **Resolution:** Master Plan is authoritative. All daily tools are ADOPT. Sequencing: foundation (Phase 4), full tools (Phase 5+).

### 5.3 Test Count Across Documents
- **CLAUDE.md:** "486+ tests"
- **This council (current-state.md):** 341 test functions
- **Gap analysis:** Mentions "486+ tests" in multiple places
- **Contradiction:** Three different numbers for the same metric.
- **Impact:** Inconsistent quality signal.
- **Resolution:** Run `pytest --co -q | tail -1` to get exact count. Update all docs.

---

## 6. Summary: Contradiction Severity

| # | Contradiction | Severity | Type |
|---|--------------|----------|------|
| 1 | Two competing phase systems | High | Plan vs Plan |
| 2 | "Phase 2" means different things | High | Plan vs Plan |
| 3 | Agent system replacement has no clear phase home | High | Plan vs Plan |
| 4 | "Local-first" vs Docker requirement | High | Vision vs Implementation |
| 5 | "Daemon-first" vs web-first architecture | High | Vision vs Implementation |
| 6 | "Autonomous agents" vs 5-tool prototype | High | Vision vs Implementation |
| 7 | "CLI as primary" vs 15 stubs | Medium | Vision vs Implementation |
| 8 | Tool approval dead code (write_file) | Medium | Code vs Code |
| 9 | SSRF bypass via exec_command + curl | Medium | Code vs Code |
| 10 | Command blocking bypass | Medium | Code vs Code |
| 11 | Embedding sync/async mismatch | Medium | Code vs Code |
| 12 | Token estimation inaccuracy | Medium | Code vs Code |
| 13 | Middleware directory missing | Low | Documentation vs Code |
| 14 | CLAUDE.md architecture diagram outdated | Low | Documentation vs Code |
| 15 | "486+ tests" vs 341 actual | Low | Documentation vs Code |
| 16 | Recommendation priority vs dependency order | Low | Plan vs Plan |
| 17 | Daily tools DEFER→ADOPT classification change | Low | Plan vs Plan |

---

## 7. Recommendations for Resolving Contradictions

### Immediate (Before Any Planning)
1. **Establish single phase system** — ROADMAP.md should reference daemon-first plan as authoritative. Remove or archive the old 10-phase system.
2. **Fix CLAUDE.md** — Remove middleware/ reference. Update test count. Update architecture diagram.
3. **Fix tool approval dead code** — Register write_file in TOOL_REGISTRY or remove from _REQUIRES_APPROVAL.
4. **Fix SSRF bypass** — Block curl/wget in exec_command or add output filtering.

### Before Phase 2
5. **Add agent system rebuild to phase plan** — It's the highest priority improvement but has no clear home in the daemon-first plan.
6. **Merge Phase 2 scopes** — Desktop-first Phase 2 (2 tasks) + Master Plan Phase 2 (8 items) = one authoritative Phase 2.
7. **Install tiktoken** — Required before compaction can be implemented accurately.

### Ongoing
8. **Run test count** — Get exact number. Update all docs.
9. **Add /project:health check** — Verify documentation matches code.
10. **Resolve "local-first" vs Docker** — Phase 2 (abstraction) + Phase 6 (embedded) resolve this. Until then, acknowledge the contradiction.
