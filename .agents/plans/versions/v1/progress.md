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
| Phase 2 | 15+ tools | ✅ Complete | 15 tools registered (5 legacy + 10 new: read_file, write_file, list_directory, grep_files, git_status, git_show, search_knowledge, current_datetime, list_available_tools, get_repo_info) |
| Phase 2 | Tool policy | ✅ Complete | Per-turn allow/deny/ask composition |
| Phase 2 | Tool security | ✅ Complete | Enhanced SSRF, path traversal, command blocking |
| Phase 2 | Context compaction | ✅ Complete | Auto at 85%, Goal/Done/State/Pending summary |
| Phase 2 | Prompt security | ✅ Complete | UNTRUSTED_SOURCE_DATA markers on web_fetch, read_file, grep_files, search_knowledge |
| Phase 2 | Intent classification | ✅ Complete | casual/admin/agent/continuation classifier |
| Phase 2 | Stall detection | ✅ Complete | Repeated identical calls → force answer |
| Phase 2 | Completion verifier | ✅ Complete | Fresh-context LLM subagent |
| Phase 2 | tiktoken | ⬜ Not started | Not yet integrated |
| Phase 2 | Run persistence | ⬜ Not started | Database-backed run store not yet implemented |
| Phase 2 | Feature flag | ✅ Complete | CORTEX_NEW_AGENT_LOOP in settings |
| Phase 3 | CLI commands (15) | ⬜ Not started | |
| Phase 3 | Bug fixes (5) | ⬜ Not started | |
| Phase 3 | Documentation cleanup | ⬜ Not started | |
| **V1 Total** | **20 components** | **🟡 15/20** | |

---

## Commit Log

- `c32b1f6` feat(daemon): V1 Phase-1 daemon foundation — PID mgmt, health checks, lifecycle, CLI
- `9348699` feat(agents): V1 Phase-2 tool infrastructure — @tool decorator, schemas, registry, policy, security
- `21d5d58` chore: remove legacy tools.py (replaced by tool_defs.py + tools/ package)
- `5514af5` feat: add 10 new @tool tools reaching 15+ total
