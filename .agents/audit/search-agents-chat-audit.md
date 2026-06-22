# Comprehensive Audit: Search, Agents, and Chat Pages

**Date:** 2026-06-22  
**Scope:** Frontend components, API clients, backend endpoints, type alignment, and UI/UX quality

---

## 1. SEARCH PAGE

### 1.1 File Paths

| File | Path | Lines |
|------|------|-------|
| Page component | `frontend/app/search/page.tsx` | 198 |
| SearchResults component | `frontend/app/search/SearchResults.tsx` | 106 |
| SearchFilters component | `frontend/app/search/SearchFilters.tsx` | 107 |
| GraphView component | `frontend/app/search/GraphView.tsx` | 213 |
| Error boundary | `frontend/app/search/error.tsx` | 25 |
| Tests | `frontend/app/search/page.test.tsx` | 102 |
| API client | `frontend/src/shared/api/search.ts` | 59 |
| Backend endpoint | `backend/app/api/v1/search.py` | 236 |

### 1.2 UI Structure

The search page uses a vertical layout inside `DashboardShell` with:
- `NeuralNetwork` background (intensity="low")
- Hero header with title "Search your workspace"
- Conversational search input (text field + Search button)
- AI Answer panel (card with Sparkles icon, shows LLM-synthesized answer)
- Sources list (cards with file icons, scores, content previews)
- Empty state with large search icon

**Components defined but NOT used in page.tsx:**
- `SearchResults.tsx` -- A standalone `SearchResults` component exists but is **NOT imported or used** in `page.tsx`. The page renders its own inline results list instead.
- `SearchFilters.tsx` -- A standalone `SearchFilters` component exists but is **NOT imported or used** in `page.tsx`. No filter UI is shown at all.
- `GraphView.tsx` -- A standalone `GraphView` component exists but is **NOT imported or used** in `page.tsx`. No graph visualization is accessible from the search page.

### 1.3 Current Functionality

**What works:**
- Search input accepts text and triggers on Enter or button click
- Calls `searchApi.unified()` for results (line 26)
- Calls `searchApi.answer()` for AI-powered answer (line 31)
- Graceful fallback when `answer()` fails -- synthesizes a basic client-side answer (lines 34-43)
- Results display with source icons (code/memory/file), file paths, content previews, scores
- Loading state disables button and shows "Searching..."
- Empty state shown before first search

**What is broken or missing:**
1. **SearchFilters component is orphaned.** `SearchFilters.tsx` supports `repo_id`, `node_type`, `language`, and `max_results` filters but is never rendered. Users cannot filter search results by repository, node type, or language.
2. **SearchResults component is orphaned.** `SearchResults.tsx` has a richer rendering (with score badges, type pills, truncated file names) but `page.tsx` uses a simpler inline implementation instead.
3. **GraphView is unreachable.** The graph visualization component requires a `repoId` prop and renders a canvas-based node graph. It is never mounted anywhere in the search page.
4. **Pagination is not implemented client-side.** The backend supports cursor-based pagination (`next_cursor`, `has_more` fields in `SearchResponse`), and the API client exposes it, but `page.tsx` makes a single request with `max_results: 20` and never uses `next_cursor`.
5. **`unified()` GET endpoint ignores some params.** The backend GET handler (`unified_search_get` at line 159) accepts `query`, `repo_id`, `max_results`, `cursor` but **not** `node_type` or `language`. These are only supported by the POST endpoint. The frontend API client always calls GET (`api.get`), so `node_type` and `language` parameters are silently dropped.
6. **No debounce on search input.** No debouncing or "search as you type" -- only explicit Enter/button trigger.
7. **Result links are non-functional.** `ExternalLink` icon is rendered (line 173) but there is no `href` or click handler to navigate to the result.
8. **Score display inconsistency.** `page.tsx` uses `(result.score * 100).toFixed(0)` (line 169) which will throw if `score` is `undefined`/`null`. The `SearchResult` type has `score: number` (non-optional), but the backend could theoretically return null.

### 1.4 Backend API Endpoints

| Method | Path | Handler | Response Model |
|--------|------|---------|----------------|
| GET | `/api/v1/search` | `unified_search_get` | `SearchResponse` |
| POST | `/api/v1/search` | `unified_search` | `SearchResponse` |
| POST | `/api/v1/search/answer` | `search_with_answer` | `SearchAnswerResponse` |

**Note:** The graph endpoints (`/api/v1/repos/{repoId}/graph`, `/api/v1/repos/{repoId}/graph/node/{nodeId}`) are defined in the API client but live in the repository router, not the search router.

### 1.5 Type Mismatches (Frontend vs Backend)

| Issue | Frontend Type | Backend Type | Severity |
|-------|--------------|--------------|----------|
| `SearchResponse.results` vs `SearchResult` | `SearchResult[]` in `SearchResponse` (types.ts:246) | `list[SearchResult]` (search.py:60) | OK - aligned |
| `SearchResult.file_path` | `string` (non-optional in types.ts:237) | `str = ""` (default in search.py:53) | OK - backend defaults |
| `SearchAnswerResponse.results` | `SearchResult[]` (types.ts:254) | `list[SearchResult]` (search.py:181) | OK - aligned |
| `SearchAnswerResponse.results` in answer endpoint | Includes `results` in response (search.py:223-235) | Frontend `answer()` returns `SearchAnswerResponse` | **Mismatch**: The frontend `searchApi.answer()` returns `Promise<SearchAnswerResponse>` which includes a `results` array, but the page only reads `.answer` (line 32). The returned results from the answer endpoint are silently discarded. |
| Missing `total` field | Frontend `SearchResponse` has `total` (types.ts:246) | Backend includes `total` (search.py:62) | OK - aligned |
| `next_cursor`/`has_more` | Defined in types (types.ts:248-249) | Defined in backend (search.py:63-64) | Unused - neither side actively uses pagination |

### 1.6 Test Coverage

- 5 tests covering: render, search, AI answer panel, empty results, loading state
- Tests mock `searchApi.unified` and `searchApi.answer` correctly
- **Missing test coverage:** GraphView, SearchFilters, SearchResults (standalone), error handling, pagination

---

## 2. AGENTS PAGE

### 2.1 File Paths

| File | Path | Lines |
|------|------|-------|
| Page component | `frontend/app/agents/page.tsx` | 334 |
| AgentEditor component | `frontend/app/agents/AgentEditor.tsx` | 208 |
| AgentChat component | `frontend/app/agents/AgentChat.tsx` | 300 |
| Error boundary | `frontend/app/agents/error.tsx` | 25 |
| Tests | `frontend/app/agents/page.test.tsx` | 144 |
| API client | `frontend/src/shared/api/agent.ts` | 118 |
| Backend endpoint | `backend/app/api/v1/agents.py` | 497 |
| Backend schemas | `backend/app/schemas/agent.py` | 116 |

### 2.2 UI Structure

The agents page uses a two-panel layout inside `DashboardShell`:
- **Left Panel** (`CollapsiblePanel`): Agent list + recent runs
  - Header with Bot icon and agent count
  - Agent list (selectable buttons with name, description, delete icon)
  - Recent runs section at bottom (status icons, truncated input)
  - "+" button to create new agent
- **Main Content Area**:
  - When no agent selected: Empty state with floating Bot icon animation, "Select or create an agent" message, Create Agent button
  - When agent selected: Agent name/description header, Edit button, `AgentChat` component
- **Modals**:
  - Create Agent modal: Name, Description, System Prompt fields, Cancel/Create buttons
  - Edit Agent modal (`AgentEditor`): Name, Description, System Prompt, Model selector (dropdown from `modelsApi.list`), Tools checkboxes (search, read_file, write_file, list_files), Cancel/Save buttons

### 2.3 Current Functionality

**What works:**
- Agent list loads on mount via `agentApi.list()` (line 58)
- Recent runs load via `agentApi.listRuns({ limit: 20 })` (line 58)
- Create agent with name, description, system_prompt
- Delete agent with confirmation dialog
- Select agent to open chat interface
- Edit agent (name, description, system_prompt, model_id, tools)
- AgentChat: sends message via `agentApi.run()`, polls for status, displays result with collapsible steps

**What is broken or missing:**
1. **AgentChat uses polling, not SSE streaming.** The backend exposes `/api/v1/agents/runs/{run_id}/stream` (SSE endpoint at agents.py:163), but `AgentChat` uses polling (2-second intervals, up to 120 attempts = 4 minutes max). This creates latency and wasted requests.
2. **No feedback UI.** The API client has `addFeedback()` (agent.ts:112), the backend has feedback endpoints (agents.py:231-290), but there is no UI component for users to rate agent runs.
3. **No metrics display.** The backend has `/agents/metrics` endpoint (agents.py:305-356) returning success_rate, avg_duration, etc., but the frontend never calls it and has no metrics dashboard.
4. **No model selection during agent creation.** The Create modal (page.tsx:261-319) only has name, description, system_prompt fields. The Edit modal has model selection, but creation defaults to `"local"`. Users cannot choose a model when creating.
5. **No tool selection during agent creation.** Same as above -- tools are only configurable in the Edit modal.
6. **Create modal missing model/tools.** The `handleCreateAgent` (page.tsx:75) does not pass `model_id` or `tools` -- only name, description, system_prompt.
7. **AgentChat polling timeout is generous but silent.** If the agent takes >4 minutes, the user gets "Timed out waiting for agent run" with no retry option.
8. **No message persistence.** `AgentChat` stores messages in local state (line 44). If the user navigates away and comes back, all conversation history is lost.
9. **Run history not linked.** The "Recent Runs" section in the sidebar shows truncated inputs but clicking on a run does nothing.
10. **Agent activation toggle missing.** `AgentUpdatePayload` supports `is_active` (agents.py:53), but the UI has no toggle for activating/deactivating agents.

### 2.4 Backend API Endpoints

| Method | Path | Handler | Response Model |
|--------|------|---------|----------------|
| GET | `/api/v1/agents` | `list_agents` | `AgentListResponse` |
| POST | `/api/v1/agents` | `create_agent` | `AgentCreateResponse` |
| GET | `/api/v1/agents/{agent_id}` | `get_agent` | `AgentGetResponse` |
| PUT | `/api/v1/agents/{agent_id}` | `update_agent` | `AgentUpdateResponse` |
| DELETE | `/api/v1/agents/{agent_id}` | `delete_agent` | `{"status": "deleted"}` |
| POST | `/api/v1/agents/runs` | `create_run` | `AgentRunCreateResponse` |
| GET | `/api/v1/agents/runs` | `list_runs` | `AgentRunListResponse` |
| GET | `/api/v1/agents/runs/{run_id}` | `get_run` | `AgentRunGetResponse` |
| GET | `/api/v1/agents/runs/{run_id}/status` | `get_run_status_endpoint` | `AgentRunStatusResponse` |
| POST | `/api/v1/agents/runs/{run_id}/stream` | `stream_run_events` | SSE stream |
| GET | `/api/v1/agents/runs/{run_id}/steps` | `get_run_steps` | `AgentRunStepsResponse` |
| POST | `/api/v1/agents/runs/{run_id}/feedback` | `add_feedback` | `AgentFeedbackCreateResponse` |
| GET | `/api/v1/agents/runs/{run_id}/feedback` | `get_feedback` | `AgentFeedbackListResponse` |
| GET | `/api/v1/agents/metrics` | `get_agent_metrics` | `AgentMetricsResponse` |

### 2.5 Type Mismatches (Frontend vs Backend)

| Issue | Frontend Type | Backend Type | Severity |
|-------|--------------|--------------|----------|
| `Agent.tools` | `string[]` (types.ts:341) | `tools_json` (JSON string on model, serialized as `list[str]` by schema) | **Handled**: Frontend API client parses JSON string (agent.ts:16) |
| `AgentRun.output` | `string \| null` (types.ts:354) | `output: str \| None` (agent.py:60) | OK |
| `AgentRun.error` | `string \| null` (types.ts:355) | `error: str \| None` (agent.py:61) | OK |
| `AgentRun` missing `completed_at` in frontend type | `completed_at: string \| null` (types.ts:357) | `completed_at: datetime \| None` (agent.py:62) | OK - serialized as ISO string |
| `AgentRunInfo.input` serialization alias | Frontend expects `input` | Backend uses `serialization_alias="input_text"` (agent.py:58) | **Potential issue**: If the schema serialization alias changes the field name in the response, the frontend would get `input_text` instead of `input`. Need to verify actual response shape. |
| `AgentCreateResponse` missing `status` | Frontend type: `{ status: string; agent: Agent }` (types.ts not explicitly defined, inferred from API client) | Backend: `AgentCreateResponse` with `status: str` and `agent: AgentInfo` | OK - aligned |
| `RunListResponse` not in types | Frontend defines `RunListResponse` (types.ts:382-384) | Backend: `AgentRunListResponse` with `runs: list[AgentRunInfo]` | OK - names differ but structure matches |

### 2.6 Test Coverage

- 4 tests covering: render list, create agent, open chat, show config
- Tests mock `agentApi.list`, `agentApi.create`, `agentApi.listRuns`, `agentApi.delete`
- **Missing test coverage:** AgentChat component, AgentEditor component, delete flow, edit flow, SSE streaming, feedback, polling timeout

---

## 3. CHAT PAGE

### 3.1 File Paths

| File | Path | Lines |
|------|------|-------|
| Page component | `frontend/app/chat/page.tsx` | 374 |
| Error boundary | `frontend/app/chat/error.tsx` | 25 |
| Tests | `frontend/app/chat/page.test.tsx` | 294 |
| API client (conversations) | **NONE** -- uses raw `api` calls | N/A |
| Backend endpoint | `backend/app/api/v1/conversations.py` | 220 |
| Backend schemas | `backend/app/schemas/conversation.py` | 47 |
| Backend model | `backend/app/models/conversation.py` | 47 |

### 3.2 UI Structure

The chat page uses a two-panel layout inside `DashboardShell`:
- **Sidebar** (w-64):
  - "New Chat" button (Plus icon + text)
  - Conversation list (MessageSquare icon + title, hover-reveal Trash2 delete button)
  - Active conversation highlighted with `bg-bg-hover`
- **Chat Area** (flex-1):
  - Messages area (scrollable, space-y-4)
    - Empty state: "Start a conversation with Cortex."
    - User messages: right-aligned Card with accent background
    - Assistant messages: left-aligned Card with MarkdownRenderer
    - Source references: inline chips showing file names
    - Token count display
    - Streaming content with pulsing indicator
    - "Thinking..." loading state
  - Input area (bottom-fixed):
    - Model selector dropdown (Brain/Cpu icons, lists available models)
    - Text input with Enter-to-send
    - Send button (accent colored)

### 3.3 Current Functionality

**What works:**
- Conversation list loads on mount via direct `api.get` call (line 57)
- Messages load when conversation selected (line 69)
- Create new conversation (line 88)
- Delete conversation (line 195)
- Send message with streaming SSE response (line 109)
- Real-time content streaming with `setStreamingContent` (line 156)
- Model selector dropdown populated from `/api/v1/models` (line 83)
- Markdown rendering with code syntax highlighting (`MarkdownRenderer`)
- Source references shown as inline chips
- Token count displayed per message
- Abort controller for cancellation (line 49, though not exposed in UI)
- Auto-scroll to bottom on new messages (line 79)

**What is broken or missing:**
1. **No dedicated API client module.** Unlike search (`searchApi`) and agents (`agentApi`), chat has no `conversationApi` module. All API calls are made directly with `api.get`/`api.post`/`api.delete` and raw `fetch`. This is inconsistent with the rest of the codebase.
2. **Create conversation response type mismatch.** The frontend calls `api.post<{ id: number }>(...)` (line 89) but the backend returns `ConversationResponse` which includes `id`, `title`, `repo_id`, `model_used`, `message_count`, `total_tokens`, `created_at`, `updated_at`. The frontend discards all fields except `id` and manually constructs the `Conversation` object (lines 92-106).
3. **Conversation list response type mismatch.** Frontend calls `api.get<{ conversations: Conversation[] }>(...)` (line 57) but backend returns `ConversationListResponse` which includes `conversations` AND `total`. The `total` field is ignored.
4. **Message response type mismatch.** Frontend calls `api.get<{ messages: Message[] }>(...)` (line 70) and uses a local `Message` interface (lines 16-22). The backend `ConversationDetailResponse` returns the conversation details plus `messages: list[ConversationMessageResponse]`. The frontend ignores conversation metadata.
5. **No conversation renaming.** Users can create and delete conversations but cannot rename them. The title is always "New Conversation" (line 90).
6. **No message editing or regeneration.** Once sent, messages cannot be edited or regenerated.
7. **No conversation search.** With many conversations, there is no way to search or filter the sidebar list.
8. **No stop/cancel button.** The `abortRef` exists (line 49) but there is no UI button to cancel an in-progress stream.
9. **No markdown in user messages.** User messages are rendered as plain text (`<p className="text-text whitespace-pre-wrap">`) while assistant messages use `MarkdownRenderer`. If user pastes markdown, it renders as plain text.
10. **SSE parsing fragility.** The `sendMessage` function (line 109) manually parses SSE with `res.body?.getReader()` and TextDecoder. Malformed SSE lines are silently skipped (line 174) with no user feedback.
11. **`streamingContent` cleared prematurely.** In the `finally` block (line 191), `setStreamingContent("")` is called even if the stream completed normally. This is fine because the `done` event already cleared it, but it's a redundant call.
12. **No conversation export.** No ability to export conversations as markdown/text.
13. **No keyboard shortcut hints.** Enter sends, but there is no Shift+Enter for newline hint in the UI.

### 3.4 Backend API Endpoints

| Method | Path | Handler | Response Model |
|--------|------|---------|----------------|
| GET | `/api/v1/conversations` | `list_conversations` | `ConversationListResponse` |
| POST | `/api/v1/conversations` | `create_conversation` | `ConversationResponse` |
| GET | `/api/v1/conversations/{conversation_id}` | `get_conversation` | `ConversationDetailResponse` |
| DELETE | `/api/v1/conversations/{conversation_id}` | `delete_conversation` | `{"status": "deleted"}` |
| POST | `/api/v1/conversations/{conversation_id}/messages` | `send_message` | SSE stream |

### 3.5 Type Mismatches (Frontend vs Backend)

| Issue | Frontend Type | Backend Type | Severity |
|-------|--------------|--------------|----------|
| `Conversation` type | `Conversation` (types.ts:723-732) | `ConversationResponse` (conversation.py:28-38) | **Aligned** but created manually on frontend |
| `Message` (local) vs `ConversationMessageResponse` | Local interface (page.tsx:16-22) with `role: string`, `tokens?: number`, `sources?: Array<...>` | `ConversationMessageResponse` (conversation.py:18-25) with `role: str`, `tokens: int`, no `sources` | **Mismatch**: Frontend `Message` has optional `sources` field not in backend schema. Backend messages never include `sources` -- these only come from the SSE stream `done` event. |
| `create_conversation` body | `{ title: "New Conversation" }` | `CreateConversationRequest(title: str, repo_id: int \| None)` | OK - repo_id optional |
| `create_conversation` response | Expects `{ id: number }` | Returns `ConversationResponse` (full object) | **Wasteful**: Frontend discards most fields |
| `list_conversations` response | Expects `{ conversations: Conversation[] }` | Returns `ConversationListResponse(conversations, total)` | **Missing `total`** in frontend usage |
| `get_conversation` response | Expects `{ messages: Message[] }` | Returns `ConversationDetailResponse` (full detail + messages) | **Missing conversation metadata** in frontend usage |
| `SendMessageRequest.content` | Sent as `{ content: ..., model: ... }` | `SendMessageRequest(content: str, model: str \| None)` | OK - aligned |

### 3.6 Test Coverage

- 8 tests covering: render input, conversation list, create conversation, model selector, empty state, send on Enter, send on button click, display user message
- Tests mock `api.get`, `api.post`, `api.delete`, `fetch`, `MarkdownRenderer`, `Dropdown`
- **Missing test coverage:** Streaming response handling, conversation deletion flow, model selection effect on messages, error states, abort/cancel, markdown rendering integration

---

## 4. CROSS-CUTTING ISSUES

### 4.1 Missing `conversationApi` Client

The search page has `searchApi`, the agents page has `agentApi`, but the chat page has **no dedicated API client**. All calls are inline with raw `api.get`/`api.post`. This is inconsistent and makes the chat code harder to maintain.

**Recommendation:** Create `frontend/src/shared/api/conversation.ts` with methods: `list()`, `create()`, `get()`, `delete()`, `sendMessage()`.

### 4.2 Orphaned Components (Search)

Three well-built components (`SearchResults`, `SearchFilters`, `GraphView`) exist in `frontend/app/search/` but are never imported by `page.tsx`. The page duplicates simpler versions of the results rendering inline.

### 4.3 SSE Streaming Inconsistency

- **Chat page:** Uses SSE streaming correctly via `fetch` + `ReadableStream` (page.tsx:124-178)
- **AgentChat:** Uses polling instead of the available SSE endpoint (`/api/v1/agents/runs/{run_id}/stream`)
- **Search page:** No streaming (synchronous POST for answer)

### 4.4 Error Boundary Duplication

All three pages (`search/error.tsx`, `agents/error.tsx`, `chat/error.tsx`) have identical error boundary implementations (25 lines each, same UI). This should be extracted to a shared component.

### 4.5 Auth Redirect Pattern

Both agents and chat pages redirect to `/auth` if not logged in (agents: page.tsx:51, chat: page.tsx:52). The search page does **not** perform this check -- it relies on the backend 401 response to fail silently.

### 4.6 Design System Compliance

All three pages follow the Warm Neural Dark design system:
- Use semantic tokens (`bg-bg-elevated`, `border-border-subtle`, `text-text`, etc.)
- Use `rounded-xl` / `rounded-2xl` for cards and inputs
- Use `framer-motion` for animations
- Use Lucide icons consistently
- Use `cn()` utility for conditional classes

**Minor deviations:**
- `page.tsx` (chat) uses inline string concatenation for conditional classes (line 223-227) instead of `cn()`
- `SearchFilters.tsx` uses `../../src/lib/utils` relative import instead of `@/lib/utils`

---

## 5. SUMMARY OF FINDINGS

### Severity: HIGH

| # | Page | Issue | Impact |
|---|------|-------|--------|
| 1 | Search | `SearchFilters`, `SearchResults`, `GraphView` components are orphaned/unused | Users cannot filter results or view code graph |
| 2 | Search | GET endpoint drops `node_type`/`language` params silently | Filter parameters have no effect when using GET |
| 3 | Chat | No dedicated `conversationApi` client | Inconsistent architecture, harder maintenance |
| 4 | Chat | Create conversation response type mismatch (discards most fields) | Potential bugs if backend response shape changes |
| 5 | Agents | No SSE streaming in AgentChat (uses polling) | Latency, wasted requests, poor UX for long-running agents |

### Severity: MEDIUM

| # | Page | Issue | Impact |
|---|------|-------|--------|
| 6 | Search | No pagination client-side | Limited to 20 results max |
| 7 | Search | Result links are non-functional (no href/click) | Users cannot navigate to code from results |
| 8 | Agents | No feedback UI despite backend support | Cannot collect user ratings on agent quality |
| 9 | Agents | No metrics display despite backend support | No visibility into agent performance |
| 10 | Agents | No model/tool selection during creation | Must create then edit to configure fully |
| 11 | Chat | No conversation renaming | Conversations stuck with "New Conversation" title |
| 12 | Chat | No stop/cancel button for streaming | Cannot abort long-running responses |
| 13 | Chat | No message editing/regeneration | Cannot fix mistakes or retry responses |

### Severity: LOW

| # | Page | Issue | Impact |
|---|------|-------|--------|
| 14 | Search | No debounce on search input | Minor -- explicit trigger is acceptable |
| 15 | Search | `score` could be undefined despite type | Potential runtime error on rare edge case |
| 16 | Agents | AgentChat messages not persisted | Conversation lost on navigation |
| 17 | Agents | Error boundary duplicated across all 3 pages | Code duplication, not DRY |
| 18 | Chat | No conversation search/filter in sidebar | Hard to find conversations with many entries |
| 19 | Chat | No Shift+Enter hint for newlines | Minor UX gap |
| 20 | Chat | No conversation export | Cannot share or archive conversations |
| 21 | All | Search page missing auth redirect check | Inconsistent auth behavior |
| 22 | Search | `SearchFilters` uses relative imports instead of aliases | Minor inconsistency |
| 23 | Chat | `page.tsx` uses string concatenation instead of `cn()` | Minor design system deviation |

