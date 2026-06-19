# Design System — Neural Dark

A monochrome dark canvas with a single electric cyan pulse as the living accent. The interface should feel like a living intelligence — responsive, fluid, and alive. AI-native operating system aesthetic.

---

## Stack

- **Framework:** Next.js 15 App Router + React 19 + TypeScript
- **Styling:** Tailwind CSS v3.4 with custom design tokens
- **Components:** Custom component library built on Radix UI primitives
- **Icons:** Lucide React
- **Animations:** framer-motion
- **Fonts:** Inter (body), JetBrains Mono (mono)
- **Dark mode:** Class-based, hardcoded dark
- **Utilities:** `cn()` from `@/lib/utils` (clsx + tailwind-merge)

---

## Tokens

All semantic tokens live in `app/globals.css` and are bridged to Tailwind with `@tailwind` directives.

| Token | Value | Usage |
| --- | --- | --- |
| `--bg-void` | `#000000` | Pure black canvas background |
| `--bg-base` | `#000000` | Page surface — OLED black |
| `--bg-elevated` | `#040406` | Cards, panels — barely above black |
| `--bg-surface` | `#0a0a0f` | Interactive surfaces |
| `--bg-hover` | `#111118` | Hover states |
| `--border-subtle` | `rgba(255,255,255,0.06)` | Hairline borders |
| `--border-default` | `rgba(255,255,255,0.10)` | Standard borders |
| `--border-accent` | `rgba(6,182,212,0.3)` | Accent borders |
| `--text-primary` | `#f0f0f5` | Primary text |
| `--text-secondary` | `#8a8a9a` | Supporting text |
| `--text-muted` | `#555566` | Hints, labels |
| `--accent` | `#06b6d4` | Primary accent — the pulse |
| `--accent-glow` | `rgba(6,182,212,0.15)` | Glow effects |
| `--accent-bright` | `#22d3ee` | Hover accent |
| `--danger` | `#ef4444` | Destructive actions |
| `--success` | `#22c55e` | Positive states |

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

Wide planning workspace with adaptive navigation:

- **Desktop:** Fixed 240px sidebar with Neural Pulse design (pulsing active indicator, glow effects, status bar)
- **Tablet:** Overlay sidebar with backdrop blur
- **Mobile:** Bottom tab bar

---

## Background System

All pages share a unified neural network canvas background (`NeuralNetwork.tsx`). The canvas is `position: fixed` covering the full viewport at `z-index: -1`.

| Page | Intensity | Notes |
| --- | --- | --- |
| Landing (`/`) | `high` | Hero background, 80 neurons |
| Dashboard (`/app`) | `medium` | 50 neurons |
| Auth (`/auth`) | `low` | Subtle, 30 neurons |
| Memory (`/memory`) | `low` | Subtle, 30 neurons |
| Vault/Settings/Profile/Admin | `medium` | Inherited through transparent DashboardShell |

**Page wrappers use `bg-transparent`** to let the canvas show through. Cards and panels use `bg-bg-elevated` (#040406) for layering depth against the OLED black base. The `html` element uses `background: #000000` to ensure OLED black across all pages.

---

## Sidebar Design (Neural Pulse)

The desktop sidebar uses the Neural Pulse design system:

- **Active indicator:** 3px pulsing cyan dot on the left edge with `pulse-dot` keyframe animation (2s cycle, opacity 0.6-1.0)
- **Active item glow:** Subtle accent box-shadow (`0 0 20px rgba(6,182,212,0.08)`)
- **Hover glow:** Soft accent shadow on hover (`0 0 15px rgba(6,182,212,0.04)`)
- **Section dividers:** Neon gradient lines (`transparent -> accent/15 -> transparent`)
- **Status bar:** Vault lock state (red/green dot) + memory count at bottom
- **User card:** Avatar with accent glow ring + online status dot
- `prefers-reduced-motion` disables all pulse animations

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
