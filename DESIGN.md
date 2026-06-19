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
| `--bg-void` | `#000000` | Deep canvas background |
| `--bg-base` | `#050508` | Page surface |
| `--bg-elevated` | `#0a0a0f` | Cards, panels |
| `--bg-surface` | `#111118` | Interactive surfaces |
| `--bg-hover` | `#1a1a24` | Hover states |
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

- **Desktop:** Collapsible sidebar (icon-only mode)
- **Tablet:** Overlay sidebar with backdrop blur
- **Mobile:** Bottom tab bar

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
