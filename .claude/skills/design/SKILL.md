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

## Skill Chain (execution order)

Each phase invokes skills in this order:

### Phase N start:
1. `cortex-repo-discovery` — find root, set CWD
2. Read `DESIGN.md` — load tokens, typography, colors, elevation
3. Read this skill's phase definition below
4. `brainstorming` (if significant design decisions in this phase)
5. `writing-plans` — create implementation plan for this phase
6. `impeccable` — enforce design quality during implementation
7. `emil-design-eng` — animation decisions for interactive elements
8. `design-taste-frontend` — anti-slop guard
9. Implement phase tasks
10. Build verification — `npm run build`
11. Commit phase

## Phases

### Phase 0: Foundation (Scaffold)

**Goal:** Working Next.js project with design system, shared UI, proxy layer.

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
│   │   │   ├── Button.tsx
│   │   │   ├── Card.tsx
│   │   │   ├── Input.tsx
│   │   │   ├── Badge.tsx
│   │   │   ├── Skeleton.tsx
│   │   │   ├── EmptyState.tsx
│   │   │   ├── StatusDot.tsx
│   │   │   ├── Dropdown.tsx
│   │   │   ├── Modal.tsx
│   │   │   ├── Toast.tsx
│   │   │   └── Tooltip.tsx
│   │   ├── layout/
│   │   │   ├── AppShell.tsx        # Sidebar + header + content area
│   │   │   ├── Sidebar.tsx
│   │   │   ├── Header.tsx
│   │   │   └── MobileNav.tsx
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

### Phase 1: Auth + Layout Shell

**Goal:** Working login/register, app shell with sidebar navigation.

**Discovery before implementation:**
```bash
# Find auth routes in backend
grep -r "login\|register\|auth\|/me" backend/app/api/ 2>/dev/null | head -10

# Find user/profile routes
grep -r "users\|profile\|/me" backend/app/api/ 2>/dev/null | head -10
```

**Files:**
```
frontend/src/app/auth/
├── page.tsx                    # Login form
├── register/page.tsx           # Register form
└── layout.tsx                  # Auth layout (centered, no sidebar)

frontend/src/shared/layout/
├── AppShell.tsx                # Full shell: sidebar + header + content
├── Sidebar.tsx                 # Nav items with icons, active state
├── Header.tsx                  # User menu, breadcrumbs
└── MobileNav.tsx               # Bottom tabs for mobile
```

**Nav items:** Discover from backend API routes and version plans. Each discovered domain gets a nav item.

### Phase 2: Main Dashboard

**Goal:** Main dashboard with system overview, quick actions, recent activity.

**Discovery before implementation:**
```bash
# Find health/status endpoints
grep -r "health\|status\|system\|metrics" backend/app/api/ 2>/dev/null | head -10

# Find dashboard-relevant endpoints
grep -r "conversations\|agents\|recent\|activity" backend/app/api/ 2>/dev/null | head -10
```

**Files:**
```
frontend/src/features/dashboard/
├── page.tsx                    # Dashboard page
├── components/
│   ├── SystemOverview.tsx      # Health cards
│   ├── QuickActions.tsx        # Quick action buttons
│   ├── RecentActivity.tsx      # Latest activity
│   └── MetricsRow.tsx          # Key stats
```

### Phase 3: Chat / Conversations

**Goal:** Full chat interface with streaming, model selection, conversation management.

**Discovery before implementation:**
```bash
# Find conversation/chat endpoints
grep -r "conversations\|chat\|messages" backend/app/api/ 2>/dev/null | head -10

# Find model endpoints
grep -r "models\|llm\|providers" backend/app/api/ 2>/dev/null | head -10
```

**Files:**
```
frontend/src/features/chat/
├── page.tsx                    # Chat page
├── components/
│   ├── ConversationList.tsx    # Sidebar list of conversations
│   ├── MessageArea.tsx         # Message display with markdown
│   ├── ChatInput.tsx           # Input with model selector
│   ├── MessageBubble.tsx       # Individual message
│   ├── StreamingIndicator.tsx  # Live typing indicator
│   └── ModelSelector.tsx       # Dropdown for model selection
```

**SSE pattern:** `ReadableStream` line-by-line parsing. Events: `chunk`, `done`, `error`.

### Phase 4: Agents

**Goal:** Agent management, agent chat, agent run history.

**Discovery before implementation:**
```bash
# Find agent endpoints
grep -r "agents\|runs\|tasks" backend/app/api/ 2>/dev/null | head -10
```

**Files:**
```
frontend/src/features/agents/
├── page.tsx                    # Agent list
├── [id]/
│   └── page.tsx                # Agent detail + chat
├── components/
│   ├── AgentCard.tsx           # Agent summary card
│   ├── AgentChat.tsx           # Chat with specific agent
│   ├── AgentRuns.tsx           # Run history
│   └── AgentConfig.tsx         # Agent configuration
```

### Phase 5: System + Settings

**Goal:** System monitoring, user settings, profile management.

**Discovery before implementation:**
```bash
# Find system/awareness endpoints
grep -r "system\|awareness\|device\|health" backend/app/api/ 2>/dev/null | head -10

# Find user/settings endpoints
grep -r "users\|settings\|profile" backend/app/api/ 2>/dev/null | head -10
```

**Files:**
```
frontend/src/features/system/
├── page.tsx                    # System overview
├── components/
│   ├── HealthDashboard.tsx     # Service health grid
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

**Goal:** Create placeholder pages for features not yet implemented in the current version.

**Discovery:** Check version plans and progress tracking to determine which features are implemented vs. future.

```bash
# Check version plans
cat .agents/plans/versions/*/progress.md 2>/dev/null | grep -A2 "Completed\|Not started"

# Check existing feature directories
ls frontend/src/features/ 2>/dev/null
```

For each discovered future feature, create:
```
frontend/src/features/<feature>/
├── page.tsx                    # Coming Soon page
```

### Phase 12: Polish

**Goal:** Final quality pass — animations, a11y, responsive, performance.

**Checks:**
- [ ] `npm run build` passes clean
- [ ] All pages render without errors
- [ ] Responsive: desktop sidebar, tablet overlay, mobile bottom tabs
- [ ] Keyboard navigation works
- [ ] Focus states visible
- [ ] Loading skeletons on all data-fetching pages
- [ ] Error boundaries on feature modules
- [ ] Token-correct Tailwind classes (read from DESIGN.md, not assumed)
- [ ] No hardcoded colors (use DESIGN.md tokens)
- [ ] `100dvh` not `100vh` for viewport heights
- [ ] Motion: 200ms default, spring for micro-interactions
- [ ] `prefers-reduced-motion` on all animations

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

**Note:** The token names above (`text-text-muted`, `text-text-primary`, etc.) are from the original project's DESIGN.md. When using this skill in a different project, **read the actual DESIGN.md** and use its token names. The Tailwind prefix rule still applies: if DESIGN.md defines a token called `primary`, Tailwind needs `text-primary` — no prefix needed unless there's a collision with Tailwind's built-in classes.

## Token Mapping

Read the project's DESIGN.md and create a mapping table. The general rule:

| DESIGN.md Token | Tailwind Class | Common Mistake |
|-----------------|---------------|----------------|
| `<name>` (#hex) | `text-<name>` or `bg-<name>` | Don't prefix with `text-text-` unless the token itself is named `text-primary` etc. |
| `<name>` with Tailwind collision | `text-token-<name>` | Avoid `text-primary` if it collides with Tailwind's `primary` utility |

**Critical:** If DESIGN.md defines `text-primary`, `text-secondary`, `text-muted` as named tokens, the Tailwind classes become `text-text-primary`, `text-text-secondary`, `text-text-muted` to avoid collision with Tailwind's built-in `text-primary` utility. Check for collisions before coding.

## Anti-Slop Checklist

Before completing, verify:
- [ ] No gradient text (`background-clip: text`) unless DESIGN.md defines it
- [ ] No glassmorphism cards as default unless DESIGN.md defines glass tokens
- [ ] No tiny uppercase tracked eyebrow on every section
- [ ] No numbered section markers (01/02/03) as scaffolding
- [ ] No hero-metric template (big number + small label + gradient accent)
- [ ] No identical card grids
- [ ] No side-stripe borders
- [ ] No bounce/elastic animations
- [ ] No page-load choreography
- [ ] Accent color ≤10% of surface area
- [ ] Body text ≥4.5:1 contrast ratio
- [ ] Line length capped at 65ch for prose

## Build Verification

After each phase:
```bash
cd frontend && npm run build
```

If build fails: fix immediately before proceeding to next phase.

## Completion

After all phases:
1. Full build verification
2. Run `impeccable polish` for final quality pass (if available)
3. Commit with descriptive message
4. Report: phases completed, files created, build status
