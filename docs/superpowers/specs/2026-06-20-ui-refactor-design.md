# Cortex UI Refactor — Design Spec

**Date:** 2026-06-20
**Status:** Approved
**Scope:** Full UI refactor — layout, navigation, pages, theme, animations

---

## 1. Identity

Cortex is a calm AI companion — a personal workspace where AI is always present but never overwhelming. The feel is Notion meets a thoughtful AI assistant. Warm, content-first, premium dark.

### Visual Language

- **Base:** Very dark gray with warm undertones (#0a0a0f → #111118), NOT pure black
- **Accent:** Softer blue-cyan (#0ea5c9), muted for warmth
- **Glass:** Translucent panels with backdrop blur, floating over content
- **Typography:** Inter for body, JetBrains Mono for code/labels
- **Physical weight:** Everything feels like it has weight but breathes

---

## 2. Navigation & Layout

### DashboardShell — All Pages Use It

Every page is wrapped in `DashboardShell`. No exceptions. No dead ends.

### Sidebar (Glass, Floating)

- Translucent backdrop blur, slightly lighter than page bg
- Two intent groups separated by a gradient divider:
  - **Work:** Dashboard, Search, Agents
  - **You:** Vault, Memory, Profile, Settings
- Admin stays conditional at bottom
- Active item: subtle glow + accent dot indicator (refined from current pulse)
- Status bar at bottom: vault lock state + memory count (clickable)
- User card at very bottom: avatar + name
- Responsive: Desktop (240px fixed), Tablet (overlay), Mobile (bottom tab bar)

### Header (Minimal, Clean)

- Left: hamburger (tablet/mobile) + Cortex logo
- Right: Command Palette trigger (Cmd+K) + Notifications bell + Avatar dropdown
- No page title here — pages own their headers

### Page Headers (Integrated Hero)

Each page has its own descriptive top area:
- Dashboard: "Welcome back, {name}" + role badge
- Search: "Search your workspace" + conversational input
- Agents: "Your agents" + create button
- Memory: "Knowledge graph" + category nodes

---

## 3. Dashboard — Command Center

### Layout: Hero + Scroll + Tabs

**Top: Welcome hero**
- User avatar with soft glow ring
- "Welcome back, {name}" in large type
- Role badge (Admin/Member) + @username
- Premium metric rings in a row: CPU, RAM, Disk with gradient fills + animated numbers
- GPU card as a compact info chip
- All metrics have glow effects on hover, animated stroke-dashoffset on load

**Below fold: Tabbed sections**
- **Activity** tab (default): Recent agent runs, latest search queries, memory additions. Timeline/feed format. Shows "what happened recently."
- **Processes** tab: Live process table — name, PID, CPU%, memory%, status. Sortable columns, filterable by name. Compact rows with subtle zebra striping.
- **Insights** tab: Memory count, indexed files, graph nodes, repo stats. Quick stats as mini cards with sparklines or trend indicators.

### Card Treatment

- Gradient fills on metric rings (cyan → blue gradient, not flat)
- Animated number counters (count up on load)
- Subtle inner shadow + border glow on hover
- Micro-interactions: scale 1.02 + shadow shift on hover
- Each card feels like a physical glass object

---

## 4. Search — Conversational AI Search

### Layout: Conversational-First

**Hero header:**
- "Search your workspace" title
- Large conversational input bar (like Perplexity's search box)
- Subtle placeholder: "Ask anything about your code, memories, or files..."

**Below input:**
- **AI Answer panel** (primary): Synthesized answer with inline citations/sources. Each citation links to the source (code chunk, memory entry, file). Appears after search executes.
- **Sources panel** (secondary): Expandable list of raw results — code chunks, memory entries, files. Each shows type badge, title, preview snippet, relevance score.
- **Filters** (collapsible bar above results): Repo, node type, language, max results. Horizontal filter chips, not a sidebar.
- **Graph toggle**: Button to switch to graph visualization view. Graph shows connections between results.

### Flow

1. User types query → debounced search
2. AI answer appears with citation markers [1] [2] [3]
3. Sources list shows all results below
4. Clicking a citation scrolls to the source
5. Graph toggle shows the relationship view

---

## 5. Agents — Hybrid Chat

### Layout: Chat + Structured Steps

**Hero header:**
- "Your agents" title
- Agent count badge
- "Create Agent" button (opens modal)

**Left panel (collapsible):**
- Agent list with status indicators (active/inactive)
- Recent runs below the agent list
- Collapsible to icon-only (48px) or fully hidden
- Toggle button in the hero header

**Main area (when agent selected):**

**Chat interface:**
- Message history flowing top to bottom
- User messages: right-aligned, accent background
- Agent responses: left-aligned, surface background
- Input bar at bottom with send button

**Structured execution:**
- When agent runs a task, response includes:
  - Step-by-step breakdown (numbered, with status icons)
  - Each step shows: action taken, tool used, result
  - Progress indicator during execution
  - Final summary with links to sources
- Steps are collapsible — can expand to see details or keep collapsed for overview

**Empty state:**
- Floating Bot icon with subtle animation
- "Select an agent or create one to get started"

---

## 6. Memory — Knowledge Graph Explorer

### Layout: Graph-First, Not List-First

**Hero header:**
- "Knowledge graph" title
- Entry count badge
- "New Memory" button
- Search bar with semantic toggle

**Main area:**

**Graph view (default):**
- Visual graph with category nodes (Code, Document, Note, Idea) as large anchor nodes
- Memory entries as smaller nodes connected to their category
- Tags shown as connecting lines between entries
- Node size = importance/recency
- Click a node to open entry detail
- Zoom/pan with mouse/touch
- Filter by category using the category nodes as toggles

**List view (toggle):**
- Switch to traditional list if preferred
- Categories as horizontal filter chips at top (not sidebar)
- Entries as cards with category badge, title, preview, tags
- Click to open detail panel

**Detail panel (right side, collapsible):**
- Full entry content
- Tags with click-to-search
- Edit/close buttons
- Related entries (connected via graph)

**Category sidebar replaced with:**
- Category nodes in the graph view
- Filter chips in the list view
- Both are horizontal/top-aligned, no inner sidebar

---

## 7. Remaining Pages

### Vault
Keep current layout (already works with DashboardShell). Visual refinement to match new softer dark theme. Lock screen → file browser with toolbar, sidebar, file list, properties panel.

### Profile
- Hero header: "Your profile"
- Avatar upload (large, centered)
- Form fields in clean cards: personal info, GitHub connect, developer profile
- Save button at bottom

### Settings
- Hero header: "Settings"
- Account info card
- Preference toggles (accent color, font, sidebar behavior)
- Danger zone (account deletion) at bottom, visually separated

### Auth
Keep separate (no DashboardShell). Login form centered. 4-step registration wizard. Clean, calm, no distractions. Add back to landing link.

### Landing Page
Keep as-is, refine visual polish to match new theme.

---

## 8. Animations & Motion

All motion follows Apple-level subtlety:

| Animation | Treatment |
|-----------|-----------|
| Page transitions | Fade + slight upward slide (opacity 0→1, y 8→0, spring damping 30) |
| Card hover | Gentle lift (translateY -2px) + soft shadow expansion + border glow fade-in |
| Sidebar active | Smooth background transition + accent dot fade-in |
| Metric rings | Animated stroke-dashoffset on load (1.5s ease-out) |
| Number counters | Count-up animation on page load |
| Graph nodes | Gentle float/breathe animation on idle |
| Tab switching | Crossfade content (opacity transition, 200ms) |
| Panel collapse/expand | Width transition with content fade |
| Reduced motion | All animations disabled via `prefers-reduced-motion` |

---

## 9. Color & Theme

| Element | Current | New |
|---------|---------|-----|
| Page bg | `#000000` (pure black) | `#0a0a0f` (warm dark) |
| Card bg | `#040406` | `#111118` (warmer) |
| Surface | `#0a0a0f` | `#16161f` |
| Hover | `#111118` | `#1c1c28` |
| Border | `rgba(255,255,255,0.06)` | `rgba(255,255,255,0.08)` |
| Accent | `#06b6d4` (cyan) | `#0ea5c9` (softer cyan-blue) |
| Accent glow | `rgba(6,182,212,0.15)` | `rgba(14,165,201,0.12)` |
| Text primary | `#f0f0f5` | `#e8e8ed` |
| Text secondary | `#8a8a9a` | `#7a7a8a` |
| Glass bg | `rgba(0,0,0,0.6)` | `rgba(10,10,15,0.7)` |

---

## 10. Summary

- All pages wrapped in DashboardShell (consistent nav)
- Glass floating sidebar with Work/You groups
- Dashboard: hero + premium metrics + tabbed content (Activity, Processes, Insights)
- Search: conversational AI-first with citations
- Agents: hybrid chat with structured step output
- Memory: knowledge graph explorer (not list-first)
- Subtle organic animations, warmer dark palette
- Page-specific hero headers, no inner sidebars (tabs + collapsible panels instead)
