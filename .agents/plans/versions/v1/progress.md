# CORTEX V1: "The Brain Works" — Progress

**Version:** 1
**Started:** 2026-06-25
**Target:** —

---

## Progress Tracker

| Phase | Component | Status | Notes |
|-------|-----------|--------|-------|
| Phase 1 | Daemon lifecycle | ✅ Complete | cortexd start/stop/status/logs |
| Phase 1 | PID management | ✅ Complete | PID file, stale detection, orphan cleanup |
| Phase 1 | Health checks | ✅ Complete | DB, Redis, Qdrant probing |
| Phase 1 | Graceful shutdown | ✅ Complete | Signal handlers, drain in-flight |
| Phase 1 | Sleep/wake | ✅ Complete | Idle detection, wake triggers |
| Phase 2 | Agent loop rebuild | ✅ Complete | Single async generator, max 25 iter, stall detection |
| Phase 2 | @tool decorator | ✅ Complete | @tool decorator, ToolRegistry, schema generation |
| Phase 2 | 15+ tools | 🔄 In progress | 5 existing tools ported to @tool decorator |
| Phase 2 | Tool policy | ✅ Complete | Per-turn allow/deny/ask composition |
| Phase 2 | Tool security | ✅ Complete | Enhanced SSRF, path traversal, command blocking |
| Phase 2 | Context compaction | ✅ Complete | Auto at 85%, Goal/Done/State/Pending summary |
| Phase 2 | Prompt security | ⬜ Not started | UNTRUSTED_SOURCE_DATA markers not yet implemented |
| Phase 2 | Intent classification | ✅ Complete | casual/admin/agent/continuation classifier |
| Phase 2 | Stall detection | ✅ Complete | Repeated identical calls → force answer |
| Phase 2 | Completion verifier | ✅ Complete | Fresh-context LLM subagent |
| Phase 2 | tiktoken | ⬜ Not started | Not yet integrated |
| Phase 2 | Run persistence | ⬜ Not started | Database-backed run store not yet implemented |
| Phase 2 | Feature flag | ✅ Complete | CORTEX_NEW_AGENT_LOOP in settings |
| Phase 3 | CLI commands (15) | ⬜ Not started | |
| Phase 3 | Bug fixes (5) | ⬜ Not started | |
| Phase 3 | Documentation cleanup | ⬜ Not started | |
| **V1 Total** | **20 components** | **🟡 13/20** | |

---

## Commit Log

- `c32b1f6` feat(daemon): V1 Phase-1 daemon foundation — PID mgmt, health checks, lifecycle, CLI
- `9348699` feat(agents): V1 Phase-2 tool infrastructure — @tool decorator, schemas, registry, policy, security
- `21d5d58` chore: remove legacy tools.py (replaced by tool_defs.py + tools/ package)
