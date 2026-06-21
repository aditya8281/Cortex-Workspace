# Design System — Warm Neural Dark

A warm dark canvas with a soft cyan accent. The interface should feel like a calm AI companion — refined, approachable, and alive. Evolved from the original Neural Dark (OLED black) to a warmer, more human-friendly palette.

---

## Stack

- **Framework:** Next.js 15 App Router + React 19 + TypeScript
- **Styling:** Tailwind CSS v3.4 with custom design tokens
- **Components:** Custom component library built on Radix UI primitives
- **Icons:** Lucide React
- **Animations:** framer-motion (spring physics, Apple-level subtlety)
- **Fonts:** Inter (body), JetBrains Mono (mono)
- **Dark mode:** Class-based, hardcoded dark
- **Utilities:** `cn()` from `@/lib/utils` (clsx + tailwind-merge)

---

## Tokens

All semantic tokens live in `app/globals.css` and are bridged to Tailwind with `@tailwind` directives.

| Token | Value | Usage |
| --- | --- | --- |
| `--bg-void` | `#0a0a0f` | Base canvas — warm dark |
| `--bg-base` | `#0a0a0f` | Page surface |
| `--bg-elevated` | `#111118` | Cards, panels |
| `--bg-surface` | `#16161f` | Interactive surfaces |
| `--bg-hover` | `#1c1c28` | Hover states |
| `--border-subtle` | `rgba(255,255,255,0.06)` | Hairline borders |
| `--border-default` | `rgba(255,255,255,0.10)` | Standard borders |
| `--border-accent` | `rgba(14,165,201,0.3)` | Accent borders |
| `--text-primary` | `#f0f0f5` | Primary text |
| `--text-secondary` | `#8a8a9a` | Supporting text |
| `--text-muted` | `#555566` | Hints, labels |
| `--accent` | `#0ea5c9` | Primary accent — soft cyan |
| `--accent-glow` | `rgba(14,165,201,0.15)` | Glow effects |
| `--accent-bright` | `#22d3ee` | Hover accent |
| `--danger` | `#ef4444` | Destructive actions |
| `--success` | `#22c55e` | Positive states |
| `--warning` | `#f59e0b` | Warning states |

---

## Typography

| Token | Font | Usage |
| --- | --- | --- |
| `--font-inter` | Inter | Body text, controls, forms |
| `--font-jetbrains-mono` | JetBrains Mono | Code, labels, metadata |

---

## Core Utilities

Defined in `app/globals.css`:

- `.glass-panel`: Translucent backdrop blur panel
- `.glass-panel-strong`: Heavier backdrop blur
- `.shimmer-bg`: Loading shimmer animation
- `.text-gradient`: Gray gradient text
- `.text-gradient-accent`: Cyan gradient text
- `.focus-ring`: Consistent focus ring styles
- `.interactive-card`: Card with hover lift and glow
- `.nav-item`: Navigation item with active state
- `.stat-card`: Stat display card
- `.modal-overlay` / `.modal-content`: Modal styles
- `.btn-glow`: Button glow effect
- `.micro-label`: Uppercase mono label

---

## Components

### Cards

Cards are rounded-xl, translucent with subtle borders. Use `glass-panel` or `interactive-card` classes.

```tsx
<Card className="overflow-hidden">
```

### Buttons

Primary buttons use accent color with glow effect. Secondary is translucent with border. Ghost is minimal.

```tsx
<Button variant="primary" size="md">Action</Button>
```

### Inputs

Inputs use rounded-xl, translucent backgrounds, cyan focus glow. Error states use danger color.

```tsx
<Input label="Username" error="Invalid" />
```

### Badges

Badges are mono, uppercase, rounded-full pills with semantic colors.

```tsx
<Badge variant="accent">Status</Badge>
```

---

## Layout

DashboardShell wraps all authenticated pages with a floating glass sidebar:

- **Desktop:** Fixed 240px floating sidebar with glass morphism, Work/You nav groups
- **Tablet:** Overlay sidebar with backdrop blur
- **Mobile:** Bottom tab bar
- **Header:** Minimal — logo, search button, notifications bell, user avatar dropdown
- **Command Palette:** Cmd+K for quick navigation

---

## Background System

All pages share a unified neural network canvas background (`NeuralNetwork.tsx`). The canvas is `position: fixed` covering the full viewport at `z-index: -1`.

| Page | Intensity | Notes |
| --- | --- | --- |
| Landing (`/`) | `high` | Hero background, 80 neurons |
| Dashboard (`/app`) | `medium` | 50 neurons |
| Auth (`/auth`) | `low` | Subtle, 30 neurons |
| Memory (`/memory`) | `low` | Subtle, 30 neurons |
| Chat (`/chat`) | `medium` | Conversation interface |
| Models (`/models`) | `medium` | Model catalog + downloads |
| Vault/Settings/Profile/Admin | `medium` | Inherited through transparent DashboardShell |

**Page wrappers use `bg-transparent`** to let the canvas show through. Cards and panels use `bg-bg-elevated` (#111118) for layering depth against the warm dark base.

---

## Component Library

### Primitives
- **Button**: primary/secondary/ghost/danger variants, sm/md/lg sizes, loading spinner
- **Input**: label, error state, password toggle
- **Card**: hover/glass/gradient/glow variants with micro-interactions
- **Badge**: default/accent/success/warning/danger
- **Skeleton**: shimmer loading placeholder
- **Tooltip**: Radix wrapper
- **Dropdown**: Radix dropdown menu
- **Modal**: Radix Dialog wrapper

### Data Display
- **MetricRing**: Animated SVG ring chart with counter (CPU/RAM/Disk)
- **TabGroup**: Tabs with animated indicator + TabPanel context
- **CollapsiblePanel**: Animated collapsible sidebar panel
- **ModelCard**: Model info card with download/install actions
- **DownloadQueuePanel**: Active download list with progress bars

### Feedback
- **Toast**: Sonner notifications
- **ErrorBoundary**: Class-based React error boundary
- **PasswordStrength**: Visual strength meter (4 bars)

### Animation
- **PageTransition**: Framer Motion page enter/exit (y:8, damping:30)
- **StaggerChildren**: Framer Motion stagger animation
- **NeuralNetwork**: Full canvas-based neural network visualization

### Overlay
- **CommandPalette**: Cmd+K palette using cmdk for page navigation

---

## Sidebar Design (Glass Floating)

The desktop sidebar uses a glass morphism floating design:

- **Background:** `bg-bg-surface/80` with `backdrop-blur-xl` — frosted glass effect
- **Border:** `border-border-subtle` — subtle separation from content
- **Shadow:** `shadow-[0_8px_32px_rgba(0,0,0,0.4)]` — floating depth
- **Border radius:** `rounded-2xl` — soft, modern feel
- **Nav groups:** "Work" (Dashboard, Search, Agents, Chat, Models) and "You" (Vault, Memory, Profile, Settings)
- **Active state:** Accent background tint with accent text
- **Hover state:** Subtle background shift
- **Status bar:** Vault lock state + memory count at bottom
- **User card:** Avatar with online status dot

---

## Interaction

- Hover lift: `hover:-translate-y-0.5`
- Focus: `focus-visible:ring-ring/50 focus-visible:ring-[3px]`
- Disabled: `disabled:pointer-events-none disabled:opacity-40`
- Page entrance: framer-motion spring animations
- Stagger: Sequential child entrance

---

## Accessibility

- Visible focus rings on all interactive controls
- High contrast text on dark surfaces
- `prefers-reduced-motion` support
- Skip-to-content link
- Keyboard navigation via Radix primitives
- ARIA labels for icon-only buttons
