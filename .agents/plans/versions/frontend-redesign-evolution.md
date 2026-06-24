# CORTEX Frontend Redesign Evolution

## Complete UI/UX transformation across 6 versions

---

## Version 0 (Current State)

**Pages:** 6 (Dashboard, Memory, Graph, Search, Vault, Settings)
**Components:** 17 custom components
**Design:** Dark-only glassmorphism, NeuralNetwork Canvas 2D background
**Navigation:** Fixed 240px sidebar (desktop), overlay sidebar (tablet), bottom tabs (mobile)
**Desktop features:** None — runs in browser
**IA complexity:** Simple — flat list of pages

---

## Version 1: The Brain Works

**No UI changes.** V1 fixes the backend (daemon lifecycle, agent loop rebuild, CLI completion). The web UI is untouched. Agent conversations stream via existing SSE mechanism.

**What changes for the user:**
- Agent actually works (streaming, tools, completion)
- CLI commands functional
- Bug fixes improve reliability

**UX impact:** Invisible — same UI, better behavior underneath.

---

## Version 2: The Architecture

**Scope:** Settings page expansion + memory enhancements

**Information Architecture:**
```
V1: Dashboard | Memory | Graph | Search | Vault | Settings
V2: Dashboard | Memory | Graph | Search | Vault | Settings
                                            ├── Providers (NEW)
                                            ├── MCP Servers (NEW)
                                            ├── Plugins (NEW)
                                            ├── Preferences (NEW)
                                            └── Routing (NEW)
```

**New components:** 5 (ProviderCard, MCPServerCard, PluginCard, ConfigEditor, RoutingTable)

**Settings redesign:**
- Settings becomes a sub-application with its own sidebar navigation
- 8 sections (General, Providers, MCP Servers, Plugins, Config, Routing, About)
- Each section has its own layout and components

**Memory page enhancements:**
- Consolidation status panel (last run, facts extracted, duplicates removed)
- Bi-temporal indicators: valid_from / valid_until dates
- Invalidated memory visual treatment (faded, strikethrough)

**Navigation:** No changes — same sidebar, same pages.

**Responsive:** Settings sidebar collapses to horizontal tabs on tablet/mobile.

**Design system:** No changes — same tokens, same patterns.

---

## Version 3: The Desktop

**Scope:** Tauri shell + command palette + keyboard shortcuts + drag-and-drop + offline indicator

**Information Architecture:**
```
V2: Dashboard | Memory | Graph | Search | Vault | Settings
V3: Dashboard | Memory | Graph | Search | Vault | Settings
  + Command Palette (overlay, Ctrl+Shift+C)
  + System Tray menu
  + Keyboard Shortcuts (global + in-app)
  + Drag-and-drop zones
  + Offline indicator
```

**Major new component: Command Palette (Ctrl+Shift+C)**
```
┌─────────────────────────────────────────────────────┐
│ 🔍 Type a command...                                │
├─────────────────────────────────────────────────────┤
│ ⚡ Ask Agent        │  Ask Cortex anything           │
│ 🧠 Memory Recall   │  Search your memories           │
│ 🔍 Search           │  Search indexed content         │
│ 📁 Open Vault      │  Browse vault files              │
│ ⚙️  Settings        │  Open settings                   │
│ 📊 Dashboard        │  Go to dashboard                 │
│ 🔄 Sync Now         │  Force memory consolidation      │
│ 📦 Backup           │  Create backup                   │
│ 🔌 MCP Servers      │  Manage MCP connections          │
│ 🧩 Plugins          │  Manage plugins                  │
├─────────────────────────────────────────────────────┤
│ Recent: "What did I work on yesterday?"              │
│         "Show me the auth flow"                      │
│         "Find files about memory consolidation"      │
└─────────────────────────────────────────────────────┘
```

**New components:** 4 (CommandPalette, SystemTray, KeyboardShortcuts, OfflineIndicator)

**System tray menu:**
```
CORTEX
├── Show Window
├── ─────────────
├── Quick Ask...        (Ctrl+Shift+A)
├── Quick Memory...     (Ctrl+Shift+M)
├── ─────────────
├── Status: 🟢 Online
├── Memory: 1,234 facts
├── Agent: Idle
├── ─────────────
├── Settings
├── ─────────────
├── Quit
```

**Drag-and-drop:**
- Drag files onto window → import to vault
- Visual feedback: dashed border + "Drop to import" overlay
- Text selection → create memory from text
- URL → fetch and index content

**Offline indicator:**
- Small dot in header: 🟢 Online / 🟡 Offline
- Shows what features are available/unavailable

**Keyboard shortcuts (global):**
- Ctrl+Shift+Space: Show/focus CORTEX window
- Ctrl+Shift+C: Command palette
- Ctrl+Shift+A: Quick agent query
- Ctrl+Shift+M: Quick memory recall

**Keyboard shortcuts (in-app):**
- Ctrl+K: Command palette (alternative)
- Ctrl+/: Toggle sidebar
- Ctrl+1-6: Navigate to pages
- ?: Show shortcuts help

**Navigation:** No changes to sidebar. New overlays and shortcuts.

**Responsive:** Same as before. Tauri window is resizable (min 800x600).

**Design system:** New tokens:
- `--color-offline`: Yellow for offline indicator
- `--color-drop-zone`: Dashed border color for drag-and-drop

---

## Version 4: The Automaton

**Scope:** Research page + sessions + scheduler UI + webhook management + MCP server config

**Information Architecture:**
```
V3: Dashboard | Memory | Graph | Search | Vault | Settings
V4: Dashboard | Memory | Graph | Search | Research | Vault | Settings
                                                  ↑ NEW
  Sessions: integrated into Agent/Conversation flow
  Scheduler: in Settings
  Webhooks: in Settings
  MCP Server: in Settings
```

**New page: /research — Deep Research**
```
┌─────────────────────────────────────────────────┐
│ Deep Research                                    │
├─────────────────────────────────────────────────┤
│ [What would you like to research?]              │
│ ┌─────────────────────────────────────────────┐ │
│ │ Compare memory architectures across mem0,   │ │
│ │ graphiti, and zep...                        │ │
│ └─────────────────────────────────────────────┘ │
│ Budget: Queries [20▼] Tokens [100k▼] Time [5m▼]│
│ [Start Research]                                │
│ ─────────────────────────────────────────────── │
│ Previous Research                               │
│ 📊 Memory Architecture Comparison   2h ago  ✅ │
│ 📊 Local LLM Performance Benchmarks 1d ago  ✅ │
│ 📊 Security Best Practices Audit    3d ago  ✅ │
└─────────────────────────────────────────────────┘
```

**New components:** 6 (ResearchProgress, SessionSelector, SchedulerTaskCard, WebhookCard, ResearchReport, MCPStatusCard)

**Research progress indicator:**
```
┌─────────────────────────────────────────────────┐
│ 🔍 Researching: "Compare memory architectures"  │
│ Phase: Synthesizing findings                    │
│ ████████████░░░░░░░░  60%                       │
│ Queries: 12/20  │  Tokens: 45K/100K  │  2m 15s  │
└─────────────────────────────────────────────────┘
```

**Session selector (in conversation header):**
```
┌──────────────────────────┐
│ 📁 Active Sessions       │
│ ──────────────────────── │
│ • Research: mem0 vs zep  │ ← current
│ • Debug auth bug          │
│ • Planning V5 features    │
│ ──────────────────────── │
│ [+ New Session]           │
│ [View All Sessions]       │
└──────────────────────────┘
```

**Settings expansion:**
```
Settings
├── General
├── Providers
├── MCP Servers (client)
├── MCP Server (server)  ← NEW
├── Plugins
├── Webhooks             ← NEW
├── Scheduler            ← NEW
├── Sessions             ← NEW
├── Research             ← NEW
├── Preferences
├── Routing
├── Backup
├── Performance
└── About
```

**Navigation:** Research added to sidebar between Search and Vault.

**Design system:** New tokens:
- `--color-research`: Deep blue for research features
- `--color-session-active`: Green for active sessions
- `--color-session-archived`: Gray for archived sessions

---

## Version 5: The Workspace

**Scope:** Email, Calendar, Tasks, Notes, Documents, Contacts — complete workspace transformation

**Information Architecture — MAJOR REDESIGN:**
```
V4: Dashboard | Memory | Graph | Search | Research | Vault | Settings

V5: Dashboard (Workspace) | Email | Calendar | Tasks | Notes | Documents | Contacts | Memory | Graph | Search | Research | Vault | Settings

Navigation split:
─────────────────────
🧠 Intelligence:  Memory, Graph, Search, Research
📋 Workspace:     Email, Calendar, Tasks, Notes, Documents, Contacts
🗄️ Storage:       Vault
⚙️ System:        Settings
─────────────────────
```

**New pages:** 6 (/email, /calendar, /tasks, /notes, /documents, /contacts)

**Dashboard becomes Workspace Hub:**
```
┌──────────────────────────────────────────────────────┐
│ CORTEX Workspace                    Tuesday, Jun 25  │
├──────────────────────────────────────────────────────┤
│                                                      │
│ 📧 Email (3 unread, 1 urgent)     📅 Today (4 events)│
│ ┌────────────────────────┐ ┌────────────────────────┐│
│ │ 🔴 Urgent: client bug  │ │ 10:00 Standup          ││
│ │ 📩 PR review request   │ │ 14:00 Design review    ││
│ │ 📩 Newsletter digest   │ │ 16:00 1:1 with manager ││
│ └────────────────────────┘ │ 17:00 Team sync        ││
│                            └────────────────────────┘│
│                                                      │
│ ✅ Tasks (2 today, 1 overdue)    📝 Notes (recent)   │
│ ┌────────────────────────┐ ┌────────────────────────┐│
│ │ 🔴 Fix auth bug        │ │ Memory Architecture    ││
│ │ 🟡 Review PR #42       │ │ Sprint Planning Notes  ││
│ │ 🟢 Write V5 docs       │ │ API Design Ideas       ││
│ └────────────────────────┘ └────────────────────────┘│
│                                                      │
│ 🤖 Agent                    📄 Documents (recent)    │
│ ┌────────────────────────┐ ┌────────────────────────┐│
│ │ Last: 2h ago — success │ │ architecture-spec.pdf  ││
│ │ Running: none           │ │ meeting-notes.docx     ││
│ │ Sessions: 3 active     │ │ api-reference.md       ││
│ └────────────────────────┘ └────────────────────────┘│
└──────────────────────────────────────────────────────┘
```

**New components:** 15+ (EmailBrowser, CalendarView, TaskManager, NotesEditor, DocumentManager, ContactManager, WorkspaceWidget, ComposeModal, EventEditor, TaskCard, NoteCard, DocumentCard, ContactCard, WorkspaceDashboard, IntegrationStatus)

**Sidebar redesign — categorized:**
```
┌──────────┐
│ 🏠 Home  │
│ ─────── │
│ 📋 WORK │
│ 📧 Email │
│ 📅 Cal   │
│ ✅ Tasks │
│ 📝 Notes │
│ 📄 Docs  │
│ 👥 People│
│ ─────── │
│ 🧠 INTEL│
│ Memory  │
│ Graph   │
│ Search  │
│ Research│
│ ─────── │
│ 🗄️ VAULT │
│ ─────── │
│ ⚙️ Settings│
└──────────┘
```

**Design system:** New tokens per workspace tool:
- `--color-email`: Blue
- `--color-calendar`: Green
- `--color-task`: Orange
- `--color-note`: Purple
- `--color-document`: Teal
- `--color-contact`: Pink

Each tool gets its own accent color for visual distinction.

**Keyboard shortcuts:**
- Ctrl+E: Email
- Ctrl+D: Calendar
- Ctrl+T: Tasks
- Ctrl+Shift+N: New Note
- Ctrl+Shift+T: New Task
- Ctrl+Shift+E: Compose Email
- Ctrl+Shift+V: New Calendar Event

**Responsive:**
- Desktop (1200px+): Full sidebar + 2-column dashboard
- Tablet (800-1199px): Collapsible sidebar + stacked dashboard
- Mobile (< 800px): Bottom tab bar (Workspace, Intel, Vault, Settings)

---

## Version 6: The Ecosystem

**Scope:** Marketplace + Workflows + Graph Intelligence + Search Quality + Accessibility + Polish

**Information Architecture — FINAL STATE:**
```
V5: Dashboard | Email | Calendar | Tasks | Notes | Docs | Contacts | Memory | Graph | Search | Research | Vault | Settings

V6: Dashboard | Email | Calendar | Tasks | Notes | Docs | Contacts | Memory | Graph | Search | Research | Vault | Marketplace | Workflows | Settings

Navigation:
─────────────────────
🏠 HOME:    Dashboard (workspace hub)
📋 WORK:    Email, Calendar, Tasks, Notes, Documents, Contacts
🧠 INTEL:   Memory, Graph, Search, Research
🗄️ STORE:   Vault
🔧 EXTEND:  Marketplace, Workflows
⚙️ SYSTEM:  Settings
─────────────────────
```

**New pages:** 3 (/marketplace, /workflows, /workflows/[id], /search/quality)

**Plugin Marketplace:**
```
┌──────────────────────────────────────────────────┐
│ 🧩 Plugin Marketplace                            │
├──────────────────────────────────────────────────┤
│ 🔍 Search plugins...           [Category ▼]      │
│                                                  │
│ ⭐ Top Rated                                     │
│ ┌────────────┐ ┌────────────┐ ┌────────────┐   │
│ │ 📊 Analytics│ │ 🔗 Slack   │ │ 📧 Gmail   │   │
│ │ v2.1 ⭐4.8 │ │ v1.3 ⭐4.6 │ │ v1.0 ⭐4.5 │   │
│ │ [Install]  │ │ [✓ Ready]  │ │ [Install]  │   │
│ └────────────┘ └────────────┘ └────────────┘   │
└──────────────────────────────────────────────────┘
```

**Visual Workflow Editor:**
```
┌──────────────────────────────────────────────────┐
│ 🔀 Daily Morning Briefing — Editor    [Save] [▶] │
├──────────────────────────────────────────────────┤
│ ┌────────┐    ┌────────┐    ┌────────┐          │
│ │📧 Email│───▶│🤖 Agent│───▶│📤 Output│          │
│ └────────┘    └────────┘    └────────┘          │
│                   ▲                              │
│ ┌────────┐        │                              │
│ │📅 Cal  │────────┘                              │
│ └────────┘                                       │
│ ┌────────┐        │                              │
│ │✅ Tasks│────────┘                              │
│ └────────┘                                       │
└──────────────────────────────────────────────────┘
```

**Search Explainability:**
```
┌──────────────────────────────────────────────────┐
│ 🔍 "memory consolidation pipeline"               │
├──────────────────────────────────────────────────┤
│ 1. Memory Consolidation Pipeline — design.md     │
│    Score: 0.95 (↑ from #3)                      │
│    Why: Exact title + graph connection (12 ent.) │
│    [Show path] [Why ranked here?]               │
└──────────────────────────────────────────────────┘
```

**Graph Intelligence UI:**
- Community visualization (colored clusters)
- Entity importance (node size = importance)
- Reasoning results (inferred relationships)
- Explainability (connection paths)

**Search Quality Dashboard:**
- Relevance metrics over time
- Cross-encoder impact visualization
- Top queries with relevance scores

**New components:** 10+ (PluginCard, MarketplaceBrowser, WorkflowCanvas, WorkflowNode, WorkflowPalette, SearchExplainability, GraphCommunities, QualityDashboard, AnalyticsWidget, AccessibilityPanel)

**Accessibility — WCAG 2.1 AA:**
- ARIA labels on all interactive elements
- Keyboard navigation for all pages
- Screen reader support (semantic HTML)
- Color contrast 4.5:1 minimum
- Focus management for modals/overlays
- Alt text for all images/icons
- Skip navigation links
- Reduced motion support
- High contrast mode option

**Loading states:** Skeleton screens replace spinners everywhere.

**Error boundaries:** Every page wrapped in error boundary with recovery options.

**Design system — final state:**
- Primary: Warm Neural Dark
- Workspace tools: Color-coded (V5)
- Graph communities: Color clusters (V6)
- Search relevance: Gradient scale (V6)
- Accessibility: High contrast mode, reduced motion

---

## Component Growth Summary

| Version | New Components | Total | Major Addition |
|---------|---------------|-------|----------------|
| V0 (current) | 0 | 17 | — |
| V1 | 0 | 17 | — |
| V2 | 5 | 22 | Settings sub-app |
| V3 | 4 | 26 | Command palette, system tray |
| V4 | 6 | 32 | Research, sessions, scheduler |
| V5 | 15+ | 47+ | Full workspace (6 new pages) |
| V6 | 10+ | 57+ | Marketplace, workflows, quality |

## Page Growth Summary

| Version | New Pages | Total | Major Addition |
|---------|-----------|-------|----------------|
| V0 (current) | 0 | 6 | — |
| V1 | 0 | 6 | — |
| V2 | 0 | 6 | Settings expands internally |
| V3 | 0 | 6 | Command palette overlay |
| V4 | 1 | 7 | /research |
| V5 | 6 | 13 | /email, /calendar, /tasks, /notes, /documents, /contacts |
| V6 | 3 | 16 | /marketplace, /workflows, /search/quality |

## Navigation Evolution

| Version | Structure | Categories |
|---------|-----------|------------|
| V0-V4 | Flat sidebar | All pages at same level |
| V5 | Categorized sidebar | Intelligence, Storage, System |
| V6 | Categorized sidebar | Home, Work, Intel, Store, Extend, System |

## Key UX Milestones

1. **V1:** Agent actually works (invisible UX improvement)
2. **V2:** Settings becomes a management hub
3. **V3:** App feels native (command palette, shortcuts, tray)
4. **V4:** Research automation (first major new feature page)
5. **V5:** Complete workspace (6 new pages, categorized nav)
6. **V6:** Ecosystem complete (marketplace, workflows, quality)
