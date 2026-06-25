# CORTEX V1: "The Brain Works"

**Version:** 1
**Date:** 2026-06-25
**Status:** Planned

---

## 1. Goals

V1 makes CORTEX production-ready and daily-drivable. The system starts reliably, the agent works correctly, the CLI manages the daemon, and every existing capability functions without fragility.

This is not a feature release. This is the version where CORTEX stops being a tech demo and starts being a tool you use every day.

### Primary Goals

1. **Daemon lifecycle** — `cortexd start|stop|status` works. PID management. Health checks. Graceful shutdown.
2. **Agent loop rebuilt** — Single streaming agent replaces broken Planner→Executor. Tools have schemas. Context compacts. Stalls are detected. Runs persist.
3. **CLI functional** — All 15 command stubs become real commands. Daemon management, agent execution, search, config via CLI.
4. **Existing capabilities preserved** — Everything that works today (auth, vault, search, memory, models, frontend) continues working with zero regression.

### Non-Goals (Explicitly Deferred)

- Event bus (V2)
- Service abstraction / swappable providers (V2)
- MCP integration (V2)
- Plugin system (V2)
- Memory consolidation pipeline (V2)
- Desktop shell / Tauri (V3)
- Embedded databases (V3)
- Task scheduler / automation (V4)
- Daily productivity tools (V5)
- Ecosystem features (V6)

---

## 2. Scope

### 2.1 Daemon Foundation

| Component | What Exists | What V1 Builds |
|-----------|-------------|----------------|
| Entrypoint | `uvicorn` launch via `make dev` | `cortexd` CLI entrypoint with lifecycle |
| Lifecycle | None | start → run → health → shutdown → crash recovery |
| PID file | None | PID lock file, orphan detection, stale PID cleanup |
| Health checks | GET /api/v1/health/live | Periodic self-check, dependency probing (DB, Redis, Qdrant) |
| Sleep/Wake | None | Sleep after configurable idle. Wake on trigger (API call, CLI command). |
| Graceful shutdown | None | Drain in-flight requests, flush state, close connections |

**Scope boundary:** The daemon wraps existing FastAPI. No new services. No new middleware. The existing backend IS the daemon kernel.

### 2.2 Agent System Rebuild

| Component | What Exists | What V1 Builds |
|-----------|-------------|----------------|
| Architecture | Planner→Executor (2 agents, 2 LLM calls) | Single streaming agent loop (1 LLM call, async generator) |
| Tools | 5 tools, no schemas, no type hints | @tool decorator with auto-generated JSON Schema |
| Tool count | 5 (exec_command, git_log, git_diff, web_fetch, ask_user) | 15+ (keep existing 5, add write_file, read_file, list_files, search_memory, search_graph, search_web, search_index, plan, ask_clarification, summarize) |
| Tool policy | HMAC approval tokens | Per-turn composition: allow/deny/ask per tool |
| Tool security | SSRF, path traversal, blocked commands | Same + broader pattern blocking, allowlist approach |
| Context management | Simple truncation | Auto-compaction at 85% with Goal/Done/State/Pending summary |
| Token estimation | `len(text) // 4` | tiktoken (cl100k_base) with 10% safety margin |
| Prompt security | None | UNTRUSTED_SOURCE_DATA markers on all external content |
| Intent classification | None | 4-way: casual (fast path, no LLM), admin, agent, continuation |
| Loop control | Hard cutoff at 10 iterations | Stall detection (repeated identical calls) + configurable max (25) |
| Completion verification | None | Fresh-context LLM subagent verifier |
| Approval state | In-memory `_approved_tools` set (lost on restart) | Database-backed, survives restart |
| Background execution | asyncio.Queue (lost on restart) | Server-side persistence, PID tracking, orphan detection |

**Scope boundary:** The agent loop is rebuilt behind a feature flag. Old path (Planner→Executor) remains available during transition. Both paths tested against all 341 existing tests.

### 2.3 CLI Completion

| Command | What Exists | What V1 Builds |
|---------|-------------|----------------|
| `cortex daemon start/stop/status/logs` | Stub | Full daemon lifecycle management |
| `cortex agent run/chat/list/cancel` | Stub | Agent execution via daemon API |
| `cortex search <query>` | Stub | Unified search via daemon API |
| `cortex index run/status` | Stub | Index management via daemon API |
| `cortex config set/get/list` | Stub | Configuration management |
| `cortex vault lock/unlock/status` | Stub | Vault management via daemon API |
| `cortex memory remember/recall/forget/status` | New | Memory management via daemon API |

**Scope boundary:** CLI connects to daemon via HTTP (existing API). No Unix socket yet (V3). JSON output by default, human-readable when attached to terminal.

### 2.4 Documentation Cleanup

| Document | Issue | V1 Fix |
|----------|-------|--------|
| CLAUDE.md | References `middleware/` directory that doesn't exist | Update to reflect actual `core/` structure |
| CLAUDE.md | "486+ tests" | Update to verified count (341+) |
| CLAUDE.md | Architecture diagram outdated | Update to match actual structure |
| ROADMAP.md | Two competing phase systems | Single numbering aligned with versions |
| All docs | Inconsistent test counts | Single verified number |

### 2.5 Bug Fixes (From Council Discovery)

| Bug | Source | V1 Fix |
|-----|--------|--------|
| `write_file` in `_REQUIRES_APPROVAL` but not in TOOL_REGISTRY (dead code) | contradictions.md 3.1 | Kept as ExecutorAgent._write_file_tool() method. Not in TOOL_REGISTRY — addressed by V1 Phase 3 cleanup |
| SSRF bypass via `exec_command` + `curl` | contradictions.md 3.2 | Block `curl`/`wget` in exec_command or add output filtering |
| Command blocking bypass (`pip3 install`, `python -m pip install`) | contradictions.md 3.3 | Broader pattern blocking or allowlist approach |
| Embedding sync/async mismatch (`asyncio.run()` in async context) | contradictions.md 3.4 | Use `loop.run_in_executor()` when event loop exists |
| Token estimation inaccuracy (`len(text) // 4`) | contradictions.md 3.5 | tiktoken with 10% safety margin |

---

## 3. Success Criteria

### Functional

| Criterion | Measure |
|-----------|---------|
| Daemon lifecycle | `cortexd start` launches daemon, `cortexd stop` shuts down gracefully, `cortexd status` reports state |
| Agent works | Single streaming agent handles 90%+ of user messages without errors |
| Compaction works | Conversations >85% of context window auto-compact without data loss |
| CLI commands | All 15 commands return correct results, proper exit codes, JSON output |
| Tool schemas | LLM receives JSON Schema for every tool, function-calling improves |
| Intent classification | Casual messages ("hi", "thanks") skip full agent loop |
| Stall detection | Agent stuck in repeated calls is forced to answer within 3 attempts |
| Prompt security | External content (retrieval, files, web) enters prompts with UNTRUSTED_SOURCE_DATA markers |
| Zero regression | All 341+ existing tests pass. Web UI unchanged. All API endpoints unchanged. |

### Quality

| Criterion | Measure |
|-----------|---------|
| Test count | 341+ (no reduction) + new agent/CLI tests |
| Lint | `make lint` passes cleanly |
| Build | `make build` succeeds for both backend and frontend |
| Documentation | All docs reflect actual codebase state |
| No feature flags left on | Agent loop behind feature flag during rollout; flag removed after verification |

---

## 4. User Impact

### Before V1

- User starts CORTEX via `make dev` or `start.sh` (manual process management)
- Agent system is broken (Planner→Executor pattern)
- CLI is 15 stubs, zero functionality
- Long conversations lose context
- Agent gets stuck in loops
- No daemon lifecycle management
- Developer experience: fragile, requires babysitting

### After V1

- User starts CORTEX via `cortexd start` (single command, daemon manages itself)
- Agent works reliably: streaming responses, 15+ tools with schemas, compaction, security
- CLI provides full daemon management and agent interaction
- Long conversations auto-compact at 85%
- Stalls are detected and resolved automatically
- System runs in background, health-checked, crash-recovered
- Developer experience: solid, reliable, daily-drivable

### Who Benefits

| User | How |
|------|-----|
| Primary user (you) | CORTEX becomes a daily tool, not a project to babysit |
| AI agents (Claude Code) | Agent system works correctly, tools have schemas, compaction prevents context loss |
| Future contributors | Clean codebase, no dead code, accurate documentation |

---

## 5. Architecture Impact

### What Changes

```
BEFORE:
  FastAPI app → manual startup → browser-only interaction
  Planner → Executor (2 LLM calls, broken)
  5 tools, no schemas, HMAC approval
  No compaction, no security markers, no stall detection
  CLI stubs (15 empty files)

AFTER:
  cortexd daemon → lifecycle management → multiple surfaces
  Single streaming agent loop (1 LLM call)
  15+ tools with @tool decorator + JSON Schema
  Auto-compaction at 85%, UNTRUSTED_SOURCE_DATA, stall detection
  CLI commands (15 working commands)
```

### What Stays

| Component | Why It Stays |
|-----------|-------------|
| FastAPI backend | The daemon kernel. All routes, all services preserved. |
| PostgreSQL 16 | Best-in-class database. No reason to change. |
| Two-password auth | Strong security model. |
| Hybrid retrieval (RRF + MMR) | Best-in-class retrieval. |
| Next.js 15 frontend | 21,800 lines of production code. |
| 341+ tests | The safety net. |
| Docker Compose | Existing infrastructure. |
| All existing services | Unchanged business logic. |

### What Gets Replaced

| Component | Why |
|-----------|-----|
| Planner→Executor | Broken two-agent pattern. Single loop is better. |
| TOOL_REGISTRY dict | No schemas. @tool decorator with auto-schema. |
| HMAC approval tokens | Per-turn policy composition is more flexible. |
| `len(text) // 4` | tiktoken is accurate. |
| asyncio.Queue background | Server-side persistence needed. |

### What Gets Added

| Component | Purpose |
|-----------|---------|
| `cortexd` entrypoint | Daemon lifecycle management |
| Agent streaming loop | Replaces Planner→Executor |
| @tool decorator system | Tool registration with auto-schema |
| Context compactor | Auto-compaction at 85% |
| Intent classifier | 4-way routing before agent loop |
| Stall detector | Loop-breaker for repeated calls |
| Completion verifier | Fresh-context LLM subagent |
| Tool policy engine | Per-turn allow/deny/ask composition |
| tiktoken integration | Accurate token counting |

---

## 6. UX Impact

### Surfaces

| Surface | V1 Change |
|---------|-----------|
| Web UI | No change. Existing functionality preserved. |
| CLI | Goes from zero to fully functional daemon management |
| API | No change. All existing endpoints preserved. New daemon lifecycle endpoints added. |
| Desktop shell | Not in V1 (V3) |
| Command palette | Not in V1 (V3) |

### Interaction Model

| Before V1 | After V1 |
|-----------|----------|
| `make dev` → open browser → use web UI | `cortexd start` → use CLI or web UI |
| Agent crashes silently | Agent stalls detected, forced to answer |
| Long conversations lose context | Auto-compaction preserves context |
| CLI does nothing | CLI manages daemon, runs agents, searches |
| No way to check system health | `cortexd status` shows health of all services |

---

## 7. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Agent loop replacement breaks existing agent tests | Medium | High | Feature flag. Old path available. Test against all 341 tests. |
| Compaction quality affects agent performance | Medium | High | Use cheaper model for compaction. Log compaction events. Allow manual override. |
| CLI commands don't match API contracts | Low | Medium | CLI tests against daemon API. JSON output verified. |
| Daemon lifecycle has edge cases (crash during startup, orphan processes) | Medium | Medium | PID file + stale PID detection. Crash recovery journal. Integration tests. |
| tiktoken adds dependency | Low | Low | Optional. Falls back to character estimation if unavailable. |
| Documentation cleanup breaks cross-references | Low | Low | Verify all links after changes. |

---

## 8. Exit Criteria (V1 Complete When)

- [ ] `cortexd start|stop|status|logs` works
- [ ] Daemon health checks report status of DB, Redis, Qdrant
- [ ] Daemon sleep/wake works
- [ ] Single streaming agent loop handles all user messages
- [ ] 15+ tools registered with @tool decorator + JSON Schema
- [ ] Auto-compaction triggers at 85% of context window
- [ ] UNTRUSTED_SOURCE_DATA markers on external content
- [ ] Intent classification routes casual messages to fast path
- [ ] Stall detection forces answer after repeated identical calls
- [ ] Completion verifier checks task completion
- [ ] All 15 CLI commands return correct results + JSON output
- [ ] All 341+ existing tests pass
- [ ] New agent/CLI tests pass (target: 50+ new tests)
- [ ] Documentation reflects actual codebase state
- [ ] All 5 bugs from council discovery fixed
- [ ] `make lint` + `make format` clean
- [ ] `make build` succeeds (backend + frontend)
