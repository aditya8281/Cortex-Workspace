# Odysseus Deep Integration Audit

**Date:** 2026-06-25
**Classification:** Competitive implementation audit — Odysseus as a competing implementation of a similar vision
**Goal:** Determine how Cortex can absorb every valuable capability from Odysseus while remaining consistent with Cortex's long-term direction

---

## 1. Feature Parity Matrix

| Capability | Cortex | Odysseus | Better | Action |
|------------|--------|----------|--------|--------|
| **FastAPI backend** | PostgreSQL + SQLAlchemy 2.0 | SQLite + SQLAlchemy | Cortex | KEEP |
| **Frontend** | Next.js 15 + React 19 + TypeScript | Vanilla JS SPA (no build) | Cortex | KEEP |
| **Auth** | JWT + refresh tokens + CSRF double-submit | Cookie sessions + Bearer ody_ tokens + bcrypt | Cortex | KEEP |
| **Encryption** | Fernet + PBKDF2 (vault) | Fernet (secrets) | Cortex | KEEP |
| **Agent system** | Planner→Executor (2-agent, no compaction, no tools schema, 5 tools) | Single streaming loop (50 rounds, 30+ tools, RAG tool selection, compaction) | **Odysseus** | **ADAPT** |
| **Tool count** | 5 (search, read_file, write_file, list_files, exec_command) | 30+ (bash, python, web_search, web_fetch, read/write/edit_file, grep, glob, ls, documents, email, calendar, tasks, notes, sessions, memory, models, skills, MCP, webhooks, UI) | **Odysseus** | **ADOPT** |
| **Tool schemas** | No parameter schemas — description only | Full OpenAI-compatible JSON Schema for every tool | **Odysseus** | **ADOPT** |
| **Tool policy** | HMAC approval tokens for 3 tools | Per-turn composition: guide-only, plan mode, disabled tools, admin gates | **Odysseus** | **ADOPT** |
| **Tool selection** | All tools injected into prompt | RAG-based retrieval (ChromaDB) + keyword hints + domain detection | **Odysseus** | **ADAPT** |
| **Context compaction** | None (simple truncation at fixed budget) | Auto at 85% with structured summary (Goal/Done/State/Pending) | **Odysseus** | **ADOPT** |
| **Context budget** | Fixed token budget | Adaptive: headroom × context_length, hard_max, explicit overrides | **Odysseus** | **ADOPT** |
| **Prompt security** | None | UNTRUSTED_SOURCE_DATA guards + prompt injection defense | **Odysseus** | **ADOPT** |
| **Memory system** | Knowledge graph + long-term memory (PostgreSQL + Qdrant) | JSON file + ChromaDB vectors + Jaccard similarity | Cortex | KEEP |
| **RAG pipeline** | HybridRetrievalV2 (vector + fulltext + graph + MMR) | ChromaDB personal-doc semantic search | Cortex | KEEP |
| **Embeddings** | ONNX BGE-M3 (768-dim) with Ollama fallback | Multi-lane (custom + fastembed) | Cortex | KEEP |
| **Knowledge graph** | Graph nodes + edges (PostgreSQL) | None | Cortex | KEEP |
| **Database** | PostgreSQL 16 (34+ tables, 25 migrations) | SQLite (7 tables) | Cortex | KEEP |
| **CLI** | 15 Commander.js stubs (zero functionality) | Platform-specific launch scripts (no CLI) | **Tie** | **BUILD** |
| **MCP integration** | None | Full MCP manager (stdio/SSE, lifecycle, tool wrapping) | **Odysseus** | **ADOPT** |
| **Background jobs** | arq (Redis-based) + asyncio tasks | Task scheduler (in-process) + background bash jobs | Cortex | KEEP |
| **Deep research** | None | IterResearch-style multi-step web research | **Odysseus** | **ADOPT** |
| **Email** | None | IMAP/SMTP with triage, tags, summaries, reply drafts | **Odysseus** | DEFER |
| **Calendar/Tasks** | None | CalDAV sync, reminders, scheduled agent tasks | **Odysseus** | DEFER |
| **Documents** | None | Writing-first editor with AI edits, suggestions, Markdown | **Odysseus** | DEFER |
| **Skills** | .agents/skills/ (dev-time only) | Disk-based skill system (YAML frontmatter + markdown, usage tracking) | **Odysseus** | **ADAPT** |
| **Session management** | Conversation model with message history | SessionManager singleton + session search + auto-sort | **Odysseus** | **ADAPT** |
| **Webhooks** | None | Outgoing webhook manager | **Odysseus** | DEFER |
| **Model serving** | Ollama integration | Cookbook (tmux-based vLLM/SGLang/llama.cpp) + model download + presets | **Odysseus** | DEFER |
| **Docker** | Docker Compose (PG + Redis + Qdrant) | Docker Compose + GPU support (NVIDIA/AMD) | **Odysseus** | DEFER |
| **Desktop** | Tauri shell (planned) | PyInstaller portable (Windows) + macOS app + systemd service | **Tie** | KEEP (Tauri) |
| **Streaming** | SSE with ReadableStream | SSE with subscriber fan-out + detached runs | **Odysseus** | **ADAPT** |
| **Detached runs** | None (tasks lost on restart) | Agent runs survive tab close (180s grace, replay buffer) | **Odysseus** | **ADOPT** |
| **Completion verifier** | None | Fresh-context LLM subagent judges task completion | **Odysseus** | **ADAPT** |
| **Loop-breaker** | None (hard cutoff at 10 iterations) | Stall detection for repeated identical calls + force-answer | **Odysseus** | **ADOPT** |
| **Intent classification** | None | Regex-based routing: casual vs agent vs admin vs continuation | **Odysseus** | **ADOPT** |
| **Plan mode** | Planner creates JSON plan | Per-turn directive: disable write tools, guide-only | **Odysseus** | **ADOPT** |
| **Low-signal detection** | None | Detects casual messages → fast path (no tools, no compaction) | **Odysseus** | **ADOPT** |
| **Domain rules** | None | Tool-to-domain mapping (web, email, docs, cookbook, etc.) | **Odysseus** | **ADAPT** |
| **Skill injection** | None at runtime | Jaccard-matched skills injected into system prompt | **Odysseus** | **ADAPT** |
| **Active document context** | None | Injects open document content + line numbers into prompt | **Odysseus** | **ADAPT** |
| **Email writing style** | None | Detects user email style, injects into prompt | **Odysseus** | **ADAPT** |
| **SSRF protection** | None in agent tools | Private URL blocking, scheme blocking, hostname validation | **Odysseus** | **ADOPT** |
| **Path confinement** | Workspace restriction | Sensitive path deny list + allowlist roots + workspace | **Odysseus** | **ADOPT** |
| **Admin tools** | None | manage_endpoints, manage_mcp, manage_webhooks, manage_tokens, manage_settings | **Odysseus** | **ADAPT** |
| **UI control** | None | ui_control tool (toggle themes, navigate, scroll) | **Odysseus** | **ADAPT** |
| **Contacts** | None | CardDAV contacts (Radicale-compatible), vCard/CSV import/export, search, resolution | **Odysseus** | **ADOPT** |
| **Email** | None | IMAP/SMTP with triage, tags, summaries, reply drafts, thread parsing, urgency detection, writing style | **Odysseus** | **ADOPT** |
| **Calendar** | None | SQLite-backed CRUD, ICS import/export, CalDAV multi-account sync, RRULE expansion, NL event parsing | **Odysseus** | **ADOPT** |
| **Tasks** | None | Scheduled task CRUD, cron/event/webhook triggers, pause/resume/revert, run history, NL→task parsing, housekeeping actions | **Odysseus** | **ADOPT** |
| **Notes** | None | Google Keep-style notes/checklists, pin/archive/reorder, reminder dispatch (browser/email/ntfy/webhook), LLM synthesis | **Odysseus** | **ADOPT** |
| **Documents** | None | Living documents with version history, PDF import/export (forms + signatures), AI tidy, signed-reply | **Odysseus** | **ADOPT** |
| **Deep research** | None | IterResearch-style multi-step web research, visual HTML reports, spinoff to chat | **Odysseus** | **ADOPT** |
| **Skills** | .agents/skills/ (dev-time only) | Disk-based skill system (YAML frontmatter + markdown, usage tracking, slash-command invocation, autonomous audit) | **Odysseus** | **ADOPT** |
| **Webhooks** | None | Outgoing webhook CRUD + test, API token sync-chat endpoint, provider auto-detection | **Odysseus** | **ADAPT** |
| **Task scheduler** | None | Cron/event/webhook triggers, 10 built-in housekeeping tasks, personal assistant crew member | **Odysseus** | **ADOPT** |
| **Governance** | Comprehensive (GOVERNANCE.md, WORKFLOWS.md, ADRs) | None | Cortex | KEEP |
| **Testing** | 486+ tests (pytest + vitest) | ~150 tests (pytest) | Cortex | KEEP |
| **Documentation** | 12+ docs (architecture, roadmap, API, DB, security, etc.) | README + setup docs | Cortex | KEEP |

---

## 2. Architecture Comparison

### Agent Model

| Aspect | Cortex | Odysseus | Winner |
|--------|--------|----------|--------|
| Architecture | Planner→Executor (2 agents) | Single streaming agent loop | **Odysseus** |
| Tool calling | Max 10 iterations, no abort | Max 50 rounds, stall detection, force-answer | **Odysseus** |
| Tool selection | All tools in prompt | RAG-based retrieval (only relevant tools) | **Odysseus** |
| Context management | Simple truncation | Auto-compaction at 85% + adaptive budget | **Odysseus** |
| Prompt security | None | UNTRUSTED_SOURCE_DATA guards | **Odysseus** |
| Completion detection | None | Fresh-context LLM verifier subagent | **Odysseus** |
| Detached execution | asyncio tasks (lost on restart) | Server-side runs with replay buffer | **Odysseus** |
| Tool policy | HMAC approval tokens | Per-turn composition (guide-only, plan mode, admin gates) | **Odysseus** |

**Verdict:** Odysseus has a strictly superior agent system. Cortex must adapt Odysseus's patterns.

### Memory System

| Aspect | Cortex | Odysseus | Winner |
|--------|--------|----------|--------|
| Storage | PostgreSQL + Qdrant (knowledge graph + vectors) | JSON file + ChromaDB | **Cortex** |
| Consolidation | Long-term memory with decay + confidence | Simple Jaccard similarity | **Cortex** |
| Knowledge graph | Graph nodes + edges with community detection | None | **Cortex** |
| Temporal tracking | Bi-temporal (valid_at/invalid_at) | None | **Cortex** |
| Retrieval | HybridRetrievalV2 (vector + fulltext + graph + MMR) | ChromaDB semantic search | **Cortex** |

**Verdict:** Cortex has a strictly superior memory system. Odysseus's memory is basic (JSON + Jaccard). No harvesting needed.

### RAG Pipeline

| Aspect | Cortex | Odysseus | Winner |
|--------|--------|----------|--------|
| Vector search | Qdrant with payload filtering | ChromaDB cosine similarity | **Cortex** |
| Fulltext search | PostgreSQL ts_vector | None | **Cortex** |
| Graph enrichment | Knowledge graph traversal | None | **Cortex** |
| Diversity reranking | MMR | None | **Cortex** |
| Score fusion | RRF + MMR | None | **Cortex** |

**Verdict:** Cortex has a strictly superior RAG pipeline. No harvesting needed.

### Tool System

| Aspect | Cortex | Odysseus | Winner |
|--------|--------|----------|--------|
| Tool count | 5 | 30+ | **Odysseus** |
| Tool schemas | No parameter schemas | Full JSON Schema | **Odysseus** |
| Tool selection | All injected | RAG-based retrieval | **Odysseus** |
| Tool policy | HMAC approval | Per-turn composition | **Odysseus** |
| MCP integration | None | Full manager | **Odysseus** |
| Security | Workspace restriction | Path confinement + SSRF + sensitive path blocking | **Odysseus** |

**Verdict:** Odysseus has a strictly superior tool system. Cortex must adapt.

### CLI

| Aspect | Cortex | Odysseus | Winner |
|--------|--------|----------|--------|
| Framework | Commander.js (15 stubs) | Platform launch scripts | Tie |
| Commands | 15 (init, install, build, start, dev, stop, status, doctor, logs, migrate, backup, deploy, update, registry, setup) | 0 (launch scripts only) | **Cortex** (scaffolded) |
| Daemon management | start/stop/status/logs | systemd service file | **Cortex** (better framework) |
| Interactive mode | None (no Ink TUI) | None | Tie |

**Verdict:** Cortex has a better CLI foundation but needs implementation. Odysseus has no CLI at all.

### Data Model

| Aspect | Cortex | Odysseus | Winner |
|--------|--------|----------|--------|
| ORM | SQLAlchemy 2.0 (async-capable) | SQLAlchemy (sync) | **Cortex** |
| Database | PostgreSQL 16 (34+ tables) | SQLite (7 tables) | **Cortex** |
| Migrations | Alembic (25 versions) | None | **Cortex** |
| Auth model | Two-password (login + vault) | Single password | **Cortex** |
| Schema design | JSONB for flexible data, soft deletes, timestamps | Basic tables | **Cortex** |

**Verdict:** Cortex has a strictly superior data model. No harvesting needed.

---

## 3. Missing Features (Cortex Lacks)

### Critical (Must Have)

1. **Streaming agent loop** — Odysseus's `stream_agent_loop()` is a 3,485-line async generator that handles: tool policy, plan mode, intent classification, low-signal detection, RAG tool selection, native function calling, context trimming, multi-round execution, completion verification, loop-breaking, skill injection. Cortex has none of this.

2. **Context compaction** — Odysseus auto-compacts at 85% context window with structured summaries (Goal/Done/State/Pending). Cortex does simple truncation at a fixed budget. Long conversations lose context.

3. **Tool schemas** — Odysseus has 60+ OpenAI-compatible function tool schemas with full JSON Schema parameters. Cortex has 5 tools with no parameter schemas. LLM function-calling is degraded without parameter schemas.

4. **RAG-based tool selection** — Odysseus embeds tool descriptions into ChromaDB and retrieves top-K relevant tools per user message. Cortex injects all tools into the prompt. With 30+ tools, injection becomes infeasible.

5. **Prompt security** — Odysseus wraps all external content with `UNTRUSTED_SOURCE_DATA` guards. Cortex has no protection against prompt injection via retrieved content.

6. **MCP integration** — Odysseus has a full MCP manager (stdio + SSE transport, lifecycle management, tool wrapping). Cortex has nothing. MCP is table stakes for agent interoperability.

7. **Detached agent runs** — Odysseus keeps agent runs server-side after SSE client disconnect (tab close, refresh). Cortex uses asyncio tasks that die with the process.

### Important (Should Have)

8. **Tool policy composition** — Odysseus composes per-turn policies: guide-only (no tools), plan mode (read-only), admin gates, per-tool disable. Cortex has HMAC approval tokens for 3 tools.

9. **Intent classification** — Odysseus classifies user input as casual/agent/admin/continuation before entering the agent loop. Casual messages get fast-path (no tools). Cortex routes everything through the same path.

10. **Loop-breaker** — Odysseus detects stall patterns (repeated identical calls) and forces an answer. Cortex hard-cuts at 10 iterations with "Task completed with maximum iterations".

11. **Completion verifier** — Odysseus spawns a fresh-context LLM subagent to judge whether the task is actually complete. Cortex has no such check.

12. **Domain-specific rules** — Odysseus maps tools to domain rule packs (web, email, docs, cookbook, etc.) and injects only relevant rules. Cortex injects the same static prompt for all tasks.

13. **Low-signal detection** — Odysseus detects casual messages ("hi", "thanks", "ok") and routes them to a fast path without entering the agent loop. Cortex always enters the loop.

14. **SSRF protection** — Odysseus blocks private URLs, localhost, metadata endpoints, internal hostnames. Cortex's `web_fetch` has no such protection.

15. **Path confinement** — Odysseus has sensitive path deny lists, allowlist roots, and workspace restriction. Cortex has only workspace restriction.

16. **Session search** — Odysseus can search across session transcripts. Cortex has no session search.

17. **Skill injection at runtime** — Odysseus matches skills to the current query via Jaccard similarity and injects relevant skills into the system prompt. Cortex's skills are dev-time only.

### Nice-to-Have (Can Defer)

18. **Model serving cookbook** — tmux-based vLLM/SGLang serving with hardware recommendations. Cortex has Ollama integration.

19. **Active document context** — Injects open document content + line numbers into prompt. Frontend-dependent.

20. **Email writing style** — Detects user's email style and injects it. Email-specific.

21. **Teacher escalation** — `ask_teacher` tool for LLM-to-LLM consultation. Novel but niche.

---

## 4.5 Daily Productivity Tools — Deep Inventory

Odysseus implements a complete "AI personal assistant" layer. These are NOT just tools — they're full subsystems with routes, services, database models, agent tools, and UI. Here's the complete inventory:

### Email System (3,694 lines — routes alone)

| Component | Odysseus Implementation | Complexity |
|-----------|------------------------|------------|
| **IMAP/SMTP** | Multi-account IMAP fetch, SMTP send with OAuth2 support | High |
| **Thread parsing** | 615-line parser: HTML/plaintext, multilingual (20+ locales), top/bottom-posted, Gmail/Yahoo/Outlook containers | High |
| **Triage** | Urgency detection, tag assignment, summary generation | Medium |
| **AI reply** | Draft replies with writing style detection, signed-reply preparation | Medium |
| **Search** | Full-text search across emails | Medium |
| **Bulk operations** | Archive, delete, mark read, bulk actions | Low |
| **Scheduled sends** | Queue emails for future delivery | Medium |
| **Calendar extraction** | Auto-extract calendar events from email bodies | Medium |

### Calendar System (1,545 lines)

| Component | Odysseus Implementation | Complexity |
|-----------|------------------------|------------|
| **CRUD** | SQLite-backed events with full CRUD | Low |
| **ICS import/export** | Standard iCalendar format support | Medium |
| **CalDAV sync** | Multi-account CalDAV (Radicale-compatible) | High |
| **RRULE expansion** | Recurring event rule parsing | High |
| **NL event parsing** | "Meet with John tomorrow at 3pm" → event | Medium |

### Task System (1,166 lines)

| Component | Odysseus Implementation | Complexity |
|-----------|------------------------|------------|
| **CRUD** | Scheduled tasks with full CRUD | Low |
| **Triggers** | Cron, event, webhook triggers | Medium |
| **Lifecycle** | Pause, resume, revert, run history | Medium |
| **NL parsing** | "Remind me to call mom every Friday" → task | Medium |
| **Housekeeping** | 10 built-in automated tasks (session tidy, doc tidy, memory tidy, email summary, email auto-reply, email calendar events, calendar classify, email tags, skills audit) | High |

### Notes System (905 lines)

| Component | Odysseus Implementation | Complexity |
|-----------|------------------------|------------|
| **Notes/Checklists** | Google Keep-style with pin/archive/reorder | Low |
| **Reminders** | Dispatch via browser, email, ntfy, webhook | Medium |
| **LLM synthesis** | AI-powered note summarization | Low |

### Documents System (1,726 lines)

| Component | Odysseus Implementation | Complexity |
|-----------|------------------------|------------|
| **Living documents** | Version history, collaborative editing | Medium |
| **PDF** | Import, render, export (forms + signatures + annotations) | High |
| **AI tidy** | AI-powered document cleanup | Low |
| **Library** | Faceted search, categories | Medium |

### Contacts System (893 lines)

| Component | Odysseus Implementation | Complexity |
|-----------|------------------------|------------|
| **CardDAV** | Radicale-compatible contacts sync | High |
| **Import/Export** | vCard, CSV formats | Medium |
| **Resolution** | Name/email → contact matching | Medium |

### Deep Research (679 lines + 486 lines handler)

| Component | Odysseus Implementation | Complexity |
|-----------|------------------------|------------|
| **Multi-step** | IterResearch-style iterative web research | High |
| **Source reading** | Fetch and read source pages | Medium |
| **Report generation** | Visual HTML reports | Medium |
| **Spinoff** | Research → chat session handoff | Low |

### Skills System (1,653 lines routes + 717 lines service)

| Component | Odysseus Implementation | Complexity |
|-----------|------------------------|------------|
| **Storage** | Disk-based SKILL.md files with YAML frontmatter | Low |
| **Invocation** | Slash-command execution | Medium |
| **Autonomous audit** | Self-edit → retry → teacher → flag | High |
| **Usage tracking** | Sidecar _usage.json | Low |
| **Duplicate detection** | Necessity and retrieval-precision checks | Medium |

### Webhooks (395 lines)

| Component | Odysseus Implementation | Complexity |
|-----------|------------------------|------------|
| **CRUD** | Webhook management with URL validation | Low |
| **API token sync** | n8n/Make/Activepieces integration | Medium |
| **Provider auto-detection** | Auto-detect webhook provider | Low |

### Task Scheduler (2,467 lines)

| Component | Odysseus Implementation | Complexity |
|-----------|------------------------|------------|
| **Cron scheduling** | Daily/weekly/monthly/cron/once with timezone | Medium |
| **Built-in actions** | 10 housekeeping tasks (no LLM needed) | Medium |
| **Agent loop execution** | Full agent loop with tool access for scheduled tasks | High |
| **Personal assistant** | CrewMember with detailed personality prompt | High |
| **Note pings** | Background scanner for due notes/reminders (60s interval) | Medium |
| **Result delivery** | Session/MCP/email delivery channels | Medium |

### Agent-to-Agent Sessions (465 lines)

| Component | Odysseus Implementation | Complexity |
|-----------|------------------------|------------|
| **Create session** | Named sessions with model selection | Low |
| **Send to session** | AI-to-AI communication | Medium |
| **List/Manage** | Archive, rename, fork, truncate | Low |

### Model Interaction (209 lines)

| Component | Odysseus Implementation | Complexity |
|-----------|------------------------|------------|
| **chat_with_model** | Send message to specific model | Low |
| **ask_teacher** | LLM-to-LLM consultation | Low |
| **list_models** | List available models across endpoints | Low |

---

## 4. Missing Abstractions

### Service Boundaries

1. **ToolIndex as a service** — Odysseus treats tool selection as a first-class service (ChromaDB-backed RAG over tool descriptions). Cortex should create `backend/app/services/tools/index.py` as a standalone service.

2. **ContextCompactor as a service** — Odysseus's compaction is a standalone module with clear interfaces (`maybe_compact()`, `trim_for_context()`). Cortex should create `backend/app/services/context/compactor.py`.

3. **PromptSecurity as a service** — Odysseus's untrusted content wrapping is a standalone module. Cortex should create `backend/app/services/context/security.py`.

4. **AgentRunManager as a service** — Odysseus's detached runs are a standalone service with subscriber fan-out. Cortex should create `backend/app/services/runner/manager.py`.

5. **ToolPolicy as a service** — Odysseus's policy composition is a standalone module. Cortex should create `backend/app/agents/policy.py`.

### Interfaces

6. **ContextProvider Protocol** — Odysseus doesn't have this (it's monolithic), but Continue does. Cortex should create a Protocol for composable context sources.

7. **ToolProvider Protocol** — Odysseus's tool system is monolithic. Cortex should create a Protocol for tool registration, selection, and execution.

8. **MemoryProvider Protocol** — Odysseus has a `MemoryProvider` ABC with `remember()`, `recall()`, `list_memories()`, `delete()`. Cortex should adopt this for pluggable memory backends.

### Architecture Patterns

9. **Streaming-first agent loop** — Odysseus's agent loop is an async generator that yields events. Cortex's loop is synchronous. Cortex should adopt streaming-first.

10. **Event-driven agent lifecycle** — Odysseus uses SSE events for agent progress. Cortex should adopt this for daemon mode.

11. **Per-turn tool policy** — Odysseus recomputes tool policy per turn (not per-session). This allows dynamic restriction (e.g., plan mode disables write tools mid-conversation).

12. **Intent classification before agent loop** — Odysseus classifies intent BEFORE entering the agent loop. This prevents unnecessary LLM calls for casual messages.

---

## 5. Missing Operational Capabilities

### Observability

1. **Agent run metrics** — Odysseus tracks: token counts, TPS, context usage %, prep timings, tool execution times. Cortex tracks nothing.

2. **Completion verification** — Odysseus spawns a fresh-context subagent to verify task completion. Cortex has no such check.

3. **Loop-breaker detection** — Odysseus detects stall patterns and forces an answer. Cortex hard-cuts.

### Recovery

4. **Detached run recovery** — Odysseus keeps runs server-side with 180s grace period. Cortex loses runs on restart.

5. **Orphan detection** — Odysseus detects orphaned runs. Cortex has no such mechanism.

### Deployment

6. **Systemd service** — Odysseus ships a systemd unit file. Cortex should too (for daemon mode).

7. **Platform launchers** — Odysseus has macOS/Windows/Linux launchers. Cortex's Tauri shell will replace these.

8. **Docker GPU support** — Odysseus has NVIDIA and AMD GPU docker-compose files. Cortex should add these.

---

## 6. Feature Harvesting

### Immediate (Phase 2 — Service Abstraction)

| Feature | Source | Complexity | Dependencies | Effort | Impact | Phase |
|---------|--------|------------|--------------|--------|--------|-------|
| Tool schemas (JSON Schema for all tools) | Odysseus tool_schemas.py | Low | None | Low | Critical | Phase 2 |
| Tool policy composition | Odysseus tool_policy.py | Low | None | Low | Critical | Phase 2 |
| Prompt security (UNTRUSTED_SOURCE_DATA) | Odysseus prompt_security.py | Low | None | Low | Critical | Phase 2 |
| Context compaction | Odysseus context_compactor.py | Medium | LLM provider | Medium | Critical | Phase 2-3 |
| Intent classification | Odysseus agent_loop.py (_classify_agent_request) | Low | None | Low | High | Phase 2 |
| Low-signal detection | Odysseus agent_loop.py (_is_casual_low_signal) | Low | None | Low | High | Phase 2 |
| SSRF protection | Odysseus tools.py (_is_private_url) | Low | None | Low | High | Phase 2 |
| Path confinement | Odysseus tool_execution.py (_resolve_tool_path) | Low | None | Low | High | Phase 2 |

### Near-term (Phase 3 — Event Bus & Jobs)

| Feature | Source | Complexity | Dependencies | Effort | Impact | Phase |
|---------|--------|------------|--------------|--------|--------|-------|
| Streaming agent loop | Odysseus agent_loop.py | High | Tool system, context | High | Critical | Phase 3 |
| Detached agent runs | Odysseus agent_runs.py | Medium | Event bus | Medium | Critical | Phase 3 |
| Loop-breaker | Odysseus agent_loop.py (_detect_runaway_call) | Low | Agent loop | Low | High | Phase 3 |
| Completion verifier | Odysseus agent_loop.py (_run_verifier_subagent) | Medium | Agent loop | Medium | High | Phase 3 |
| Session search | Odysseus session_search.py | Medium | Session model | Medium | Medium | Phase 3 |
| Skill injection at runtime | Odysseus agent_loop.py + skills.py | Medium | Skill system | Medium | Medium | Phase 3 |

### Long-term (Phase 4+)

| Feature | Source | Complexity | Dependencies | Effort | Impact | Phase |
|---------|--------|------------|--------------|--------|--------|-------|
| RAG-based tool selection | Odysseus tool_index.py | High | Embeddings, tool system | High | Medium | Phase 4+ |
| Deep research engine | Odysseus deep_research.py | High | Web search, agent loop | High | High | Phase 5+ |
| Email integration | Odysseus email routes + tools (3,694 lines) | High | IMAP/SMTP, thread parser, agent loop | High | High | Phase 5+ |
| Calendar system | Odysseus calendar routes (1,545 lines) | High | CalDAV, ICS, RRULE, agent loop | High | High | Phase 5+ |
| Task scheduler | Odysseus task_scheduler.py (2,467 lines) | High | Agent loop, event bus, housekeeping | High | Critical | Phase 4+ |
| Notes system | Odysseus note_routes.py (905 lines) | Medium | Database, reminders | Medium | Medium | Phase 5+ |
| Documents system | Odysseus document_routes.py (1,726 lines) | High | PDF rendering, version history, frontend | High | Medium | Phase 5+ |
| Contacts system | Odysseus contacts_routes.py (893 lines) | Medium | CardDAV, database | Medium | Medium | Phase 5+ |
| Skills system | Odysseus skills.py + routes (1,653 lines) | High | Disk storage, LLM audit, slash commands | High | High | Phase 4+ |
| Webhooks | Odysseus webhook_routes.py (395 lines) | Medium | Event bus, API tokens | Medium | Medium | Phase 4+ |
| Model serving cookbook | Odysseus cookbook routes + hwfit | High | GPU, model management | High | Low | Phase 6+ |
| UI control tool | Odysseus ui_control | Medium | Frontend WebSocket | Medium | Low | Phase 6+ |
| Teacher escalation | Odysseus ask_teacher | Low | LLM provider | Low | Low | Phase 4+ |
| Agent-to-agent sessions | Odysseus session_tools.py (465 lines) | Medium | Agent loop, model routing | Medium | Medium | Phase 4+ |

---

## 7. Implementation Strategy

### 7.1 Feature Adoption Plan

#### Tier 1: Critical (Phase 2 — Service Abstraction)

**1. Tool System Rebuild**
- Adopt Odysseus's `tool_schemas.py` — create full JSON Schema definitions for all 5 existing tools
- Adopt Odysseus's `tool_policy.py` — create `ToolPolicy` dataclass with per-turn composition
- Adopt Odysseus's `tool_security.py` — SSRF protection, path confinement, sensitive path blocking
- Refactor `backend/app/agents/tools.py` into `backend/app/agents/tools/` package

**2. Agent Loop Rebuild**
- Replace Planner→Executor with single streaming agent loop
- Adopt Odysseus's intent classification (casual/admin/agent/continuation)
- Adopt Odysseus's low-signal detection (fast path for casual messages)
- Adopt Odysseus's loop-breaker (stall detection + force-answer)
- Max rounds: start at 25 (Odysseus uses 50)

**3. Context Compaction**
- Adopt Odysseus's `context_compactor.py` — auto-compaction at 85%
- Adopt structured summary format (User Goal/Done/State/Pending)
- Create `backend/app/services/context/compactor.py`

**4. Prompt Security**
- Adopt Odysseus's `prompt_security.py` — UNTRUSTED_SOURCE_DATA guards
- Create `backend/app/services/context/security.py`
- Apply to all external content (file contents, search results, MCP responses)

#### Tier 2: High Impact (Phase 3 — Event Bus & Jobs)

**5. Detached Agent Runs**
- Adopt Odysseus's `agent_runs.py` — server-side runs with subscriber fan-out
- 180s grace period after last subscriber disconnects
- Replay buffer for late-joining subscribers
- Create `backend/app/services/runner/manager.py`

**6. Completion Verifier**
- Adopt Odysseus's `_run_verifier_subagent()` — fresh-context LLM judges completion
- Spawn after agent loop exits (not during)
- Use cheaper/faster model for verification

**7. Runtime Skill Injection**
- Adopt Odysseus's Jaccard-matched skill injection into system prompt
- Integrate with existing `.agents/skills/` directory
- Create `backend/app/services/skills/injector.py`

**8. Session Search**
- Adopt Odysseus's `session_search.py` — search across session transcripts
- Create `backend/app/services/sessions/search.py`

#### Tier 3: Daily Tools Foundation (Phase 4 — CLI & Scheduler)

**9. Task Scheduler**
- Adopt Odysseus's `task_scheduler.py` (2,467 lines) — cron/event/webhook triggers, serial execution
- Adopt 10 built-in housekeeping tasks (session tidy, doc tidy, memory tidy, email summary, etc.)
- Adopt personal assistant CrewMember with personality prompt
- Create `backend/app/services/scheduler/task_scheduler.py`
- New model: `ScheduledTask` (cron, event, webhook triggers, run history)

**10. Skills System (Runtime)**
- Adopt Odysseus's disk-based skill system with YAML frontmatter
- Adopt slash-command invocation, autonomous audit, usage tracking
- Create `backend/app/services/skills/` package

**11. Webhooks**
- Adopt Odysseus's webhook CRUD + test + API token sync
- Create `backend/app/services/webhooks/manager.py`

**12. Agent-to-Agent Sessions**
- Adopt Odysseus's session tools — create, send, list, manage, archive, fork
- Create `backend/app/agents/tools/session_tools.py`

**13. Teacher Escalation**
- Adopt Odysseus's `ask_teacher` tool — LLM-to-LLM consultation
- Create `backend/app/agents/tools/ask_teacher.py`

**14. RAG-based Tool Selection**
- Adopt Odysseus's `tool_index.py` — only when tool count exceeds 15+
- Create `backend/app/services/tools/rag_selector.py`

**15. Domain-specific Rules**
- Adopt Odysseus's tool-to-domain mapping
- Create `backend/app/services/context/domain_rules.py`

#### Tier 4: Daily Productivity Tools (Phase 5+ — Full AI Assistant)

**16. Email System** (Odysseus: 3,694 lines routes + 615 lines thread parser)
- Adopt IMAP/SMTP integration (multi-account, OAuth2)
- Adopt thread parsing (HTML/plaintext, 20+ locales, Gmail/Yahoo/Outlook)
- Adopt triage, urgency detection, tag assignment
- Adopt AI reply with writing style detection
- Adopt calendar extraction from email bodies
- Adopt scheduled sends, bulk operations
- Create `backend/app/services/email/` package (imap, smtp, parser, triage, reply)
- Create `backend/app/api/v1/email.py` routes
- Create `backend/app/agents/tools/email_tools.py`
- New models: `EmailAccount`, `EmailMessage`, `EmailTag`

**17. Calendar System** (Odysseus: 1,545 lines)
- Adopt CRUD with SQLite → PostgreSQL
- Adopt ICS import/export
- Adopt CalDAV multi-account sync (Radicale-compatible)
- Adopt RRULE expansion for recurring events
- Adopt NL event parsing ("Meet with John tomorrow at 3pm")
- Create `backend/app/services/calendar/` package (crud, ics, caldav, rrule, parser)
- Create `backend/app/api/v1/calendar.py` routes
- Create `backend/app/agents/tools/calendar_tools.py`
- New models: `Calendar`, `CalendarEvent`

**18. Notes System** (Odysseus: 905 lines)
- Adopt Google Keep-style notes with checklists
- Adopt pin/archive/reorder
- Adopt reminder dispatch (browser/email/ntfy/webhook)
- Adopt LLM synthesis
- Create `backend/app/services/notes/` package
- Create `backend/app/api/v1/notes.py` routes
- New models: `Note`

**19. Documents System** (Odysseus: 1,726 lines)
- Adopt living documents with version history
- Adopt PDF import/export (forms + signatures + annotations)
- Adopt AI tidy, signed-reply preparation
- Adopt library facets
- Create `backend/app/services/documents/` package
- Create `backend/app/api/v1/documents.py` routes
- Create `backend/app/agents/tools/document_tools.py`
- New models: `Document`, `DocumentVersion`

**20. Contacts System** (Odysseus: 893 lines)
- Adopt CardDAV contacts (Radicale-compatible)
- Adopt vCard/CSV import/export
- Adopt contact resolution for email/calendar
- Create `backend/app/services/contacts/` package
- Create `backend/app/api/v1/contacts.py` routes
- New models: `Contact`

**21. Deep Research** (Odysseus: 679 lines routes + 486 lines handler)
- Adopt IterResearch-style multi-step web research
- Adopt visual HTML reports
- Adopt spinoff to chat session
- Create `backend/app/services/research/` package
- Create `backend/app/api/v1/research.py` routes
- Create `backend/app/agents/tools/research_tools.py`

### 7.2 Architecture Adoption Plan

**Agent Architecture:**
```
Current:  User → PlannerAgent → ExecutorAgent → RunManager
                           ↓              ↓              ↓
                      JSON plan     Tool calling     Track steps

Adopted:  User → IntentClassifier → AgentLoop → RunManager
                    ↓                    ↓              ↓
              casual/agent/admin   Streaming loop   Detached runs
              fast path / full     Tool policy      Replay buffer
                                   Context compaction
                                   Completion verification
                                   Loop-breaker
```

**Tool Architecture:**
```
Current:  TOOL_REGISTRY = {name: handler}
          No schemas, no policy, no selection

Adopted:  ToolRegistry (decorator-based)
          + ToolSchemas (JSON Schema per tool)
          + ToolPolicy (per-turn composition)
          + ToolSecurity (SSRF, path confinement)
          + ToolSelector (RAG-based, when 15+ tools)
```

**Context Architecture:**
```
Current:  Simple truncation at fixed budget

Adopted:  ContextCompactor (auto at 85%)
          + ContextBudget (adaptive: headroom × context_length)
          + PromptSecurity (UNTRUSTED_SOURCE_DATA guards)
          + DomainRules (tool-to-domain mapping)
          + SkillInjection (Jaccard-matched at runtime)
```

### 7.3 Refactoring Plan

**Phase 2 refactors:**
1. `backend/app/agents/tools.py` → `backend/app/agents/tools/` package (split into registry, schemas, policy, security)
2. `backend/app/agents/executor.py` → `backend/app/agents/loop.py` (unified streaming loop)
3. `backend/app/agents/planner.py` → deprecate (planner becomes a tool, not a separate agent)
4. Add `backend/app/services/context/` package (compactor, security, budget)
5. Add `backend/app/agents/policy.py` (tool policy composition)

**Phase 3 refactors:**
1. `backend/app/agents/background.py` → `backend/app/services/runner/` package (manager, persistence, replay)
2. Add `backend/app/services/sessions/search.py`
3. Add `backend/app/services/skills/injector.py`
4. Add `backend/app/services/context/domain_rules.py`

### 7.4 Migration Plan

**No data migration needed.** All changes are additive:
- New files/packages (tool system, context services, runner)
- Modified files (agent loop, tools registration)
- Deprecated files (planner.py — keep for backward compat during transition)

**API migration:**
- Agent run API stays the same (AgentRun/AgentStep models unchanged)
- New endpoints: `/api/v1/sessions/{id}/search`, `/api/v1/agent/runs/{id}/subscribe`
- SSE event format extended (add tool_policy, compaction, completion events)

### 7.5 Quick Wins

| Win | Effort | Impact | How |
|-----|--------|--------|-----|
| Add JSON Schema to 5 existing tools | 1 hour | High | Copy Odysseus tool_schemas.py pattern |
| Add SSRF protection to web_fetch | 30 min | High | Copy Odysseus _is_private_url |
| Add path confinement to file tools | 30 min | High | Copy Odysseus _resolve_tool_path |
| Add UNTRUSTED_SOURCE_DATA to RAG results | 1 hour | High | Copy Odysseus prompt_security.py |
| Add intent classification (casual detection) | 2 hours | High | Copy Odysseus _classify_agent_request |
| Add context compaction | 4 hours | Critical | Adapt Odysseus context_compactor.py |
| Add ToolPolicy dataclass | 1 hour | High | Copy Odysseus tool_policy.py |
| Add loop-breaker | 1 hour | High | Copy Odysseus _detect_runaway_call |

### 7.6 High Impact Changes

1. **Unified agent loop** — Replace Planner→Executor with streaming loop. This is the single most impactful change. Estimated effort: 2-3 days.

2. **Context compaction** — Auto-compaction at 85% with structured summaries. Enables long conversations. Estimated effort: 1 day.

3. **Detached agent runs** — Server-side runs with replay buffer. Enables daemon mode. Estimated effort: 1-2 days.

4. **Tool system rebuild** — Decorator-based tools with JSON Schema + policy + security. Foundation for all other improvements. Estimated effort: 1-2 days.

### 7.7 Long-Term Opportunities

1. **Deep research engine** — Adapt Odysseus's IterResearch-style multi-step web research. High complexity but high value for knowledge workers.

2. **Email/Calendar integration** — Not core to Cortex's vision but valuable for "AI companion" use case. Defer until daemon mode is stable.

3. **Documents editor** — Writing-first editor with AI edits. Defer until frontend is more mature.

4. **Model serving cookbook** — tmux-based model serving with hardware recommendations. Defer until model management is more mature.

5. **RAG-based tool selection** — Only needed when tool count exceeds 15+. Defer until tool system is stable.

6. **Teacher escalation** — LLM-to-LLM consultation. Novel but niche. Defer.

---

## 8. What Odysseus Would Miss if Replaced by Cortex

| Capability | Odysseus Has | Cortex Has | Gap |
|------------|-------------|------------|-----|
| Knowledge graph | No | Yes (graph_nodes, graph_edges) | Odysseus would lose graph-based reasoning |
| Bi-temporal knowledge | No | Yes (valid_at, invalid_at) | Odysseus would lose temporal tracking |
| PostgreSQL | SQLite (7 tables) | PostgreSQL 16 (34+ tables) | Odysseus would lose scale and reliability |
| Next.js frontend | Vanilla JS SPA | Next.js 15 + React 19 | Odysseus would lose modern frontend |
| Two-password auth | Single password | Login + vault passwords | Odysseus would lose vault isolation |
| CSRF protection | None | Double-submit cookie pattern | Odysseus would lose CSRF protection |
| Hybrid RAG | ChromaDB only | Vector + fulltext + graph + MMR | Odysseus would lose retrieval quality |
| Embedding caching | None | EmbeddingCache table | Odysseus would lose embedding efficiency |
| Knowledge graph traversal | None | Graph traversal + community detection | Odysseus would lose connected reasoning |
| Model catalog | Basic model list | Full catalog with providers, variants, benchmarks | Odysseus would lose model intelligence |
| Governance | None | GOVERNANCE.md, WORKFLOWS.md, ADRs | Odysseus would lose development process |
| Testing | ~150 tests | 486+ tests | Odysseus would lose test coverage |

---

## 9. What Cortex Would Miss if Replaced by Odysseus

| Capability | Cortex Has | Odysseus Has | Gap |
|------------|-----------|--------------|-----|
| Streaming agent loop | No (sync) | Yes (3,485 lines) | **Critical** |
| Context compaction | No | Yes (auto at 85%) | **Critical** |
| Tool schemas | No | Yes (60+ tools) | **Critical** |
| Tool policy | HMAC tokens | Per-turn composition | **Critical** |
| Prompt security | No | Yes (UNTRUSTED_SOURCE_DATA) | **Critical** |
| MCP integration | No | Yes (full manager) | **Critical** |
| Detached runs | asyncio tasks | Server-side with replay | **Critical** |
| Intent classification | No | Yes (casual/admin/agent) | **Important** |
| Loop-breaker | No | Yes (stall detection) | **Important** |
| Completion verifier | No | Yes (fresh-context subagent) | **Important** |
| RAG tool selection | No | Yes (ChromaDB embeddings) | **Important** |
| SSRF protection | No | Yes (private URL blocking) | **Important** |
| Path confinement | Basic | Full (sensitive + allowlist) | **Important** |
| Deep research | No | Yes (IterResearch-style) | **Nice-to-have** |
| Email | No | Yes (IMAP/SMTP) | **Nice-to-have** |
| Skills at runtime | No | Yes (Jaccard injection) | **Nice-to-have** |

---

## 10. Integration Priority Order

```
Phase 2 (Service Abstraction):
  1. Tool system rebuild (schemas + policy + security)
  2. Agent loop rebuild (streaming + intent + low-signal)
  3. Context compaction (auto at 85%)
  4. Prompt security (UNTRUSTED_SOURCE_DATA)

Phase 3 (Event Bus & Jobs):
  5. Detached agent runs (server-side + replay)
  6. Loop-breaker (stall detection)
  7. Completion verifier (fresh-context subagent)
  8. Session search
  9. Runtime skill injection

Phase 4 (CLI & Daily Tools Foundation):
  10. Task scheduler (cron/event/webhook triggers, housekeeping)
  11. Skills system (runtime, slash-commands, autonomous audit)
  12. Webhooks (CRUD + API token sync)
  13. Agent-to-agent sessions
  14. Teacher escalation
  15. RAG-based tool selection (when 15+ tools)
  16. Domain-specific rules

Phase 5+ (Full AI Assistant):
  17. Deep research engine (multi-step web research)
  18. Email system (IMAP/SMTP, triage, AI reply, thread parsing)
  19. Calendar system (CRUD, ICS, CalDAV, NL parsing)
  20. Notes system (checklists, reminders, LLM synthesis)
  21. Documents system (living docs, PDF, AI tidy)
  22. Contacts system (CardDAV, resolution)
  23. UI control tool
  24. Model serving cookbook
```

---

## 11. Key Insight

Odysseus is a **monolithic FastAPI app** with SQLite, vanilla JS frontend, and in-process everything. It's a working prototype of the "AI workspace" vision — but with a complete **daily productivity layer** (email, calendar, tasks, notes, documents, contacts, research, skills, webhooks, task scheduler).

Cortex is a **distributed architecture** with PostgreSQL, Next.js, Qdrant, Redis, and planned Tauri desktop shell. It's a more robust foundation but with a broken agent system and **zero daily productivity tools**.

**The integration strategy is clear:** Keep Cortex's superior infrastructure (database, frontend, RAG, memory, auth, governance) and absorb EVERYTHING valuable from Odysseus:

1. **Agent intelligence** (streaming loop, tools, compaction, security) — Phase 2-3
2. **Daily productivity foundation** (task scheduler, skills, webhooks, sessions) — Phase 4
3. **Full AI assistant layer** (email, calendar, notes, documents, contacts, research) — Phase 5+

Cortex becomes strictly better than Odysseus by combining:
- Odysseus's **agent intelligence** (streaming loop, 30+ tools, compaction, security)
- Odysseus's **daily productivity** (email, calendar, tasks, notes, documents, contacts)
- Odysseus's **automation** (task scheduler, housekeeping, webhooks)
- Cortex's **infrastructure** (PostgreSQL, Next.js, Qdrant, Redis, knowledge graph)
- Cortex's **governance** (GOVERNANCE.md, WORKFLOWS.md, ADRs, 486+ tests)
- Cortex's **long-term vision** (daemon-first, Tauri desktop, model freedom)

The result is an AI workspace that is both **intelligent** (Odysseus patterns), **productive** (Odysseus daily tools), and **robust** (Cortex infrastructure).

**Total harvesting scope:** ~15,000+ lines of Odysseus code to adapt across 24 integration items.
