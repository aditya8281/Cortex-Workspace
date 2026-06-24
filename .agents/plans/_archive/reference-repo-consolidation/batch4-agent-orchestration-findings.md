# Batch 4 — Agent, Orchestration & Tool System Findings

**Date:** 2026-06-25
**Repos:** Continue, Odysseus, Strands Tools
**Focus:** Agent architecture, orchestration, execution engines, workflow systems, tool systems, tool registries, planning systems, context gathering, repository intelligence, automation, command systems, CLI architecture, developer workflows

---

## Continue — The Mature Coding Agent

### Architecture Summary

TypeScript monorepo: `core/` (shared library) + `extensions/cli/` (CLI) + `extensions/vscode/` (IDE) + `gui/` (React frontend). 1544 source files. Commander.js CLI. Ink-based TUI.

**Key pattern:** Core library shared across CLI, VS Code, and IntelliJ extensions. CLI is a thin wrapper around core capabilities.

### Agent Architecture

**Execution model:** Tool-calling loop built on OpenAI chat completion protocol with function/tool calling.

```
User Input → System Message (rules + prompt files + context items)
  → LLM.chat() with tool definitions
  → LLM returns tool_call → callTool() dispatch
  → Tool result → appended to messages → next LLM iteration
  → Until LLM returns no tool calls (or max iterations)
```

**Key abstractions:**
- `ILLM` interface — `streamChat()`, `complete()`, `embed()`, `rerank()`, `countTokens()`
- `Tool` type — `name`, `description`, `parameters` (JSON Schema), `function` handler
- `IContextProvider` — abstract base for context gathering
- `BaseContextProvider` — implements `getContextItems()` + `loadSubmenuItems()`

### Tool System (18 built-in + MCP)

**Tool definition pattern:**
```typescript
export const readFileTool: Tool = {
  type: "function",
  displayTitle: "Read File",
  wouldLikeTo: "read {{{ filepath }}}",
  isCurrently: "reading {{{ filepath }}}",
  hasAlready: "read {{{ filepath }}}",
  readonly: true,
  isInstant: true,
  group: BUILT_IN_GROUP_NAME,
  function: {
    name: BuiltInToolNames.ReadFile,
    description: "Use this tool if you need to view the contents of an existing file.",
    parameters: {
      type: "object",
      required: ["filepath"],
      properties: {
        filepath: { type: "string", description: "..." },
      },
    },
  },
  defaultToolPolicy: "allowedWithoutPermission",
  toolCallIcon: "DocumentIcon",
  preprocessArgs: async (args, { ide }) => { ... },
  evaluateToolCallPolicy: (basePolicy, _, processedArgs) => { ... },
};
```

**Key features:**
- `preprocessArgs` — transform args before execution (path resolution)
- `evaluateToolCallPolicy` — per-tool permission evaluation
- `systemMessageDescription` — structured prompt examples for LLM
- `ToolOverrideConfig` — config-driven tool customization (modify descriptions, disable tools, change titles)
- `applyToolOverrides()` — processes override list at config load time

**Built-in tools:** readFile, createNewFile, runTerminalCommand, grepSearch, globSearch, ls, editFile, multiEdit, viewDiff, viewRepoMap, viewSubdirectory, codebase, fetchUrlContent, searchWeb, readCurrentlyOpenFile, createRuleBlock, requestRule, readSkill

**MCP integration:** `MCPManagerSingleton` manages all MCP connections. Tools discovered from MCP servers are registered as `MCPTool` instances alongside built-in tools. URI scheme: `mcp://<serverId>/<toolName>`.

### Context Gathering (20+ providers)

**Architecture:**
```
User query → Context providers invoked in parallel
  → Each returns ContextItem[] (title, content, uri, etc.)
  → Items formatted into system message or user prompt
  → Passed to LLM with tool definitions
```

**IContextProvider interface:**
```typescript
interface IContextProvider {
  getDescription(): ContextProviderDescription;
  getContextItems(query: string, extras: ContextProviderExtras): Promise<ContextItem[]>;
  getSubmenuItems(args: LoadSubmenuItemsArgs): Promise<ContextSubmenuItem[]>;
}
```

**Built-in providers:** Clipboard, Codebase, Code, CurrentFile, Custom, Database, DebugLocals, Diff, Discord, Docs, File, Folder, GitCommit, GitHubIssues, Google, CodeReview, Terminal, URL, Web, Open

### Context Compaction

**Algorithm:** Auto-triggers at 85% of context window (configurable via `AUTO_COMPACT_BUFFER_RATIO = 0.8`).

```typescript
// Compaction prompt
const COMPACTION_PROMPT = "Please provide a concise summary of our conversation so far,
  capturing the key context, decisions made, and current state...";

async function compactChatHistory(chatHistory, model, llmApi, options) {
  // 1. Check if compaction prompt + history exceeds context limit
  // 2. If so, prune history to fit
  // 3. Send compaction prompt to LLM
  // 4. LLM produces structured summary
  // 5. Replace old messages with summary message
  // 6. Return compactedHistory + compactionIndex
}
```

**Safety:** Infinite loop detection — if compaction produces output longer than input, stop. Prune last message if still too long after compaction.

### CLI Architecture

**Framework:** Commander.js + Ink (React for terminal)

**Commands:** `chat`, `serve`, `review`, `checks`, `ls` (list sessions), `init`

**Key patterns:**
- Headless mode (JSON/stdout) vs interactive TUI (Ink/React)
- Double Ctrl+C to exit (within 1 second)
- Session management: fork, resume, new
- Slash commands: `/help`, `/clear`, `/exit`, `/model`, `/config`, `/compact`
- `@` for file context attachment
- `!` for shell mode

**Session persistence:** JSON files in `~/.continue/sessions/`

### Repository Intelligence

- **CodebaseIndexer** — indexes codebase for semantic search
- **DocsService** — indexes documentation
- **Tree-sitter queries** — code snippet extraction, import analysis, static context
- **GrepSearch + FileGlobSearch** — built-in search tools
- **CodebaseTool** — semantic codebase search via embeddings

---

## Odysseus — The Feature-Rich Agent Platform

### Architecture Summary

Python FastAPI backend. 30+ tools, 20+ CLI scripts, event bus, task scheduler, background jobs, deep research, MCP integration, context compaction, prompt security.

**Key pattern:** Single FastAPI app with domain routes. Agent loop in `src/agent_loop.py`. Tools in `src/agent_tools/`. Services in `src/services/`.

### Agent Architecture

**Execution model:** Multi-turn tool-calling loop with regex-based tool parsing.

```
User message
  → Action intent classification (action_intents.py)
  → Tool policy composition (tool_policy.py)
  → System prompt assembly (agent_loop.py)
  → LLM call with tool schemas
  → Parse response for tool invocations (3 formats: XML, function-call, markdown)
  → Execute tool → inject result → next iteration
  → Until no tool calls or max iterations
```

**Key abstractions:**
- `ToolSpec` — Pydantic model for tool definitions
- `ToolBlock` — parsed tool invocation from LLM output
- `ToolPolicy` — per-turn tool availability composition
- `McpManager` — MCP server lifecycle management

### Tool System (30+ tools)

**Tool definition pattern:**
```python
# TOOL_SPEC dictionary approach
TOOL_SPEC = {
    "name": "file_read",
    "description": "File reading tool...",
    "inputSchema": {"json": {"type": "object", "properties": {...}, "required": [...]}}
}

def file_read(tool: ToolUse, **kwargs) -> ToolResult:
    ...
```

**Tool invocation formats (3):**
1. XML: `<tool_name><param>value</param></tool_name>`
2. Function-call: `{"name": "tool_name", "arguments": {...}}`
3. Markdown: `` ```tool_name\n{"param": "value"}\n``` ``

**Tool dispatch:** `execute_tool_block()` routes to native handler or MCP fallback. Path confinement enforced for file operations.

**Tool policy composition:**
```python
def build_effective_tool_policy():
    # 1. Start with all tools enabled
    # 2. Apply tool_policy_directives (from system prompt patterns)
    # 3. Apply owner_privilege restrictions
    # 4. Apply plan_mode allowlist (read-only tools only)
    # 5. Apply guide_only_mode (no tools at all)
    # 6. Return effective set
```

### Context Gathering

**Multi-stage pipeline:**
1. Chat context building (message history)
2. Action intent classification (regex patterns)
3. Tool policy composition
4. System prompt assembly (with untrusted context wrapper)
5. Context budgeting (auto-scales based on model's context window)
6. Context compaction (auto-triggers at 85% utilization)

**Prompt security:** `<<<UNTRUSTED_SOURCE_DATA>>>` / `<<<END_UNTRUSTED_SOURCE_DATA>>>` markers for external data. `UNTRUSTED_CONTEXT_POLICY` system prompt injected.

**Context compaction:** Self-summarizes older messages via the same LLM. Produces structured summaries (User Goal, What Was Done, Current State, Pending/Next Steps, Key Context).

### Event Bus & Task Scheduler

**Event bus:** Lightweight pub/sub for automation. Fires events (session creation, message sends). Triggers scheduled tasks that match event thresholds.

**Task scheduler:** Cron-like scheduling with `next_run`/`last_run` tracking. Shared TTL cache for deduplicating concurrent fetches. Shell/file tools offered by default to scheduled agent tasks.

**Background jobs:** Detached subprocesses with PID tracking. Restart-safe (status derived from exit-code files). Auto-continue (monitor re-invokes agent when jobs finish).

### CLI Architecture

**20+ specialized CLIs:** odysseus, odysseus-cookbook, odysseus-mail, odysseus-calendar, odysseus-mcp, odysseus-research, odysseus-backup, odysseus-skills, odysseus-sessions, odysseus-contacts, etc.

**Key pattern:** Each domain gets its own CLI script. All share the same FastAPI backend.

---

## Strands Tools — The Tool Library

### Architecture Summary

Python package (`strands-agents-tools`). 47 tool files. Built on `strands-agents` SDK. Two registration patterns: legacy `TOOL_SPEC` dict and modern `@tool` decorator.

**Key pattern:** Each tool is a self-contained Python module. No central registry — tools discovered individually by the agent.

### Tool Registration

**Legacy pattern (TOOL_SPEC dict):**
```python
TOOL_SPEC = {
    "name": "file_read",
    "description": "...",
    "inputSchema": {"json": {"type": "object", "properties": {...}}}
}
def file_read(tool: ToolUse, **kwargs) -> ToolResult:
    ...
```

**Modern pattern (@tool decorator):**
```python
from strands import tool

@tool
def calculator(expression: str, mode: str = None) -> dict:
    """Calculator powered by SymPy..."""
    ...
```

The `@tool` decorator introspects type annotations + docstring to auto-generate TOOL_SPEC. No manual schema needed.

**Key design:** `agent` parameter auto-injected by Strands SDK — gives tools access to parent agent's registry, model, and context.

### Agent Orchestration

**`use_agent` — Child Agent Creation:**
```python
@tool
def use_agent(
    prompt: str,
    system_prompt: str = None,
    model_provider: str = None,  # "bedrock", "anthropic", "ollama", "env", None (inherit)
    model_settings: dict = None,
    tools: List[str] = None,
) -> Dict[str, Any]:
```
Creates fresh agent with own context. Model switching is core value — cheap model for exploration, expensive for synthesis.

**`swarm` — Multi-Agent Coordination:**
```python
@tool
def swarm(
    task: str,
    agents: List[Dict[str, Any]],  # {name, system_prompt, tools, model_provider}
    max_handoffs: int = 20,
    max_iterations: int = 20,
    execution_timeout: float = 900.0,
    repetitive_handoff_detection_window: int = 8,
) -> Dict[str, Any]:
```
SDK auto-injects `handoff_to_agent` and `complete_swarm_task` tools. Decentralized coordination — peers hand off to each other. Repetitive behavior detection prevents infinite loops.

**`workflow` — DAG-Based Execution:**
```python
# Actions: create, start, status, list, delete
# Tasks with dependencies, priorities (1-5), per-task model providers
# ThreadPoolExecutor with min/max workers
# Persistent state to JSON files
# File system watching for external updates
```

### Dynamic Tool Loading

**Hot-reload:** Strands auto-scans `cwd()/tools/` directory. Python files there are hot-reloaded without explicit calls.

**Explicit loading:** `load_tool(path, name)` registers tools from arbitrary paths. Security toggle: `STRANDS_DISABLE_LOAD_TOOL` env var.

### MCP Client

**Connection architecture:** Per-operation connection pattern (not persistent). Supports stdio, SSE, and streamable HTTP transports.

**MCPTool wrapper:** Wraps external MCP tools in agent-compatible interface. Thread-safe with Lock per connection.

**Tool discovery:** Connect → list_tools → wrap each as MCPTool → register in agent's tool_registry.

### Memory Tools

**5 backends:** Bedrock Knowledge Base, AgentCore Memory, Mem0, Elasticsearch, MongoDB Atlas.

**Pattern:** Action-based dispatch (`action="store|retrieve|delete|list"`). User consent for mutations. Pluggable backends.

---

## Cortex Current Agent Architecture

### Agent System

**Two-agent architecture:** PlannerAgent (produces JSON plan) → ExecutorAgent (executes via LLM tool-calling loop).

**Execution flow:**
```
POST /agents/runs {agent_id, input}
  → AgentRunManager.run_agent()
    → PlannerAgent.plan(input_text) → JSON plan array
    → For each step:
        → ExecutorAgent.run(goal, context)
          → LLM chat with tool schemas
          → Tool calls → execute_tool() → observation
          → Loop until LLM returns text or max 10 iterations
        → Persist AgentStep
        → Emit SSE event
```

**Tool system:** 5 global tools + 4 agent tools. No parameter schemas in tool definitions. HMAC-signed approval tokens for dangerous tools.

**Key limitations:**
- No multi-agent routing (plan references "researcher"/"reviewer" but only executor exists)
- No inter-step dependency resolution
- Agent runs use asyncio tasks (not arq) — lost on restart
- Agents sandboxed to `~/.cortex-agent-workspace`
- Tool schemas lack parameter definitions

### CLI Architecture

**15 Commander.js commands — all stubs.** Zero functionality. No backend API integration.

### Context Assembly

**RAG pipeline:** HybridRetrievalV2 (vector + fulltext) → RRF merge → MMR diversity → token-budgeted context.

**Limitations:**
- Graph search never called by RAG pipeline
- Long-term memory not connected to RAG
- No prompt templating
- Token estimation by character count
- Agent runs don't use RAG pipeline

### Command System

**No formal command system.** Strategic commands in CLAUDE.md are documentation only, not runtime features.

---

## Comparative Analysis

| Dimension | Continue | Odysseus | Strands Tools | Cortex |
|-----------|----------|----------|---------------|--------|
| **Agent model** | Tool-calling loop (OpenAI protocol) | Tool-calling loop (3 parsing formats) | SDK Agent with tool registry | Planner→Executor (2-agent) |
| **Multi-agent** | No | No (single agent) | use_agent, swarm, workflow | No (planner delegates to single executor) |
| **Tool count** | 18 built-in + MCP | 30+ native + MCP | 47 tools + dynamic loading | 9 (5 global + 4 agent) |
| **Tool definition** | TypeScript Tool type with full schema | TOOL_SPEC dict + regex parsing | @tool decorator (auto-schema) | Function + docstring (no schema) |
| **Tool policy** | ToolPolicy + evaluateToolCallPolicy | Per-turn policy composition | ENV toggles + consent gates | HMAC approval tokens |
| **Context providers** | 20+ providers (parallel) | Multi-stage pipeline | N/A (agent SDK handles) | RAG pipeline (sequential) |
| **Context compaction** | Auto at 85% context window | Auto at 85% with structured summary | N/A | None |
| **CLI** | Commander.js + Ink TUI | 20+ specialized CLIs | Pure library (no CLI) | 15 stubs (zero functionality) |
| **MCP** | Full (MCPManagerSingleton) | Full (McpManager) | Full (MCPClient + MCPTool) | None |
| **Event system** | Protocol messages (IDE↔Core) | Event bus + task scheduler | N/A | SSE streaming + WebSocket |
| **Workflow** | No (sequential tool calls) | Deep research orchestration | DAG workflow with ThreadPoolExecutor | No (sequential plan steps) |
| **Session persistence** | JSON files | SQLite + JSON | N/A | PostgreSQL |
| **Prompt security** | Untrusted context markers | UNTRUSTED_SOURCE_DATA guards | Tool consent gates | HMAC approval tokens |
| **Model switching** | Config-driven | Endpoint resolver | Per-task model providers | Single model (llm_manager) |
| **Dynamic loading** | Config-driven tool overrides | Filesystem tools | Hot-reload from tools/ directory | None |
| **Repository intelligence** | CodebaseIndexer + Tree-sitter | Filesystem tools + RAG | N/A | HybridRetrievalV2 + GraphBuilder |

---

## Key Findings for Cortex

### 1. Tool System is the #1 Agent Gap

**Cortex current:** 9 tools, no parameter schemas, no tool policy, no dynamic loading.

**Reference:** Continue (18 tools with full schemas, policy, overrides), Odysseus (30+ tools with 3 parsing formats, policy composition), Strands (47 tools with @tool auto-schema, hot-reload).

**Recommendation:** Rebuild tool system with:
- Full JSON Schema parameter definitions (required for proper LLM function-calling)
- `@tool`-style decorator pattern (auto-generate schema from type hints + docstring)
- Per-tool policy evaluation (allow/deny/ask per context)
- Dynamic tool loading from `tools/` directory
- MCP tool integration

### 2. Context Compaction is Missing

**Cortex current:** No compaction. Token budget is fixed (4000 for RAG, 28000 for history). Simple truncation.

**Reference:** Continue and Odysseus both auto-compact at 85% context utilization. LLM produces structured summary (User Goal, What Was Done, Current State, Pending).

**Recommendation:** Implement auto-compaction:
- Trigger at 80% of model's context window
- LLM summarizes conversation into structured format
- Replace old messages with summary
- Detect infinite loops (compaction output > input)

### 3. Agent Loop Needs Hardening

**Cortex current:** Max 10 iterations, no abort, no compaction, no streaming tool results.

**Reference:** Continue: AbortController per message, streaming via ReadableStream, compaction safety. Odysseus: action intent classification, tool policy per-turn, prompt security guards.

**Recommendation:**
- Add AbortController for cancellation
- Add streaming tool results (not just final output)
- Add action intent classification (route chat vs agent vs command)
- Add prompt security guards for external data

### 4. Multi-Agent Orchestration is Available

**Cortex current:** Single executor. Plan references different agent types but all route to same executor.

**Reference:** Strands provides three patterns:
- `use_agent` — child agent with model switching
- `swarm` — decentralized multi-agent with auto-handoff
- `workflow` — DAG-based with dependency resolution

**Recommendation:** Start with `use_agent` pattern (simplest). Cortex's PlannerAgent can delegate subtasks to child executors with different models/tools. Add swarm/workflow later.

### 5. CLI Needs Implementation

**Cortex current:** 15 stubs, zero functionality.

**Reference:** Continue: Commander.js + Ink TUI with headless mode, session management, slash commands. Odysseus: 20+ specialized CLIs per domain.

**Recommendation:** Implement CLI in phases:
- Phase 1: `cortex status`, `cortex start`, `cortex stop` (daemon management)
- Phase 2: `cortex chat` (interactive agent session)
- Phase 3: `cortex search`, `cortex index` (knowledge base operations)
- Phase 4: `cortex agent run` (agent execution from CLI)

### 6. Context Providers Should Be Pluggable

**Cortex current:** RAG pipeline is monolithic (vector + fulltext + graph).

**Reference:** Continue has 20+ context providers implementing `IContextProvider`. Each provider is independent, returns `ContextItem[]`, and can be loaded in parallel.

**Recommendation:** Refactor RAG into context provider pattern:
- `CodeContextProvider` — code search (current HybridRetrievalV2)
- `MemoryContextProvider` — long-term memory (currently orphaned)
- `GraphContextProvider` — graph traversal (currently unused by RAG)
- `DocumentContextProvider` — document search (current fulltext)
- Each provider implements `getContextItems(query) → ContextItem[]`
- Parallel execution, token budgeting across providers

### 7. Event Bus Enables Decoupled Architecture

**Cortex current:** No event bus. SSE streaming is direct (not pub/sub).

**Reference:** Odysseus has event bus + task scheduler. Events trigger scheduled tasks. Background jobs are restart-safe.

**Recommendation:** Add lightweight event bus:
- Events: `message.received`, `agent.step.completed`, `index.file.changed`, `memory.extracted`
- Subscribers: logging, metrics, notifications, auto-indexing
- Enables decoupled services for daemon mode

### 8. Prompt Security is Underspecified

**Cortex current:** No prompt security guards. External data injected directly into context.

**Reference:** Continue uses `<<<UNTRUSTED_SOURCE_DATA>>>` markers. Odysseus uses `UNTRUSTED_CONTEXT_POLICY` system prompt. Strands uses tool consent gates.

**Recommendation:** Add prompt security layer:
- Wrap all RAG results in guarded blocks
- Inject `UNTRUSTED_CONTEXT_POLICY` into system prompt
- Label all external data sources
- Prevent prompt injection via retrieved content

---

## Recommendations

### ADOPT

| ID | Recommendation | Source | Impact | Effort |
|----|---------------|--------|--------|--------|
| A9 | @tool decorator pattern for auto-schema generation | Strands | Critical | Medium |
| A10 | Context compaction at 80% context window | Continue + Odysseus | Critical | Medium |
| A11 | IContextProvider interface for pluggable context | Continue | Critical | High |
| A12 | Prompt security guards for external data | Continue + Odysseus | Important | Low |
| A13 | Action intent classification (chat vs agent vs command) | Odysseus | Important | Medium |

### ADAPT

| ID | Recommendation | Source | Impact | Effort |
|----|---------------|--------|--------|--------|
| AD13 | Child agent delegation with model switching | Strands use_agent | Critical | Medium |
| AD14 | Per-tool policy evaluation (allow/deny/ask) | Continue ToolPolicy | Important | Medium |
| AD15 | Dynamic tool loading from tools/ directory | Strands load_tool | Important | Low |
| AD16 | CLI implementation (3-phase) | Continue + Odysseus | Critical | High |
| AD17 | Event bus for decoupled services | Odysseus event_bus | Important | Medium |
| AD18 | AbortController for agent cancellation | Continue | Important | Low |
| AD19 | Structured compaction summaries (Goal/Done/State/Pending) | Odysseus context_compactor | Important | Low |
| AD20 | MCP tool wrapper pattern | Strands MCPTool | Important | Medium |

### REPLACE

| ID | Recommendation | Source | Impact | Effort |
|----|---------------|--------|--------|--------|
| R5 | Replace planner→executor with tool-calling loop | Continue + Odysseus | Critical | High |
| R6 | Replace manual tool schemas with auto-generated | Strands @tool | Critical | Medium |
| R7 | Replace fixed token budget with adaptive compaction | Continue + Odysseus | Critical | Medium |

### DEFER

| ID | Recommendation | Source | Impact | When |
|----|---------------|--------|--------|------|
| D13 | Swarm multi-agent coordination | Strands swarm | Important | After AD13 |
| D14 | DAG workflow execution | Strands workflow | Important | After AD13 |
| D15 | Ink-based TUI for CLI | Continue | Nice-to-have | Phase 4 CLI |
| D16 | Deep research orchestration | Odysseus | Important | After MI phases |
| D17 | Task scheduler (cron-like) | Odysseus | Important | Daemon Phase 3 |

### REJECT

| ID | Recommendation | Source | Reason |
|----|---------------|--------|--------|
| X10 | 3 tool invocation formats (XML/function/markdown) | Odysseus | Use standard OpenAI function-calling only |
| X11 | Regex-based tool parsing | Odysseus | Use structured JSON tool calls |
| X12 | Separate CLI per domain (20+ CLIs) | Odysseus | Single CLI with subcommands is cleaner |

---

## Priority-Ordered Summary

| Priority | ID | Classification | Impact | Effort | Phase |
|----------|-----|---------------|--------|--------|-------|
| 1 | R5 | REPLACE | Critical | High | Phase 2 (service abstraction) |
| 2 | A9 | ADOPT | Critical | Medium | Phase 2 |
| 3 | R6 | REPLACE | Critical | Medium | Phase 2 |
| 4 | A10 | ADOPT | Critical | Medium | Phase 2 |
| 5 | R7 | REPLACE | Critical | Medium | Phase 2 |
| 6 | A11 | ADOPT | Critical | High | Phase 2-3 |
| 7 | AD13 | ADAPT | Critical | Medium | Phase 3 |
| 8 | AD16 | ADAPT | Critical | High | Phase 4 |
| 9 | A13 | ADOPT | Important | Medium | Phase 3 |
| 10 | A12 | ADOPT | Important | Low | Phase 2 |
| 11 | AD14 | ADAPT | Important | Medium | Phase 3 |
| 12 | AD15 | ADAPT | Important | Low | Phase 2 |
| 13 | AD17 | ADAPT | Important | Medium | Phase 3 |
| 14 | AD18 | ADAPT | Important | Low | Phase 2 |
| 15 | AD19 | ADAPT | Important | Low | Phase 2 |
| 16 | AD20 | ADAPT | Important | Medium | Phase 3 |
| 17 | D13 | DEFER | Important | High | After AD13 |
| 18 | D14 | DEFER | Important | High | After D13 |
| 19 | D15 | DEFER | Nice-to-have | High | Phase 4 |
| 20 | D16 | DEFER | Important | High | After MI phases |
| 21 | D17 | DEFER | Important | Medium | Phase 3 |
