# CORTEX Weaknesses — Evidence-Based

**Date:** 2026-06-25
**Purpose:** What Cortex does poorly, verified against reference repositories.

---

## 1. Agent System — Broken (Critical)

### 1.1 Planner→Executor Two-Agent Pattern
- **Reality:** planner.py (101 lines) creates a plan, executor.py (316 lines) executes it. Two separate LLM calls per user message.
- **Problem:** Adds latency and complexity without benefit. A single agent with good tools and a planning tool achieves the same result more reliably.
- **Evidence:** planner.py `_build_system_prompt()` appends context. executor.py calls `llm_manager.chat()` directly. No shared state between them.
- **Reference comparison:** Odysseus has a single 3,485-line streaming agent loop. Continue has a single tool-calling loop. Strands has a single execution loop with hooks.
- **Severity:** Critical — this is the weakest subsystem across all reference repos.

### 1.2 Tool System — 5 Tools, No Schemas
- **Reality:** 5 tools registered: exec_command, git_log, git_diff, web_fetch, ask_user. No parameter schemas on any tool.
- **Problem:** LLM function-calling is degraded without parameter schemas. LLM doesn't know what arguments tools accept.
- **Evidence:** tools.py — tools registered as `(name, description, handler)` tuples. No JSON Schema, no type hints in tool spec.
- **Reference comparison:** Odysseus has 60+ tools with full JSON Schema. Strands has @tool decorator with auto-schema. Continue has 18 tools with Tool type.
- **Severity:** Critical — can't extend tools without forking.

### 1.3 No Context Compaction
- **Reality:** No compaction exists. Simple truncation at fixed token budget.
- **Problem:** Long conversations lose context. No structured memory of what was accomplished.
- **Evidence:** executor.py has no compaction logic. conversation_service.py uses `len(text) // 4` for token estimation (rough approximation).
- **Reference comparison:** Odysseus auto-compacts at 85% with Goal/Done/State/Pending summary. Continue auto-compacts at 85%.
- **Severity:** Critical — Cortex is the ONLY repo without context compaction.

### 1.4 No Prompt Security
- **Reality:** No guards on external data entering prompts.
- **Problem:** Retrieved content, file contents, search results could inject prompts.
- **Evidence:** No UNTRUSTED_SOURCE_DATA markers anywhere in the codebase.
- **Reference comparison:** Odysseus wraps all external content with UNTRUSTED_SOURCE_DATA guards. Continue uses untrusted context markers.
- **Severity:** Critical — security vulnerability in agent mode.

### 1.5 Approval State In-Memory Only
- **Reality:** `_approved_tools` set in tools.py is a Python set. Lost on restart. Not shared across workers.
- **Problem:** Agent approval tokens disappear on restart. Can't share approval across multiple worker processes.
- **Evidence:** tools.py — `_approved_tools: set[str] = set()` at module level.
- **Reference comparison:** Odysseus has server-side run persistence with replay buffer.
- **Severity:** High — agent state is fragile.

### 1.6 Max Iterations Hardcoded
- **Reality:** `max_iterations = 10` in executor.py, not configurable per-agent.
- **Problem:** Can't tune per task complexity. 10 is arbitrary.
- **Evidence:** executor.py line ~20.
- **Reference comparison:** Odysseus uses 50 rounds with stall detection. Continue uses configurable limits with AbortController.
- **Severity:** Medium — functional but inflexible.

### 1.7 No Detached Runs
- **Reality:** Background agent execution uses in-memory asyncio.Queue. Tasks die with the process.
- **Problem:** Agent runs lost on restart. No persistence. No replay.
- **Evidence:** background.py (54 lines) — `subscribe(run_id)` returns an `asyncio.Queue`.
- **Reference comparison:** Odysseus keeps runs server-side with 180s grace period and replay buffer.
- **Severity:** High — daemon mode requires persistent runs.

### 1.8 No Intent Classification
- **Reality:** All user input goes through the same Planner→Executor path.
- **Problem:** Casual messages ("hi", "thanks") trigger full agent loop. Wasted LLM calls.
- **Evidence:** No classification logic anywhere in the agent system.
- **Reference comparison:** Odysseus classifies as casual/admin/agent/continuation before entering the loop. Casual messages get fast path.
- **Severity:** Medium — wastes resources on simple interactions.

### 1.9 No Loop-Breaker
- **Reality:** Hard cutoff at 10 iterations with "Task completed with maximum iterations".
- **Problem:** Can't detect stall patterns (repeated identical calls). Forces completion even when agent is stuck.
- **Evidence:** executor.py — loop exits at max_iterations.
- **Reference comparison:** Odysseus detects repeated identical calls and forces an answer.
- **Severity:** Medium — agent gets stuck on repetitive patterns.

---

## 2. CLI — Non-Functional (Critical)

- **Reality:** 15 Commander.js stubs, all logging "not yet implemented". 158 total lines.
- **Problem:** No command-line interface for daemon management, agent execution, or knowledge operations.
- **Evidence:** Every command file is 2-4 lines of `console.log("not yet implemented")`.
- **Reference comparison:** Continue has working CLI with headless + Ink TUI. Odysseus has 20+ specialized CLIs.
- **Severity:** Critical — no daemon management possible without CLI.

---

## 3. MCP Integration — Zero (Critical)

- **Reality:** No MCP client, no MCP server, no MCP tool wrapping.
- **Problem:** Can't interoperate with MCP ecosystem. Can't use external MCP tools. Can't expose Cortex tools to other MCP clients.
- **Evidence:** No MCP references anywhere in the codebase.
- **Reference comparison:** Odysseus has full MCP manager. Continue has MCPManagerSingleton. Strands has MCPTool wrapper. AnythingLLM has MCP hypervisor. All 3 Batch 4 repos have MCP — it's table stakes.
- **Severity:** Critical — MCP is the standard for agent tool interoperability.

---

## 4. Event Bus — None (Important)

- **Reality:** Direct SSE streaming, no pub/sub. Services are tightly coupled.
- **Problem:** Can't decouple services for daemon mode. Can't trigger tasks on events. Can't subscribe to system events.
- **Evidence:** background.py uses direct asyncio.Queue. No event publish/subscribe pattern.
- **Reference comparison:** Odysseus has event bus + task scheduler. Events trigger scheduled tasks.
- **Severity:** High — daemon mode requires decoupled services.

---

## 5. Provider Abstraction — Hardcoded (Important)

### 5.1 Embedding Service
- **Reality:** Three-tier hardcoded fallback: ONNX → Ollama → mock.
- **Problem:** Can't add new embedding providers without forking. Can't configure per-vault.
- **Evidence:** embedding_service.py (204 lines) — if/elif chain for provider selection.
- **Reference comparison:** Mem0 has 8 embedding providers via base class. LlamaIndex has 70+ backends. AnythingLLM has 15 embedding engines.
- **Severity:** High — limits extensibility.

### 5.2 Vector Store
- **Reality:** Qdrant-only. No abstraction layer.
- **Problem:** Can't swap vector store. Desktop mode requires Qdrant running.
- **Evidence:** core/vector_db.py (85 lines) — direct Qdrant client calls.
- **Reference comparison:** Mem0 has 24 swappable backends. LlamaIndex has 70+. AnythingLLM has 10.
- **Severity:** High — blocks desktop mode.

### 5.3 LLM Providers
- **Reality:** llm/manager.py supports Ollama, llama.cpp, mock. No formal interface.
- **Problem:** Adding new providers requires modifying manager.py directly.
- **Evidence:** llm/manager.py (369 lines) — routing logic embedded in manager.
- **Reference comparison:** Mem0 has 18 providers via LLMBase class. AnythingLLM has 35+ providers.
- **Severity:** Medium — functional but not extensible.

---

## 6. Plugin System — None (Important)

- **Reality:** No plugin architecture. No extension points. No way to add capabilities without modifying core code.
- **Problem:** Can't extend Cortex without forking. No community contribution path.
- **Evidence:** No plugin directory, no plugin interface, no plugin loading.
- **Reference comparison:** Open WebUI has 6-layer plugin system. AnythingLLM has 5-layer system. Strands has @tool decorator with dynamic loading.
- **Severity:** High — limits extensibility and community adoption.

---

## 7. Context Management — Primitive (Important)

### 7.1 No Composable Context Sources
- **Reality:** Monolithic RAG pipeline (vector + fulltext + graph). No way to independently tune or add context sources.
- **Problem:** Can't add new context sources (e.g., vault files, recent conversations) without modifying the pipeline.
- **Evidence:** hybrid_retrieval.py handles all three sources internally.
- **Reference comparison:** Continue has 20+ IContextProvider implementations. Each is independent, composable, and token-budgeted.
- **Severity:** High — limits context intelligence.

### 7.2 Token Estimation
- **Reality:** `len(text) // 4` in conversation_service.py. Rough character-based approximation.
- **Problem:** Overestimates or underestimates actual token count. Can cause context overflow or waste.
- **Evidence:** conversation_service.py line ~50.
- **Reference comparison:** Odysseus uses tiktoken for accurate counting. Continue uses proper tokenization.
- **Severity:** Medium — functional but inaccurate.

---

## 8. Frontend Duplication (Medium)

- **Reality:** Two API client layers exist: monolithic `cortexApi.ts` (536 lines) and modular `src/shared/api/` (900 lines). Both real.
- **Problem:** Confusing which to use. Potential for divergent behavior.
- **Evidence:** Both files import and use in different pages.
- **Severity:** Medium — technical debt, not blocking.

---

## 9. Middleware Location Mismatch (Low)

- **Reality:** CLAUDE.md says middleware lives in `backend/app/middleware/`. Actually lives in `core/` files.
- **Problem:** Documentation says one thing, code does another. Confusing for new developers.
- **Evidence:** CLAUDE.md line ~30: `├── middleware/ # CORS, rate limiting, CSRF, request logging`. No middleware/ directory exists.
- **Severity:** Low — documentation drift.

---

## 10. Schema Debt (Low)

- **Reality:** model_variants has 4 duplicate columns overlapping with quantizations: bits_per_param, quantization_bits, quality_multiplier, speed_multiplier.
- **Problem:** Data redundancy, potential inconsistency.
- **Evidence:** Migration c00000000005 documents this inline.
- **Severity:** Low — documented, not causing issues yet.

---

## 11. Rust Crates — Scaffolding Only (Low)

- **Reality:** cortex-code-intel (51 lines) only parses Python. cortex-file-watcher (32 lines) has no IPC.
- **Problem:** Code intelligence is minimal. File watcher isn't integrated.
- **Evidence:** JS/TS grammars are dependencies but not wired. File watcher prints to stdout with no structured output.
- **Severity:** Low — not blocking current functionality.

---

## 12. Test Coverage Gaps (Low)

- **Reality:** 341 tests, but thin coverage on: frontend shared UI (only Button tested), CLI (no tests), Rust crates (no tests), some frontend pages (4 untested).
- **Problem:** Regressions possible in untested areas.
- **Evidence:** Only 10 frontend test files out of 48 TS/TSX files.
- **Severity:** Low — backend is well-tested, frontend and CLI need more.

---

## Summary: Weakness Severity Ranking

| Rank | Weakness | Severity | Impact |
|------|----------|----------|--------|
| 1 | Agent system (broken loop, no tools schemas, no compaction, no security) | Critical | Core functionality degraded |
| 2 | CLI (15 stubs, zero functionality) | Critical | No daemon management |
| 3 | MCP integration (zero) | Critical | No ecosystem interop |
| 4 | Event bus (none) | Important | Can't decouple services |
| 5 | Provider abstraction (hardcoded) | Important | Can't extend providers |
| 6 | Plugin system (none) | Important | Can't extend without forking |
| 7 | Context management (primitive) | Important | Limited context intelligence |
| 8 | Frontend duplication (two API clients) | Medium | Technical debt |
| 9 | Middleware location mismatch | Low | Documentation drift |
| 10 | Schema debt (duplicate columns) | Low | Data redundancy |
| 11 | Rust crates (scaffolding) | Low | Minimal code intelligence |
| 12 | Test coverage gaps | Low | Regressions possible |
