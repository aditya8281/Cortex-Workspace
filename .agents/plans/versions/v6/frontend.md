# V6 Frontend: The Ecosystem

## Overview

V6 is the culmination of the frontend redesign — from a simple web UI to a complete desktop workspace. The plugin marketplace enables extensibility. The visual workflow editor enables complex automation. Graph intelligence brings the knowledge graph to life. Search explainability makes retrieval transparent. The UI is polished, accessible, and production-ready.

## Information Architecture Changes

```
V5 IA:
  Dashboard (Workspace) | Email | Calendar | Tasks | Notes | Documents | Contacts | Memory | Graph | Search | Research | Vault | Settings

V6 IA:
  Dashboard (Workspace) | Email | Calendar | Tasks | Notes | Documents | Contacts | Memory | Graph | Search | Research | Vault | Marketplace | Workflows | Settings

  Navigation:
  ─────────────────────────
  🏠 HOME:    Dashboard (workspace hub)
  📋 WORK:    Email, Calendar, Tasks, Notes, Documents, Contacts
  🧠 INTEL:   Memory, Graph, Search, Research
  🗄️ STORE:   Vault
  🔧 EXTEND:  Marketplace, Workflows
  ⚙️ SYSTEM:  Settings
  ─────────────────────────
```

## New Pages

### /marketplace — Plugin Marketplace

Full-page marketplace browser with search, categories, ratings, install:

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
│ │ 1.2K inst. │ │ 890 inst.  │ │ 567 inst.  │   │
│ │ [Install]  │ │ [✓ Ready]  │ │ [Install]  │   │
│ └────────────┘ └────────────┘ └────────────┘   │
│                                                  │
│ 🆕 New Releases                                  │
│ ┌────────────┐ ┌────────────┐ ┌────────────┐   │
│ │ 🤖 ChatGPT │ │ 📊 Grafana │ │ 🔐 Auth    │   │
│ │ v1.0 ⭐4.2 │ │ v1.1 ⭐4.4 │ │ v1.0 ⭐4.3 │   │
│ │ [Install]  │ │ [Install]  │ │ [Install]  │   │
│ └────────────┘ └────────────┘ └────────────┘   │
│                                                  │
│ 📦 Installed (3)                                 │
│ Slack Integration v1.3  [Configure] [Disable]   │
│ Analytics Dashboard v2.1 [Configure] [Disable]  │
│ GitHub Integration v1.0 [Configure] [Disable]   │
└──────────────────────────────────────────────────┘
```

### /workflows — Visual Workflow Editor

```
┌──────────────────────────────────────────────────┐
│ 🔀 Workflows                    [+ New Workflow]  │
├──────────────────────────────────────────────────┤
│                                                  │
│ 📋 Daily Briefing              Enabled  ✅       │
│    Last run: 2h ago | Runs: 45 | Avg: 12s       │
│    [Edit] [Run Now] [Disable] [Delete]          │
│                                                  │
│ 📋 Email Triage                Enabled  ✅       │
│    Last run: 1d ago | Runs: 30 | Avg: 8s        │
│    [Edit] [Run Now] [Disable] [Delete]          │
│                                                  │
│ 📋 Research & Report           Disabled ⬜       │
│    Last run: 5d ago | Runs: 12 | Avg: 45s       │
│    [Edit] [Run Now] [Enable] [Delete]           │
│                                                  │
│ [+ New Workflow] [📂 Import] [📋 Templates]      │
└──────────────────────────────────────────────────┘
```

### /workflows/[id] — Visual DAG Editor

```
┌──────────────────────────────────────────────────┐
│ 🔀 Daily Morning Briefing — Editor    [Save] [▶] │
├──────────────────────────────────────────────────┤
│                                                  │
│ ┌────────┐    ┌────────┐    ┌────────┐          │
│ │📧 Email│───▶│🤖 Agent│───▶│📤 Output│          │
│ └────────┘    └────────┘    └────────┘          │
│                   ▲                              │
│ ┌────────┐        │                              │
│ │📅 Cal  │────────┘                              │
│ └────────┘                                       │
│                                                  │
│ ┌────────┐        │                              │
│ │✅ Tasks│────────┘                              │
│ └────────┘                                       │
│                                                  │
│ ──────────────────────────────────────────────── │
│ Node Properties                                  │
│ Type: Agent | Model: default                     │
│ Prompt: "Create a morning briefing from..."      │
│ [Delete Node] [Duplicate] [Configure]            │
└──────────────────────────────────────────────────┘
```

Canvas features:
- Drag-and-drop node creation from palette
- Connect nodes by dragging edges
- Node configuration panel (right side)
- Zoom/pan navigation (Ctrl+scroll, middle-click drag)
- Mini-map for large workflows
- Color-coded by node type
- Error indicators on failed runs
- Execution history overlay

### /search/quality — Search Quality Dashboard

```
┌──────────────────────────────────────────────────┐
│ 📊 Search Quality                                │
├──────────────────────────────────────────────────┤
│ Period: [Last 7 days ▼]                          │
│                                                  │
│ Total searches: 234                              │
│ Avg results clicked: 2.3                         │
│ Zero-result rate: 3%                             │
│                                                  │
│ Relevance: ████████████████████░░  92%           │
│ (↑5% from baseline)                             │
│                                                  │
│ Cross-encoder impact:                            │
│ Without: 78% | With: 92% (+18%)                │
│                                                  │
│ Top queries:                                     │
│ 1. "memory consolidation" — 100%                 │
│ 2. "agent loop" — 95%                           │
│ 3. "embeddings" — 90%                           │
└──────────────────────────────────────────────────┘
```

## Modified Pages

### Search — Explainability Panel

```
┌──────────────────────────────────────────────────┐
│ 🔍 "memory consolidation pipeline"               │
├──────────────────────────────────────────────────┤
│                                                  │
│ 1. Memory Consolidation Pipeline — design.md     │
│    Score: 0.95 (↑ from #3)                      │
│    Why: Exact title + graph connection (12 ent.) │
│    [Show path] [Why ranked here?]               │
│                                                  │
│ 2. Phase 3: Memory Consolidation — Phase-3.md    │
│    Score: 0.92 (↓ from #1)                      │
│    Why: Direct content + high importance entity  │
│    [Show path] [Why ranked here?]               │
│                                                  │
│ Quality: 95% relevance | 4 sources              │
│ Time: 120ms (recall: 80ms, rerank: 40ms)        │
└──────────────────────────────────────────────────┘
```

### Graph — Community View

```
┌──────────────────────────────────────────────────┐
│ 🔗 Knowledge Graph          [Entities] [Communities]│
├──────────────────────────────────────────────────┤
│                                                  │
│      🔵 Memory Cluster                          │
│     ┌───┐ ┌───┐ ┌───┐                          │
│     │mem│──│ded│──│ext│                          │
│     └─┬─┘ └───┘ └─┬─┘                          │
│       │            │                            │
│     ┌─┴─┐      ┌──┴──┐                         │
│     │con│      │bi-  │                         │
│     │tra│      │temp │                         │
│     └───┘      └─────┘                         │
│                                                  │
│ Communities: Memory (5), Agent (8), Graph (4)   │
│ Inferred: 3 new relationships                   │
│ [Show Inferred] [Reason About...]              │
└──────────────────────────────────────────────────┘
```

### Settings — Final Configuration

```
Settings
├── General
├── Providers
├── MCP Servers (client)
├── MCP Server (server)
├── Plugins
├── Webhooks
├── Scheduler
├── Sessions
├── Research
├── Contacts
├── API Keys
├── Preferences
├── Routing
├── Backup
├── Performance
├── Analytics        ← NEW
├── Accessibility    ← NEW
└── About            ← NEW (version, health, diagnostics)
```

## Navigation — Final State

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
│ 🔧 EXTEND│
│ Plugins │
│ Workflows│
│ ─────── │
│ ⚙️ Settings│
└──────────┘
```

## Design System — Final State

Complete token set across all versions:
- Primary: Warm Neural Dark (from V1)
- Workspace tools: Color-coded (V5)
- Graph communities: Color clusters (V6)
- Search relevance: Gradient scale (V6)
- Accessibility: High contrast mode, reduced motion

Components across all versions:
- 30+ custom components (Button, Card, Modal, CommandPalette, etc.)
- Skeleton loading states (V6)
- Error boundaries (V6)
- Keyboard shortcuts overlay (V3+)
- Drag-and-drop zones (V3+)

## Keyboard Shortcuts — Complete Map

| Shortcut | Action | Version |
|----------|--------|---------|
| Ctrl+Shift+Space | Focus app | V3 |
| Ctrl+Shift+C | Command palette | V3 |
| Ctrl+Shift+A | Quick agent query | V3 |
| Ctrl+Shift+M | Quick memory recall | V3 |
| Ctrl+E | Go to Email | V5 |
| Ctrl+D | Go to Calendar | V5 |
| Ctrl+T | Go to Tasks | V5 |
| Ctrl+Shift+N | New Note | V5 |
| Ctrl+Shift+T | New Task | V5 |
| Ctrl+Shift+E | Compose Email | V5 |
| Ctrl+Shift+V | New Calendar Event | V5 |
| Ctrl+1-6 | Navigate to page | V3 |
| Ctrl+K | Command palette (alt) | V3 |
| Ctrl+/ | Toggle sidebar | V3 |
| ? | Show shortcuts | V3 |
| Esc | Close overlay/modal | V1 |
| / | Focus search | V1 |
| Ctrl+S | Save current state | V1 |

## Responsive Behavior — Final State

Desktop (1200px+): Full sidebar + multi-column dashboard
Tablet (800-1199px): Collapsible sidebar + stacked dashboard
Mobile (< 800px): Bottom tab bar (Workspace, Intel, Vault, Settings)

Tauri window: resizable, min 800x600, remembers position/size.

## Accessibility — WCAG 2.1 AA

- ARIA labels on all interactive elements
- Keyboard navigation for all pages
- Screen reader support (semantic HTML)
- Color contrast 4.5:1 minimum
- Focus management for modals/overlays
- Alt text for all images/icons
- Skip navigation links
- Reduced motion support
- High contrast mode option

## Frontend Evolution Summary

| Version | Pages | Components | IA Complexity | Desktop Features |
|---------|-------|------------|---------------|------------------|
| V1 | 6 | 17 | Simple | None |
| V2 | 6 + Settings | 22 | Simple+ | None |
| V3 | 6 + Settings + Command Palette | 25 | Moderate | System tray, hotkey, drag-drop |
| V4 | 7 + Research + Sessions | 30 | Moderate+ | Scheduler UI, webhook config |
| V5 | 13 + Email + Calendar + Tasks + Notes + Docs + Contacts | 40+ | Complex | Full workspace |
| V6 | 15 + Marketplace + Workflows + Quality | 50+ | Full ecosystem | Complete desktop app |
