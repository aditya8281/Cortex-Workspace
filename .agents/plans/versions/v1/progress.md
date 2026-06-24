# CORTEX V1: "The Brain Works" — Progress

**Version:** 1
**Started:** —
**Target:** —

---

## Progress Tracker

| Phase | Component | Status | Notes |
|-------|-----------|--------|-------|
| Phase 1 | Daemon lifecycle | ⬜ Not started | cortexd start/stop/status/logs |
| Phase 1 | PID management | ⬜ Not started | PID file, stale detection, orphan cleanup |
| Phase 1 | Health checks | ⬜ Not started | DB, Redis, Qdrant probing |
| Phase 1 | Graceful shutdown | ⬜ Not started | Drain in-flight, flush state |
| Phase 1 | Sleep/wake | ⬜ Not started | Idle detection, wake triggers |
| Phase 2 | Agent loop rebuild | ⬜ Not started | Single streaming loop (replaces Planner→Executor) |
| Phase 2 | @tool decorator | ⬜ Not started | Auto-generated JSON Schema |
| Phase 2 | 15+ tools | ⬜ Not started | With schemas, policy, security |
| Phase 2 | Context compaction | ⬜ Not started | Auto at 85%, Goal/Done/State/Pending |
| Phase 2 | Prompt security | ⬜ Not started | UNTRUSTED_SOURCE_DATA markers |
| Phase 2 | Intent classification | ⬜ Not started | Casual/admin/agent/continuation |
| Phase 2 | Stall detection | ⬜ Not started | Repeated identical calls → force answer |
| Phase 2 | Completion verifier | ⬜ Not started | Fresh-context LLM subagent |
| Phase 2 | Tool policy | ⬜ Not started | Per-turn allow/deny/ask |
| Phase 2 | tiktoken | ⬜ Not started | Accurate token counting |
| Phase 2 | Run persistence | ⬜ Not started | Server-side, replay buffer |
| Phase 3 | CLI commands (15) | ⬜ Not started | daemon, agent, search, config, vault, memory |
| Phase 3 | Bug fixes (5) | ⬜ Not started | Dead code, SSRF, blocking, sync/async, tokens |
| Phase 3 | Documentation cleanup | ⬜ Not started | CLAUDE.md, test count, architecture |
| **V1 Total** | **19 components** | **⬜ 0/19** | |

---

## Commit Log

(No commits yet — version not started)
