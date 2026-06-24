# V3 Frontend: The Desktop

## Overview

V3 transforms the web frontend into a native desktop application via Tauri 2.x. The web UI runs inside Tauri's webview. New desktop-native features: system tray, global hotkey, command palette, drag-and-drop, keyboard shortcuts, offline indicator. This is where the frontend starts to feel like a real application, not a website.

## Information Architecture Changes

```
V2 IA:
  Dashboard | Memory | Graph | Search | Vault | Settings

V3 IA:
  Dashboard | Memory | Graph | Search | Vault | Settings
  + Command Palette (overlay, Ctrl+Shift+C)
  + System Tray menu
  + Keyboard Shortcuts (global + in-app)
  + Drag-and-drop zones
  + Offline indicator
```

## New Components

### Command Palette (Ctrl+Shift+C)

Full-screen overlay with fuzzy search across all app features:

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

Features:
- Fuzzy search across commands, memories, files, recent actions
- Keyboard navigation (↑↓ to select, Enter to execute, Esc to close)
- Recent actions list
- Category filters (Agent, Memory, Files, Settings)
- Quick agent query without leaving current page

### System Tray Menu

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

### Keyboard Shortcuts

Global (system-wide):
- `Ctrl+Shift+Space`: Show/focus CORTEX window
- `Ctrl+Shift+C`: Command palette
- `Ctrl+Shift+A`: Quick agent query
- `Ctrl+Shift+M`: Quick memory recall

In-app:
- `Ctrl+K`: Command palette (alternative)
- `Ctrl+/`: Toggle sidebar
- `Ctrl+1-6`: Navigate to pages (Dashboard, Memory, Graph, Search, Vault, Settings)
- `Ctrl+N`: New conversation
- `Ctrl+S`: Save current state
- `Esc`: Close overlay/modal
- `?`: Show shortcuts help

### Drag-and-Drop

Drag files onto the app window:
- Single file → import to vault
- Multiple files → batch import
- Text selection → create memory from text
- URL → fetch and index content

Visual feedback: drop zone overlay with dashed border + "Drop to import" message.

### Offline Indicator

Small indicator in the header:
- 🟢 Online (green dot)
- 🟡 Offline (yellow dot + "Offline" label)
- Shows what features are available/unavailable

## Navigation Changes

Desktop app gains:
- Window title bar shows current page + system status
- Sidebar collapse toggle (Ctrl+/)
- Breadcrumb navigation in header
- Quick-switch between pages (Ctrl+1-6)

## Memory Page Changes

- Drag-and-drop zone for importing files to memory
- Bulk actions (select multiple → delete, tag, export)
- Keyboard navigation (↑↓ to select, Enter to expand)

## Graph Page Changes

- Drag-and-drop: drag node to create connection
- Keyboard shortcuts for graph navigation
- Export graph as image (PNG/SVG)

## Search Page Changes

- Search input auto-focuses on page load
- Keyboard navigation through results
- Preview panel shows result content on hover/select

## Dashboard Changes

- Quick stats cards with click-through
- Recent activity timeline
- System health indicators
- Quick actions bar (Ask Agent, Search, Import)

## Design System

No major design system changes. New tokens:
- `--color-offline`: Yellow for offline indicator
- `--color-drop-zone`: Dashed border color for drag-and-drop

## Responsive Behavior

Desktop (1200px+): Full sidebar + content
Tablet (800-1199px): Collapsible sidebar + content
Mobile (< 800px): Bottom tab bar (existing pattern)

Tauri window is resizable. Minimum size: 800x600.
