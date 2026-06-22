# Cortex UX/Productivity/Observability Prioritized Roadmap

Generated: 2026-06-22

---

## Part 1: Critical Evaluation of Frontend Audit Recommendations

### Recommendation 1: Decompose Memory page into smaller components

**Verdict: REJECT — Do not decompose.**

The memory page is 1310 lines with 30+ state variables. However:

- **State is tightly coupled.** Sync status, learning data, memory entries, search results, and view modes all interact. Splitting into components would require either prop drilling 15+ props through 3-4 levels, or introducing a context provider that adds more complexity than it removes.
- **The Vault page decomposition (7 hooks) is not a model to replicate everywhere.** Vault has genuinely independent concerns (lock state, navigation, selection, CRUD, UI mode). Memory's concerns are interdependent — sync status affects what's displayed, learning data depends on the same API calls, view mode determines which data is visible.
- **Line count is not a code smell.** The page is well-structured with clear sections: data fetching (lines 133-292), sync management (lines 228-267), learning data (lines 150-177), memory operations (lines 273-350), rendering (lines 700+). The complexity is inherent to the feature, not accidental.
- **Splitting would create 5-6 new files** (MemorySyncPanel, MemoryGraphView, MemoryListView, MemoryLearningView, MemorySyncModal) that each need 8-12 props passed from the parent. The parent would still need all 30+ state variables to coordinate them.
- **No maintainability gain.** Each extracted component would still need to understand the full sync/memory/learning state graph. The cognitive load doesn't decrease — it just moves across files.

**If the page needs improvement, the right move is:**
- Extract the `categoryColors`, `categoryNodeColors`, `categoryChipColors` constants to a shared file (trivial, no architectural impact)
- Extract the sync modal form logic into a custom hook (`useSyncModal`) — this is genuinely independent and could reduce ~100 lines from the main component
- But a full decomposition is a solution in search of a problem

**Priority: None — Skip entirely.**

---

### Recommendation 2: Wire up Cmd+K command palette

**Verdict: ALREADY DONE — The audit is incorrect.**

Evidence:
- `DashboardShell.tsx:571`: `<CommandPalette open={commandPaletteOpen} onOpenChange={setCommandPaletteOpen} />` — the component IS rendered
- `DashboardShell.tsx:454`: `<button onClick={() => setCommandPaletteOpen(true)}>` — the header search button opens it
- `CommandPalette.tsx:44`: `if ((e.metaKey || e.ctrlKey) && e.key === "k")` — keyboard shortcut IS registered
- `CommandPalette.tsx:25-36`: 10 page navigation items are defined
- The component uses `cmdk` with proper search, keyboard navigation, and animated overlay

**The command palette is fully functional.** The audit incorrectly stated it was "not wired up." It is wired up, rendered, and responds to Cmd+K.

**However, there are genuine improvements possible:**
- The palette only navigates to pages. It could also search conversations, agents, models, and memory entries.
- It could show recent actions or frequently visited pages.
- It could integrate with the search API for cross-entity search.

**Priority: Enhancement (not a fix) — Can be improved later as a power-user feature.**

---

### Recommendation 3: Apply accent color preference globally

**Verdict: VALID — This is a broken feature that should be fixed.**

The settings page saves `accent_color` to user preferences (settings/page.tsx:59-66), but:
- No code reads this preference and applies it to CSS variables
- The accent color is hardcoded as `cyan` (#06b6d4) in `tailwind.config.ts`
- Changing the setting has zero visual effect — it's a dead feature

**This is a genuine bug, not an enhancement.** Users who change their accent color expect it to work. The feature exists in the UI, saves to the backend, but does nothing.

**Implementation approach:**
1. Add a CSS variable `--accent` and `--accent-rgb` to `:root` in `globals.css`
2. Create a React context/provider that reads user preferences and sets these variables
3. Replace hardcoded `cyan` references in Tailwind config with the CSS variable
4. Apply font size preference similarly (set `fontSize` on `<html>`)

**Backend required:** None — preferences are already saved and returned in the user profile.

**Priority: HIGH — Fix broken feature.**

---

### Recommendation 4: Add conversation previews to chat sidebar

**Verdict: VALID but requires backend changes — Implement as a focused feature.**

The chat sidebar currently shows conversation titles only. Adding last message previews would:
- Help users quickly identify conversations without opening them
- Match the UX pattern of every messaging app (WhatsApp, Telegram, Slack)
- Reduce time-to-find for users with many conversations

**Backend requirement:**
- Add `last_message_content: str | None` and `last_message_at: datetime | None` to `ConversationResponse` schema
- Modify `list_conversations` to JOIN with the last message and include a truncated preview
- This is a clean, small backend change (5-10 lines in schema, 10-15 lines in query)

**Frontend requirement:**
- Add preview text to conversation list items in `chat/page.tsx`
- Truncate to ~60 characters with ellipsis
- Show timestamp relative ("2m ago", "1h ago")

**Priority: MEDIUM — High user value, low implementation cost.**

---

### Recommendation 5: Add batch download operations

**Verdict: REJECT — Low value, high complexity.**

The downloads page already has individual pause/resume/cancel/retry buttons per download. Batch operations would require:
- Multi-select state management
- Checkbox UI per download item
- Batch action toolbar
- Confirmation modals for batch operations
- Error handling for partial failures (some succeed, some fail)

**Why this is low value:**
- Downloads are typically 1-3 at a time, not dozens
- Each download has different failure modes (network, disk space, permission)
- Batch retry doesn't help if the failure is systemic (e.g., Ollama server down)
- The existing per-item controls are sufficient for the actual use case

**This is a solution in search of a problem.** The audit identified it because it exists in other download managers, not because users need it here.

**Priority: None — Skip entirely.**

---

## Part 2: Higher-Value Improvements (Beyond Audit Recommendations)

These are features and improvements that would have greater impact on Cortex's usability, power, and product quality than the audit recommendations.

### Tier 1: High Impact, Low Effort (Implement Now)

#### 1.1 Fix Accent Color Application (Broken Feature)

**User value:** Users expect their accent color preference to work. Currently it's a dead feature.
**Engineering cost:** ~2 hours. Create a provider, add CSS variables, update Tailwind config.
**Maintenance cost:** Low. One provider, one CSS variable set.
**Long-term impact:** Foundation for theming system. Every future color preference builds on this.
**Priority:** HIGH — Fix broken feature.
**Timing:** Now.

#### 1.2 Conversation Previews in Chat Sidebar

**User value:** Immediate identification of conversations without opening them. Reduces time-to-find.
**Engineering cost:** ~3 hours. Backend: 15 lines (schema + query). Frontend: 20 lines (UI + formatting).
**Maintenance cost:** Low. Simple data addition, no new patterns.
**Long-term impact:** Improves chat UX, which is one of the most-used features.
**Priority:** MEDIUM-HIGH — High value, low cost.
**Timing:** Now.

#### 1.3 Notification Center (Backend exists, frontend missing)

**User value:** The backend has full notification CRUD (list, mark read, mark all read, delete) but the frontend only shows an unread count badge. Users cannot view, manage, or dismiss notifications.
**Engineering cost:** ~4 hours. Create a NotificationPanel dropdown, wire to existing API endpoints.
**Maintenance cost:** Low. Reuses existing backend infrastructure.
**Long-term impact:** Enables future notification types (download complete, sync finished, agent run complete, system alerts).
**Priority:** HIGH — Backend infrastructure already exists, just needs frontend.
**Timing:** Now.

---

### Tier 2: High Impact, Medium Effort (Implement Next)

#### 2.1 Model Quick Switcher (Global)

**User value:** Currently, model selection is page-specific (chat has a dropdown, agents have a dropdown, but they're independent). A global model switcher would let users change the active model from anywhere, with the selection persisting across pages.
**Engineering cost:** ~6 hours. Create a model context provider, add a model switcher to DashboardShell header, persist selection to localStorage.
**Maintenance cost:** Low. One context, one UI component.
**Long-term impact:** Reduces friction when experimenting with different models. Users can quickly compare outputs across pages.
**Priority:** MEDIUM-HIGH — Significant UX improvement for power users.
**Timing:** After Tier 1.

#### 2.2 Background Task Center

**User value:** Background tasks (embedding, indexing, graph building, sync) run silently. Users have no visibility into what's happening, how long it will take, or whether something failed. A task center would show:
- Active tasks with progress bars
- Recent task history with success/failure status
- Task logs for debugging

**Engineering cost:** ~8 hours. Backend: Add a `TaskLog` model and API endpoints. Frontend: Create a TaskCenter panel (could be a slide-over or modal). Wire to existing arq worker events.
**Maintenance cost:** Medium. New model, new API, new UI component. But the arq worker infrastructure already exists.
**Long-term impact:** Critical for user trust. Users need to know that background work is happening and succeeding. Without this, users will think the system is broken when indexing takes 5 minutes.
**Priority:** HIGH — Fills a critical visibility gap.
**Timing:** After Tier 1.

#### 2.3 Search Results Improvements

**User value:** The search page works but could be more powerful:
- Filter by source type (code, document, memory, conversation)
- Filter by date range
- Sort by relevance, date, or source
- Show search query expansion (what terms were added/modified)

**Engineering cost:** ~6 hours. Backend: Add filter params to search endpoint. Frontend: Add filter chips and sort dropdown.
**Maintenance cost:** Low. Extends existing search infrastructure.
**Long-term impact:** Makes search more useful for power users with large knowledge bases.
**Priority:** MEDIUM — Good UX improvement, moderate cost.
**Timing:** After Tier 1.

---

### Tier 3: Medium Impact, Medium Effort (Implement Later)

#### 3.1 Agent Activity Center

**User value:** Agent runs happen in the background. Users can see run history on the agents page, but there's no centralized view of all agent activity across all agents. An activity center would show:
- All recent agent runs across all agents
- Real-time status of running agents
- Quick access to run details and logs

**Engineering cost:** ~6 hours. Backend: The `/agents/runs` endpoint already exists. Frontend: Create an AgentActivityPanel that aggregates runs from all agents.
**Maintenance cost:** Low. Reuses existing agent run infrastructure.
**Long-term impact:** Centralizes agent monitoring, which becomes critical as users create more agents.
**Priority:** MEDIUM — Good for power users with multiple agents.
**Timing:** After Tier 2.

#### 3.2 Retrieval Debugging Panel

**User value:** When search results are poor, users have no way to understand why. A debugging panel would show:
- Which collections were searched
- Which retrieval strategies were used (semantic, keyword, graph)
- RRF fusion scores
- MMR diversity filtering
- Which results were filtered out and why

**Engineering cost:** ~8 hours. Backend: Add debug mode to hybrid retrieval that returns scoring details. Frontend: Create a RetrievalDebugPanel that shows the scoring breakdown.
**Maintenance cost:** Medium. Requires modifying the retrieval pipeline to return debug data.
**Long-term impact:** Critical for power users and developers who want to understand and improve retrieval quality. Also invaluable for debugging user-reported search issues.
**Priority:** MEDIUM — High value for developers, moderate for end users.
**Timing:** After Tier 2.

#### 3.3 Memory Graph Improvements

**User value:** The memory graph view currently shows nodes and edges but doesn't allow:
- Clicking a node to see its connections
- Filtering by category or date
- Zooming and panning
- Exporting the graph

**Engineering cost:** ~8 hours. Frontend: Upgrade the graph visualization library (currently custom SVG), add interaction handlers.
**Maintenance cost:** Medium. Graph visualization libraries can be complex.
**Long-term impact:** Makes the memory graph a more useful tool for understanding knowledge relationships.
**Priority:** MEDIUM — Good for users who actively use the graph view.
**Timing:** After Tier 2.

---

### Tier 4: Lower Impact, Higher Effort (Consider Carefully)

#### 4.1 Command Palette Enhancement

**User value:** The command palette currently only navigates to pages. Enhancing it to search across entities (conversations, agents, models, memory entries) would make it a true power-user tool.
**Engineering cost:** ~8 hours. Backend: Add a unified search endpoint that returns entities across all types. Frontend: Update CommandPalette to show entity results with type icons.
**Maintenance cost:** Medium. New search endpoint, new result rendering.
**Long-term impact:** Makes the command palette the primary navigation method for power users.
**Priority:** LOW-MEDIUM — Nice to have, not essential.
**Timing:** After Tier 3.

#### 4.2 Download Manager Improvements

**User value:** The download manager works but could show:
- Download speed history (chart)
- Estimated time remaining based on actual speed
- Disk space predictions ("This model needs 4.2GB, you have 12GB free")
- Download scheduling (pause during certain hours)

**Engineering cost:** ~8 hours. Backend: Track download speed over time, add disk space checks. Frontend: Add speed chart, disk space indicator.
**Maintenance cost:** Medium. New tracking infrastructure, new UI components.
**Long-term impact:** Makes the download manager more informative and trustworthy.
**Priority:** LOW — Current download manager is functional.
**Timing:** After Tier 3.

#### 4.3 Indexing Monitoring Dashboard

**User value:** Users can configure indexing rules in settings but have no visibility into:
- What's currently being indexed
- Indexing speed and progress
- Which files are excluded and why
- Index health and completeness

**Engineering cost:** ~10 hours. Backend: Add indexing status endpoints, track indexing metrics. Frontend: Create an IndexingDashboard page or panel.
**Maintenance cost:** Medium. New monitoring infrastructure.
**Long-term impact:** Critical for users who rely on indexing for search quality.
**Priority:** LOW — Current indexing config is sufficient for most users.
**Timing:** After Tier 4.

---

## Part 3: Implementation Roadmap

### Phase 1: Fix Broken Features + Quick Wins (1-2 days)

1. **Fix accent color application** — Create ThemeProvider, add CSS variables, update Tailwind config
2. **Add conversation previews to chat sidebar** — Backend schema change + frontend UI update
3. **Build notification center** — Frontend NotificationPanel using existing backend API

### Phase 2: Power User Features (3-5 days)

4. **Model quick switcher** — Global model context + DashboardShell header switcher
5. **Background task center** — TaskLog model + API + TaskCenter panel
6. **Search result improvements** — Filter chips, sort options, query expansion display

### Phase 3: Observability & Debugging (3-5 days)

7. **Agent activity center** — Aggregated agent run view across all agents
8. **Retrieval debugging panel** — Debug mode in retrieval pipeline + scoring breakdown UI
9. **Memory graph improvements** — Better visualization, interaction, and filtering

### Phase 4: Polish & Power Features (2-3 days)

10. **Command palette enhancement** — Entity search across conversations, agents, models, memory
11. **Download manager improvements** — Speed tracking, disk space, scheduling
12. **Indexing monitoring dashboard** — Indexing status, progress, health

---

## Part 4: What NOT to Implement

1. **Memory page decomposition** — State is tightly coupled; splitting adds complexity without benefit
2. **Batch download operations** — Low value; downloads are 1-3 at a time with per-item controls
3. **Admin pagination** — Current scale doesn't require it; add when needed
4. **Over-engineered component splitting** — Only split when there's a clear maintainability gain

---

## Part 5: Architecture Alignment Check

All recommended features have proper backend support:

| Feature | Backend Support | Changes Needed |
|---------|----------------|----------------|
| Accent color fix | ✅ Preferences saved in user profile | CSS variable provider (frontend only) |
| Conversation previews | ⚠️ Schema lacks `last_message` field | Add field to schema + modify list query |
| Notification center | ✅ Full CRUD API exists | Frontend component only |
| Model quick switcher | ✅ `/api/v1/models` returns all models | Frontend context + UI only |
| Background task center | ⚠️ arq workers exist, no task log API | Add TaskLog model + endpoints |
| Search improvements | ✅ Search API exists | Add filter params to existing endpoint |
| Agent activity center | ✅ `/agents/runs` exists | Frontend aggregation only |
| Retrieval debugging | ⚠️ Retrieval pipeline exists, no debug mode | Add debug flag to retrieval |
| Memory graph improvements | ✅ Graph data exists | Frontend visualization upgrade |
| Command palette enhancement | ✅ Search API exists | Add unified entity search endpoint |
| Download improvements | ✅ Download infrastructure exists | Add speed tracking to existing manager |
| Indexing monitoring | ⚠️ Indexing config exists, no status API | Add indexing status endpoint |

No feature is frontend-only without backend support. All features either use existing backend infrastructure or require minimal backend additions.
