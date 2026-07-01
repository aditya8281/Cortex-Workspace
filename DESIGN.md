---
name: CORTEX
description: "Local-first machine intelligence layer — calm, spatial, persistent, always aware."
colors:
  primary: "#00acc1"
  primary-hover: "#26c6da"
  primary-muted: "rgba(0,172,193,0.18)"
  primary-faint: "rgba(0,172,193,0.08)"
  accent-red: "#d32f2f"
  accent-red-bright: "#e53935"
  accent-red-muted: "rgba(211,47,47,0.20)"
  accent-red-faint: "rgba(211,47,47,0.08)"
  accent-cyan: "#00acc1"
  accent-cyan-bright: "#26c6da"
  accent-cyan-muted: "rgba(0,172,193,0.18)"
  accent-cyan-faint: "rgba(0,172,193,0.08)"
  void: "#0d0d0d"
  bg-base: "#0d0d0d"
  bg-elevated: "#1c1c1c"
  bg-surface: "#2a2a2a"
  bg-hover: "#363636"
  bg-glass: "rgba(26,26,26,0.85)"
  bg-widget: "rgba(26,26,26,0.75)"
  text-primary: "#f0f0f0"
  text-secondary: "#a0a0a0"
  text-muted: "#7a7a7a"
  text-inverse: "#0d0d0d"
  border-subtle: "rgba(255,255,255,0.06)"
  border-default: "rgba(255,255,255,0.12)"
  border-accent: "rgba(0,172,193,0.30)"
  border-red: "rgba(211,47,47,0.35)"
  border-cyan: "rgba(0,172,193,0.35)"
  border-input-focus: "rgba(211,47,47,0.40)"
  danger: "#e74c3c"
  success: "#2ecc71"
  warning: "#f39c12"
typography:
  display:
    fontFamily: "Geist, system-ui, sans-serif"
    fontSize: "clamp(1.75rem, 3vw, 2.25rem)"
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: "-0.02em"
  headline:
    fontFamily: "Geist, system-ui, sans-serif"
    fontSize: "1.25rem"
    fontWeight: 600
    lineHeight: 1.4
  title:
    fontFamily: "Geist, system-ui, sans-serif"
    fontSize: "0.9375rem"
    fontWeight: 500
    lineHeight: 1.4
  body:
    fontFamily: "Geist, system-ui, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 400
    lineHeight: 1.6
  caption:
    fontFamily: "Geist, system-ui, sans-serif"
    fontSize: "0.75rem"
    lineHeight: 1.4
  label:
    fontFamily: "Geist, system-ui, sans-serif"
    fontSize: "0.625rem"
    fontWeight: 600
    lineHeight: 1.4
    letterSpacing: "0.1em"
  mono:
    fontFamily: "'JetBrains Mono', monospace"
    fontSize: "0.8125rem"
    fontWeight: 400
    lineHeight: 1.5
rounded:
  sm: "6px"
  md: "10px"
  lg: "16px"
  xl: "24px"
  full: "9999px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "24px"
  xl: "32px"
  "2xl": "48px"
zIndex:
  base: "0"
  dock: "50"
  commandbar: "80"
  dropdown: "100"
  sticky: "200"
  modal-backdrop: "300"
  modal: "400"
  toast: "500"
  tooltip: "600"
components:
  button-primary:
    backgroundColor: "{colors.accent-red}"
    textColor: "#ffffff"
    rounded: "{rounded.md}"
    padding: "8px 16px"
  button-primary-hover:
    backgroundColor: "{colors.accent-red-bright}"
  button-ghost:
    backgroundColor: "transparent"
    textColor: "{colors.text-secondary}"
    rounded: "{rounded.md}"
    padding: "8px 16px"
  button-ghost-hover:
    backgroundColor: "{colors.bg-surface}"
    textColor: "{colors.text-primary}"
  card:
    backgroundColor: "{colors.bg-elevated}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.lg}"
    padding: "{spacing.md}"
  card-glass:
    backgroundColor: "{colors.bg-widget}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.lg}"
    padding: "{spacing.md}"
  input:
    backgroundColor: "{colors.bg-surface}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.md}"
    padding: "8px 12px"
  nav-item:
    backgroundColor: "transparent"
    textColor: "{colors.text-secondary}"
    rounded: "{rounded.md}"
    padding: "8px 12px"
  nav-item-active:
    backgroundColor: "{colors.accent-red-muted}"
    textColor: "{colors.accent-red}"
  badge:
    backgroundColor: "rgba(14,165,201,0.12)"
    textColor: "{colors.primary}"
    rounded: "{rounded.full}"
    padding: "2px 8px"
  dock-item:
    backgroundColor: "transparent"
    textColor: "{colors.text-secondary}"
    rounded: "{rounded.md}"
    size: "40px"
  dock-item-hover:
    backgroundColor: "{colors.accent-red-muted}"
    textColor: "{colors.text-primary}"
  dock-item-active:
    backgroundColor: "{colors.accent-red-muted}"
    textColor: "{colors.accent-red}"
---

# Design System: CORTEX

> Auto-generated from live code by `/impeccable document`.

## 1. Overview

**Creative North Star: "The Calm Machine"**

CORTEX is not an application you open — it is a layer of intelligence that lives on your machine. The design reflects a machine that breathes: industrial precision meets warm humanity. Spatial, persistent, always aware. Every screen reveals what CORTEX knows, not what CORTEX can do.

The interface is dark-only, warm, and restrained. It rejects the anxiety of notification-heavy dashboards, the flatness of generic chat UIs, and the spectacle of AI magic aesthetics. Depth is conveyed through tonal layering — surfaces rise from a warm void through progressively lighter grays, never through decorative shadows or translucent panels. The dual-accent system (silk red + cyan) is used sparingly: ≤10% of any surface.

**Key Characteristics:**
- Dark-only warm canvas with dual-accent system: silk red for actions + alertness, cyan for AI + data
- Restrained palette: accent on ≤10% of any surface
- Geist font: one family carries everything, tight hierarchy
- Spatial depth via tonal layering, not heavy shadows
- Motion that conveys state, never decoration. GSAP for JS-driven animations, CSS transitions for simple state changes
- Every animation respects `prefers-reduced-motion`
- Glassmorphism used selectively only in the Neural Hub redesign (dock, hub widgets, auth cards, command bar)
- Floating glass dock (auto-hide), command palette (⌘K), radial system ribbon at top

## 2. Colors: The Warm Void Palette

A restrained warm-dark palette built around a dual-accent system: **silk red** for actions, alerts, and emotion; **cyan** for AI, neural activity, and data. The neutral scale progresses from deep void through elevated surfaces, each step slightly warmer than true gray to maintain approachability.

### Silk Red Accent

- **Red** (`#d32f2f`): Primary accent for buttons, active dock items, emphasis. 4.2:1 contrast on bg-base — passes for large text and UI components.
- **Red Bright** (`#e53935`): Hover state for red elements, pulse animation, glowing indicators. 5.4:1 on bg-base.
- **Red Muted** (`rgba(211,47,47,0.20)`): Background tint for active states (dock items, command bar selection), badge fills.
- **Red Faint** (`rgba(211,47,47,0.08)`): Subtle background tint for hover states, ghost buttons.

### Cyan Neural Accent

- **Cyan** (`#00acc1`): Neural accent — data visualization, AI status, focus rings. 7.6:1 contrast on bg-base.
- **Cyan Bright** (`#26c6da`): Hover state for cyan elements, bright glow, active AI indicators. 10.3:1 on bg-base.
- **Cyan Muted** (`rgba(0,172,193,0.18)`): Subtle neural aura, background tint for AI-related surfaces.
- **Cyan Faint** (`rgba(0,172,193,0.08)`): Very subtle background tint for passive AI surfaces.

### Accent Usage Rules

| Context | Use | Reason |
|---------|-----|--------|
| Buttons (primary) | Silk red | Action requires emphasis |
| Navigation (active) | Silk red | Current focus indicator |
| Focus rings | Silk red variant | Consistent with action accent |
| Dock (active item) | Silk red bg + text | Current mode indicator |
| Command bar (selected) | Red muted bg | Active option highlight |
| Data viz / AI status | Cyan | Information, not action |
| Neural particles | Cyan | AI ambiance |
| Processing indicators | Cyan | Data flow, not user action |
| Profile avatar | Red muted bg | User identity marker |

### Neutral

- **Void / bg-base** (`#0d0d0d`): The deepest layer. Page background, the canvas everything sits on. Warm near-black with amber tint, never pure `#000000`.
- **Elevated** (`#1c1c1c`): Cards, panels, modals. One step above void — enough contrast to separate content.
- **Surface** (`#2a2a2a`): Interactive surfaces — input fields, dropdown backgrounds, active hover zones.
- **Hover** (`#363636`): Hover state background for nav items, buttons, list rows.
- **Glass** (`rgba(26,26,26,0.85)`): Glass-morphism overlays (dock, command bar). Backdrop-blur(16px) + backdrop-blur-2xl. Used only in Neural Hub redesign.
- **Widget** (`rgba(26,26,26,0.75)`): Hub widget cards (glass style). Backdrop-blur(16px). Used only in Neural Hub redesign.

### Borders

- **Subtle** (`rgba(255,255,255,0.06)`): Hairline borders on cards, dividers, separators. Barely visible.
- **Default** (`rgba(255,255,255,0.12)`): Standard borders on inputs, interactive elements, dock container.
- **Accent** (`rgba(0,172,193,0.30)`): Cyan accent border for AI-active states.
- **Red** (`rgba(211,47,47,0.35)`): Silk red border for focus, active, error-associated elements.
- **Cyan** (`rgba(0,172,193,0.35)`): Cyan border for AI-active states, data-focused elements.
- **Input Focus** (`rgba(211,47,47,0.40)`): Input focus ring color. 2px outline at 40% opacity — meets 3:1 contrast for focus indicators (WCAG 2.2).

### Text

- **Primary** (`#f0f0f0`): Body text, headings, labels. 17.8:1 against bg-base. High contrast.
- **Secondary** (`#a0a0a0`): Supporting text, descriptions, nav labels. 7.7:1 against bg-base.
- **Muted** (`#7a7a7a`): Placeholders, disabled states, hints. **4.5:1 against bg-base** — verified minimum. Do not darken.
- **Inverse** (`#0d0d0d`): Text on colored backgrounds (buttons, badges).

### Semantic

- **Danger** (`#e74c3c`): Destructive actions, error states, critical alerts.
- **Success** (`#2ecc71`): Positive confirmations, healthy status, completed states.
- **Warning** (`#f39c12`): Caution indicators, pending states, non-critical alerts.

### Shadow Vocabulary (Accent-Glow)

- **Subtle** (`0 1px 2px rgba(0,0,0,0.4)`): Cards at rest, minimal separation.
- **Card** (`0 2px 8px rgba(0,0,0,0.4), 0 0 0 1px rgba(255,255,255,0.04)`): Elevated cards, panels. Faint border-rim creates materiality.
- **Elevated** (`0 4px 16px rgba(0,0,0,0.5), 0 0 0 1px rgba(255,255,255,0.05)`): Dropdowns, popovers, floating elements.
- **Modal** (`0 8px 32px rgba(0,0,0,0.6), 0 0 0 1px rgba(255,255,255,0.05)`): Modal dialogs, overlays.
- **Red Glow** (`0 0 24px rgba(211,47,47,0.18)`): Silk red glow — buttons, active dock items, hero elements.
- **Cyan Glow** (`0 0 24px rgba(0,172,193,0.14)`): Cyan glow — AI activity, neural data visualization.
- **Red Strong** (`0 0 40px rgba(211,47,47,0.25)`): Hero moments, critical alerts, pulsing animation.
- **Cyan Strong** (`0 0 40px rgba(0,172,193,0.20)`): Active AI processing, data flow animation.

### Named Rules

**The 10% Rule.** The accent color appears on ≤10% of any given screen. Its rarity is the point. Reserve accents for: primary actions, current navigation state, focus indicators, and status signals.

**The Never-Pure-Black Rule.** The deepest color is `#0d0d0d` — warm near-black with amber tint. Pure `#000000` creates a hole, not a surface. The void must feel like material, not absence.

**The Red-Cyan Separation Rule.** Red is for actions, alerts, and active selection. Cyan is for AI activity, data visualization, and information. Never use red for a passive information display. Never use cyan for a primary action button. When both appear on the same screen, the ratio must be visibly skewed toward one — a 50/50 split creates visual noise.

## 3. Typography

**Primary Font:** Geist (with system-ui fallback)
**Mono Font:** JetBrains Mono (with monospace fallback)

**Hierarchy uses fixed rem scale** (not fluid clamp beyond display). Tight ratio at ~1.2 between steps. Product register: users view at consistent DPI, no benefit from fluid scaling on body text.

### Hierarchy

- **Display** (600, `clamp(1.75rem, 3vw, 2.25rem)`, 1.2): Page titles, hero headings. Used once per page max. Tight letter-spacing (`-0.02em`) for weight without bulk.
- **Headline** (600, `1.25rem`, 1.4): Section headings, card titles. Clear hierarchy break from body.
- **Title** (500, `0.9375rem`, 1.4): Subsection headings, nav items, prominent labels. The workhorse heading size.
- **Body** (400, `0.875rem`, 1.6): Paragraphs, descriptions, content text. Capped at 65–75ch line length for readability.
- **Caption** (400, `0.75rem`, 1.4): Smaller body text, secondary descriptions.
- **Label** (600, `0.625rem`, 1.4, `letter-spacing: 0.1em`): Uppercase micro-labels, metadata, status indicators. Used sparingly — one per section maximum.
- **Mono** (400, `0.8125rem`, 1.5): Code blocks, data values, timestamps, file paths, version badges, system status text in NeuralRibbon.

### Named Rules

**The One Family Rule.** Geist carries everything. No serif, no display, no decorative fonts. The only exception is JetBrains Mono for code and data.

**The Label Restraint Rule.** Uppercase micro-labels (`0.625rem`, `letter-spacing: 0.1em`) appear once per section maximum. Two labels stacked above a heading is visual noise.

**The Fixed Scale Rule.** Product UIs use fixed rem values (not fluid clamp) for body, headline, title, caption, label, mono. Only display uses clamp. Users view at consistent DPI; fluid body text reduces control without benefit.

## 4. Elevation

CORTEX uses a hybrid model: **tonal layering** at rest (surfaces rise from void through progressively lighter grays), **structural shadows** for floating elements (dropdowns, modals, tooltips), and **accent glow shadows** for state indicators (active, focus, AI processing). Glass elements (dock, widgets, command bar) layer on top via backdrop-blur — the glass effect creates its own elevation through material simulation.

The default state is flat. Shadows appear only on interaction or to separate floating elements from content.

### Shadow Vocabulary

- **Subtle** (`0 1px 2px rgba(0,0,0,0.4)`): Cards at rest, minimal separation.
- **Card** (`0 2px 8px rgba(0,0,0,0.4), 0 0 0 1px rgba(255,255,255,0.04)`): Elevated cards, panels. Faint border-rim creates materiality.
- **Elevated** (`0 4px 16px rgba(0,0,0,0.5), 0 0 0 1px rgba(255,255,255,0.05)`): Dropdowns, popovers, command bar. Deepest shadow for floating UI.
- **Modal** (`0 8px 32px rgba(0,0,0,0.6), 0 0 0 1px rgba(255,255,255,0.05)`): Modal dialogs, overlays.
- **Dock Shadow** (`0 8px 32px rgba(0,0,0,0.5)`): Dock container shadow — hand-written because dock uses glass bg.
- **Red Glow** (`0 0 24px rgba(211,47,47,0.18)`): Active dock items, red action buttons, pulsing indicators.
- **Cyan Glow** (`0 0 24px rgba(0,172,193,0.14)`): AI activity, hover on data-focused widgets, focus glow.
- **Red Strong** (`0 0 40px rgba(211,47,47,0.25)`): Hero moments, critical alerts.
- **Cyan Strong** (`0 0 40px rgba(0,172,193,0.20)`): Active AI processing, data flow animation.

### Named Rules

**The Flat-By-Default Rule.** Surfaces are flat at rest. Shadows appear only as a response to state (hover, elevation, focus, active).

**The Glow Restraint Rule.** Glow shadows are accent-colored and rare. One glowing element per viewport maximum. Two glowing elements simultaneously is a light show, not an interface.

## 5. Components

### Buttons

- **Shape:** Gently curved edges (10px radius), 44px minimum height.
- **Primary (Red):** Silk Red background (`#d32f2f`), white text. 150ms ease-out bg transition. Hover: Red Bright (`#e53935`) with subtle red glow. Active: scale(0.98). Focus: 2px input-focus ring. Disabled: 0.35 opacity.
- **Secondary (Ghost):** Transparent background, secondary text (`#a0a0a0`). Hover: surface background (`#2a2a2a`) with primary text. 150ms transitions.
- **State rule:** One primary button per visible area.

### Dock (Neural Hub)

- **Position:** Fixed bottom-center, z-dock (50), centered with `-translate-x-1/2`.
- **Container:** Glass background (`--bg-glass`, rgba(26,26,26,0.85)), backdrop-blur-2xl, rounded-2xl, 1px default border, shadow for elevation.
- **Items:** 10 mode buttons + 1 circular profile avatar button (separated by vertical divider).
- **Default:** 40×40px touch target, transparent bg, secondary text. Opacity starts at 0 (GSAP staggers in).
- **Hover:** Red muted background at 50%, primary text. Tooltip appears above with label + shortcut.
- **Active:** Red muted background, red text and icon, red glow pulse animation (`animate-glow-pulse-red`), small red indicator line at bottom of icon.
- **Auto-hide:** In mode view, dock slides down 8px + fades over 250ms after 3s idle. Reappears on mouse move within 60px of bottom edge. On hub page, always visible.
- **Keyboard:** ⌘1–⌘0 for all 10 modes. Fires `onModeChange` callback.
- **Entrance:** GSAP stagger from center, 0.4s duration, power3.out. Container fades in separately.
- **States:** focus-visible ring, hover scale 1.1 on icon, active mode pulse (scale 1.08 yoyo).
- **Tooltip:** Absolute positioned above icon, elevated bg, border, label + shortcut in mono.

### Command Bar (Palette)

- **Status:** Production — fuzzy search over 22 command items, keyboard navigation, group headers.
- **Position:** Fixed top-[72px] (below NeuralRibbon), centered horizontally, z-commandbar (80).
- **Container:** Glass background, backdrop-blur-2xl, rounded-2xl, max-w-lg, deep shadow.
- **Backdrop:** Fixed overlay, `bg-black/30 backdrop-blur-sm`. Click to close.
- **Input:** Full-width, transparent bg, placeholder muted text, focus-visible red ring.
- **Items:** 44px height, icon + label + description + shortcut. Hover/selected: red muted background at 40%.
- **Results:** Max 8 items shown. Empty state: "No results for 'query'" with monospace quoted text.
- **Groups:** "Navigation" (2 items: Ask, Go to Hub), optional "Context" (1 item: Close Mode), "Modes" (10 items).
- **Keyboard:** ⌘K toggle, Escape close, ArrowUp/Down navigation (wraps), Enter select, group headers.
- **Footer:** Navigation hints (↑↓ Navigate · ↵ Select · ⎋ Close).

### Hub Widgets (Glass Cards)

- **Position:** 2-column grid (`grid-cols-2`), max-w-2xl, centered.
- **Container:** Glass background (`--bg-widget`, rgba(26,26,26,0.75)), backdrop-blur-2xl, rounded-2xl, 1px subtle border.
- **Content:** Icon (20px) + uppercase label (xs, semibold, tracking-widest) + preview children (xs, muted text).
- **Hover:** Border shifts to default, -translate-y-0.5 lift, glow shadow (red or cyan based on `glowColor` prop).
- **States:** Active glow (shadow-red/shadow-cyan) when `isActive` prop set. Active indicator line at top edge (1px colored line).
- **Entrance:** GSAP stagger from grid, 0.35s, power3.out, scale 0.96→1.
- **Exit hint:** Chevron arrow (opacity 0→40% on group-hover) at bottom-right.
- **Variants:** `spanFull` prop for 2-column span (used by Brain + Systems widgets).
- **Data:** Supports `renderLive` callback for API data or `fallback` static content. Error state: "Offline" in danger/70 italic.

### NeuralRibbon (System Status Bar)

- **Position:** Fixed top, full-width, z-sticky (200). Contains a 24px-tall bar + optional expanded panel + offline banner.
- **Bar:** `bg-bg-base/80 backdrop-blur-sm`, bottom border subtle, centered.
- **Status dot:** CSS-styled `w-1.5 h-1.5 rounded-full` with semantic color (success/warning/danger). Pulse animation (`animate-pulse-dot`) for online status.
- **Status label:** Uppercase mono (ONLINE/DEGRADED/OFFLINE). Color-coded text (success/warning/danger). Click to expand services panel.
- **Metrics (conditional):** Active model name (with BrainIcon), tokens/second counter, VRAM usage. Hidden when data is unavailable.
- **Version badge:** Hardcoded `v1.0`, mono, 10px, 50% opacity.
- **Expanded panel:** `bg-bg-elevated`, rounded-xl, elevated shadow, animate-fade-in-scale. Lists per-service health status with color-coded dots.
- **Offline banner:** `bg-danger/10`, `border-b danger/20`, centered mono text: "Backend unreachable — some features unavailable".
- **TPS counter:** GSAP `interpolate()` over 30 frames for smooth animation.
- **Polling:** Fetches `/api/v1/system/health` every 30s. Fetches model catalog on mount.
- **States:** mounted ref prevents setState after unmount.

### Cards / Containers

- **Corner Style:** Gently curved (16px radius).
- **Background:** Elevated (`#1c1c1c`) — one step above the void.
- **Border:** Subtle (`rgba(255,255,255,0.06)`) — structural, not decorative.
- **Shadow Strategy:** Flat at rest. On hover: Elevated shadow with 1px upward lift (`translateY(-1px)`).
- **Glass variant:** Widget bg (`rgba(26,26,26,0.75)`) with backdrop-blur(16px). Used only in Neural Hub.
- **Internal Padding:** 16px standard.

### Inputs / Fields

- **Style:** Surface background (`#2a2a2a`), default border, 10px radius, 44px minimum height.
- **Focus:** Border shifts to input-focus (`rgba(211,47,47,0.40)`) with 2px outline at 40% opacity. 200ms ease-out transition.
- **Placeholder:** Muted text (`#7a7a7a`) — 4.5:1 contrast on bg-base. Never lighter.
- **Error:** Border shifts to danger (`#e74c3c`).
- **Disabled:** 35% opacity, pointer-events none.

### Badges / Status

- **Style:** Rounded-full pill, mono font (JetBrains Mono, `0.625rem`), uppercase, `letter-spacing: 0.1em`.
- **Semantic variants:** Success (green tint + green text), warning (amber tint + amber text), danger (red tint + red text).

### Skeleton States

- **Style:** Surface background (`#2a2a2a`) with shimmer animation (background-position slide, 2s linear infinite). Killed by `prefers-reduced-motion`.
- **Shape:** Matches the content it replaces.

### Toast Notifications

- **Position:** Bottom-right on desktop, bottom-center on mobile.
- **Style:** Elevated background, subtle border, 10px radius, z-toast.
- **Entrance:** Slide from right + opacity, 250ms ease-out.
- **Exit:** Slide out + opacity, 200ms ease-in.

### Modal Dialogs

- **Overlay:** Void at 60% opacity, fixed position, z-modal-backdrop.
- **Content:** Elevated background, 24px radius, Modal shadow.
- **Entrance:** Scale 0.95→1 + opacity, 200ms ease-out.
- **Exit:** Scale 1→0.95 + opacity, 200ms ease-in.
- **Focus trap:** Tab cycles within modal. Escape closes.

### Navigation (Dock)
Covered in Dock component section above. No legacy sidebar navigation remains.

### Surface Interactive Mixin
Utility class `.surface-interactive` provides consistent hover/press behavior:
- **Default:** Flat.
- **Hover:** `translateY(-1px)`, box-shadow elevation, border-color shift. 150ms ease-out.
- **Active:** `translateY(0)`, reduced shadow (press effect).

## 6. Motion

Motion is functional, not decorative. Every animation answers "why" — spatial consistency, state indication, feedback, or preventing a jarring change.

### Principles

- **Easing:** `cubic-bezier(0.16, 1, 0.3, 1)` (exponential out) for entrances and reveals. `cubic-bezier(0.4, 0, 1, 1)` for exits. No bounce, elastic, or spring curves.
- **Duration:** 150–250ms for state transitions (hover, focus, active). 300–400ms for entrances (staggered). 120ms for mode crossfade.
- **Reduced motion:** All animations check `prefers-reduced-motion`. GSAP animations use `gsap.matchMedia()` to wrap. CSS animations use the standard `@media` query. Neural particles use `display: none !important` under reduced motion, not just slowed.
- **GPU-only:** `transform` + `opacity` only. Never animate layout properties (`width`, `height`, `margin`, `padding`).
- **No orchestrated page-load sequences.** Product loads into a task; users don't watch it load.

### GSAP Usage

- **Hub entrance:** Timeline sequence: greeting (y: -12 → 0, 0.35s) → search bar (y: -8 → 0, 0.3s, -0.1s overlap) → widgets stagger (y: 16 → 0, scale 0.96 → 1, stagger 0.04s from start, 0.35s each).
- **Dock entrance:** Stagger items from center (y: 16, opacity: 0, scale: 0.9, 0.4s each, stagger 0.035s). Container fades in with 0.2s delay.
- **Dock auto-hide:** Show: y: 0, opacity 1, 0.3s power3.out. Hide: y: 8, opacity 0, 0.25s power2.out, then pointer-events-none.
- **Mode crossfade:** 0.05s instant fade-out → 0.12s fade-in power2.out. Fast — avoids disorienting users.
- **Active mode pulse:** scale 1 → 1.08 (yoyo, repeat: 1, 0.15s power2.out).
- **TPS counter:** `gsap.utils.interpolate()` over 30 animation frames for smooth number transitions.

### CSS Animations (Tailwind)

- `animate-fade-in`: 200ms ease-out-expo, translateY(6px).
- `animate-fade-in-scale`: 200ms ease-out-expo, scale 0.96.
- `animate-slide-in-right`: 250ms ease-out-expo, translateX(12px).
- `animate-scale-in`: 200ms ease-out-expo, scale 0.92 → 1.
- `animate-scale-out`: 120ms ease-in, scale 1 → 0.95.
- `animate-glow-pulse-red/cyan`: 2s ease-in-out infinite, box-shadow oscillates between glow and strong-glow.
- `animate-shimmer`: 2s linear infinite, background-position slide for skeleton loading.
- `animate-pulse-dot`: 1.5s ease-in-out infinite, opacity 0.4 ↔ 1.
- `animate-shake`: 0.4s ease-in-out, translateX oscillation for form validation errors.

### Keyframes

All keyframes defined in `tailwind.config.ts` and `globals.css`. Motion-safe prefix applied only where GSAP handles the animation and a CSS fallback exists. GSAP-managed animations don't need `motion-safe:` — GSAP's matchMedia handles reduced motion directly.

## 7. Do's and Don'ts

### Do:

- **Do** use Geist for everything — headings, body, labels, buttons. One family, tight hierarchy.
- **Do** keep accent at ≤10% of any surface. Reserve red for actions and active states; reserve cyan for AI activity and data.
- **Do** use tonal layering for depth — Void → Elevated → Surface → Hover. No shadows at rest.
- **Do** respect `prefers-reduced-motion` on every animation. GSAP uses `gsap.matchMedia()`. CSS uses `@media (prefers-reduced-motion: reduce)`.
- **Do** use 44px minimum touch targets on all interactive elements. Dock items use 40×40px with comfortable gap.
- **Do** show system status visibly — health indicators, vault lock state, model status via NeuralRibbon.
- **Do** use skeleton states for loading, not spinners.
- **Do** write error messages with fix instructions, not just "Something went wrong."
- **Do** use `100dvh` for viewport heights, never `100vh`.
- **Do** test contrast: body text ≥4.5:1 against its background. Muted text (`#7a7a7a`) on bg-base (`#0d0d0d`) = 4.5:1 ✓.
- **Do** use GSAP (`@gsap/react`) for JavaScript-driven animations (dock, hub entrance, mode crossfade).
- **Do** use CSS transitions for simple state changes (hover, focus, active) with motion-safe prefix.
- **Do** use `cubic-bezier(0.16, 1, 0.3, 1)` (exponential out) as the default easing for entrances and reveals.
- **Do** use `cubic-bezier(0.4, 0, 1, 1)` (standard ease-in) for exits and dismissals.
- **Do** animate only `transform` and `opacity`. Never layout properties.
- **Do** use glassmorphism selectively: dock, hub widgets, command bar — nowhere else.
- **Do** keep keyboard shortcuts discoverable: show ⌘K in the hub search bar, show ⌘ shortcuts in dock tooltips and command bar items.

### Don't:

- **Don't** use purple/blue AI gradients, sparkles, neon glows, or "AI magic" aesthetics.
- **Don't** make the homepage a conversation screen. CORTEX is not a chatbot.
- **Don't** use glassmorphism or backdrop-blur as a default — only dock, hub widgets, command bar.
- **Don't** use the neural network canvas background decoratively. If used, it must be data-driven (knowledge graph visualization).
- **Don't** use gradient text (`background-clip: text`). Use a single solid color.
- **Don't** use side-stripe borders (`border-left` > 1px as colored accent).
- **Don't** use tiny uppercase tracked eyebrows above every section. One label per section maximum.
- **Don't** use numbered section markers (01/02/03) as scaffolding.
- **Don't** use identical card grids — same-sized cards with icon + heading + text, repeated endlessly.
- **Don't** use `scale(0)` on any entrance animation. Start from `scale(0.95)` + opacity.
- **Don't** use `ease-in` on any UI interaction. Reserve ease-in for exits.
- **Don't** use `transition: all`. Specify exact properties.
- **Don't** use `100vh` for viewport heights. Use `100dvh`.
- **Don't** use pure `#000000`. The deepest color is `#0d0d0d` — warm near-black.
- **Don't** use Inter, Roboto, or any font outside Geist + JetBrains Mono.
- **Don't** use modals as first thought. Exhaust inline alternatives first.
- **Don't** add decorative motion. Every animation answers "why does this animate?"
- **Don't** use bounce, elastic, or spring animations on UI elements. No `cubic-bezier` with overshoot values (e.g., > 1 on any coordinate).
- **Don't** animate layout properties (`width`, `height`, `margin`, `padding`). GPU-only: `transform` + `opacity`.
- **Don't** use `--ease-spring` or other overshoot easings in CSS custom properties.
- **Don't** use emoji in place of SVG icons for UI elements. System status dots use CSS-styled divs, not emoji. If emoji appear inline in data displays, they need `aria-label` on the parent.
- **Don't** leave unused CSS custom properties — if an easing curve isn't used by any component, remove the variable.
- **Don't** override font size with arbitrary values (`text-[11px]`, `text-[10px]`) without a tokenized alternative. Prefer existing scale tokens (`text-xs`, `text-mono`).
- **Don't** duplicate profile navigation — the dock should have one profile entry, not two buttons.
