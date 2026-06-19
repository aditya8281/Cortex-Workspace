# Cortex Design System

## 1. Visual Theme & Atmosphere

**Mood:** Dark cybernetic with a glowing cyan pulse — a precision workspace that feels both technical and alive.

**Aesthetic:** Deep charcoal backgrounds with subtle glass morphism surfaces, cyan accent lighting, and gradient text treatments. The interface balances dense data presentation with micro-interactions that reward exploration. Every hover state, transition, and animation is intentional — the interface breathes.

**Signature Elements:**
- Glass morphism panels (`glass-panel`, `glass-panel-strong`) for headers and elevated surfaces
- Cyan gradient text for hero content (`text-gradient-accent`)
- Smooth 1px lift + glow on interactive cards (`interactive-card`)
- Staggered entrance animations for grid content (`appear-stagger`)
- Pulse-glow animation on accent elements (`animate-pulse-glow`)
- Focus rings with `ring-2 ring-accent/30 ring-offset-2 ring-offset-bg`

---

## Design Principles

1. **Local-first clarity** — Every interface element communicates that data stays on the user's machine
2. **Technical confidence** — Professional, precise, never toy-like; users trust this with their code and data
3. **Minimal surface** — Show only what's needed; complexity is available but never forced
4. **Consistent rhythm** — 8px spacing grid, predictable component patterns across all pages
5. **Motion with purpose** — Animations are never decorative; they communicate state changes, hierarchy, and feedback
6. **Glass when elevated** — Floating elements (headers, modals, tooltips) use glass morphism to signal depth

---

## 2. Color Palette & Roles

### Backgrounds (Deep Charcoal Layering)

| Descriptive Name | Hex Code | Functional Role |
|------------------|----------|-----------------|
| **Void Black** | `#09090b` | Page background — the deepest layer, absorbs light, never scrolled |
| **Surface Slate** | `#131316` | Input fields, elevated panels — slightly raised from void, functional |
| **Card Stone** | `#18181b` | Cards, modals, panels — primary content containers |
| **Elevated Ash** | `#1f1f23` | Dropdowns, popovers, tooltips — floating elements |
| **Hover Smoke** | `#27272a` | Hover states — interactive feedback layer |
| **Glass Black** | `rgba(24,24,27,0.6)` | Glass panels — transparent elevated surfaces with backdrop-blur |

### Borders

| Descriptive Name | Hex Code | Functional Role |
|------------------|----------|-----------------|
| **Divider Line** | `#27272a` | Default borders — separates content areas |
| **Subtle Edge** | `#1f1f23` | Subtle dividers — minimal separation, nearly invisible |
| **Accent Border** | `rgba(6,182,212,0.3)` | Accented borders — active/focused state |

### Text (Crisp Contrast Hierarchy)

| Descriptive Name | Hex Code | Functional Role |
|------------------|----------|-----------------|
| **Primary White** | `#fafafa` | Headings, primary content — maximum readability |
| **Secondary Silver** | `#a1a1aa` | Descriptions, metadata — supporting text |
| **Muted Zinc** | `#71717a` | Labels, hints — non-essential information only |

### Accent (Cyan Pulse)

| Descriptive Name | Hex Code | Functional Role |
|------------------|----------|-----------------|
| **Cyan Core** | `#06b6d4` | Primary actions, active links — the brand heartbeat |
| **Cyan Glow** | `#22d3ee` | Hover states — energized interaction |
| **Cyan Glow Shadow** | `rgba(6,182,212,0.15)` | Background glow — shadow-glow, hover states |
| **Cyan Wash** | `rgba(6,182,212,0.12)` | Accent backgrounds — tinted containers |
| **Cyan Whisper** | `rgba(6,182,212,0.06)` | Subtle backgrounds — barely-there accents |

### Semantic (Status Signals)

| Descriptive Name | Hex Code | Functional Role |
|------------------|----------|-----------------|
| **Error Red** | `#ef4444` | Danger states — always paired with icons/text |
| **Error Wash** | `rgba(239,68,68,0.12)` | Error backgrounds — tinted danger areas |
| **Success Green** | `#22c55e` | Confirmation — positive feedback |
| **Success Wash** | `rgba(34,197,94,0.12)` | Success backgrounds — tinted confirmation |
| **Warning Amber** | `#f59e0b` | Warning states — caution indicators |
| **Warning Wash** | `rgba(245,158,11,0.12)` | Warning backgrounds — tinted caution areas |

### Accessibility Notes

- All text colors meet WCAG AA (4.5:1 minimum) against their backgrounds
- Semantic colors (`error`, `success`) always pair with icons/text, never color-only
- `text-muted` at 4.8:1 is borderline; use only for non-essential labels
- Focus rings always visible: `focus:ring-2 focus:ring-accent/10`
- Reduced motion: animations respect `prefers-reduced-motion`

---

## Typography

### Font Stack

**UI Font:** Inter — geometric, neutral, engineered for screens. Weights 400 (body) through 600 (headings). No italic — always upright, always precise.

**Code Font:** JetBrains Mono — ligature-aware monospace for code blocks, terminal output, and technical values. Weights 400-500.

### Type Scale

| Tailwind Class | Size | Line Height | Weight | Usage |
|----------------|------|-------------|--------|-------|
| `text-[10px]` | 10px | 14px | 500 | Badges, labels (absolute minimum) |
| `text-[11px]` | 11px | 16px | 500 | Captions, metadata |
| `text-xs` | 12px | 16px | 400 | Small text, helper text |
| `text-sm` | 14px | 20px | 400 | Body text, form inputs |
| `text-base` | 16px | 24px | 400 | Default body text |
| `text-lg` | 18px | 28px | 400 | Large body text |
| `text-xl` | 20px | 28px | 600 | Section headers |
| `text-2xl` | 24px | 32px | 600 | Page titles |
| `text-4xl` | 36px | 40px | 600 | Display (landing) |
| `text-5xl` | 48px | 48px | 600 | Display (landing) |
| `text-6xl` | 60px | 56px | 600 | Display (landing) |

### Typography Rules

- **Minimum size:** 14px (`text-sm`) for all body text — 10px only for badges/labels
- **Line height:** 1.5-1.75 for body text, tighter for headings
- **Line length:** 60-75 characters maximum per line for readability
- **No all-caps** except for tiny labels under 11px
- **Weight discipline:** 400 for reading, 600 for hierarchy — never bold in between
- **Gradient headings:** Use `text-gradient` for hero spans, `text-gradient-accent` for accent hero text

---

## Spacing System

Base unit: **4px**

| Token | Value | Usage |
|-------|-------|-------|
| `gap-1` | 4px | Tight spacing (icon to label) |
| `gap-2` | 8px | Default element spacing |
| `gap-3` | 12px | Form field spacing |
| `gap-4` | 16px | Card padding, section spacing |
| `gap-5` | 20px | Card internal padding |
| `gap-6` | 24px | Section gaps |
| `gap-8` | 32px | Major section separation |

### Rules

- Cards: `p-5` (20px) internal padding — consistent across all pages
- Form fields: `gap-3` (12px) between fields
- Page sections: `gap-6` (24px) between major sections
- Dashboard max width: `max-w-4xl` (896px)
- Form max width: `max-w-2xl` (672px)

---

## Border Radius

| Token | Value | Usage |
|-------|-------|-------|
| `rounded-md` | 6px | Small elements |
| `rounded-lg` | 8px | Buttons, inputs, cards **default** |
| `rounded-xl` | 12px | Modals, large cards, elevated panels |
| `rounded-full` | 9999px | Avatars, badges, pills |

### Rules

- All interactive elements use `rounded-lg` (8px) consistently
- Modals use `rounded-xl` (12px) for premium feel
- Never use `rounded-none` except for dividers

---

## Shadows

| Token | Value | Usage |
|-------|-------|-------|
| `shadow-subtle` | `0 1px 2px rgba(0,0,0,0.3)` | Subtle elevation |
| `shadow-card` | `0 2px 8px rgba(0,0,0,0.3), 0 0 0 1px rgba(255,255,255,0.03)` | Cards |
| `shadow-elevated` | `0 4px 16px rgba(0,0,0,0.4), 0 0 0 1px rgba(255,255,255,0.04)` | Dropdowns, popovers |
| `shadow-glow` | `0 0 20px rgba(6,182,212,0.1)` | Accent glow (primary buttons) |
| `shadow-glow-strong` | `0 0 30px rgba(6,182,212,0.2)` | Strong accent glow (hover) |
| `shadow-modal` | `0 8px 32px rgba(0,0,0,0.5), 0 0 0 1px rgba(255,255,255,0.04)` | Modals, dialogs |

### Rules

- Cards use `shadow-card` by default
- Primary buttons get `shadow-glow` for emphasis, `shadow-glow-strong` on hover
- Modals use `shadow-modal` + backdrop blur
- Dropdowns use `shadow-elevated`

---

## Glass Morphism

CSS classes defined in `globals.css`:

| Class | Backdrop Blur | Usage |
|-------|---------------|-------|
| `glass-panel` | 12px | Headers, navigation bars |
| `glass-panel-strong` | 20px | Modals, elevated overlays |

### Rules

- Headers use `glass-panel` for sticky navigation
- Context menus and floating panels use `glass-panel`
- Never use glass on cards that need consistent backgrounds

---

## Animations & Keyframes

### Defined Animations

| Class | Duration | Timing | Usage |
|-------|----------|--------|-------|
| `animate-fade-in` | 250ms | ease-out | Page load, content appear |
| `animate-fade-in-up` | 300ms | ease-out | Step transitions, content reveal |
| `animate-fade-in-scale` | 200ms | ease-out | Modals, dialogs |
| `animate-slide-in-right` | 200ms | ease-out | Side panel, notification |
| `animate-slide-in-left` | 200ms | ease-out | Sidebar, menu |
| `animate-pulse-dot` | 2s loop | ease-in-out | Status indicators |
| `animate-pulse-glow` | 2s loop | ease-in-out | Accent glow pulse |
| `animate-shimmer` | 2s loop | linear | Loading skeletons |
| `animate-scale-press` | 200ms | ease-out | Button press feedback |
| `animate-spin-slow` | 3s loop | linear | Decorative spinner |

### Staggered Entrance

Use the `appear-stagger` class on grid containers. Children animate in with staggered delays (50ms each, up to 450ms for 10 items).

```html
<div class="appear-stagger grid grid-cols-3 gap-4">
  <Card>...</Card>
  <Card>...</Card>
  <Card>...</Card>
</div>
```

### Interactive Card

```html
<div class="interactive-card p-5">
  <!-- content -->
</div>
```

Lifts 1px on hover, adds glow border, scales to 0.995 on press.

### Rules

- Respect `prefers-reduced-motion`
- Never animate `width`, `height`, `top`, `left` — use `transform` only
- Exit animations 60-70% of enter duration
- Max 2 animated elements per view (not counting staggered children)

---

## Component Stylings

* **Buttons:** Four variants:
  - **Primary** (`variant="primary"`): Solid cyan accent, white text, glow shadow, lifts on hover
  - **Secondary** (`variant="secondary"`): Dark card background, subtle border, hover adds accent border
  - **Ghost** (`variant="ghost"`): Transparent, silver text, minimal hover background
  - **Danger** (`variant="danger"`): Red tinted background, red text, border, for destructive actions
  - All use `rounded-lg` (8px), sizes sm/md/lg, loading spinner state

* **Cards/Containers:** `rounded-lg`, deep stone background (`bg-bg-card`), subtle shadow with 1px white edge (`shadow-card`). Card component accepts `hover` prop (adds interactive-card styling) and `glass` prop (glass morphism). Internal padding: 20px (`p-5`).

* **Inputs/Forms:** 40px height, 8px border radius (`rounded-lg`), slate surface background. Border: 1px solid divider line. Focus ring: `ring-2 ring-accent/10` with `border-accent/40`. Error state: red border at 50% opacity. Placeholder text: muted zinc. Font size: 14px. Password fields include a visibility toggle.

* **Modals/Dialogs:** Fixed overlay with `bg-bg/85 backdrop-blur-sm`. Content uses `modal-content` class: `rounded-xl (12px)`, elevated ash background, `shadow-modal`, `animate-fade-in-scale` entrance. Context menus use glass-panel styling.

* **Dropdowns/Popovers:** Elevated ash background (`bg-elevated`), subtle edge border, `rounded-lg` (8px), `shadow-elevated` for depth. `animate-fade-in` entrance.

* **Badges/Tags:** Pill-shaped (`rounded-full`), 10-11px text, accent wash background with cyan text for primary, neutral for secondary.

* **Navigation/Sidebar:** 
  - Sidebar: `w-56`, `bg-bg-surface`, collapsible with hamburger toggle
  - Nav items: `.nav-item` class — flex row with icon + label, hover/active states
  - Active nav: `.nav-item.active` — cyan accent background (`bg-accent-faint`), accent text, subtle border
  - Header: `glass-panel`, sticky, with breadcrumb in center, avatar dropdown on right

---

## CSS Utility Classes

Defined in `globals.css`:

| Class | Purpose |
|-------|---------|
| `.glass-panel` | Glass morphism (12px blur) |
| `.glass-panel-strong` | Strong glass morphism (20px blur) |
| `.shimmer-bg` | Animated loading shimmer |
| `.text-gradient` | White-to-silver gradient text |
| `.text-gradient-accent` | Cyan gradient text for hero accent |
| `.focus-ring` | Enhanced focus ring utility |
| `.appear-stagger` | Staggered children entrance animation |
| `.interactive-card` | Card with hover lift + glow + press |
| `.file-item` | File list item hover state |
| `.toolbar-btn` | Toolbar button with scale press |
| `.status-dot` | Status indicator dot |
| `.nav-item` | Sidebar navigation item |
| `.page-header` | Page title + subtitle section |
| `.stat-card` | Stats/metrics card |
| `.modal-overlay` | Modal backdrop overlay |
| `.modal-content` | Modal dialog content container |

---

## Icon System

### Rules

- **Stroke width**: 1.5px for UI icons (Heroicons outline)
- **Size**: `h-4 w-4` (16px) for inline, `h-5 w-5` (20px) for standalone, `h-3.5 w-3.5` (14px) for small
- **Color**: `text-text-secondary` default, `text-accent` for active/primary, `text-error` for destructive
- **Source**: Heroicons outline only (inline SVG)
- **Never use emojis** as icons — always SVG

---

## Responsive Breakpoints

| Prefix | Min Width | Usage |
|--------|-----------|-------|
| `sm` | 640px | Small tablets, large phones |
| `md` | 768px | Tablets |
| `lg` | 1024px | Small desktops |
| `xl` | 1280px | Large desktops |

### Layout Rules

- Mobile-first: base styles are mobile, `sm:` and up for larger
- Content max-width: `max-w-4xl` (896px) for dashboard, `max-w-2xl` (672px) for forms
- Grid: `grid-cols-1 sm:grid-cols-2 lg:grid-cols-3` for card layouts
- No horizontal scroll on any screen size
- Sidebar collapses on mobile via hamburger toggle

---

## Accessibility Checklist

### Critical (Must Have)

- [x] Contrast 4.5:1 for all text
- [x] Visible focus rings on all interactive elements (`focus:ring-2 focus:ring-accent/10`)
- [x] Alt text for meaningful images
- [x] `aria-label` for icon-only buttons
- [x] Keyboard navigation support
- [x] Form labels with `htmlFor` / semantic label
- [x] Error messages near related fields
- [x] Respect `prefers-reduced-motion`

### Layout

- [x] Viewport meta tag (never disable zoom)
- [x] Mobile-first responsive
- [x] No horizontal scroll
- [x] Min 16px body text on mobile
- [x] Touch targets >= 44x44px

### Motion

- [x] Respect `prefers-reduced-motion`
- [x] Duration 150-300ms for micro-interactions
- [x] Use `transform` not `width`/`height`

---

## Anti-Patterns

### Never

- Use emojis as icons
- Mix icon styles (filled + outline) at same level
- Use `text-xs` (12px) for body text
- Disable zoom with viewport meta
- Remove focus rings
- Use `px` values in responsive layouts
- Animate `width` or `height`
- Use color as only indicator of state

### Avoid

- More than 2 animations per view (excluding staggered children)
- Inline styles for design tokens
- Hardcoded colors (use tokens)
- Text < 10px for any user-facing content
- Horizontal scroll on mobile
- Inconsistent border radii (stick to `rounded-lg`)
- Mixing glass and solid surfaces at the same elevation
