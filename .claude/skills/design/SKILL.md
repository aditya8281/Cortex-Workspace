---
name: design
description: "Full frontend rebuild from scratch — iterative loop covering scaffold, auth, layout, all features, and polish. Reads DESIGN.md tokens, discovers backend API routes, builds production architecture with Coming Soon placeholders for future versions."
---

# /design — Frontend From Scratch

Rebuilds an entire frontend iteratively. Each phase produces a working, buildable state. Loop continues until all core capabilities are covered and build passes.

**Works for any project** — discovers DESIGN.md, API routes, and version plans dynamically. Not hardcoded to any specific project.

## Absolute Rules

1. **DESIGN.md is law.** Colors, typography, elevation, components — all from the project's DESIGN.md. No improvisation on palette.
2. **Dark-only** (unless DESIGN.md specifies light mode support). No theme toggle unless DESIGN.md defines one.
3. **Production at every phase.** Each phase ends with `npm run build` passing.
4. **Expandable.** Every page module is a self-contained directory. Adding a feature = adding a directory.
5. **Coming Soon for future versions.** Pages for unimplemented features get a styled placeholder with description of what's coming.
6. **Token-correct Tailwind.** Read the actual token names from DESIGN.md and map them correctly. Never guess token names — always verify against DESIGN.md.
7. **No hardcoded colors.** Use DESIGN.md tokens everywhere. No `#fff`, `#000`, or arbitrary hex values.
8. **No gradient text** unless DESIGN.md explicitly defines gradient text tokens.
9. **No glassmorphism as default** unless DESIGN.md defines glass tokens.
10. **No Inter font** unless DESIGN.md specifies Inter. Use whatever font DESIGN.md defines.

## Step 0: Project Discovery

Before any phase, discover the project's context:

```bash
# 1. Find repo root (walk up looking for CLAUDE.md or package.json or pyproject.toml)
REPO_ROOT=$(pwd)
while [ "$REPO_ROOT" != "/" ] && [ ! -f "$REPO_ROOT/CLAUDE.md" ] && [ ! -f "$REPO_ROOT/package.json" ] && [ ! -f "$REPO_ROOT/pyproject.toml" ]; do
  REPO_ROOT=$(dirname "$REPO_ROOT")
done
cd "$REPO_ROOT"
echo "Repo root: $REPO_ROOT"

# 2. Read DESIGN.md (required — this IS the design system)
cat DESIGN.md 2>/dev/null | head -100 || echo "WARNING: No DESIGN.md found"

# 3. Discover frontend framework
ls frontend/package.json 2>/dev/null && echo "Frontend: EXISTS" || echo "Frontend: EMPTY"

# 4. Discover backend API routes (what we're building for)
# For FastAPI:
ls backend/app/api/v1/ 2>/dev/null | grep -v __init__ | grep -v __pycache__
# For Express:
ls backend/routes/ 2>/dev/null
# For Django:
ls backend/*/urls.py 2>/dev/null
# For Go:
ls backend/*/handler*.go 2>/dev/null
# Generic fallback:
find backend/ -name "*.py" -path "*/routes/*" -o -name "*.py" -path "*/api/*" 2>/dev/null | head -20

# 5. Discover version/phase plans
ls .agents/plans/versions/ 2>/dev/null
cat .agents/plans/IMPLEMENTATION_STEPS.md 2>/dev/null | head -50

# 6. Check existing frontend state
ls frontend/src/ 2>/dev/null | head -10
find frontend/src -name 'page.tsx' 2>/dev/null | wc -l
```

Determine:
- Frontend exists? Yes/No (if No, scaffold from scratch)
- Current phase (count existing page.tsx files, compare to phase plan)
- Backend API domains (what features to build)
- Design system location (DESIGN.md)
- Version plan structure (what version numbering is used)

---

## Frontend Skill Chain (MANDATORY — execution order)

Every phase MUST invoke these skills in this order. No shortcuts. No skipping. Each skill adds a layer of quality that compounds.

### Pre-Implementation Skills (Before writing any code)

| Order | Skill | When | Purpose |
|-------|-------|------|---------|
| 1 | **`cortex-repo-discovery`** | Every run | Find repo root, set CWD |
| 2 | **Read `DESIGN.md`** | Every run | Load tokens, typography, colors, elevation |
| 3 | **Read `.claude/skills/design/SKILL.md`** | Every run | Load full phase plan |
| 4 | **`brainstorming`** | Phase 0, 3, 4, and any phase with significant design decisions | Explore approaches before committing. Ask clarifying questions. Present 2-3 options. Get user approval. |
| 5 | **`writing-plans`** | Each phase | Create bite-sized implementation plan with exact file paths, code, test commands. TDD when applicable. |
| 6 | **`ui-ux-pro-max`** | Phase 0, 1, 2, 5, 12 | Design intelligence — style selection, palette selection, font pairings, layout systems, UX guidelines. Use when designing pages, choosing color schemes, or making structural UI decisions. |

### Implementation Skills (During coding)

| Order | Skill | When | Purpose |
|-------|-------|------|---------|
| 7 | **`impeccable`** | All phases | Design quality enforcement — contrast, typography, layout, anti-slop rules. The general craft gate. |
| 8 | **`ui-styling`** | All phases | Tailwind CSS + shadcn/ui component creation. Use for building accessible components, responsive layouts, dark mode, design system tokens. |
| 9 | **`emil-design-eng`** | Phase 1, 2, 3, 4, 12 (any phase with interactive elements) | **Primary animation authority.** Emil Kowalski's philosophy — unseen details compound, motion must justify itself, taste is trained. For every animation decision: is this justified? Is frequency appropriate? Does easing feel right? |
| 10 | **`design-taste-frontend`** | All phases | Anti-slop guard. Catches gradient text, glassmorphism defaults, identical card grids, numbered sections, hero-metric templates. Continuous taste check during implementation. |
| 11 | **`ui-ux-pro-max`** | During component creation | Reference for component patterns, accessibility guidelines, interaction patterns. |

### Post-Implementation Skills (After code is written)

| Order | Skill | When | Purpose |
|-------|-------|------|---------|
| 12 | **`review-animations`** | After any phase with animations/motion | Brutal animation review against Emil Kowalski's 10 non-negotiable standards. Flags: `transition: all`, `scale(0)`, `ease-in` on UI, non-GPU properties, missing `prefers-reduced-motion`, wrong transform-origin, symmetric timing. Default is flagging — approval is earned. |
| 13 | **`impeccable polish`** | Phase 12 (final) | Final quality pass — contrast verification, motion decisions, responsive check, anti-slop checklist |
| 14 | **`cortex-system-validation`** | After each phase | Verify build passes |
| 15 | **`brainstorming`** | Phase 12 | Final design review — does the whole thing feel right? |

### Skill Quick Reference by Phase

| Phase | Pre-Implementation | Implementation | Post-Implementation |
|-------|-------------------|----------------|---------------------|
| **0: Foundation** | brainstorming, writing-plans, ui-ux-pro-max | impeccable, ui-styling | cortex-system-validation |
| **1: Auth + Layout** | brainstorming, writing-plans, ui-ux-pro-max | impeccable, ui-styling, emil-design-eng, design-taste-frontend | review-animations, cortex-system-validation |
| **2: Dashboard** | brainstorming, writing-plans, ui-ux-pro-max | impeccable, ui-styling, emil-design-eng, design-taste-frontend | review-animations, cortex-system-validation |
| **3: Chat** | brainstorming, writing-plans, ui-ux-pro-max | impeccable, ui-styling, emil-design-eng, design-taste-frontend | review-animations, cortex-system-validation |
| **4: Agents** | writing-plans, ui-ux-pro-max | impeccable, ui-styling, emil-design-eng, design-taste-frontend | review-animations, cortex-system-validation |
| **5: System + Settings** | writing-plans | impeccable, ui-styling, design-taste-frontend | cortex-system-validation |
| **6–11: Coming Soon** | writing-plans | impeccable, ui-styling | cortex-system-validation |
| **12: Polish** | brainstorming, writing-plans | impeccable, ui-styling, emil-design-eng, design-taste-frontend, ui-ux-pro-max | review-animations, impeccable polish, cortex-system-validation |

---

## Emil Kowalski Animation Principles (applied in Phases 1, 2, 3, 4, 12)

These are the animation rules from `emil-design-eng`. Every animation MUST pass these before shipping.

### The Ten Non-Negotiable Standards

1. **Justified motion.** Every animation must answer "why does this animate?" — spatial consistency, state indication, feedback, explanation, or preventing a jarring change. "It looks cool" on a frequently-seen element is a block.

2. **Frequency-appropriate.** Match motion to how often it's seen. Keyboard-initiated and 100+/day actions get **no** animation. Tens/day gets reduced motion. Occasional gets standard. Rare/first-time can have delight.

3. **Responsive easing.** Entering/exiting elements use `ease-out` or a strong custom curve. `ease-in` on UI is a block — it delays the moment the user watches most. Built-in CSS easings are too weak; expect custom cubic-beziers.

4. **Sub-300ms UI.** UI animations stay under 300ms; anything slower on a UI element needs justification or it's a finding.

5. **Origin & physical correctness.** Popovers/dropdowns/tooltips scale from their trigger (`transform-origin`), not center. Never animate from `scale(0)` — start from `scale(0.9–0.97)` + opacity. Modals are exempt — they stay centered.

6. **Interruptibility.** Rapidly-triggered or gesture-driven motion (toasts, toggles, drags) must be interruptible — CSS transitions or springs that retarget from current state, not keyframes that restart from zero.

7. **GPU-only properties.** Animate `transform` and `opacity` only. Animating `width`/`height`/`margin`/`padding`/`top`/`left` is a performance finding.

8. **Accessibility.** `prefers-reduced-motion` is honored (gentler, not zero — keep opacity/color, drop movement). Hover animations gated behind `@media (hover: hover) and (pointer: fine)`.

9. **Asymmetric enter/exit.** Deliberate actions (press, hold, destructive confirm) animate slower; system responses snap. Symmetric timing on a press-and-release is a finding.

10. **Cohesion.** Motion matches the component's personality and the rest of the product. Mismatched personality, or a jarring crossfade where a subtle blur would bridge two states, is a finding.

### Animation Budgets

| Element | Duration | Easing | Notes |
|---------|----------|--------|-------|
| Button hover | 150ms | ease-out | Background/color only |
| Button press | 80ms | ease-in-out | Scale 0.97–1.0, subtle |
| Dropdown/popover | 200ms | ease-out + custom curve | Scale from trigger origin |
| Modal enter | 250ms | ease-out | Center, scale 0.95→1 + opacity |
| Modal exit | 200ms | ease-in | Faster out than in |
| Toast enter | 250ms | ease-out | Slide from edge |
| Toast exit | 200ms | ease-in | Slide out |
| Page transition | 200–300ms | ease-out | Crossfade or slide |
| Skeleton pulse | 1.5s | ease-in-out infinite | Opacity 0.4→0.7 |
| Loading spinner | N/A | N/A | Pure rotation, no easing |
| Sidebar active | 200ms | ease-out | Background color transition |
| Card hover | 150ms | ease-out | Shadow + subtle lift (translateY) |

### Anti-Patterns (Block on Sight)

- `transition: all` — unbounded property animation
- `scale(0)` — appears from nowhere
- `ease-in` on any UI interaction — feels sluggish
- Animation on keyboard shortcut, command-palette toggle, or 100+/day action
- UI duration > 300ms with no stated reason
- `transform-origin: center` on a trigger-anchored element
- Keyframes on toasts, toggles, or anything rapidly triggered
- Animating layout properties (`width`/`height`/`margin`/`padding`/`top`/`left`)
- Missing `prefers-reduced-motion` handling on movement
- Ungated `:hover` motion
- Everything-at-once entrance where a 30–80ms stagger belongs

---

## Taste & Anti-Slop Rules (applied in ALL phases)

These come from `design-taste-frontend`, `ui-ux-pro-max`, and `impeccable`. They run continuously during implementation.

### Absolute Bans

- **Gradient text.** `background-clip: text` with a gradient. Decorative, never meaningful. Use a single solid color.
- **Glassmorphism as default.** Blurs and glass cards used decoratively. Rare and purposeful, or nothing.
- **Hero-metric template.** Big number, small label, supporting stats, gradient accent. SaaS cliché.
- **Identical card grids.** Same-sized cards with icon + heading + text, repeated endlessly.
- **Tiny uppercase tracked eyebrow above every section.** The 2023-era kicker — "ABOUT", "PROCESS", "PRICING" above each heading. One named kicker as a deliberate brand system is voice; an eyebrow on every section is AI grammar.
- **Numbered section markers as default scaffolding** (01 / 02 / 03). Numbers earn their place when the section actually IS a sequence.
- **Side-stripe borders.** `border-left` or `border-right` greater than 1px as colored accent. Never intentional.
- **Text overflow.** Long heading words + large clamp scales + narrow grids cause overflow. Test at every breakpoint.
- **Bounce/elastic animations.** No bounce, no elastic easing on UI elements.
- **Page-load choreography.** Don't gate content visibility on a class-triggered transition.

### Category-Reflex Check

Run at two altitudes:

1. **First-order:** If someone could guess the theme + palette from the category alone, it's the first training-data reflex. Rework until the answer isn't obvious from the domain.
2. **Second-order:** If someone could guess the aesthetic family from category-plus-anti-references, it's the trap one tier deeper. Rework until both answers are not obvious.

### Contrast & Readability

- Body text ≥4.5:1 contrast ratio against its background
- Large text (≥18px or bold ≥14px) ≥3:1
- Placeholder text needs the same 4.5:1
- Gray text on colored backgrounds → use darker shade of background's own hue
- Cap body line length at 65–75ch
- `text-wrap: balance` on h1–h3; `text-wrap: pretty` on long prose

---

## Phases

### Phase 0: Foundation (Scaffold)

**Goal:** Working Next.js project with design system, shared UI, proxy layer.

**Skills to invoke:** brainstorming, writing-plans, ui-ux-pro-max, impeccable, ui-styling

**Files to create:**
```
frontend/
├── package.json
├── next.config.ts
├── tsconfig.json
├── tailwind.config.ts
├── postcss.config.js
├── src/
│   ├── app/
│   │   ├── layout.tsx              # Root layout, font from DESIGN.md, dark bg
│   │   ├── globals.css             # Tailwind directives + design tokens
│   │   ├── page.tsx                # Redirect to main page
│   │   └── loading.tsx
│   ├── shared/
│   │   ├── design/
│   │   │   └── tokens.ts           # DESIGN.md tokens as TS constants
│   │   ├── ui/
│   │   │   ├── Button.tsx          # Animated hover/press per Emil's budgets
│   │   │   ├── Card.tsx            # Subtle lift on hover
│   │   │   ├── Input.tsx           # Focus state transitions
│   │   │   ├── Badge.tsx
│   │   │   ├── Skeleton.tsx        # Pulse animation per budget
│   │   │   ├── EmptyState.tsx
│   │   │   ├── StatusDot.tsx       # Gentle pulse for active status
│   │   │   ├── Dropdown.tsx        # Scale from trigger, 200ms ease-out
│   │   │   ├── Modal.tsx           # Center scale 0.95→1, 250ms ease-out
│   │   │   ├── Toast.tsx           # Interruptible slide, 250ms ease-out
│   │   │   └── Tooltip.tsx         # Scale from trigger, 150ms ease-out
│   │   ├── layout/
│   │   │   ├── AppShell.tsx        # Sidebar + header + content area
│   │   │   ├── Sidebar.tsx         # Active state: 200ms ease-out bg
│   │   │   ├── Header.tsx
│   │   │   └── MobileNav.tsx       # Bottom tabs, active indicator animation
│   │   ├── auth/
│   │   │   └── AuthProvider.tsx     # JWT context, auto-refresh
│   │   ├── api/
│   │   │   └── client.ts           # fetch wrapper with CSRF, auth
│   │   └── types/
│   │       └── index.ts            # Shared TypeScript types
│   └── features/
│       └── (empty — populated in later phases)
```

**Key decisions:**
- `cn()` utility for class merging (clsx + tailwind-merge)
- `api` client with automatic JWT refresh on 401
- AuthProvider bootstraps via `GET /me` (or project's auth endpoint)
- Proxy: Next.js API route → backend (same-origin, no CORS)
- Tailwind config extends DESIGN.md tokens directly
- Read the project's actual font from DESIGN.md (don't assume Geist)
- ALL animations follow Emil Kowalski budgets from the start
- `prefers-reduced-motion` built into every animated component from Day 1

### Phase 1: Auth + Layout Shell

**Goal:** Working login/register, app shell with sidebar navigation.

**Skills to invoke:** brainstorming, writing-plans, ui-ux-pro-max, impeccable, ui-styling, emil-design-eng, design-taste-frontend

**Discovery before implementation:**
```bash
grep -r "login\|register\|auth\|/me" backend/app/api/ 2>/dev/null | head -10
grep -r "users\|profile\|/me" backend/app/api/ 2>/dev/null | head -10
```

**Files:**
```
frontend/src/app/auth/
├── page.tsx                    # Login form — subtle focus transitions
├── register/page.tsx           # Register form
└── layout.tsx                  # Auth layout (centered, no sidebar)

frontend/src/shared/layout/
├── AppShell.tsx                # Full shell: sidebar + header + content
├── Sidebar.tsx                 # Nav items with active indicator animation
├── Header.tsx                  # User menu, breadcrumbs
└── MobileNav.tsx               # Bottom tabs for mobile
```

**Animation decisions (invoke `emil-design-eng`):**
- Sidebar active indicator: 200ms ease-out background transition
- Form focus states: 150ms ease-out border/glow
- Page transition between auth pages: 200ms crossfade
- Button hover: 150ms ease-out background
- Button press: 80ms ease-in-out scale 0.97→1
- NO page-load choreography on auth page

### Phase 2: Main Dashboard

**Goal:** Main dashboard with system overview, quick actions, recent activity.

**Skills to invoke:** brainstorming, writing-plans, ui-ux-pro-max, impeccable, ui-styling, emil-design-eng, design-taste-frontend

**Discovery before implementation:**
```bash
grep -r "health\|status\|system\|metrics" backend/app/api/ 2>/dev/null | head -10
grep -r "conversations\|agents\|recent\|activity" backend/app/api/ 2>/dev/null | head -10
```

**Files:**
```
frontend/src/features/dashboard/
├── page.tsx                    # Dashboard page
├── components/
│   ├── SystemOverview.tsx      # Health cards — status dot pulse for healthy
│   ├── QuickActions.tsx        # Action buttons — hover/press per Emil budgets
│   ├── RecentActivity.tsx      # Activity list — staggered entrance 30-80ms
│   └── MetricsRow.tsx          # Key stats — number count-up on mount (rare, OK)
```

**Animation decisions (invoke `emil-design-eng`):**
- Staggered list entrance: 30–80ms delay between items, ease-out, only on first load
- Status dot pulse: gentle opacity pulse for "healthy" state, 1.5s ease-in-out infinite
- Card hover: 150ms ease-out shadow + translateY(1-2px) — NOT a big lift
- Metric numbers: count-up animation on mount is OK (rare, first-time)
- NO bounce, no elastic, no page-load choreography
- `prefers-reduced-motion`: skip stagger, keep opacity transitions

### Phase 3: Chat / Conversations

**Goal:** Full chat interface with streaming, model selection, conversation management.

**Skills to invoke:** brainstorming, writing-plans, ui-ux-pro-max, impeccable, ui-styling, emil-design-eng, design-taste-frontend

**Discovery before implementation:**
```bash
grep -r "conversations\|chat\|messages" backend/app/api/ 2>/dev/null | head -10
grep -r "models\|llm\|providers" backend/app/api/ 2>/dev/null | head -10
```

**Files:**
```
frontend/src/features/chat/
├── page.tsx                    # Chat page
├── components/
│   ├── ConversationList.tsx    # Sidebar list — active state 200ms ease-out
│   ├── MessageArea.tsx         # Message display with markdown
│   ├── ChatInput.tsx           # Input with model selector
│   ├── MessageBubble.tsx       # Individual message — enter 200ms ease-out
│   ├── StreamingIndicator.tsx  # Live typing indicator — subtle pulse
│   └── ModelSelector.tsx       # Dropdown — scale from trigger origin
```

**SSE pattern:** `ReadableStream` line-by-line parsing. Events: `chunk`, `done`, `error`.

**Animation decisions (invoke `emil-design-eng`):**
- New message entrance: 200ms ease-out, slide up + opacity (NOT from scale(0))
- Streaming cursor: subtle blink, 1s infinite — NOT a spinning loader
- Conversation list active: 200ms ease-out background transition
- Model dropdown: 200ms ease-out, scale from trigger origin (NOT center)
- Send button: 80ms press scale, 150ms hover background
- Keyboard shortcut (Cmd+Enter): NO animation — fires instantly
- `prefers-reduced-motion`: messages appear instantly, no slide

### Phase 4: Agents

**Goal:** Agent management, agent chat, agent run history.

**Skills to invoke:** writing-plans, ui-ux-pro-max, impeccable, ui-styling, emil-design-eng, design-taste-frontend

**Discovery before implementation:**
```bash
grep -r "agents\|runs\|tasks" backend/app/api/ 2>/dev/null | head -10
```

**Files:**
```
frontend/src/features/agents/
├── page.tsx                    # Agent list
├── [id]/
│   └── page.tsx                # Agent detail + chat
├── components/
│   ├── AgentCard.tsx           # Agent summary card — hover lift
│   ├── AgentChat.tsx           # Chat with specific agent
│   ├── AgentRuns.tsx           # Run history — staggered list
│   └── AgentConfig.tsx         # Agent configuration
```

**Animation decisions (invoke `emil-design-eng`):**
- Agent card hover: 150ms ease-out shadow + translateY(1-2px)
- Run history list: staggered entrance 30-80ms on first load
- Agent status transitions: 200ms ease-out color change
- `prefers-reduced-motion`: instant state changes, no stagger

### Phase 5: System + Settings

**Goal:** System monitoring, user settings, profile management.

**Skills to invoke:** writing-plans, impeccable, ui-styling, design-taste-frontend

**Discovery before implementation:**
```bash
grep -r "system\|awareness\|device\|health" backend/app/api/ 2>/dev/null | head -10
grep -r "users\|settings\|profile" backend/app/api/ 2>/dev/null | head -10
```

**Files:**
```
frontend/src/features/system/
├── page.tsx                    # System overview
├── components/
│   ├── HealthDashboard.tsx     # Service health grid — status dots pulse
│   ├── HardwareInfo.tsx        # Hardware info
│   └── Logs.tsx                # System logs viewer

frontend/src/features/settings/
├── page.tsx                    # Settings page
├── components/
│   ├── ProfileSection.tsx      # User profile
│   ├── SecuritySection.tsx     # Password, 2FA
│   ├── AppearanceSection.tsx   # Theme settings
│   └── NotificationSection.tsx # Notification prefs
```

### Phase 6–11: Future Features (Coming Soon)

**Goal:** Create placeholder pages for features not yet implemented.

**Skills to invoke:** writing-plans, impeccable, ui-styling

**Discovery:**
```bash
cat .agents/plans/versions/*/progress.md 2>/dev/null | grep -A2 "Completed\|Not started"
ls frontend/src/features/ 2>/dev/null
```

### Phase 12: Polish

**Goal:** Final quality pass — EVERY skill runs here.

**Skills to invoke:** ALL of them — brainstorming, writing-plans, ui-ux-pro-max, impeccable, ui-styling, emil-design-eng, design-taste-frontend, review-animations, impeccable polish

**Checks:**
- [ ] `npm run build` passes clean
- [ ] All pages render without errors
- [ ] Responsive: desktop sidebar, tablet overlay, mobile bottom tabs
- [ ] Keyboard navigation works
- [ ] Focus states visible on all interactive elements
- [ ] Loading skeletons on all data-fetching pages
- [ ] Error boundaries on feature modules
- [ ] Token-correct Tailwind classes (read from DESIGN.md)
- [ ] No hardcoded colors
- [ ] `100dvh` not `100vh` for viewport heights
- [ ] **Every animation passes Emil's 10 non-negotiable standards**
- [ ] **`prefers-reduced-motion` on ALL animations**
- [ ] **No `transition: all` anywhere**
- [ ] **No `scale(0)` anywhere**
- [ ] **No `ease-in` on any UI interaction**
- [ ] **No layout property animations** (`width`, `height`, `margin`, `padding`)
- [ ] **All dropdowns/popovers scale from trigger origin, not center**
- [ ] **Interruptible motion on toasts and toggles**
- [ ] **GPU-only animation properties** (transform + opacity only)
- [ ] **Contrast ≥4.5:1 on all body text**
- [ ] **No anti-slop patterns** (gradient text, glassmorphism default, identical cards, eyebrows, numbered sections, side-stripe borders)
- [ ] **Stagger on first-load lists** (30–80ms), not on high-frequency actions

---

## ComingSoon Component Template

Every Coming Soon page uses this pattern (adapt icons/titles to match the project):

```tsx
"use client";

import { type ReactNode } from "react";
import { cn } from "@/lib/utils";

interface ComingSoonProps {
  icon: ReactNode;
  title: string;
  description: string;
  version?: string;
}

export function ComingSoon({ icon, title, description, version }: ComingSoonProps) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] px-6 text-center">
      <div className="mb-6 text-text-muted opacity-40">{icon}</div>
      <h1 className="text-headline font-semibold text-text-primary mb-3">{title}</h1>
      <p className="text-body text-text-secondary max-w-md mb-4">{description}</p>
      {version && (
        <span className="inline-flex items-center gap-1.5 font-mono text-label px-3 py-1 rounded-full bg-accent/10 text-accent border border-accent/20">
          {version}
        </span>
      )}
    </div>
  );
}
```

**Note:** The token names above are from the original project's DESIGN.md. When using this skill in a different project, **read the actual DESIGN.md** and use its token names.

## Token Mapping

Read the project's DESIGN.md and create a mapping table. The general rule:

| DESIGN.md Token | Tailwind Class | Common Mistake |
|-----------------|---------------|----------------|
| `<name>` (#hex) | `text-<name>` or `bg-<name>` | Don't prefix with `text-text-` unless the token itself is named `text-primary` etc. |
| `<name>` with Tailwind collision | `text-token-<name>` | Avoid `text-primary` if it collides with Tailwind's `primary` utility |

**Critical:** If DESIGN.md defines `text-primary`, `text-secondary`, `text-muted` as named tokens, the Tailwind classes become `text-text-primary`, `text-text-secondary`, `text-text-muted` to avoid collision with Tailwind's built-in `text-primary` utility.

---

## Build Verification

After each phase:
```bash
cd frontend && npm run build
```

If build fails: fix immediately before proceeding to next phase.

## Completion

After all phases:
1. Full build verification
2. Run `impeccable polish` for final quality pass
3. Run `review-animations` on all animated components
4. Commit with descriptive message
5. Report: phases completed, files created, build status
