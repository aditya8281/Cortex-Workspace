Last updated: 2026-06-29

---
name: CORTEX
description: "Local-first machine intelligence layer — calm, spatial, persistent, always aware."
colors:
  primary: "#0ea5c9"
  primary-hover: "#38bdf8"
  primary-muted: "rgba(14,165,201,0.25)"
  primary-faint: "rgba(14,165,201,0.08)"
  neutral-void: "#0a0a0f"
  neutral-elevated: "#111118"
  neutral-surface: "#16161f"
  neutral-hover: "#1c1c28"
  neutral-border-subtle: "rgba(255,255,255,0.08)"
  neutral-border: "rgba(255,255,255,0.12)"
  text-primary: "#e8e8ed"
  text-secondary: "#7a7a8a"
  text-muted: "#555566"
  danger: "#ef4444"
  success: "#22c55e"
  warning: "#f59e0b"
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
- Dark-only warm canvas with soft cyan accent
- Restrained palette: accent on ≤10% of any surface
- Geist font: one family carries everything, tight hierarchy
- Spatial depth via tonal layering, not heavy shadows
- Motion that conveys state, never decoration
- Every animation respects `prefers-reduced-motion`
- No glassmorphism, no neural canvas, no decorative backgrounds

## 2. Colors

A restrained warm-dark palette built around a single cyan accent. The neutral scale progresses from deep void through elevated surfaces, each step slightly warmer than true gray to maintain approachability.

### Primary

- **Pulse Cyan** (`#0ea5c9`): The single accent. Used for primary actions, active navigation, focus rings, status indicators, and links. Appears on ≤10% of any given screen — its rarity is the point.
- **Cyan Hover** (`#38bdf8`): Brighter cyan for hover states on primary buttons and interactive accent elements.
- **Cyan Muted** (`rgba(14,165,201,0.25)`): Reduced-opacity cyan for secondary accent backgrounds — active nav items, selected states, badge backgrounds.
- **Cyan Faint** (`rgba(14,165,201,0.08)`): Barely-there cyan tint for the lightest accent surfaces — active sidebar items, subtle selection indicators.

### Neutral

- **Void** (`#0a0a0f`): The deepest layer. Page background, the canvas everything sits on. Warm near-black, never pure `#000000`.
- **Elevated** (`#111118`): Cards, panels, modals. One step above void — enough contrast to separate content from background.
- **Surface** (`#16161f`): Interactive surfaces — input fields, dropdown backgrounds, active hover zones. The "touchable" layer.
- **Hover** (`#1c1c28`): Hover state background for nav items, buttons, list rows. The lightest neutral in regular use.

### Borders

- **Subtle** (`rgba(255,255,255,0.08)`): Hairline borders on cards, dividers, separators. Barely visible — structural, not decorative.
- **Default** (`rgba(255,255,255,0.12)`): Standard borders on inputs, interactive elements, panels that need clearer definition.
- **Accent** (`rgba(14,165,201,0.3)`): Cyan-tinted borders for focused inputs, active states, accent-outlined elements.

### Text

- **Primary** (`#e8e8ed`): Body text, headings, labels — the dominant reading color. High contrast against all neutral backgrounds.
- **Secondary** (`#7a7a8a`): Supporting text, descriptions, nav labels at rest. Readable but clearly subordinate.
- **Muted** (`#555566`): Hints, placeholders, disabled states, metadata. Lowest-contrast text — still meets 4.5:1 against Void.

### Semantic

- **Danger** (`#ef4444`): Destructive actions, error states, critical alerts.
- **Success** (`#22c55e`): Positive confirmations, healthy status, completed states.
- **Warning** (`#f59e0b`): Caution indicators, pending states, non-critical alerts.

### Named Rules

**The 10% Rule.** The accent color appears on ≤10% of any given screen. Its rarity is the point. If every button, link, and badge is cyan, none of them stand out. Reserve it for: primary actions, current navigation state, focus indicators, and status signals.

**The Never-Pure-Black Rule.** The deepest color is `#0a0a0f` — warm near-black with a hint of blue. Pure `#000000` creates a hole, not a surface. The void must feel like material, not absence.

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

- **Shape:** Gently curved edges (`8px` radius)
- **Primary:** Pulse Cyan background (`#0ea5c9`), white text, 44px minimum height. 200ms ease-out background transition. Focus: 2px cyan ring (`rgba(14,165,201,0.3)`).
- **Ghost:** Transparent background, secondary text color (`#7a7a8a`). Hover: surface background (`#16161f`) with primary text. 150ms transitions.
- **State rule:** One primary button per visible area. Multiple primaries compete for attention.

### Cards / Containers

- **Corner Style:** Gently curved (`12px` radius)
- **Background:** Elevated (`#111118`) — one step above the void
- **Border:** Subtle (`rgba(255,255,255,0.08)`) — structural, not decorative
- **Shadow Strategy:** Flat at rest. On hover: transition to Elevated shadow (`0 4px 16px`) with subtle border brightening and 2px upward lift.
- **Internal Padding:** 16px standard

### Inputs / Fields

- **Style:** Surface background (`#16161f`), default border (`rgba(255,255,255,0.12)`), 8px radius, 44px minimum height
- **Focus:** Border shifts to accent (`rgba(14,165,201,0.3)`) with 2px accent ring (`rgba(14,165,201,0.12)`). 200ms ease-out transition.
- **Placeholder:** Muted text (`#555566`) — same 4.5:1 contrast as body text
- **Error:** Border shifts to danger (`#ef4444`), ring follows
- **Disabled:** 40% opacity, pointer-events none

### Navigation

- **Style:** Vertical sidebar items with icon + label
- **Default:** Secondary text (`#7a7a8a`), transparent background
- **Hover:** Primary text (`#e8e8ed`), hover background (`#1c1c28`), 150ms transition
- **Active:** Primary accent text (`#0ea5c9`), faint accent background (`rgba(14,165,201,0.08)`)
- **Typography:** Title weight (500), 14px
- **Mobile:** Bottom tab bar with icons only, active indicator

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
- **Style:** Elevated background, subtle border, 12px radius
- **Entrance:** Slide from right + opacity, 250ms ease-out
- **Exit:** Slide out + opacity, 200ms ease-in
- **Interruptible:** Yes — rapid triggers retarget from current state, not restart

### Modal Dialogs

- **Overlay:** Void at 60% opacity, fixed position
- **Content:** Elevated background, 16px radius, Modal shadow
- **Entrance:** Scale 0.95→1 + opacity, 250ms ease-out (center origin)
- **Exit:** Scale 1→0.95 + opacity, 200ms ease-in
- **Focus trap:** Tab cycles within modal. Escape closes.

## 6. Do's and Don'ts

### Do:

- **Do** use Geist for everything — headings, body, labels, buttons. One family, tight hierarchy.
- **Do** keep accent at ≤10% of any surface. Reserve cyan for: primary actions, active nav, focus rings, status indicators.
- **Do** use tonal layering for depth — Void → Elevated → Surface → Hover. No shadows at rest.
- **Do** respect `prefers-reduced-motion` on every animation. Keep opacity/color transitions, kill movement.
- **Do** use 44px minimum touch targets on all interactive elements.
- **Do** show system status visibly — health indicators, vault lock state, model status.
- **Do** use skeleton states for loading, not spinners in content areas.
- **Do** write error messages with fix instructions, not just "Something went wrong."
- **Do** use `100dvh` for viewport heights, never `100vh`.
- **Do** test contrast: body text ≥4.5:1 against its background. Muted text (`#555566`) on Void (`#0a0a0f`) = 4.8:1 ✓.

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
