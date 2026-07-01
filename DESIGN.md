Last updated: 2026-07-01

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
  accent-cyan: "#00acc1"
  accent-cyan-bright: "#26c6da"
  accent-cyan-muted: "rgba(0,172,193,0.18)"
  neutral-void: "#0d0d0d"
  neutral-bg-base: "#0d0d0d"
  neutral-elevated: "#1c1c1c"
  neutral-surface: "#2a2a2a"
  neutral-hover: "#363636"
  neutral-bg-glass: "rgba(26,26,26,0.85)"
  neutral-bg-widget: "rgba(26,26,26,0.75)"
  neutral-border-subtle: "rgba(255,255,255,0.06)"
  neutral-border: "rgba(255,255,255,0.12)"
  text-primary: "#f0f0f0"
  text-secondary: "#a0a0a0"
  text-muted: "#7a7a7a"
  text-inverse: "#0d0d0d"
  border-red: "rgba(211,47,47,0.35)"
  border-cyan: "rgba(0,172,193,0.35)"
  border-input-focus: "rgba(211,47,47,0.40)"
  shadow-red: "0 0 24px rgba(211,47,47,0.18)"
  shadow-cyan: "0 0 24px rgba(0,172,193,0.14)"
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
    lineHeight: 1.3
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
  md: "8px"
  lg: "12px"
  xl: "16px"
  full: "9999px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "24px"
  xl: "32px"
  "2xl": "48px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "#ffffff"
    rounded: "{rounded.md}"
    padding: "8px 16px"
  button-primary-hover:
    backgroundColor: "{colors.primary-hover}"
  button-ghost:
    backgroundColor: "transparent"
    textColor: "{colors.text-secondary}"
    rounded: "{rounded.md}"
    padding: "8px 16px"
  button-ghost-hover:
    backgroundColor: "{colors.neutral-surface}"
    textColor: "{colors.text-primary}"
  card:
    backgroundColor: "{colors.neutral-elevated}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.lg}"
    padding: "{spacing.md}"
  input:
    backgroundColor: "{colors.neutral-surface}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.md}"
    padding: "8px 12px"
  nav-item:
    backgroundColor: "transparent"
    textColor: "{colors.text-secondary}"
    rounded: "{rounded.md}"
    padding: "8px 12px"
  nav-item-active:
    backgroundColor: "{colors.primary-faint}"
    textColor: "{colors.primary}"
  badge:
    backgroundColor: "rgba(14,165,201,0.12)"
    textColor: "{colors.primary}"
    rounded: "{rounded.full}"
    padding: "2px 8px"
---

# Design System: CORTEX

## 1. Overview

**Creative North Star: "The Calm Machine"**

CORTEX is not an application you open — it is a layer of intelligence that lives on your machine. The design reflects a machine that breathes: industrial precision meets warm humanity. Spatial, persistent, always aware. Every screen reveals what CORTEX knows, not what CORTEX can do.

The interface is dark-only, warm, and restrained. It rejects the anxiety of notification-heavy dashboards, the flatness of generic chat UIs, and the spectacle of AI magic aesthetics. Depth is conveyed through tonal layering — surfaces rise from a warm void through progressively lighter grays, never through decorative shadows or translucent panels. The accent color is used sparingly: a single point of cyan energy that signals "alive" without shouting.

**Key Characteristics:**
- Dark-only warm canvas with dual-accent system: silk red for actions + alertness, cyan for AI + data
- Restrained palette: accent on ≤10% of any surface
- Geist font: one family carries everything, tight hierarchy
- Spatial depth via tonal layering, not heavy shadows
- Motion that conveys state, never decoration
- Every animation respects `prefers-reduced-motion`
- Glassmorphism used selectively only in the Neural Hub redesign (dock, hub widgets, auth cards)

### Relationship to redesign0.md

The `docs/design/redesign0.md` document defines a specific redesign of the CORTEX UI into a **Neural Hub** layout (bottom dock, full-screen mode immersion, glass widgets). That redesign deliberately diverges from DESIGN.md defaults in three ways:
1. **Glassmorphism** used for the dock, hub widgets, and auth cards (banned in DESIGN.md default)
2. **Neural particles** as an extremely dim background layer (banned in DESIGN.md)
3. **Dual-accent system** (silk red + cyan) instead of single cyan accent

DESIGN.md remains the canonical design system — all palette values, typography sizes, radii, z-index, motion curves, and component specs. redesign0.md is a specific application of these tokens to a new layout architecture. DESIGN.md tokens must match what is implemented in `tailwind.config.ts`.

## 2. Colors

A restrained warm-dark palette built around a dual-accent system: **silk red** for actions, alerts, and emotion; **cyan** for AI, neural activity, and data. The neutral scale progresses from deep void through elevated surfaces, each step slightly warmer than true gray to maintain approachability.

### Silk Red Accent

- **Red** (`#d32f2f`): Primary accent for buttons, active dock items, emphasis. 4.2:1 contrast on bg-base — passes for large text and UI components.
- **Red Bright** (`#e53935`): Hover state for red elements, pulse animation, glowing indicators. 5.4:1 on bg-base.
- **Red Muted** (`rgba(211,47,47,0.20)`): Background tint for active states, badge fills, selected items.

### Cyan Neural Accent

- **Cyan** (`#00acc1`): Neural accent — data visualization, AI status, focus rings. 7.6:1 contrast on bg-base. Used alongside red for non-action accent (AI activity, data displays).
- **Cyan Bright** (`#26c6da`): Hover state for cyan elements, bright glow, active AI indicators. 10.3:1 on bg-base.
- **Cyan Muted** (`rgba(0,172,193,0.18)`): Subtle neural aura, background tint for AI-related surfaces.

### Accent Usage Rules

| Context | Use | Reason |
|---------|-----|--------|
| Buttons (primary) | Silk red | Action requires emphasis |
| Navigation (active) | Silk red | Current focus indicator |
| Focus rings | Silk red variant | Consistent with action accent |
| Data viz / AI status | Cyan | Information, not action |
| Neural particles | Cyan | AI ambiance |
| Processing indicators | Cyan | Data flow, not user action |
| Status badges (active) | Red badge | Attention signal |
| Status badges (info) | Cyan badge | Information signal |

### Neutral

- **Void / bg-base** (`#0d0d0d`): The deepest layer. Page background, the canvas everything sits on. Warm near-black with amber tint, never pure `#000000`.
- **Elevated** (`#1c1c1c`): Cards, panels, modals. One step above void — enough contrast to separate content.
- **Surface** (`#2a2a2a`): Interactive surfaces — input fields, dropdown backgrounds, active hover zones.
- **Hover** (`#363636`): Hover state background for nav items, buttons, list rows.
- **Glass** (`rgba(26,26,26,0.85)`): Glass-morphism overlays (dock, command bar). Used only in Neural Hub redesign.
- **Widget** (`rgba(26,26,26,0.75)`): Hub widget cards (glass style). Used only in Neural Hub redesign.

### Borders

- **Subtle** (`rgba(255,255,255,0.06)`): Hairline borders on cards, dividers, separators. Barely visible.
- **Default** (`rgba(255,255,255,0.12)`): Standard borders on inputs, interactive elements.
- **Red** (`rgba(211,47,47,0.35)`): Silk red border for focus, active, error-associated elements.
- **Cyan** (`rgba(0,172,193,0.35)`): Cyan border for AI-active states, data-focused elements.
- **Input Focus** (`rgba(211,47,47,0.40)`): Input focus ring color.

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

- **Red Glow** (`0 0 24px rgba(211,47,47,0.18)`): Silk red glow — buttons, active dock items, hero elements.
- **Cyan Glow** (`0 0 24px rgba(0,172,193,0.14)`): Cyan glow — AI activity, neural data visualization.
- **Red Strong** (`0 0 40px rgba(211,47,47,0.25)`): Hero moments, critical alerts, pulsing.
- **Cyan Strong** (`0 0 40px rgba(0,172,193,0.20)`): Active AI processing, data flow animation.

### Named Rules

**The 10% Rule.** The accent color appears on ≤10% of any given screen. Its rarity is the point. If every button, link, and badge is red or cyan, none stand out. Reserve accents for: primary actions, current navigation state, focus indicators, and status signals.

**The Never-Pure-Black Rule.** The deepest color is `#0d0d0d` — warm near-black with amber tint. Pure `#000000` creates a hole, not a surface. The void must feel like material, not absence.

**The Red-Cyan Separation Rule.** Red is for actions, alerts, and active selection. Cyan is for AI activity, data visualization, and information. Never use red for a passive information display. Never use cyan for a primary action button. When both appear on the same screen, the ratio must be visibly skewed toward one — a 50/50 split creates visual noise.

## 3. Typography

**Primary Font:** Geist (with system-ui fallback)
**Mono Font:** JetBrains Mono (with monospace fallback)

**Character:** A modern geometric sans-serif designed for interfaces. Clean, technical, and familiar to users of Linear, Figma, and Raycast. One family carries the entire hierarchy — no display fonts, no serif accents, no decorative pairings. JetBrains Mono handles code, data values, timestamps, and file paths.

### Hierarchy

- **Display** (600, `clamp(1.75rem, 3vw, 2.25rem)`, 1.2): Page titles, hero headings. Used once per page max. Tight letter-spacing (`-0.02em`) for weight without bulk.
- **Headline** (600, `1.25rem`, 1.3): Section headings, card titles. Clear hierarchy break from body.
- **Title** (500, `0.9375rem`, 1.4): Subsection headings, nav items, prominent labels. The workhorse heading size.
- **Body** (400, `0.875rem`, 1.6): Paragraphs, descriptions, content text. Capped at 65–75ch line length for readability.
- **Label** (600, `0.625rem`, 1.4, `letter-spacing: 0.1em`): Uppercase micro-labels, metadata, status indicators. Used sparingly — one per section maximum.
- **Mono** (400, `0.8125rem`, 1.5): Code blocks, data values, timestamps, file paths, version badges.

### Named Rules

**The One Family Rule.** Geist carries everything. No serif, no display, no decorative fonts. If Geist can't express it, the problem is the content, not the typeface. The only exception is JetBrains Mono for code and data.

**The Label Restraint Rule.** Uppercase micro-labels (`0.625rem`, `letter-spacing: 0.1em`) appear once per section maximum. Two labels stacked above a heading is visual noise. If a section needs more than one label, promote one to a title.

## 4. Elevation

Depth is conveyed entirely through tonal layering — no shadows at rest, no backdrop-blur, no glassmorphism. Surfaces rise from the warm void by becoming progressively lighter: Void → Elevated → Surface → Hover. The difference is subtle but enough to create spatial hierarchy.

Shadows appear only on interaction: hover states on cards, focus rings on inputs, floating elements (dropdowns, modals, tooltips). When shadows do appear, they are structural — they separate a floating element from its background — not decorative.

### Shadow Vocabulary

- **Subtle** (`0 1px 2px rgba(0,0,0,0.4)`): Cards at rest, minimal separation. The lightest touch.
- **Card** (`0 2px 8px rgba(0,0,0,0.4), 0 0 0 1px rgba(255,255,255,0.04)`): Elevated cards, panels. The faint border-rim creates materiality.
- **Elevated** (`0 4px 16px rgba(0,0,0,0.5), 0 0 0 1px rgba(255,255,255,0.05)`): Dropdowns, popovers, floating elements that need clear separation from content.
- **Modal** (`0 8px 32px rgba(0,0,0,0.6), 0 0 0 1px rgba(255,255,255,0.05)`): Modal dialogs, overlays. Deepest shadow for the highest z-layer.
- **Glow** (`0 0 20px rgba(6,182,212,0.12)`): Accent glow on focus, active state. Signals "alive" without being decorative.
- **Glow-Strong** (`0 0 40px rgba(6,182,212,0.2)`): Reserved for hero moments — a single glowing element on a page, never multiple.

### Named Rules

**The Flat-By-Default Rule.** Surfaces are flat at rest. Shadows appear only as a response to state (hover, elevation, focus). If a card has a shadow when nothing is hovering it, the shadow is wrong.

**The Glow Restraint Rule.** Glow shadows (`glow`, `glow-strong`) are accent-colored and rare. One glowing element per viewport maximum. Two glowing elements simultaneously is a light show, not an interface.

## 5. Components

Every component follows the tonal layering system: flat at rest, state changes through background shifts and subtle shadows. Consistent affordances across all surfaces — same button shape, same form vocabulary, same icon style.

### Buttons

- **Shape:** Gently curved edges (`10px` radius)
- **Primary (Red):** Silk Red background (`#d32f2f`), white text, 44px minimum height. 150ms ease-out bg + shadow transition. Hover: Red Bright (`#e53935`) with subtle red glow. Active: scale(0.98). Focus: 2px input-focus ring (`rgba(211,47,47,0.4)`). Disabled: 0.35 opacity, no shadow.
- **Secondary (Ghost):** Transparent background, secondary text (`#a0a0a0`). Hover: surface background (`#2a2a2a`) with primary text. 150ms transitions.
- **Tertiary (Neural):** Surface background (`#2a2a2a`), Cyan text (`#00acc1`). Hover: cyan muted bg, cyan bright text.
- **State rule:** One primary button per visible area. Multiple primaries compete for attention.

### Cards / Containers

- **Corner Style:** Gently curved (`16px` radius)
- **Background:** Elevated (`#1c1c1c`) — one step above the void
- **Border:** Subtle (`rgba(255,255,255,0.06)`) — structural, not decorative
- **Shadow Strategy:** Flat at rest. On hover: transition to Elevated shadow with subtle border brightening and 2px upward lift. Red glow for action cards, cyan glow for data/AI cards.
- **Glass variant:** Widget bg (`rgba(26,26,26,0.75)`) with backdrop-blur(16px). Used only in Neural Hub.
- **Internal Padding:** 16px standard

### Inputs / Fields

- **Style:** Surface background (`#2a2a2a`), default border (`rgba(255,255,255,0.12)`), `10px` radius, 44px minimum height
- **Focus:** Border shifts to input-focus (`rgba(211,47,47,0.4)`) with 2px ring at 30% opacity. 200ms ease-out transition.
- **Placeholder:** Muted text (`#7a7a7a`) — 4.5:1 contrast on bg-base. Never lighter.
- **Error:** Border shifts to danger (`#e74c3c`), ring shifts to danger at 25% opacity.
- **Disabled:** 35% opacity, pointer-events none.

### Navigation (Legacy Sidebar)

- **Style:** Vertical sidebar items with icon + label (current, being replaced by dock in redesign0)
- **Default:** Secondary text (`#a0a0a0`), transparent background
- **Hover:** Primary text (`#f0f0f0`), hover background (`#363636`), 150ms transition
- **Active:** Silk Red text (`#d32f2f`), red muted background (`rgba(211,47,47,0.20)`)
- **Typography:** Title weight (500), 14px
- **Mobile:** Bottom tab bar with icons only, active indicator

### Navigation (Dock — Neural Hub)

- **Style:** Floating glass-morphism bottom dock, centered, 10 icons
- **Default:** Secondary text (`#a0a0a0`), transparent background, 48×48px touch target
- **Hover:** Primary text (`#f0f0f0`), red muted background, 150ms ease-out. Cyan glow tooltip above.
- **Active:** Silk Red text (`#d32f2f`), red muted background, red glow shadow
- **Auto-hide:** In mode view, dock slides down 16px + fades after 3s idle. Reappears on mouse move at bottom edge.

### Badges / Status

- **Style:** Rounded-full pill, mono font (JetBrains Mono, `0.625rem`), uppercase, `letter-spacing: 0.1em`
- **Default:** Faint accent background, accent text
- **Semantic variants:** Success (green tint + green text), warning (amber tint + amber text), danger (red tint + red text)

### Skeleton States

- **Style:** Surface background (`#16161f`) with subtle shimmer animation
- **Animation:** Background-position slide, 2s linear infinite. Killed by `prefers-reduced-motion`.
- **Shape:** Matches the content it replaces — rectangular for text lines, circular for avatars, rounded for buttons

### Toast Notifications

- **Position:** Bottom-right on desktop, bottom-center on mobile
- **Style:** Elevated background, subtle border, `10px` radius, z-toast
- **Entrance:** Slide from right + opacity, 250ms ease-out
- **Exit:** Slide out + opacity, 200ms ease-in
- **Interruptible:** Yes — rapid triggers retarget from current state, not restart

### Modal Dialogs

- **Overlay:** Void at 60% opacity, fixed position, z-modal-backdrop
- **Content:** Elevated background, `24px` radius, Modal shadow
- **Entrance:** Scale 0.95→1 + opacity, 250ms ease-out (center origin)
- **Exit:** Scale 1→0.95 + opacity, 200ms ease-in
- **Focus trap:** Tab cycles within modal. Escape closes.

## 6. Do's and Don'ts

### Do:

- **Do** use Geist for everything — headings, body, labels, buttons. One family, tight hierarchy.
- **Do** keep accent at ≤10% of any surface. Reserve red for actions and active states; reserve cyan for AI activity and data.
- **Do** use tonal layering for depth — Void → Elevated → Surface → Hover. No shadows at rest.
- **Do** respect `prefers-reduced-motion` on every animation. Keep opacity/color transitions, kill movement.
- **Do** use 44px minimum touch targets on all interactive elements.
- **Do** show system status visibly — health indicators, vault lock state, model status.
- **Do** use skeleton states for loading, not spinners in content areas.
- **Do** write error messages with fix instructions, not just "Something went wrong."
- **Do** use `100dvh` for viewport heights, never `100vh`.
- **Do** test contrast: body text ≥4.5:1 against its background. Muted text (`#7a7a7a`) on bg-base (`#0d0d0d`) = 4.5:1 ✓.

### Don't:

- **Don't** use purple/blue AI gradients, sparkles, neon glows, or "AI magic" aesthetics. CORTEX is not magic — it's a machine that understands you.
- **Don't** make the homepage a conversation screen. CORTEX is not a chatbot. Intelligence is shown, not prompted.
- **Don't** use floating AI cards, rounded dashboard widgets, or chat-first layouts. (PRODUCT.md: "Do NOT use: Floating AI cards, rounded dashboard widgets, or chat-first layouts.")
- **Don't** use glassmorphism, backdrop-blur, or translucent panels as a default. Depth comes from tonal layering, not blur.
- **Don't** use the neural network canvas background. The void is the background. Content is the signal.
- **Don't** use gradient text (`background-clip: text`). Decorative, never meaningful. Use a single solid color.
- **Don't** use side-stripe borders (`border-left` > 1px as colored accent). Never intentional.
- **Don't** use tiny uppercase tracked eyebrows above every section. One label per section maximum.
- **Don't** use numbered section markers (01/02/03) as scaffolding. Numbers earn their place only when the section IS a sequence.
- **Don't** use identical card grids — same-sized cards with icon + heading + text, repeated endlessly.
- **Don't** use `scale(0)` on any entrance animation. Start from `scale(0.95)` + opacity.
- **Don't** use `ease-in` on any UI interaction. It delays the moment the user watches most. Use ease-out or custom curves.
- **Don't** use `transition: all`. Specify exact properties.
- **Don't** use `100vh` for viewport heights. Use `100dvh`.
- **Don't** use pure `#000000`. The deepest color is `#0a0a0f` — warm near-black.
- **Don't** use Inter, Roboto, or any font outside Geist + JetBrains Mono.
- **Don't** use modals as first thought. Exhaust inline / progressive alternatives first.
- **Don't** add decorative motion. Every animation answers "why does this animate?" — spatial consistency, state indication, feedback, or preventing a jarring change.
- **Don't** use bounce, elastic, or spring animations on UI elements.
- **Don't** animate layout properties (`width`, `height`, `margin`, `padding`). GPU-only: `transform` + `opacity`.
