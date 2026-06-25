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
| Phase 2 | Agent loop rebuild | ⬜ Not started | |
| Phase 2 | @tool decorator | ✅ Complete | @tool decorator, ToolRegistry, schema generation |
| Phase 2 | 15+ tools | ⬜ Not started | 5 existing tools ported to @tool decorator |
| Phase 2 | Tool policy | ✅ Complete | Per-turn allow/deny/ask composition |
| Phase 2 | Tool security | ✅ Complete | Enhanced SSRF, path traversal, command blocking |
| Phase 2 | Context compaction | ⬜ Not started | |
| Phase 2 | Prompt security | ⬜ Not started | |
| Phase 2 | Intent classification | ⬜ Not started | |
| Phase 2 | Stall detection | ⬜ Not started | |
| Phase 2 | Completion verifier | ⬜ Not started | |
| Phase 2 | tiktoken | ⬜ Not started | |
| Phase 2 | Run persistence | ⬜ Not started | |
| Phase 2 | Feature flag | ✅ Complete | CORTEX_NEW_AGENT_LOOP in settings |
| Phase 3 | CLI commands (15) | ⬜ Not started | |
| Phase 3 | Bug fixes (5) | ⬜ Not started | |
| Phase 3 | Documentation cleanup | ⬜ Not started | |
| **V1 Total** | **19 components** | **🟡 9/19** | |

---

## Commit Log

- `c32b1f6` feat(daemon): V1 Phase-1 daemon foundation — PID mgmt, health checks, lifecycle, CLI
- `9348699` feat(agents): V1 Phase-2 tool infrastructure — @tool decorator, schemas, registry, policy, security
- `21d5d58` chore: remove legacy tools.py (replaced by tool_defs.py + tools/ package)
