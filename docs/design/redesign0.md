# Redesign v0 — CORTEX UI

**Document:** Redesign source of truth
**Date:** 2026-07-01
**Status:** Active

## Reality Legend

Every feature below is tagged with a backend reality marker:

| Marker | Meaning |
|--------|---------|
| ✅ | Backend exists now — feature works today |
| 🟡 | Backend exists, but dependent on hardware/config |
| 🔴 | Planned for a future version — not yet built |
| 🟢 | Frontend-only — no backend needed |

This document is the **execution contract** between UI design and backend. Features marked 🔴 must be wired through the planned version. Frontend should degrade gracefully when 🔴 features are unavailable.

---

## Design Philosophy

> Warm black foundation. Silk red accent. Cyan neural glow. Like a real Jarvis.

Every surface should feel warm, intelligent, alive. Not cold-dark (pure #000/#111) but **warm-dark** — deep charcoal with subtle amber undertones. The silk red provides passion and alertness. The cyan provides the "brain" — neural network ambiance, data flow visualization, machine intelligence aura.

**Dark-only.** No light mode.

**Relationship to DESIGN.md:** This redesign deliberately diverges from the current `DESIGN.md` in three ways: (1) glass-morphism is used selectively for the dock, command bar, and hub widgets; (2) neural particle animation runs as an extremely dim background layer; (3) the accent is a **dual-accent system** (silk red for actions + emotion, cyan for data + AI) rather than a single cyan accent. These are intentional choices for the "Jarvis" aesthetic. All other DESIGN.md rules (tonal layering, contrast, font choices, motion discipline, 10% accent rule per-element) still apply.

---

## Color Palette — Contrast Verified

All values checked against WCAG AA. `text-muted` and `accent-red` were brightened from v0 for compliance.

### Warm-Black Scale (Neutrals)

| Token | Hex | OKLCH | Luminance | Usage | Contrast |
|-------|-----|-------|-----------|-------|----------|
| `--bg-base` | `#0d0d0d` | `oklch(0.06 0.01 60)` | 0.0040 | Deepest background (page canvas) | — |
| `--bg-surface` | `#1c1c1c` | `oklch(0.11 0.01 60)` | 0.0103 | Cards, panels, sidebars | 15.9:1 vs primary |
| `--bg-elevated` | `#2a2a2a` | `oklch(0.16 0.01 60)` | 0.0176 | Hover states, active items | 5.8:1 vs secondary |
| `--bg-glass` | `rgba(26,26,26,0.85)` | — | — | Glass-morphism overlays, dock, command bar | — |
| `--bg-widget` | `rgba(26,26,26,0.75)` | — | — | Hub widget cards (glass style) | — |

All neutrals tinted toward amber hue (oklch hue 60) at minimal chroma (0.01) for warmth without visible color shift.

### Silk Red Accent

| Token | Hex | OKLCH | Luminance | Usage | Contrast on bg-base |
|-------|-----|-------|-----------|-------|---------------------|
| `--accent-red` | `#d32f2f` | `oklch(0.50 0.21 30)` | 0.1539 | Primary accent — buttons, active states, emphasis | 4.2:1 ✅ large text / UI |
| `--accent-red-bright` | `#e53935` | `oklch(0.56 0.22 30)` | 0.1903 | Hover, glow, pulse animation | 5.4:1 ✅ |
| `--accent-red-muted` | `rgba(211,47,47,0.20)` | — | — | Background tint, badge fill | — |

### Cyan Neural Accent

| Token | Hex | OKLCH | Luminance | Usage | Contrast on bg-base |
|-------|-----|-------|-----------|-------|---------------------|
| `--accent-cyan` | `#00acc1` | `oklch(0.62 0.12 210)` | 0.3360 | Neural glow, data viz, AI status | 7.6:1 ✅ |
| `--accent-cyan-bright` | `#26c6da` | `oklch(0.72 0.12 210)` | 0.4875 | Hover, bright glow, active AI | 10.3:1 ✅ |
| `--accent-cyan-muted` | `rgba(0,172,193,0.18)` | — | — | Background tint, subtle neural aura | — |

### Text

| Token | Hex | OKLCH | Luminance | Usage | Contrast vs bg-base | Contrast vs bg-surface |
|-------|-----|-------|-----------|-------|---------------------|------------------------|
| `--text-primary` | `#f0f0f0` | `oklch(0.93 0.005 0)` | 0.8948 | Body, headings | 17.8:1 ✅ | 15.9:1 ✅ |
| `--text-secondary` | `#a0a0a0` | `oklch(0.65 0.01 0)` | 0.3604 | Subtitles, metadata | 7.7:1 ✅ | 6.9:1 ✅ |
| `--text-muted` | `#7a7a7a` | `oklch(0.50 0.01 0)` | 0.1865 | Placeholders, disabled, hints | **4.5:1** ✅ | 4.0:1 ✅ large text |
| `--text-inverse` | `#0d0d0d` | — | 0.0040 | Text on colored/light backgrounds | — | — |

`text-muted` (#7a7a7a) is the **maximum darkness** that can meet 4.5:1 on `bg-base`. Do not darken. Placeholder text gets this same color, not a lighter gray.

### Borders

| Token | Value | Usage |
|-------|-------|-------|
| `--border-subtle` | `rgba(255,255,255,0.06)` | Hairline dividers, separator lines |
| `--border-default` | `rgba(255,255,255,0.12)` | Input borders, card edges, panel bounds |
| `--border-red` | `rgba(211,47,47,0.35)` | Red glow border — focus, active |
| `--border-cyan` | `rgba(0,172,193,0.35)` | Cyan glow border — neural active |
| `--border-input-focus` | `rgba(211,47,47,0.40)` | Input focus ring |

### Shadows (Accent-Glow)

| Token | Value | Usage |
|-------|-------|-------|
| `--shadow-red` | `0 0 24px rgba(211,47,47,0.18)` | Red glow — buttons, active states |
| `--shadow-cyan` | `0 0 24px rgba(0,172,193,0.14)` | Cyan glow — AI activity, neural pulse |
| `--shadow-red-strong` | `0 0 40px rgba(211,47,47,0.25)` | Hero moments, critical alerts |
| `--shadow-cyan-strong` | `0 0 40px rgba(0,172,193,0.20)` | Active AI processing |

### Semantic

| Token | Hex | Usage |
|-------|-----|-------|
| `--success` | `#2ecc71` | Healthy, synced, completed |
| `--warning` | `#f39c12` | Degraded, pending, caution |
| `--danger` | `#e74c3c` | Error, down, critical |

---

## Design Tokens (CSS Variables)

```css
:root {
  /* Backgrounds */
  --bg-base: #0d0d0d;
  --bg-surface: #1c1c1c;
  --bg-elevated: #2a2a2a;
  --bg-glass: rgba(26, 26, 26, 0.85);
  --bg-widget: rgba(26, 26, 26, 0.75);
  
  /* Silk Red Accent */
  --accent-red: #d32f2f;
  --accent-red-bright: #e53935;
  --accent-red-muted: rgba(211, 47, 47, 0.20);
  
  /* Cyan Neural Accent */
  --accent-cyan: #00acc1;
  --accent-cyan-bright: #26c6da;
  --accent-cyan-muted: rgba(0, 172, 193, 0.18);
  
  /* Text — all contrast verified */
  --text-primary: #f0f0f0;
  --text-secondary: #a0a0a0;
  --text-muted: #7a7a7a;
  --text-inverse: #0d0d0d;
  
  /* Borders */
  --border-subtle: rgba(255, 255, 255, 0.06);
  --border-default: rgba(255, 255, 255, 0.12);
  --border-red: rgba(211, 47, 47, 0.35);
  --border-cyan: rgba(0, 172, 193, 0.35);
  --border-input-focus: rgba(211, 47, 47, 0.40);
  
  /* Glow Shadows */
  --shadow-red: 0 0 24px rgba(211, 47, 47, 0.18);
  --shadow-cyan: 0 0 24px rgba(0, 172, 193, 0.14);
  --shadow-red-strong: 0 0 40px rgba(211, 47, 47, 0.25);
  --shadow-cyan-strong: 0 0 40px rgba(0, 172, 193, 0.20);
  
  /* Semantic */
  --success: #2ecc71;
  --warning: #f39c12;
  --danger: #e74c3c;
  
  /* Radii */
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 16px;
  --radius-xl: 24px;
  --radius-full: 9999px;
  
  /* Typography */
  --font-sans: 'Geist', system-ui, sans-serif;
  --font-mono: 'JetBrains Mono', 'Geist Mono', monospace;
  
  /* Typography scale (fixed rem — product register) */
  --text-xs: 0.625rem;   /* 10px — labels, badges */
  --text-sm: 0.75rem;    /* 12px — metadata, captions */
  --text-base: 0.875rem; /* 14px — body, content */
  --text-md: 0.9375rem;  /* 15px — titles, subsection heads */
  --text-lg: 1.125rem;   /* 18px — section headings */
  --text-xl: 1.25rem;    /* 20px — card titles, panel headers */
  --text-2xl: 1.5rem;    /* 24px — page titles, mode headers */
  --text-3xl: 1.75rem;   /* 28px — hub greeting, large display */
  
  /* Navigation */
  --topbar-height: 24px;
  --dock-height: 56px;
  --ribbon-height: 24px;
  
  /* Z-index scale — semantic, never arbitrary */
  --z-base: 0;
  --z-dock: 50;
  --z-dropdown: 100;
  --z-sticky: 200;
  --z-modal-backdrop: 300;
  --z-modal: 400;
  --z-toast: 500;
  --z-tooltip: 600;
  
  /* Motion tokens */
  --ease-out: cubic-bezier(0.16, 1, 0.3, 1);
  --ease-in: cubic-bezier(0.4, 0, 1, 1);
  --ease-out-expo: cubic-bezier(0.16, 1, 0.3, 1);
  --ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1);
  
  --duration-instant: 0ms;
  --duration-fast: 150ms;
  --duration-normal: 200ms;
  --duration-slow: 300ms;
}
```

**Font:** Geist (system-ui fallback) for all UI. JetBrains Mono for code, data values, timestamps, file paths, and version badges. **One family for UI** — no display fonts, no serif pairings, no decorative typography.

---

## Typography Hierarchy

Fixed rem scale per product register — no fluid clamp on UI body text. Display headings at most `clamp(1.75rem, 3vw, 2.25rem)` per the hub greeting only.

| Token | Size | Weight | Line Height | Letter Spacing | Used For |
|-------|------|--------|-------------|----------------|----------|
| `display` | `clamp(1.75rem, 3vw, 2.25rem)` | 600 | 1.2 | `-0.02em` | Hub greeting only (one per page) |
| `headline` | `1.25rem` | 600 | 1.3 | `-0.01em` | Mode titles, section headings |
| `title` | `0.9375rem` | 500 | 1.4 | `normal` | Subsection headings, nav items |
| `body` | `0.875rem` | 400 | 1.6 | `normal` | Content text, descriptions |
| `caption` | `0.75rem` | 400 | 1.4 | `normal` | Metadata, timestamps, file sizes |
| `label` | `0.625rem` | 600 | 1.4 | `0.08em` | Uppercase micro-labels (max once/section) |
| `mono` | `0.8125rem` | 400 | 1.5 | `normal` | Code, data values, file paths |

**Line length:** Prose capped at 65–75ch. Data tables can run denser (120ch+). Code blocks use `mono` token.

**Heading wrap:** `text-wrap: balance` on h1–h3. `text-wrap: pretty` on long prose to reduce orphans.

**Label restraint:** Uppercase labels appear **once per section maximum**. Two stacked labels above a heading is visual noise.

---

## Component & Interaction States

Every interactive element defines all six states. This is the canonical reference.

### Buttons

| State | Primary (Silk Red) | Secondary (Ghost) | Tertiary (Neural) |
|-------|-------------------|-------------------|-------------------|
| **Default** | `--accent-red` bg, white text, 44px min-h | Transparent bg, `--text-secondary` text | `--bg-surface` bg, `--accent-cyan` text |
| **Hover** | `--accent-red-bright` bg, soft `--shadow-red` | `--bg-elevated` bg, `--text-primary` text | `--accent-cyan-muted` bg, `--accent-cyan-bright` text |
| **Focus** | 2px `--border-input-focus` ring, offset 2px | Same ring | Same ring (cyan variant) |
| **Active** | Scale 0.98, brighter glow | Scale 0.98 | Scale 0.98 |
| **Disabled** | Opacity 0.35, no shadow, pointer-events none | Opacity 0.35 | Opacity 0.35 |
| **Loading** | Show skeleton shimmer overlay, hide text | Spinner replaces icon | Spinner replaces icon |

Transition: all state changes `--duration-fast` `--ease-out`.

One primary button per visible area. Multiple primaries compete.

### Inputs & Fields

| State | Style |
|-------|-------|
| **Default** | `--bg-surface` bg, `--border-default` border, `--radius-md`, 44px min-h |
| **Hover** | `--border-default` → slightly brighter (`rgba(255,255,255,0.18)`) |
| **Focus** | Border → `--border-input-focus`, 2px ring `--border-input-focus` at 30% opacity. 200ms `--ease-out` |
| **Error** | Border → `--danger`, ring → `rgba(231,76,60,0.25)` |
| **Disabled** | Opacity 0.35, pointer-events none |
| **Filled** | Label floats up if using floating-label pattern; border unchanged |

Placeholder: `--text-muted` color (4.5:1 ✅). Never a lighter gray.

### Navigation Items (Dock Icons)

| State | Style |
|-------|-------|
| **Default** | `--text-secondary`, no bg, 48×48 min touch |
| **Hover** | `--text-primary`, `--bg-elevated` bg, 150ms |
| **Active** | `--accent-red` text, red glow ring, `--accent-red-muted` bg |
| **Disabled** | Opacity 0.3, no tooltip shown |

### Badges / Pills

`--radius-full`, `--text-xs` weight 600, uppercase `letter-spacing: 0.08em`, padding `2px 8px`.

| Variant | bg | text |
|---------|----|------|
| Red | `--accent-red-muted` | `--accent-red-bright` |
| Cyan | `--accent-cyan-muted` | `--accent-cyan-bright` |
| Green | `rgba(46,204,113,0.15)` | `#2ecc71` |
| Amber | `rgba(243,156,18,0.15)` | `#f39c12` |

### Cards / Containers

- **Rest:** `--bg-surface`, `--border-subtle`, `--radius-lg`, flat shadow
- **Hover:** `--bg-elevated` bg, `--border-default` border, `--shadow-red` or `--shadow-cyan` glow (matching card context), 2px upward translateY
- **Interactive:** cursor pointer, 200ms `--ease-out` on transform + bg + border
- **Glass cards (hub widgets):** `--bg-widget`, `backdrop-filter: blur(16px)`, `--border-subtle`

### Modals

- Overlay: `--bg-base` at 60% opacity, fixed, `--z-modal-backdrop`
- Content: `--bg-surface`, `--radius-xl`, modal shadow (`0 8px 32px rgba(0,0,0,0.6)`)
- Entrance: scale 0.95 → 1 + opacity, 250ms `--ease-out`
- Exit: scale 1 → 0.95 + opacity, 200ms `--ease-in`
- Focus trap: Tab cycles within modal. Escape closes.

### Toast

- Position: Bottom-right desktop, bottom-center mobile
- Style: `--bg-elevated`, `--border-default`, `--radius-md`, `--z-toast`
- Entrance: translateX(100%) → 0 + opacity, 250ms `--ease-out`
- Exit: translateX(100%) + opacity 0, 200ms `--ease-in`
- Interruptible: rapid triggers retarget from current state, never restart

---

## Motion & Animation

### Easing Vocabulary

| Curve | Value | Used For |
|-------|-------|----------|
| `--ease-out` | `cubic-bezier(0.16, 1, 0.3, 1)` | Default — entrances, state changes, reveals |
| `--ease-in` | `cubic-bezier(0.4, 0, 1, 1)` | Exits only — elements leaving viewport |
| `--ease-out-expo` | `cubic-bezier(0.16, 1, 0.3, 1)` | Glow pulses, data flow animations |
| `--ease-spring` | `cubic-bezier(0.34, 1.56, 0.64, 1)` | Dock icon bounce, notification pop — rare, small scale |

**No bounce, elastic, or spring on UI transitions.** The only spring usage is sub-20px micro-interactions (dock icon scale on hover).

### Duration

| Token | Value | Used For |
|-------|-------|----------|
| `--duration-instant` | 0ms | State changes that must be immediate (button active scale) |
| `--duration-fast` | 150ms | Hover, focus, small state changes. 80% of interactions |
| `--duration-normal` | 200ms | Panel slides, reveals, card hover. Most transitions |
| `--duration-slow` | 300ms | Mode switches, modal entrances, orchestrated sequences |

### What Moves

Every animation answers "why does this move?" — categorized below.

**State change (150ms, ease-out):**
- Button hover (bg + shadow + scale 1.02)
- Input focus (border + ring)
- Nav item active (bg + text color)
- Toggle switch (thumb position + track color)

**Reveal (200–300ms, ease-out):**
- Panel slides from edge
- Conversation list slides in
- Command bar slides up + backdrop blur
- Modal entrance (scale + opacity)
- New message appears (fade + slide up)

**Data change (500ms, ease-out, opacity-only):**
- Widget metric updates (opacity pulse on changed value)
- Status indicator transitions
- Progress bar fill

**Continuous (2s loop, muted — always behind `prefers-reduced-motion: reduce`):**
- Neural particle drift (extremely dim, 0.3 opacity max)
- Status pulse on active connections
- Data flow glow animation on hub widgets

**Navigation (150ms, ease-out):**
- Mode switch crossfade
- Hub → Mode zoom
- Dock auto-hide / appear

### Motion Rules

1. **Never animate layout properties** (`width`, `height`, `padding`, `margin`, `top`, `left`). GPU-only: `transform` + `opacity`.
2. **Never use `transition: all`** — specify exact properties.
3. **No orchestrated page-load sequences.** Product loads into a task; users don't watch it load.
4. **Staggered list entrances are legitimate.** Each item delays 50ms, max 300ms total. Don't suppress all motion to avoid the "reflex" — just make each reveal fit the content it reveals.
5. **Skeleton shimmer** for loading states: `background-position` slide, 2s linear infinite. `--bg-elevated` base, gradient shimmer toward `--bg-surface`.

### Reduced Motion

**Mandatory:** Every animation must respect `prefers-reduced-motion: reduce`.

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

Exceptions (zero only):
- **Opacity-only transitions** for state changes (hover, focus, active) — these don't cause motion sickness and preserve usability
- **Neural particles** must be `display: none` — not just slowed, fully removed

---

**Reality:** 🟢 Frontend-only. Auth API exists on backend (`auth/` router — JWT access/refresh cookies, register, login, me, ws-token). This section defines the UI forms only.

## Auth Pages

### Login
- Username field
- Password field
- "Sign In" button (silk red, subtle glow on hover)
- Link to Register
- Animated background (neural particle network — cyan on warm black)

### Register
- Username
- Password
- Confirm Password
- Name
- Nickname
- Storage Path — default: `~/cortex/<username>`
- Custom path toggle: "Browse" button opens native OS file picker (`accept="dir"`)
- Absolute path displayed in field (e.g., `/home/adi/cortex/adi`)
- Bio (textarea, optional)
- GitHub username
- GitHub Token (password field, optional)
- Vault Password
- Confirm Vault Password
- "Create Account" button
- Link to Login

### Auth Design Rules
- Glass-morphism card centered on page
- Neural network particle animation in background (cyan nodes + connections)
- Form fields: dark surface, subtle red border on focus, cyan glow for active
- Submit button: silk red bg, subtle pulse animation, red glow shadow
- Input transitions: smooth 200ms ease
- Validation errors: red border + red text, shake animation
- Success transition: fade to main layout (no page reload)

---

## Main Layout — Neural Hub

No sidebar. No traditional nav bar. The interface is a **living mission control** centered on a command-driven interaction model.

### Core Layout

```
┌──────────────────────────────────────────────────────────────┐
│  ⚡ Neural Status Ribbon (thin, always visible, animated)    │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│                                                              │
│                     H U B   V I E W                          │
│                                                              │
│        [Live Widget Grid — pulse, breathe, flow]             │
│                                                              │
│                                                              │
│                                                              │
│                                                              │
│                                                              │
│                                                              │
│   ┌──────────────────────────────────────────────────────┐   │
│   │  ⚡  Ask Cortex anything...                    ⌘K   │   │
│   └──────────────────────────────────────────────────────┘   │
│                                                              │
├──────────────────────────────────────────────────────────────────────┤
│  ┌──┐ ┌──┐ ┌──┐ ┌──┐ ┌──┐ ┌──┐ ┌──┐ ┌──┐ ┌──┐ ┌──┐ 🟢 adi      │
│  │💬│ │🔍│ │🧠│ │🔐│ │📚│ │📐│ │🛠️│ │⚙️│ │🖥️│ │👤│ dock  │
│  └──┘ └──┘ └──┘ └──┘ └──┘ └──┘ └──┘ └──┘ └──┘ └──┘              │
└──────────────────────────────────────────────────────────────┘
```

**Three navigation methods — all work simultaneously:**

| Method | Trigger | Behavior |
|--------|---------|----------|
| **Command Bar** | `⌘K` / click input | Spotlight-style. Type anything. Routes to mode or action. |
| **Floating Dock** | Visible at bottom | Click icon → full-screen mode. Auto-hides when idle. |
| **Hub Widgets** | Click any card | Deep-dive into that domain. Context-aware. |

---

## Mode Interaction & Navigation

### Mode Switching

| Method | Action | Behavior |
|--------|--------|----------|
| Dock click | Click mode icon | Instant switch to that mode. 150ms crossfade. |
| Command bar | Type mode name | Fuzzy match → select → switch |
| Keyboard | `⌘1`–`⌘0` | Switch to dock position 1-10 |
| Keyboard | `⌘K` then type | Spotlight-style, type mode or action |
| Back button | `← Back to Hub` in top bar | Return to hub, 200ms fade |
| Escape | `Esc` | If in mode → return to hub. If in command bar → close it |

### State Persistence

When switching between modes, each mode preserves its state:

| Mode | What Persists |
|------|---------------|
| Chat | Active conversation, scroll position, input draft |
| Search | Last query, results, scroll position |
| Brain | Active tab, scroll position |
| Vault | **Locked** — auto-locks on mode switch (configurable) |
| ModelBook | Active tab, scroll position |
| Code | Open file, cursor position, open panels |
| Utility | Active sidebar tab, toolbox input state |
| Settings | Active sidebar tab, edited-but-unsaved fields (yellow dot) |
| Systems | Active tab, auto-refresh state |
| Profile | Active sidebar tab |

**Return to previous mode:** Each mode switch pushes onto a simple stack. `← Back` returns to the previous mode on the stack, not always the hub. Example:
- Hub → Chat → Vault → Search
- `← Back` → Vault → Chat → Hub
- Stack max depth: 5. Oldest entries drop off.

### Mode Counts

Dock: `💬 🔍 🧠 🔐 📚 📐 🛠️ ⚙️ 🖥️ 👤` — 10 modes

| # | Icon | Mode | Description |
|---|------|------|-------------|
| 1 | 💬 | Chat | Conversation with Cortex |
| 2 | 🔍 | Search | Unified search (RAG, web, chat, code) |
| 3 | 🧠 | Brain | Memory management, sync, file graph |
| 4 | 🔐 | Vault | Encrypted file storage, file manager |
| 5 | 📚 | ModelBook | AI model marketplace, browse/download/manage |
| 6 | 📐 | Code | Editor, LSP, AST, agent-in-the-loop, skills |
| 7 | 🛠️ | Utility | Toolbox, roadmap, knowledge explorer, scratchpad |
| 8 | ⚙️ | Settings | App configuration |
| 9 | 🖥️ | Systems | Hardware monitor, services, logs |
| 10 | 👤 | Profile | User info, vault config, admin panel |

Active mode icon: red accent glow ring.
Hover: cyan glow + tooltip.
Right side: user avatar + online status dot.
Click user → profile quick panel (not full page).

### Command Bar in Mode Context

When inside a mode, `⌘K` shows context-aware commands first, then general commands:

| Context | Priority Results |
|---------|-----------------|
| In Chat | `/remember`, `/clear`, `/save`, `/model` |
| In Code | `/fix`, `/explain`, `/test`, `/review`, `/refactor`, `/skill`, `/mcp` |
| In Vault | `/lock`, `/encrypt`, `/decrypt`, `/shred`, `/import` |
| In Utility | `/toolbox`, `/roadmap`, `/scratchpad`, `/format`, `/hash` |
| In Search | `/web`, `/chat`, `/code`, `/files` |
| In ModelBook | `/download`, `/delete`, `/compare`, `/installed` |
| General | `settings`, `profile`, `system`, `hub` — always available |

Fuzzy search mode names + actions. Results appear below as you type (glass dropdown, max 8 results). Arrow keys navigate, Enter selects, Escape dismisses. Shows keyboard shortcut hints next to each result.

### Mode View (full-screen immersion)

When you click a widget or use command bar → the mode takes over:

```
┌──────────────────────────────────────────────────────────────┐
│  ← Back to Hub     💬 Chat                       ⋮ opts   │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│                                                              │
│            [Full-screen mode content fills here]              │
│                                                              │
│            No sidebar. No distractions.                      │
│                                                              │
│            The mode IS the interface.                        │
│                                                              │
│                                                              │
│                                                              │
├──────────────────────────────────────────────────────────────────────┤
│  ┌──┐ ┌──┐ ┌──┐ ┌──┐ ┌──┐ ┌──┐ ┌──┐ ┌──┐ ┌──┐ ┌──┐  🟢 adi  │
└──────────────────────────────────────────────────────────────────────┘
```

- Full viewport. No sidebar. No chrome.
- Top ribbon becomes minimal (just `← Back` + mode name + actions). The `⋮ opts` menu contains mode-specific secondary actions.
- Dock stays visible at bottom, auto-hides after 3s idle (pops back on mouse move).
- Smooth transition: hub widgets zoom into full mode (250ms ease).
- Escape key or click `← Back to Hub` returns to hub (or previous mode in stack).

---

## Neural Hub View (Landing Page)

The hub is the **default state** — a grid of live glass-morphism widgets showing real-time system state.

```
┌─────────────────────────────────────────────────────────────────────┐
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ 💬 CHAT     │  │ 🔍 SEARCH   │  │ 🧠 BRAIN    │  │ 🔐 VAULT    │  │ 📚 MODELS   │  │
│  │ Last 3 msgs │  │ Quick find   │  │ Index stats  │  │ File count   │  │ Active model │  │
│  │ scrolling   │  │ trending     │  │ sync status  │  │ Lock status  │  │ Downloads    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ 📐 CODE     │  │ 🛠️ UTILITY │  │ ⚙️ SETTINGS  │  │ 🖥️ SYSTEMS  │  │ 👤 PROFILE  │  │
│  │ LSP status   │  │ Quick tools  │  │ Quick links  │  │ CPU 45%     │  │ adi · 🟢    │  │
│  │ open files   │  │ roadmap      │  │              │  │ RAM 6.2 GB  │  │ online      │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                                                             │
│         Background: neural particle network (very subtle)                                    │
│         Nodes pulse with data activity,                                                      │
│         connections light up on interaction                                                  │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

- 2×5 widget grid. Each widget = one mode.
- Widgets: glass morphism (`backdrop-filter: blur(16px)`, warm black).
- Each widget shows live preview of its domain (last chat messages, CPU usage, etc.).
- Click any widget → full-screen immersion into that mode.
- Widgets auto-rearrange based on usage (frequent = larger/left).
- Subtle red glow on active widget, cyan pulse on new data.
- Background: neural particle animation (always on, very dim).

### Neural Status Ribbon

Thin (24px) strip at the very top of the screen.

```
⚡ ONLINE  ·  🧠 llama3.1:8b  ·  📡 42 tps  ·  💾 2.4 GB VRAM  ·  🟢 All Systems Nominal
```

- Always visible, always animating (subtle pulse with data flow).
- Color-coded status dots: 🟢 healthy, 🟡 degraded, 🔴 down.
- Click → expand to system detail panel (drop-down).
- If Qdrant is down → shows yellow, no crash.

---

**Reality:** ✅ Backend APIs exist. Chat endpoints at `/api/v1/conversations/`, SSE streaming via `/api/v1/chat/stream`, WebSocket chat at `/ws/chat`. Memory toggle uses `/api/v1/memory/search`. Model selector reads from `/api/v1/models/ollama/catalog`.

## 💬 Chat Mode

Full-screen chat with Cortex. Conversation list slides in on demand.

### Layout

```
┌──────────────────────────────────────────────────────────────────────┐
│  ← Hub     💬 Chat  ·  Current: "Embeddings pipeline"              │
│                                                                      │
│          [☰ Conversation List] toggle — slides in on demand         │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─ Conversation List (slide-over, 360px, glass, left) ─────────┐  │
│  │                                                               │  │
│  │  🔍 Search conversations...                            [+ New]│  │
│  │  ───────────────────────────────────────────────────────────── │  │
│  │                                                                │  │
│  │  📅 Today                                                      │  │
│  │  ├─ 💬 How does auth work?                           🟢 2:30  │  │
│  │  ├─ 💬 Qdrant connection fix                         🟢 1:15  │  │
│  │  └─ 💬 Neural hub design                                  12:45│  │
│  │                                                                │  │
│  │  📅 Yesterday                                                  │  │
│  │  ├─ 💬 Code review for PR #42                          9:20 AM│  │
│  │  └─ 💬 Setting up embeddings                           4:30 AM│  │
│  │                                                                │  │
│  │  [x] Close                                                    │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                                                              │  │
│  │    ┌──────────────────────────────────────────────────────┐  │  │
│  │    │  You                                     👤 adi    │  │  │
│  │    │                                                      │  │  │
│  │    │  How does the embedding pipeline work in Cortex?    │  │  │
│  │    │                                 12:45 PM  ✓✓  ⋮   │  │  │
│  │    └──────────────────────────────────────────────────────┘  │  │
│  │                                                              │  │
│  │    ┌─── CORTEX ───────────────────────────────────────────┐  │  │
│  │    │ ▲ (cyan accent line on left border)                  │  │  │
│  │    │                                                      │  │  │
│  │    │ The embedding pipeline runs in 3 stages:             │  │  │
│  │    │ 1. Chunking — 512-token chunks with overlap          │  │  │
│  │    │ 2. ONNX optimization                                 │  │  │
│  │    │ 3. Qdrant storage — 768-dim vectors                  │  │  │
│  │    │                                                      │  │  │
│  │    │ ▓▓▓▓▓▓▓▓░░░░░░  [streaming cursor — pulse]          │  │  │
│  │    │                                     12:45 PM  ⋮    │  │  │
│  │    └──────────────────────────────────────────────────────┘  │  │
│  │                                                              │  │
│  │    [↻ Regenerate] [📋 Copy] [🔗 Share] [+ Add to Memory]  │  │
│  │                                                              │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  ⚡  Ask Cortex anything...                      [📎] [🎤]  │  │
│  │  ──────────────────────────────────────────────────────────── │  │
│  │  🧠 Memory: 2 contexts active  ·  📁 3 files in scope       │  │
│  │  💡 Try: "What changed in Qdrant?"  "Show memory stats"     │  │
│  └──────────────────────────────────────────────────────────────┘  │
├──────────────────────────────────────────────────────────────────────────────┤
│  ┌──┐ ┌──┐ ┌──┐ ┌──┐ ┌──┐ ┌──┐ ┌──┐ ┌──┐ ┌──┐ ┌──┐        🟢 adi  │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Design Rules

**Conversation list:** Hidden by default. Toggle via ☰ or swipe right. 360px glass panel slides from left. Groups by date. Search filters titles + content. [+ New] starts blank conversation.

**Message bubbles:** User = right-aligned, `--bg-elevated` surface. Assistant = left-aligned, glass-morphism card, 2px cyan accent line on left border. Streaming = animated cursor (`▓` fill left-to-right, 800ms pulse).

**Message actions (appear on hover):**
- `↻ Regenerate` — re-runs the last turn
- `📋 Copy` — copies message content
- `🔗 Share` — creates shareable link (opens dialog)
- `+ Add to Memory` — saves snippet to long-term memory

**Context ribbon (below input):** Shows active memory contexts, referenced files, suggested follow-ups. Auto-collapses after 3s idle.

**Empty state:**
```
💬 Start a Conversation
I'm Cortex — your local AI brain.
Ask me anything about your code, files, or just have a conversation.
💡 Try asking: "How does the vector search work?" / "Show recent memory paths"
```

**Input bar:** Full-width, glass-morphism, `--radius-lg`. Placeholder: `⚡ Ask Cortex anything...`. Right side: `📎` attach, `🎤` voice (future), `→` send (silk red). Shift+Enter newline, Enter send. Disabled during streaming with "Stop" button.

**Model info:** Top bar shows current model. `⋮ opts` menu → model selector dropdown.

---

**Reality:** ✅ Backend exists. Search endpoint `POST /api/v1/search` with hybrid RAG (vector + fulltext + graph), `GET /api/v1/search`, `POST /api/v1/search/answer` for RAG-answered queries. Memory search at `/api/v1/memory/search`.

**Prefix system — reality check:**
- *(none)* → ✅ RAG pipeline exists
- `/web` → 🔴 Not built (planned v1.11 I4 — Proactive Assistance / web search tool)
- `/chat` → 🟡 Episodic memory exists (`cortex_episodic.py`) but not prefix-routed
- `/code` → 🔴 Not built (planned v1.12 symbol index)
- `/files` → 🟡 File index exists in knowledge ingestion but no dedicated prefix endpoint
- `/vault` → 🟡 Vault search exists (`POST /api/v1/privacy/vault/search`) but no prefix endpoint

**Frontend must:**
- Default (no prefix) → hit `/api/v1/search`
- Show graceful "not yet available" for `/web`, `/code`, `/files` prefixes
- Route `/vault` prefix to vault search endpoint when vault is unlocked; show "vault locked" when locked
- Route `/chat` prefix to episodic memory search endpoint

## 🔍 Search Mode

Full-screen unified search. One search bar, prefix-based routing to different knowledge domains.

### Layout

```
┌──────────────────────────────────────────────────────────────────┐
│  ← Hub     🔍 Search                                   ⋮      │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌──────────────────────────────────────────────────────────┐   │
│   │  🔍  Search across Cortex...               /web  /chat  │   │
│   └──────────────────────────────────────────────────────────┘   │
│   ┌──────────────────────────┬───────────────────────────────┐   │
│   │  Results                 │  Filters / Metadata           │   │
│   │                          │                               │   │
│   │  ┌──────────────────┐   │  📂 Source: All                │   │
│   │  │ Result card 1    │   │  📅 Date: Any                  │   │
│   │  │ snippet + source │   │  🏷️ Type: Any                  │   │
│   │  │ score + path     │   │  🎯 Relevance: >0.5            │   │
│   │  └──────────────────┘   │                               │   │
│   │  ┌──────────────────┐   │  Quick Filters:                │   │
│   │  │ Result card 2    │   │  [Memories] [Files] [Chat]     │   │
│   │  └──────────────────┘   │  [Web] [Code]                  │   │
│   │  ┌──────────────────┐   │                               │   │
│   │  │ Result card 3    │   │  Neural activity indicator    │   │
│   │  └──────────────────┘   │  (pulses during search)       │   │
│   │                          │                               │   │
│   └──────────────────────────┴───────────────────────────────┘   │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Prefix System

| Prefix | Searches | Backend Pipeline | Example |
|--------|----------|-----------------|---------|
| *(none)* | All indexed memory | RAG (vector + fulltext + graph, RRF + MMR) | `how does auth work?` |
| `/web` | Web + indexed memory | Web search tool → RAG rerank | `/web latest python 3.13 features` |
| `/chat` | Chat history only | Episodic memory search | `/chat what did we say about qdrant?` |
| `/code` | Code symbols + files | Symbol index + AST search | `/code function validate_token` |
| `/files` | File contents + names | File index search | `/files config.py` |
| `/vault` | Vault filenames + tags | Vault index (content stays encrypted) | `/vault tax-2025` |

### Result Cards

Glass-morphism card showing title, file path, snippet with highlighted terms, relevance score (color-coded), source type badge, timestamp, and action buttons.

### Search Modes

**Default (RAG):** Queries vector DB + fulltext + knowledge graph. RRF fusion + MMR diversity. Returns top 10-20 results.

**/web:** Web search via tool. 5-10 results. Optional LLM summarization. Cached (refetch after 5 min).

**/chat:** Episodic memory search. Returns relevant exchanges with context. Grouped by conversation.

---

**Reality:** 🟡 Partially built. Core memory APIs exist:
- ✅ Knowledge health/stats at `GET /api/v1/memory/knowledge/health`, `GET /api/v1/memory/knowledge/stats`
- ✅ Memory CRUD at `/api/v1/memory/long-term`, `/api/v1/memory/working`, `/api/v1/memory/episodic`, `/api/v1/memory/semantic`
- ✅ Knowledge graph at `/api/v1/memory/graph` (nodes + edges)
- ✅ RAG search at `POST /api/v1/search`
- 🔴 **File watcher auto-sync** not built (planned v1.09 K4 — Watchdog Auto-Sync)
- 🔴 **File connection graph** (D3 interactive) not built — knowledge graph exists but file-level relationship visualization doesn't (planned v1.09 K10 — Nice priority)
- 🔴 **Memory consolidation, SM-2, compression** not built (planned v1.09 K12-K16)
- 🟢 **Memory paths UI + managed paths** is frontend-only config, stores in settings

**Frontend must:**
- Hit `/api/v1/memory/knowledge/health` and `/api/v1/memory/knowledge/stats` for real data
- Show "Indexing not started" when knowledge engine hasn't ingested anything
- Memory stats widget reads from backend — show "no data yet" if stats endpoints return empty

## 🧠 Brain Mode (Memory)

Full-screen mode — the living brain of Cortex. Memory management, sync, file connection graph.

### Layout

```
┌──────────────────────────────────────────────────────────────────┐
│  ← Hub     🧠 Memory / Brain                          ⋮ opts  │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  📂 Managed Paths                     [+ Add Path]       │   │
│  │  ┌────────────────────────────────────────────────────┐  │   │
│  │  │  ~/projects/cortex           🔄 auto   [x]         │  │   │
│  │  │  ~/projects/work             ✅ synced  [x]         │  │   │
│  │  │  ~/Documents/notes           ⏸ paused  [x]         │  │   │
│  │  │  ~/projects/personal         🔄 auto   [x]         │  │   │
│  │  └────────────────────────────────────────────────────┘  │   │
│  │                                                           │   │
│  │  Exclusions:  node_modules/*  .git/*  __pycache__/       │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────┬─────────────────────────────────┐  │
│  │  🔄 Sync Controls        │  📊 Memory Stats               │  │
│  │                          │                                 │  │
│  │  [⚡ Sync Now]           │  Files indexed: 12,847         │  │
│  │                          │  Total chunks:  284,291        │  │
│  │  Auto-sync: ● ON ○ OFF  │  Last sync:     2 min ago      │  │
│  │                          │  Sync duration: 4.2s           │  │
│  │  Status: 🟢 Synced       │  Storage:       1.2 GB         │  │
│  │                          │                                 │  │
│  │  Sync History ▼          │  [Re-index All]                │  │
│  │  ┌────────────────────┐  │                                 │  │
│  │  │ 2m ago · 142 files │  │  🏷️ Active Watches: 4          │  │
│  │  │ 15m ago · 89 files │  │                                 │  │
│  │  │ 1h ago · 23 files  │  │                                 │  │
│  │  └────────────────────┘  │                                 │  │
│  └──────────────────────────┴─────────────────────────────────┘  │
│                                                                  │
│  ═══════════════════ File Connection Graph ═══════════════════   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  [Interactive D3 graph — files as nodes,                 │   │
│  │   connections as edges. Color-coded by language.         │   │
│  │   Click node → highlight connections + preview.          │   │
│  │   Filter by type, search within graph.]                  │   │
│  │                                                          │   │
│  │  ⚡ Live: pulses when files change                       │   │
│  │  🔴 = actively changing, 🟢 = new, ⚪ = stable           │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Filter: [All] [Python] [JS/TS] [Rust] [Go] [Config]           │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Sections

**1. Memory Paths** — List of watched directories. Each entry: path + status badge (auto/synced/paused) + remove. "Add Path" → OS folder picker. Pattern exclusions: `node_modules/*`, `.git/*`, `__pycache__/*`, custom. Drag to reorder priority.

**2. Sync Controls** — "Sync Now" button (silk red, pulse during sync). Auto-sync toggle. Status: 🟢 Synced / 🟡 Syncing / 🔴 Error / ⏸ Paused. Sync history with time, file count, duration.

**3. File Connection Graph** — Interactive D3 graph. Edges = imports, references, symbol links (AST). Color-coded by language. Click node → highlight connections + file info. Zoom, pan, drag. Search within graph. Live pulse on file change.

**4. Memory Stats** — Files indexed, chunks, embeddings, last sync, storage used, active watches.

**5. Include/Exclude Patterns** — Global include/exclude, per-path overrides, pattern tester.

---

**Reality:** ✅ Fully built. Vault API at `/api/v1/privacy/vault/`: unlock, lock, status, list files, upload, preview, download, delete, rename, move, update metadata, create folder, search, export, change password. Fernet encryption, AES-256-GCM. Split pane is pure frontend state.

**Frontend must:**
- All file operations hit the vault API
- Lock state is local (no backend call — vault tracks its own session)
- Split pane is browser-local state only

## 🔐 Vault Mode

Encrypted personal file storage. File manager layout. Reveals **nothing** on lock screen — no file count, no size.

### Lock State

```
┌──────────────────────────────────────────────────────────────┐
│  ← Hub     🔐 Vault                                     ⋮  │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│                                                              │
│                          🔐                                  │
│                                                              │
│                 ┌──────────────────────┐                    │
│                 │                      │                    │
│                 │  [────────────────]  │                    │
│                 │  Vault Password      │                    │
│                 │                      │                    │
│                 │  [🔓 Unlock]         │                    │
│                 └──────────────────────┘                    │
│                                                              │
│                                                              │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

Clean glass-morphism card centered. Password field only. No metadata revealed.

Lock screen rules:
- Enter key submits, Escape clears field.
- Red glow border on wrong attempt + shake animation.
- Failed attempt cooldowns: 10s → 30s → 2min → 15min.
- After 5 failures → full logout required.
- "Forgot Password?" → requires re-auth with login credentials, then vault reset.

### Unlocked Layout — File Manager

```
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│  ← Hub     🔐 Vault · ~/Cortex/vault/                                    ⋮ opts  🔒 Lock  │
├─────── Directory Tree ───────┬──────────── File List — 24 items ───────────────────────────┤
│                              │                                                                 │
│  🔐 Vault Root          │  Name                    Size      Type      Modified      Status│
│  ├── 📁 documents/      │  ────────────────────────────────────────────────────────────│
│  │   ├── 📁 work/       │  📁 documents/           --       Folder    2d ago        🔒  │
│  │   └── 📁 personal/   │  📁 photos/               --       Folder    5d ago        🔓  │
│  ├── 📁 photos/         │  📄 tax-2025.pdf        2.4 MB   PDF       2d ago        🔒  │
│  ├── 📁 projects/       │  📄 credentials.txt     8 KB     Text      1w ago        🔒  │
│  │   └── 📁 cortex/     │  📄 notes.md            16 KB    Markdown  3w ago        🔓  │
│  ├── 📁 backups/        │  📄 id_rsa              3 KB     Key File  1mo ago       🔒  │
│  │                       │  📄 budget.xlsx         128 KB   Spreadsheet 2d ago     🔒  │
│  └── 📁 archive/         │  📸 vacation.jpg        4.1 MB   Image     1w ago       🔓  │
│                          │  🎬 demo.mp4            124 MB   Video     2w ago       🔒  │
│  📦 Used: 1.2 GB / 50 GB │  📄 passport-scan.pdf   6.8 MB   PDF       1mo ago      🔒  │
│  🔐 Encrypted: 18 files  │  ...                                                         │
│  🔓 Decrypted: 6 files   │                                                                 │
│                          ├────── Preview ─────────────────────────────────────────────┤
│  Quick Actions:          │                                                                 │
│  [📥 Import]             │  🔐 tax-2025.pdf                                              │
│  [📤 Export]             │  Size: 2.4 MB · Encrypted: AES-256-GCM                       │
│  [➕ New Folder]         │  Added: 2 days ago · Last accessed: never                    │
│  [⚡ Batch Encrypt]      │                                                                 │
│                          │  [🔓 Decrypt + Open] [📤 Export Decrypted] [🗑 Shred] [⋯]  │
│                          └───────────────────────────────────────────────────────────────┤
├──────────────────────────────────────────────────────────────────────────────────────────┤
│  📁 6 dirs · 🔒 18 encrypted · 🔓 6 decrypted · 1.2 GB / 50 GB           🔐 Locked  │
├──────────────────────────────────────────────────────────────────────────────────────────┤
│  ⚡  /encrypt tax-2025.pdf · /decrypt notes.md · /import ~/Downloads/                   │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

### Sortable Columns

| Column | Sort |
|--------|------|
| Name | Alphabetical, folders first |
| Size | Ascending/descending |
| Type | Grouped by extension |
| Modified | Chronological |
| Status | 🔒 encrypted / 🔓 decrypted |

Column widths adjustable by dragging headers.

### File Status Icons

| Icon | Meaning |
|------|---------|
| 🔒 | Encrypted (stored encrypted) |
| 🔓 | Decrypted (currently unencrypted in vault) |
| 🔄 | Encrypting/Decrypting in progress |
| ⚠️ | Corrupted (key mismatch) |

### Directory Tree (Left Panel)

Collapsible tree. Shows vault folder structure. Click folder → navigate. Right-click → new folder, paste, properties.

### Split Pane Mode

Toggle with `Ctrl+U`. Two panes side-by-side for copy/move:

- `F5` = copy selected files from active pane to other pane's current directory
- `F6` = move
- Each pane has its own directory tree

### Operations

| Operation | Behavior |
|-----------|----------|
| **Encrypt** | Drag & drop or `/encrypt` → file encrypted with Fernet |
| **Decrypt** | Click 🔓 → file decrypted to temp, opened in viewer |
| **Shred** | Overwrite 3x (random→zeros→random) then delete — irreversible |
| **Import** | OS file picker → copies into vault + auto-encrypts |
| **Export** | Decrypts and exports decrypted copy to chosen location |
| **Batch encrypt/decrypt** | Multi-select → bulk action |
| **View in-place** | Decrypt to temp, open system viewer, auto-shred temp on close |

### Category Sidebar

| Category | Shows |
|----------|-------|
| 📁 All Files | Everything |
| 🔒 Encrypted | Only locked files |
| 🔓 Decrypted | Currently decrypted files |
| 🕐 Recent | Last 30 days |
| ⭐ Favorites | Starred files |
| 📦 Large Files | >100 MB |
| 🗑 Trash | Soft-deleted (auto-shred after 30 days) |
| 🏷️ Tags | Grouped by color tag |

### Auto-Lock

| Trigger | Behavior |
|---------|----------|
| Idle 5 min | Auto-lock, return to lock screen |
| Switch mode | Auto-lock (configurable toggle) |
| Manual lock | Click 🔒 in bottom bar or `/lock` |
| 5 failed attempts | Force re-login to Cortex account |

Auto-lock countdown visible in bottom bar: `🔐 Vault locked · Auto-lock in 4:32`

### Context Menu (Right-Click)

```
🔓 Decrypt + Open
📤 Export Decrypted Copy...
─────────────────
🔒 Re-encrypt with New Key
📋 Copy to...
✂️ Move to...
✏️ Rename
─────────────────
⭐ Add to Favorites
🏷️ Add Tag...
─────────────────
🗑 Shred (Secure Delete)
📋 Copy Path
📄 Properties
```

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `↑↓` | Navigate files |
| `Enter` | Open / Decrypt + Open |
| `F2` | Rename |
| `F5` | Copy (split pane) |
| `F6` | Move (split pane) |
| `F8` / `Del` | Shred |
| `Ctrl+E` | Encrypt selected |
| `Ctrl+D` | Decrypt selected |
| `Ctrl+I` | Import files |
| `Ctrl+F` | Search vault |
| `Ctrl+Shift+N` | New folder |
| `Ctrl+A` | Select all |
| `Ctrl+U` | Toggle split pane |
| `Space` | Toggle file preview |
| `/` | Quick filter |
| `Esc` | Clear filter / close preview |

### Empty / New User States

**Empty vault (created but no files):**
```
🔐 Vault is empty. Drop files here to encrypt them securely.
/encrypt ~/Documents/tax-2025.pdf
/import ~/Downloads/
```

**No vault yet (new user):**
```
🔐 Your secure vault hasn't been created yet.
Vault location: ~/Cortex/vault/
[Create Vault] with password setup
```

---

**Reality:** 🟡 Partially built.
- ✅ Ollama catalog at `/api/v1/models/ollama/catalog` (name, size, quantization, digest, modified date)
- ✅ Installed models at `/api/v1/models/installed` (real Ollama data)
- ✅ Model downloads at `/api/v1/downloads` (progress, queue, history)
- ✅ Model comparison via `/api/v1/models/ollama/catalog` (metadata-only — no benchmarks, no MMLU)
- 🔴 **HuggingFace browse** not planned (would require HF token integration)
- 🟢 **Model settings** (provider selection, GPU layers) read from backend config
- 🟡 **Active model** tracked in LLM service state

**Frontend must:**
- Model detail = only what Ollama returns (name, size, quant, digest, modified). No MMLU, no VRAM predictions, no benchmark estimates.
- "Download" = hits download endpoint, tracks progress via downloads API
- "Compare" = table of real fields only. No fantasy stats.
- HuggingFace tab = show "Coming soon — requires HuggingFace token" until built
- Always show "Ollama disconnected" state when link is down

## 📚 ModelBook Mode

Marketplace & manager for AI models. Browse, download, delete, compare.

### Layout

```
┌──────────────────────────────────────────────────────────────────────┐
│  ← Hub     📚 ModelBook                                      ⋮    │
├────── Browse ── Installed ── Compare ── Downloads ─────────────────┤
│                                                                      │
│  ┌─── Filters ────────┐ ┌─── Model List ─────────────────────────┐ │
│  │                    │ │                                          │ │
│  │  🔍 Search...     │ │  📦 llama3.1:8b                          │ │
│  │                    │ │  Meta Llama 3.1 8B                      │ │
│  │  Provider          │ │  4.9 GB · Q4_K_M · Updated 2d ago      │ │
│  │  [✓] Ollama       │ │  🟢 Installed           [Open] [🗑]     │ │
│  │  [ ] llama.cpp    │ │                                          │ │
│  │                    │ │  ─────────────────────────────────────    │ │
│  │  Size              │ │                                          │ │
│  │  [✓] <3B          │ │  📦 qwen2.5:7b                          │ │
│  │  [✓] 3B-8B        │ │  Qwen 2.5 7B                           │ │
│  │  [ ] 8B-30B       │ │  4.3 GB · Q4_K_M · Updated 1w ago      │ │
│  │  [ ] 30B+          │ │  📥 Not installed       [Download]      │ │
│  │                    │ │                                          │ │
│  │  Quantization      │ │  ─────────────────────────────────────    │ │
│  │  [✓] Q4_K_M       │ │                                          │ │
│  │  [✓] Q5_K_M       │ │  📦 nomic-embed-text                    │ │
│  │                    │ │  274 MB · F16 · Updated 1mo ago        │ │
│  │  Sort:             │ │  🟢 Installed           [Open] [🗑]     │ │
│  │  [Name ▼]          │ │                                          │ │
│  │                    │ │                  Page 1 of 4  [← →]     │ │
│  └────────────────────┘ └──────────────────────────────────────────┘ │
│                                                                      │
│  Status bar: 🟢 Ollama  ·  📥 1 active  ·  💾 8.97 GB used         │
├──────────────────────────────────────────────────────────────────────┤
│  ⚡  /download qwen2.5:7b · /compare llama3.1 qwen2.5 · /installed │
└──────────────────────────────────────────────────────────────────────┘
```

### Tabs

| Tab | Content |
|-----|---------|
| **Browse** | Model list with filters — discover new models |
| **Installed** | Only downloaded models |
| **Compare** | Side-by-side model comparison |
| **Downloads** | Active download queue + history |

### Model Detail Panel

Shows what Ollama provides: name, description, size, quantization, modified date, digest, provider, variants.

```
📦 Name: llama3.1:8b
📏 Size: 4.9 GB (Q4_K_M)
📅 Updated: 2 days ago
🔑 Digest: a7b...f3c2
🏢 Provider: Ollama

Other variants: Q4_0 · Q4_K_M · Q5_K_M · Q8_0
[Download Variant] [Use in Chat] [Delete]
```

### Compare Tab

Table comparing selected models on available metadata: size, quantization, parameters, context length, provider, install status.

### Downloads Tab

Active downloads with progress bar, speed, ETA. History of completed/failed downloads.

### Installed Tab

Table of local models: name, size, quantization, provider, active status. Group by model with variant expand.

### Bottom Status Bar

```
🟢 Ollama connected:300s · 📥 2 downloads · 💾 8.97 GB used · 🧠 Active: llama3.1:8b
```

### Provider Support

| Provider | Source | Data Available |
|----------|--------|---------------|
| Ollama | Local instance | Name, size, quant, digest, modified date |
| llama.cpp | GGUF files on disk | File name, size |
| HuggingFace | Remote browse | Name, description, size (requires HF token) |

---

**Reality:** 🔴 Mostly planned. Current backend has only:
- ✅ GitHub integration endpoints at `/api/v1/github` (PRs, issues, repos)
- 🔴 **LSP integration** — planned v1.12 P01 (tree-sitter AST engine, 13+ languages)
- 🔴 **Code analysis** — planned v1.12 P02-P03
- 🔴 **Agent coding tools** (rename, extract, find-refs) — planned v1.12 P04
- 🔴 **Agent-in-the-loop protocol** — planned v1.12 P05
- 🔴 **Subagent delegation** — planned v1.12 P06 (documented in P11.md)
- 🔴 **Git intelligence** — planned v1.12 P07
- 🔴 **Code review / doc / test generation** — planned v1.12 P08-P10
- 🔴 **CI/CD integration** — planned v1.12 P11
- 🟢 **Skills/Hooks/MCP management** — file-based infrastructure (`.claude/skills/`, `.claude/hooks/`). These are files on disk, not API endpoints. Frontend reads/writes skill files directly.

**Frontend must:**
- Show "Code intelligence: preparing" state when LSP/AST features are unavailable
- Terminal → embed xterm.js, communicate via WebSocket (planned v1.12)
- Skills/Hooks/MCP → read/write files directly (use local file API or backend file endpoint)
- File tree → read project structure via filesystem
- Dark state for all v1.12 features: show coming-soon message
- GitHub panel → hits real backend endpoint, works today

## 📐 Code Mode

Full IDE with AI superpowers. Editor, LSP, AST, Git, Agent-in-the-loop protocol.

### Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ← Hub     📐 Code  ·  auth_flow.py  ·  feat/auth   ⟐ Split  ⟐ Tab  ···  │
├─── Files ── AST ── LSP ── Git ── Agent ── Skills ── Terminal ─────────────────┤
│                                                                              │
│  ┌─── File Tree (slide, 280px) ───┐ ┌─── Editor ────────────────────────┐  │
│  │  🔍 Filter files...       ⊞    │ │  feature/auth_flow.py    📄 *    │  │
│  │  src/                        │ │ ─────────────────────────────────── │  │
│  │  ├─ 🔷 components/           │ │                                     │  │
│  │  │  ├─ 🔷 auth/              │ │ 1  import jwt                      │  │
│  │  │  │  ├─ login.tsx          │ │ 2  from fastapi import Depends     │  │
│  │  │  │  ├─ register.tsx       │ │ 3                                  │  │
│  │  │  │  └─ oauth.tsx          │ │ 4  async def validate(             │  │
│  │  │  ├─ login.tsx 🟡            │ │ 5      token: str                │  │
│  │  │  └─ shared/               │ │ 6  ════🔴 unused import os ════  │  │
│  │  ├─ 🔷 hooks/                │ │ 7      ) -> User:                 │  │
│  │  │  └─ useAuth.ts            │ │ 8      return decode(token)        │  │
│  │  └─ utils/                   │ │ 9                                  │  │
│  │     └─ validators.py         │ │ 10                                 │  │
│  │                              │ │ 11                                 │  │
│  │                             │ │ 12                                 │  │
│  │  📦 Python · 147 files      │ └──────────────────────────────────────┘  │
│  └──────────────────────────────┘                                          │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  🔵 LSP Ready  │  ⚠ 3 warnings  │  🔴 1 error  │  Ln 6, Col 15   │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
├──────────────────────────────────────────────────────────────────────────────┤
│  ⚡  /fix unused import · /explain validate() · /test · /review            │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Tool Tabs

| Tab | Icon | Panel Location |
|-----|------|---------------|
| Files | 📂 | Left collapsible — file tree |
| AST | 🌳 | Left collapsible — tree view of code structure |
| LSP | 🔵 | Right collapsible — diagnostics list |
| Git | 🔀 | Right collapsible — diff + commit |
| Agent | 🤖 | Right collapsible — code agent chat + actions |
| Skills | 🧩 | Right collapsible — skill/hook/MCP management |
| Terminal | ⌨️ | Bottom collapsible — command output |

Click tab → panel slides in. Click again → closes. Multiple can stack.

### Agent Panel (Agent-in-the-Loop Protocol)

Right-side panel. User sends coding requests → agent reads file → makes change → runs test → shows diff → user applies or rejects.

```
🤖 Code Agent  ·  focus: auth_flow.py

💬 You: fix unused import on line 6

🤖 Cortex: Removed `import os` — not used.
┌─────────────────────────┐
│  - import os            │
│  ✓ Test: lint passes    │
└─────────────────────────┘
[✓ Apply] [↻ Try Different] [📋 Diff]

💬 You: add type hints to validate()
🤖 Cortex: Scanning usage sites...
│ 🟢 Types found: str, User
│ 🟢 No breaking changes
└── All checks passed ✅
[✓ Apply] [↻ Regenerate] [📋 Diff]
```

### Subagent Delegation UI

For complex tasks, shows decomposition tree with parallel agents:

```
🤖 Refactoring auth_flow.py
📋 Task 1: Extract JWT logic       🟢 Done
📋 Task 2: Add validation middleware 🟡 Running
📋 Task 3: Update tests          ⏳ Pending
├── 🔄 Subagent 2: Parallel fan-out (3 agents)
│   ├─ 🟢 verify_jwt_signature.py
│   ├─ 🟢 validate_refresh_token.py
│   └─ ⏳ token_storage.py
│   ✓ 2/3 complete  ·  ⏱ 4.2s
└────────────────────────────────
```

### Skills Panel (Hooks, MCP, Skill Manager)

Right-side panel — full developer ecosystem management. Three sections stacked vertically.

#### Skill Manager

List of installed skills with toggle activation, status badge, and actions:

```
🧩 Skills  ·  .claude/skills/ (12 installed)
┌──────────────────────────────────────────────────────────┐
│  [📦 New Skill]  [🔄 Refresh]  [📥 Import]              │
│                                                           │
│  🟢  cortex-repo-discovery            [⚡] [✏️] [🗑]  │
│  🟢  cortex-repository-intelligence   [⚡] [✏️] [🗑]  │
│  🟢  cortex-system-validation         [⚡] [✏️] [🗑]  │
│  🟡  cortex-architecture-drift        [⚡] [✏️] [🗑]  │
│  🔴  cortex-update-checker            [⚡] [✏️] [🗑]  │
│                                                           │
│  ─────────────────────────────────────────────             │
│  [+ Create Skill]                                         │
│                                                           │
│  Skill directory: .claude/skills/                         │
└──────────────────────────────────────────────────────────┘
```

- Status: 🟢 active, 🟡 disabled, 🔴 error
- `[📦 New Skill]` — guided form (name, description, triggers, code template)
- `[📥 Import]` — file picker for skill .md files
- `[⚡]` — toggle activation
- `[✏️]` — open skill editor (inline, syntax-highlighted)
- `[🗑]` — delete with confirmation

#### Hooks Manager

Git hooks + lifecycle hooks with enable/disable and inline editing:

```
🔗 Hooks  ·  .claude/hooks/
┌──────────────────────────────────────────────────────────┐
│  pre-commit   🟢  [Edit] [Test] [📋 View Log]         │
│  pre-push     🟢  [Edit] [Test] [📋 View Log]         │
│  post-merge   ⏸  [Edit] [Test] [📋 View Log]         │
│  post-checkout 🟢  [Edit] [Test] [📋 View Log]         │
│  ─────────────────────────────────────────────             │
│  [+ Add Hook]                                              │
│  Type: [pre-commit ▼]  Command: [______] + [Args]        │
└──────────────────────────────────────────────────────────┘
```

- Status per hook: 🟢 active, ⏸ disabled, 🔴 error
- `[Edit]` — opens inline editor with the hook script
- `[Test]` — dry-run the hook, show output
- `[📋 View Log]` — last 50 lines of hook execution log
- `[+ Add Hook]` — form: select type (pre-commit, pre-push, post-merge, post-checkout), enter command and args

#### MCP Server Manager

Configure, test, and monitor MCP servers:

```
🔌 MCP Servers
┌──────────────────────────────────────────────────────────┐
│  🟢  context7          [🔌 Config] [📋 Logs] [🗑]    │
│      └─ Command: npx @context7/mcp                      │
│      └─ Status: connected · 142ms latency               │
│                                                           │
│  🟢  sequential-thinking [🔌 Config] [📋 Logs] [🗑]    │
│      └─ Command: node mcp-sequential-thinking           │
│      └─ Status: connected · 85ms latency                │
│                                                           │
│  🔴  playwright        [🔌 Config] [📋 Logs] [🗑]    │
│      └─ Command: npx @anthropic/playwright-mcp          │
│      └─ Status: disconnected · Last error: ENOENT       │
│                                                           │
│  ─────────────────────────────────────────────             │
│  [+ Add MCP Server]                                       │
│                                                           │
│  Name: [______]  Command: [______]                       │
│  Args: [______]  Env vars: [_______|_______]              │
│  [🔌 Test Connection]                                     │
└──────────────────────────────────────────────────────────┘
```

- Status per server: 🟢 connected, 🟡 connecting, 🔴 error
- `[🔌 Config]` — edit name, command, args, env vars
- `[📋 Logs]` — streaming logs from the MCP server process
- `[🗑]` — remove server configuration
- `[+ Add MCP Server]` — form with name, command, args, env vars
- `[🔌 Test Connection]` — pings the MCP server, shows response time

#### Skill Marketplace

Browse and install skills from the Cortex ecosystem:

```
📦 Skill Marketplace
┌──────────────────────────────────────────────────────────┐
│  🔍 Search skills...                                     │
│                                                           │
│  🔥 Trending                                              │
│  ├─ Code Review Assistant     ⭐ 142    [Install]       │
│  ├─ Memory Optimizer          ⭐ 98     [Install]       │
│  └─ Web Search Pro            ⭐ 73     [Install]       │
│                                                           │
│  Categories: [All] [Code] [Memory] [System] [Utility]   │
│                                                           │
│  Source: Cortex Community Registry                        │
└──────────────────────────────────────────────────────────┘
```

### AST Explorer

```
🔴 Line 6  ·  Unused import 'os'       [Quick Fix: Remove] [Explain]
🟡 Line 12 ·  Variable 'x' not used    [Quick Fix: Prefix _] [Explain]
🟡 Line 23 ·  Missing return type       [Quick Fix: Add -> None] [Explain]
🟢 Line 1  ·  Import 'jwt' not used?   (false positive — used as type)
```

### Git Panel

Shows diff for current file, stage/unstage inline, commit with message, recent commits.

### Inline Code Actions (Editor Gutter)

Line-level actions on hover:

```
💡 Explain  ·  🧪 Test  ·  📝 Doc  ·  ⚡ Fix  ·  📋 Copy
```

### Split View

Tab bar supports multiple open files. `⟐` button splits editor horizontally/vertically. Side-by-side diff view.

### Empty State

```
📐 Code Hub — Open a project to start coding
[📂 Open Project] [📁 Recent Projects ▾]
💡 Commands:  /explain  /review  /test  /fix
```

---

## 🛠️ Utility Mode

Personal toolbox, roadmap explorer, knowledge base, scratchpad, and quick actions.

### Layout

```
┌──────────────────────────────────────────────────────────────────┐
│  ← Hub     🛠️ Utility                                     ⋮   │
├────── sidebar ──────────┬────────────── main panel ────────────┤
│                         │                                          │
│  ├─ 🧰 Toolbox         │  [Panel content changes per category]  │
│  ├─ 🗺️ Roadmap        │                                          │
│  ├─ 📚 Knowledge Base  │                                          │
│  ├─ 📝 Scratchpad      │                                          │
│  └─ ⚡ Quick Actions   │                                          │
│                         │                                          │
└──────────────────────────────────────────────────────────────────┘
```

### 1. 🧰 Toolbox

Developer utility tools in a card grid layout:

```
🧰 Toolbox
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ JSON         │  │ Base64       │  │ Regex        │
│ Formatter    │  │ Encode/Decode│  │ Tester       │
│ ───────────  │  │ ───────────  │  │ ───────────  │
│ [Paste →     │  │ Input →      │  │ Pattern:     │
│  format]     │  │ encode/decode│  │ Test string: │
│ ✓ Valid JSON │  │ 📋 Copy      │  │ 3 matches    │
└──────────────┘  └──────────────┘  └──────────────┘

┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ UUID Gen     │  │ Timestamp    │  │ Hash Gen     │
│ ───────────  │  │ ───────────  │  │ ───────────  │
│ [v4] [v7]   │  │ Unix → Date  │  │ MD5 SHA256   │
│ uuid-abc...  │  │ Date → Unix  │  │ ───────────  │
│ 📋 Copy      │  │ 1740787200  │  │ [Select text │
└──────────────┘  └──────────────┘  │  → hash]     │
                                   └──────────────┘

┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ URL Tool     │  │ Markdown     │  │ Diff Viewer  │
│ ───────────  │  │ Preview      │  │ ───────────  │
│ Encode/decode│  │ ───────────  │  │ Side A │ B  │
│ 📋 Copy      │  │ Live render  │  │ ───────────  │
└──────────────┘  └──────────────┘  └──────────────┘
```

Tools:
| Tool | Input | Output |
|------|-------|--------|
| **JSON Formatter** | Paste JSON or URL | Pretty-printed tree, validation status, line number on error |
| **Base64** | Text or file | Encoded/decoded output, copy button |
| **Regex Tester** | Pattern + test string + flags | Match highlights, group capture table, explanation |
| **UUID Generator** | — | v4 or v7 UUID, click to copy, bulk generate N |
| **Timestamp Converter** | Unix epoch or date string | Human-readable ↔ Unix, timezone-aware |
| **Hash Generator** | Text input | MD5, SHA1, SHA256, SHA512 — all shown at once |
| **URL Encoder/Decoder** | URL string | Encoded/decoded, component vs full encoding |
| **Markdown Preview** | Markdown textarea | Live rendered preview (scroll sync) |
| **Diff Viewer** | Text A vs Text B | Side-by-side diff, character-level highlighting |

### 2. 🗺️ Roadmap

Project roadmap and version progression viewer:

```
🗺️ Cortex Roadmap
┌──────────────────────────────────────────────────────────────────┐
│                                                                   │
│  🎯 Current Focus: v1.09 — The Knowledge (18 phases, 108 tasks)  │
│                                                                   │
│  Timeline ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░░░░░░░░░░░  42% complete   │
│                                                                   │
│  ┌────── Versions ────────────────────────────────────────────┐  │
│  │  ✅ v1.01 Foundation        │  ✅ v1.02 The Brain          │  │
│  │  ✅ v1.03 The Memory        │  ✅ v1.04 The Awareness      │  │
│  │  ✅ v1.05 The Vault          │  ✅ v1.06 The Developer      │  │
│  │  ✅ v1.07 The Interaction    │  🔄 v1.09 The Knowledge     │  │
│  │  🔲 v1.08 The Planning       │  🔲 v1.10 The Scheduler     │  │
│  │  🔲 v1.11 The Researcher     │  🔲 v1.12 The Developer     │  │
│  │  🔲 v1.13 The Optimizer     │  🔲 v1.14 The Polished      │  │
│  │  🔲 v2  The Architecture    │  🔲 v3  The Desktop         │  │
│  │  🔲 v4  The Automaton       │  🔲 v5  The Workspace       │  │
│  │  🔲 v6  The Ecosystem       │                              │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                   │
│  Current Version: Capability Status                               │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Phases  ✅ 6/18  ·  Tasks  ✅ 42/108                     │  │
│  │  ┌──────────────────────────────────────────────────────┐ │  │
│  │  │  Phase 1: Knowledge Directory Ingest    ✅ Complete │ │  │
│  │  │  Phase 2: Knowledge Sync                  ✅ Complete │ │  │
│  │  │  ...                                              │ │  │
│  │  │  Phase 12: Prospective Memory             🔄 In Progress│ │
│  │  └──────────────────────────────────────────────────────┘ │  │
│  │                                                           │  │
│  │  [📄 View Full Plan] [📊 Metrics] [🗓️ Estimate]          │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

- Version tree with visual status (✅ completed, 🔄 in progress, 🔲 planned)
- Current version focus with phase-level breakdown
- Progress bar with percentage
- Click version card → open detailed plan document
- "View Full Plan" → opens `.agents/plans/` in Code mode or browser

### 3. 📚 Knowledge Base

Project documentation explorer:

```
📚 Knowledge Base
┌──────────────────────────────────────────────────────────────────┐
│  🔍 Search documentation, plans, ADRs...                        │
│                                                                  │
│  Categories:                                                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  📐 Architecture         ├─ Overview                      │  │
│  │                          ├─ Data Flow                     │  │
│  │                          └─ Security Model                │  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │  📖 Guides               ├─ Governance                    │  │
│  │                          ├─ API Reference                 │  │
│  │                          └─ Database Schema               │  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │  📝 Decisions (ADRs)      ├─ ADR-001: FastAPI Migration   │  │
│  │                          ├─ ADR-002: Vector DB Selection  │  │
│  │                          └─ ADR-003: Auth Architecture    │  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │  🗺️ Plans                ├─ Implementation Steps         │  │
│  │                          ├─ Version Roadmap              │  │
│  │                          └─ Active Phase Plans           │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  Recently viewed: [Architecture Overview] [ADR-002]             │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

- Browse by category: Architecture, Guides, ADRs, Plans
- Search across all documentation
- Recently viewed list for quick access
- Click → open document in reader (or in Code mode for editing)

### 4. 📝 Scratchpad

Quick temporary notes:

```
📝 Scratchpad
┌──────────────────────────────────────────────────────────────┐
│  ┌────────────────────────────────────────────────────────┐  │
│  │                                                         │  │
│  │  Notes persist across mode switches, clear on session  │  │
│  │  end or manually.                                      │  │
│  │                                                         │  │
│  │  # Ideas for Utility Mode features                     │  │
│  │  - Add a color picker                                  │  │
│  │  - Terminal calculator                                 │  │
│  │  - File format converter                               │  │
│  │                                                         │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                               │
│  Line 4 · 68 words     [📋 Copy All] [🗑 Clear] [💾 Save to File] │
└──────────────────────────────────────────────────────────────┘
```

- Simple textarea, auto-saves to session storage
- No formatting toolbar (just plain text / markdown)
- "Clear" has undo prompt (`Undo? [↻]`)
- "Save to File" → opens save dialog
- Character/word count in bottom bar

### 5. ⚡ Quick Actions

Customizable shortcuts for frequent operations:

```
⚡ Quick Actions
┌──────────────────────────────────────────────────────────────┐
│                                                               │
│  Predefined Actions                                           │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  🏗️ Run Diagnostics     → Full system health check    │  │
│  │  🗑️ Clear Cache          → Delete temp files           │  │
│  │  📤 Export Memory        → Export all memory to JSON   │  │
│  │  🔄 Resync All           → Full memory re-index        │  │
│  │  📊 Health Report        → Generate health summary     │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                               │
│  Custom Actions                                               │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  [⚡ New Action]                                        │  │
│  │                                                         │  │
│  │  Name: [______]                                        │  │
│  │  Command: [______]                                     │  │
│  │  Icon: [⚡ ▼]                                          │  │
│  │  [Save]                                                │  │
│  │                                                         │  │
│  │  Your custom actions appear here as clickable cards    │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

- **Predefined:** Run Diagnostics, Clear Cache, Export Memory, Resync All, Health Report — each runs a backend command and shows result in status area
- **Custom:** User creates own actions (name + command/API call chain)
- Click action → runs with brief loading state + result notification
- Actions can be reordered via drag handle

### Empty State

```
🛠️ Welcome to Utility
Your personal toolbox. Explore tools, roadmap, and project knowledge.
Try: /toolbox format some JSON, /roadmap see what's planned
```

**Reality:** 🟢 Frontend-only. All Utility tools (JSON formatter, Base64, Regex, UUID, Timestamp, Hash, URL tool, Markdown preview, Diff viewer) run in-browser via JavaScript — no backend calls. Roadmap reads plan files from `.agents/plans/` directory. Knowledge base reads docs/ files. Scratchpad uses browser `sessionStorage`. Quick actions trigger backend commands (diagnostics, cache clear, memory export).

---

## ⚙️ Settings Mode

**Reality:** 🟡 Partially built.
- ✅ Config model (`core/config.py`) defines all settings schemas
- ✅ Settings endpoints at `/api/v1/privacy/settings` for user-facing settings
- ✅ Security settings (token expiry, CSRF, HTTPS redirect) all configured in core config
- 🟡 **Service controls** (start/stop Qdrant, Redis) — Docker/systemd managed, not API-controlled. Show status only.
- 🔴 **AI Model settings** (GPU layers, batch size) — config values exist but no dynamic update. Requires restart.
- 🟢 **Rate limits** — middleware reads from config file, not real-time configurable via UI
- 🟢 **Storage paths** — configured via `.env`, not dynamically changeable at runtime

**Frontend must:**
- Show service status (🟢/🟡/🔴) read-only — start/stop buttons disabled, tooltip "Managed by systemd/Docker"
- Settings form sends updates to backend settings API
- "🔄 Restart Required" badge on AI Model and Storage settings
- Rate Limits panel reads from health endpoint — display-only, no edit

App configuration with sidebar categories.

### Layout

```
┌──────────────────────────────────────────────────────────────────┐
│  ← Hub     ⚙️ Settings                                   ⋮    │
├────── sidebar ──────────┬────────── panel ─────────────────────┤
│                         │                                        │
│  ├─ ⚡ General         │  [Panel content changes per category] │
│  ├─ 🧠 AI Model        │                                        │
│  ├─ 💾 Storage         │                                        │
│  ├─ 🔌 Services        │                                        │
│  ├─ 🔒 Security        │                                        │
│  ├─ ⚡ Rate Limits     │                                        │
│  └─ ℹ️ About          │                                        │
│                         │                                        │
│ 🚪 [Sign Out]          │                                        │
└─────────────────────────────────────────────────────────────────┘
```

Active sidebar item: red underline accent.

### Panels

**General:** App name, theme, language, startup behavior.

**AI Model:** Provider selection (Ollama/llama.cpp), active model, generation settings (context size, max tokens, temperature, batch), hardware (GPU layers, CPU threads, mmap, concurrency), llama.cpp model path.

**Storage:** Path configuration (Cortex root, memory, vault) with native folder picker. Usage breakdown (memory index, vault, models).

**Services:** Qdrant (host, port, gRPC toggle, connection status), Redis (URL, status), PostgreSQL (masked URL, status). Each has test connection button.

**Security:** Token expiry, refresh rotation, secret key (masked), HTTPS redirect toggle + port. Vault auto-lock timer, lock-on-mode-switch toggle, shred-on-delete toggle.

**Rate Limits:** Enabled toggle, requests per window, window seconds. Current usage display.

**About:** Version, build hash, tech stack, host info. Live console logs with level filter. Diagnostics button.

### Design Notes

- Each panel scrolls independently — sidebar stays fixed.
- Changed but unsaved fields show yellow dot.
- Inputs requiring restart show `🔄 Restart Required` badge.
- Database URLs show password as `***` — never in plain text.

**Reality:** 🟡 Partially built.
- ✅ System metrics at `GET /api/v1/system/metrics` (CPU%, RAM, disk, uptime)
- ✅ System logs at `GET /api/v1/system/logs` (level-filtered, paginated)
- ✅ LLM health at `GET /api/v1/system/llm/health` (model status, TPS, latency)
- ✅ Health endpoint at `GET /api/v1/system/health`
- ✅ WebSocket system at `/ws/system` (live metrics streaming)
- 🟡 **GPU monitoring** — depends on nvidia-smi availability. Frontend must detect GPU presence and show "No GPU detected" when absent.
- 🟡 **Process list** — available via ps/system APIs but not exposed via dedicated endpoint. Can be added to metrics endpoint.
- 🟡 **Storage mount points** — available via OS-level calls but not exposed via dedicated endpoint.
- 🟡 **Network interfaces/ports** — available via OS-level calls but not exposed via dedicated endpoint.
- 🔴 **Service controls** (restart backend/PostgreSQL) — Docker/systemd managed, not API-controlled.

**Frontend must:**
- Poll `GET /api/v1/system/metrics` every 5s for CPU/RAM/storage data
- Poll `GET /api/v1/system/llm/health` every 30s for LLM status
- Subscribe to `/ws/system` for live metrics stream (lower latency than polling)
- GPU section = conditional render: if nvidia-smi data present in metrics, show it; otherwise show "No dedicated GPU detected"
- Service cards = read-only status (🟢/🟡/🔴), no start/stop buttons
- Live Logs = stream via `/ws/system` or poll `GET /api/v1/system/logs` with level filter
- Processes = data from metrics endpoint's top_processes field

## 🖥️ Systems Mode

Live hardware monitor, service status, process viewer, log viewer.

### Layout

```
┌────────────────────────────────────────────────────────────────────────────┐
│  ← Hub     🖥️ Systems                                              ⋮    │
├────── sidebar ────────┬───────────── main panel ──────────────────────────┤
│                       │                                                     │
│  ├─ 📊 Overview      │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────┐ │
│  ├─ 🖥️ CPU          │  │ 🖥️ CPU  │ │ 🎮 GPU   │ │ 💾 RAM   │ │ 💿 Disk│ │
│  ├─ 🎮 GPU          │  │ ▓▓▓ 45% │ │ ▓▓ 32%   │ │ ▓▓▓ 62%  │ │ ▓▓38% │ │
│  ├─ 💾 RAM           │  │ 45°C     │ │ 62°C 6GB  │ │ 6.2/16GB │ │ 78/120│ │
│  ├─ 💿 Storage       │  └──────────┘ └──────────┘ └──────────┘ └───────┘ │
│  ├─ 🌐 Network       │                                                    │
│  ├─ 🧠 Services      │  ┌──────────┐ ┌───────────────────────────┐      │
│  ├─ 📋 Processes     │  │ 🧠 LLM  │ │ 📋 Recent Events          │      │
│  └─ 📜 Live Logs     │  │ 42 tps   │ │ 14:32 Vault unlocked     │      │
│                      │  └──────────┘ │ 14:30 Login from 192.168 │      │
│  Status bar:          │               └───────────────────────────┘      │
│  🟢 All systems       │                                                    │
│  Uptime: 2h 14m      │  [🏗️ Run Diagnostics] [📋 Export Report]        │
└────────────────────────────────────────────────────────────────────────────┘
```

### Sidebar Categories

| Tab | Content |
|-----|---------|
| 📊 Overview | Dashboard — mini cards + services + events |
| 🖥️ CPU | Per-core usage, temp, frequency, top processes |
| 🎮 GPU | Model, VRAM, utilization, temp, GPU processes |
| 💾 RAM | Used/total, swap, top RAM consumers |
| 💿 Storage | Mount points, Cortex paths breakdown |
| 🌐 Network | Interfaces, ports, active connections |
| 🧠 Services | Detailed service status + controls |
| 📋 Processes | Filterable process list with Cortex/system filters |
| 📜 Live Logs | Real-time Cortex log viewer with level filter |

### Overview

4 real-time mini cards (CPU, GPU, RAM, Disk) with sparkline bars, temp, and usage numbers. Service health strip. Recent events feed.

### CPU Detail

Per-core utilization as horizontal bars. Top CPU-consuming processes with PID, name, CPU%, RAM%, command.

### GPU Detail

Model name, driver version, utilization bar, VRAM bar, temperature, fan speed, power draw. GPU processes list. If no GPU: "No dedicated GPU detected — running on CPU."

### Storage

Mount points table. Cortex paths breakdown (index, vault, models, logs). Clear temp button.

### Network

Interfaces (name, IP, RX/TX, status). Ports in use (port, service, PID, status).

### Services

Service table (status, uptime, version). Click → detail panel with host, config, connection latency, actions (restart, configure, view logs).

### Processes

Filterable table. Filter chips: [All] [🧠 Cortex] [🖥️ System] [🌐 Network]. Auto-refresh.

### Live Logs

Real-time streaming. Level filter: 🔴 Error / 🟡 Warn / 🔵 Info / ⚪ Debug. Pause, copy all, search filter. Auto-scrolls to bottom.

### Auto-Refresh Intervals

| Panel | Interval |
|-------|----------|
| Overview | 5s |
| CPU | 5s |
| GPU | 5s |
| RAM | 5s |
| Storage | 30s |
| Network | 15s |
| Services | 30s |
| Processes | 5s |
| Logs | Real-time stream |

Each has toggle in top-right. Overview respects individual panel settings.

### Unavailable States

```
⚠️ No dedicated GPU detected. Running on CPU only.
🔴 Ollama not responding. LLM features unavailable.
⚠️ No active model. Go to ModelBook to download one.
```

**Reality:** 🟡 Partially built.
- ✅ Profile endpoints at `/api/v1/interaction/profile` (get/update user info)
- ✅ Auth system at `auth/` router (login, register, me, sessions)
- ✅ User management at `/api/v1/interaction/users` (admin: list, search, edit, disable, create)
- ✅ Notification preferences at `/api/v1/interaction/notifications`
- 🟡 **Vault settings** — password change, auto-lock timer exist in vault API
- 🟡 **Integrations** — GitHub token exists in profile, test connection available
- 🔴 **Activity log** — audit log exists at `/api/v1/privacy/audit` but user-facing activity feed not built
- 🔴 **Admin audit log** — `/api/v1/privacy/audit` exists, frontend panel needed
- 🟡 **Sessions** — auth system tracks sessions, `/auth/sessions` endpoint available

**Frontend must:**
- Profile form → `GET/PUT /api/v1/interaction/profile`
- Sessions → `GET /api/v1/auth/sessions` with kill buttons
- Activity → read from `/api/v1/privacy/audit` (admin) or `/api/v1/memory/episodic` for user history
- Admin sections hidden behind `user.is_admin` flag from `/auth/me` response
- Integrations → GitHub: `GET/PUT /api/v1/interaction/profile` (includes github token fields)

## 👤 Profile Mode

User profile, vault settings, integrations, sessions, activity. Admin users see additional management panels.

### Layout

```
┌──────────────────────────────────────────────────────────────────────┐
│  ← Hub     👤 Profile                                        ⋮    │
├──────── sidebar ──────────┬────────── panel ───────────────────────┤
│                           │                                          │
│  👤 adi                   │  [Panel content changes per category]  │
│  🟢 Online                │                                          │
│  ──────────────────────   │                                          │
│  ├─ 👤 Profile           │                                          │
│  ├─ 🔐 Vault Settings   │                                          │
│  ├─ 🔑 Integrations     │                                          │
│  ├─ 📋 Sessions          │                                          │
│  └─ 📜 Activity          │                                          │
│                           │                                          │
│  ═══ Admin ═══           │  (admin-only sections hidden from users) │
│  ├─ 👥 User Management   │                                          │
│  ├─ 📊 System Monitor    │                                          │
│  └─ 📋 Audit Log         │                                          │
│                           │                                          │
│ 🚪 [Sign Out]            │                                          │
└──────────────────────────────────────────────────────────────────────┘
```

### User Panels

**Profile:** Avatar (change photo), name, nickname, bio (textarea), storage path (with folder picker). Save/discard buttons.

**Vault Settings:** Change password (current + new + confirm). Vault location path. Auto-lock timer, lock-on-mode-switch, shred-on-delete toggles.

**Integrations:** GitHub (username + token, test connection, disconnect). LLM provider (provider dropdown, URL, connection status).

**Sessions:** Current session info (OS, browser, IP, login time). Other active sessions with kill button. "Sign Out All Other Devices" action.

**Activity:** Chronological feed of user actions (chats, searches, vault unlocks, model downloads, settings changes). Date-grouped.

### Admin Sections (visible only if `is_admin`)

**User Management:** User table with status, storage, created date. Search, edit, disable, delete. Create new user form (username, password, admin toggle, storage path).

**System Monitor:** Service control panel (backend, PostgreSQL, Qdrant, Redis, Ollama) with restart buttons. CPU/RAM/Disk gauges. Run diagnostics, export health report.

**Audit Log:** Filterable event log (time, user, event). Filter chips: [All] [Login] [Vault] [Downloads] [Admin] [Errors]. Export CSV. Auto-refresh toggle.

### Non-Admin Users

See only: Profile, Vault Settings, Integrations, Sessions, Activity. No divider, no admin section.

---

## Command Bar Reference

| Command | Behavior |
|---------|----------|
| `chat` | Opens Chat mode |
| `search` | Opens Search mode |
| `brain` / `memory` | Opens Brain mode |
| `vault` | Opens Vault mode |
| `models` / `modelbook` | Opens ModelBook |
| `code` | Opens Code mode |
| `utility` / `toolbox` | Opens Utility mode |
| `settings` | Opens Settings mode |
| `system` | Opens Systems mode |
| `profile` | Opens Profile mode |
| `hub` | Return to hub |

### Chat

| Command | Behavior |
|---------|----------|
| `/remember` | Save last message to memory |
| `/clear` | Clear current conversation |
| `/model X` | Switch active model |

### Search

| Command | Behavior |
|---------|----------|
| `/web query` | Web search |
| `/chat query` | Search chat history |
| `/code query` | Search code symbols |
| `/files query` | Search file contents |
| `/vault query` | Search vault filenames |

### Brain

| Command | Behavior |
|---------|----------|
| `memory recent N` | Show N recent memories |
| `memory sync` | Trigger sync now |

### Vault

| Command | Behavior |
|---------|----------|
| `/lock` | Lock vault immediately |
| `/unlock` | Show lock screen |
| `/encrypt path` | Encrypt a file |
| `/decrypt name` | Decrypt a file |
| `/shred name` | Secure delete |
| `/import path` | Import file(s) |
| `/export name path` | Export decrypted copy |

### ModelBook

| Command | Behavior |
|---------|----------|
| `/download name` | Download model |
| `/delete name` | Delete installed model |
| `/compare a b` | Compare two models |
| `/installed` | Show installed tab |
| `/model info name` | Show model details |
| `/set-active name` | Set active model |
| `/update all` | Check all for updates |

### Code

| Command | Behavior |
|---------|----------|
| `/fix` | Fix current file diagnostics |
| `/explain X` | Explain symbol/function X |
| `/refactor X to Y` | Refactor symbol |
| `/review` | Code review current file/diff |
| `/test` | Generate tests for function |
| `/doc` | Generate docstrings |
| `/rename X to Y` | Rename symbol |
| `/find-refs X` | Find all references to X |
| `/go-to-def X` | Go to definition |
| `/format` | Format file |
| `/open path` | Open specific file |
| `/terminal` | Open terminal panel |
| `/skill new` | Create new skill |
| `/skill list` | List all installed skills |
| `/skill toggle name` | Enable/disable skill |
| `/skill edit name` | Edit skill code |
| `/skill import` | Import skill from file |
| `/hook list` | List all hooks |
| `/hook add type cmd` | Add new hook |
| `/hook toggle name` | Enable/disable hook |
| `/mcp list` | List MCP servers |
| `/mcp add name cmd` | Add MCP server |
| `/mcp test name` | Test MCP connection |
| `/mcp logs name` | View MCP server logs |

### Utility

| Command | Behavior |
|---------|----------|
| `utility toolbox` | Open toolbox |
| `utility roadmap` | Open roadmap |
| `utility knowledge` | Open knowledge base |
| `utility scratchpad` | Open scratchpad |
| `utility actions` | Open quick actions |
| `/format json` | Format JSON in clipboard |
| `/encode base64 text` | Base64 encode text |
| `/decode base64 text` | Base64 decode text |
| `/hash text` | Generate hash of text |
| `/uuid` | Generate UUID |
| `/timestamp value` | Convert timestamp |

### Settings

| Command | Behavior |
|---------|----------|
| `settings general` | General settings |
| `settings ai` | AI model settings |
| `settings storage` | Storage settings |
| `settings security` | Security settings |
| `health check` | Run system diagnostics |

### Systems

| Command | Behavior |
|---------|----------|
| `system cpu` | CPU details |
| `system gpu` | GPU details |
| `system memory` | RAM details |
| `system storage` | Storage details |
| `system network` | Network details |
| `system services` | Service status |
| `system processes` | Process list |
| `system logs` | Live logs |

### Profile

| Command | Behavior |
|---------|----------|
| `profile` | Open profile |
| `vault settings` | Vault config |
| `sessions` | Active sessions |
| `sign out` | Sign out |
| `admin users` | User management (admin) |
| `admin audit` | Audit log (admin) |

---

## Transitions

| Transition | Animation | Duration |
|-----------|-----------|----------|
| Hub → Mode | Widget zooms, content fades in | 250ms |
| Mode → Hub | Content fades out, grid fades in | 200ms |
| Mode → Mode | Quick crossfade | 150ms |
| Command bar open | Slide up + blur backdrop | 150ms |
| Command bar close | Slide down + unblur | 100ms |
| Widget data update | Opacity pulse on changed section | 500ms |
| Dock auto-hide | Slide down 16px + fade | 300ms |
| Dock appear | Slide up + fade | 150ms |
| Conversation list slide | Slide right from left | 200ms |
| New message appear | Fade + slide up | 150ms |
| Input expand (multi-line) | Height transition | 100ms |
| Context ribbon collapse | Fade out | 300ms |
| Error shake | Horizontal shake | 400ms |
| Mode zoom (from widget) | Widget scales up, content fills | 250ms |
| Panel slide | Panel slides from edge | 200ms |

---

## Notes

- This is the **source of truth** for redesign decisions.
- Every future UI discussion updates this document.
- Implement in phases: Auth → Layout → Each feature page.
- Dark-only. No light mode.
- Font: Geist (UI), Geist Mono (code).
- Glass-morphism: `backdrop-filter: blur(12px)` on overlays/modals, `backdrop-filter: blur(16px)` on hub widgets.
- No sidebar exists anywhere. All navigation is command bar + floating dock.
