---
description: "Full frontend rebuild from scratch — scaffold, auth, layout, all version features, polish. Iterative loop until build passes and all core capabilities covered."
---

# /project:design — Frontend From Scratch

Rebuilds the entire frontend iteratively. Each phase produces a working, buildable state. Loops until all core capabilities covered and `npm run build` passes clean.

**Works for any project** — discovers DESIGN.md, API routes, and version plans dynamically. Not hardcoded to any specific project.

## ARGUMENTS

`$ARGUMENTS` — Optional: specific phase number to start from (e.g., `3`), or `resume` to continue from last built phase, or empty to start from Phase 0.

## Execution Flow

### Step 0: Discovery + State Assessment

```bash
# Find repo root (walk up looking for CLAUDE.md or package.json or pyproject.toml)
REPO_ROOT=$(pwd)
while [ "$REPO_ROOT" != "/" ] && [ ! -f "$REPO_ROOT/CLAUDE.md" ] && [ ! -f "$REPO_ROOT/package.json" ] && [ ! -f "$REPO_ROOT/pyproject.toml" ]; do
  REPO_ROOT=$(dirname "$REPO_ROOT")
done
cd "$REPO_ROOT"
echo "Repo root: $REPO_ROOT"

# Check frontend state
ls frontend/package.json 2>/dev/null && echo "EXISTS" || echo "EMPTY"
ls frontend/src/ 2>/dev/null | head -5
find frontend/src -name 'page.tsx' 2>/dev/null | wc -l

# Discover backend API routes (what we're building for)
# FastAPI:
ls backend/app/api/v1/ 2>/dev/null | grep -v __init__ | grep -v __pycache__
# Express:
ls backend/routes/ 2>/dev/null
# Django:
ls backend/*/urls.py 2>/dev/null
# Go:
ls backend/*/handler*.go 2>/dev/null

# Read design system
cat DESIGN.md 2>/dev/null | head -50
```

Determine:
- Frontend exists? Yes/No
- Current phase (count existing page.tsx files, compare to phase plan)
- Backend API domains (what features to build)

### Step 1: Skill Chain Setup

Load these skills IN ORDER before any implementation:

1. **`cortex-repo-discovery`** — find root, set CWD
2. **Read `DESIGN.md`** — load all tokens, typography, elevation, components
3. **Read `.claude/skills/design/SKILL.md`** — load full phase plan with animation budgets and anti-slop rules
4. **`brainstorming`** — if significant design decisions needed for current phase
5. **`writing-plans`** — create implementation plan for current phase
6. **`ui-ux-pro-max`** — design intelligence, style selection, palette, font pairings, layout systems, UX guidelines
7. **`impeccable`** — enforce design quality during implementation — contrast, typography, layout, craft
8. **`ui-styling`** — Tailwind CSS + shadcn/ui component creation, accessible components, responsive layouts
9. **`emil-design-eng`** — **primary animation authority** — every animation decision goes through Emil's philosophy and budgets
10. **`design-taste-frontend`** — anti-slop guard — catches gradient text, glassmorphism, identical cards, eyebrows, numbered sections

### Step 2: Dependency Check

```bash
# Check Node.js
node --version 2>/dev/null || echo "MISSING: Node.js"

# Check npm
npm --version 2>/dev/null || echo "MISSING: npm"

# Check if frontend dir has package.json
cat frontend/package.json 2>/dev/null | head -5 || echo "NO PACKAGE.JSON"

# Check backend is running (for API proxy)
# Detect port from project config
BACKEND_PORT=$(grep -o 'PORT=[0-9]*' .env 2>/dev/null | head -1 | cut -d= -f2 || echo "8000")
curl -s http://localhost:${BACKEND_PORT}/api/v1/health 2>/dev/null | head -1 || echo "BACKEND NOT RUNNING"
```

If dependencies missing: install them. If backend not running: note it (frontend still builds, API calls fail gracefully).

### Step 3: Phase Execution Loop

```
FOR each phase from START_PHASE to 12:
  1. Read phase definition from .claude/skills/design/SKILL.md
  2. Invoke skill chain for this phase (see skill matrix in SKILL.md)
  3. Create all files for this phase
  4. Run: cd frontend && npm run build
  5. If build fails: fix errors, re-run build
  6. Run review-animations if phase has motion (Phase 1, 2, 3, 4, 12)
  7. Commit: "feat(frontend): Phase N — [phase name]"
  8. Report: files created, build status
  9. Continue to next phase
END FOR
```

### Step 4: Final Validation

After all phases complete:

```bash
# Full build
cd frontend && npm run build

# Type check (if tsconfig has strict)
npx tsc --noEmit 2>/dev/null

# Check for forbidden patterns (use the actual token names from DESIGN.md)
grep -rn 'font-inter\|text-primary\|text-secondary\|text-muted\|bg-surface\|bg-elevated\|rounded-xl\|100vh\|transition: all\|scale(0)\|ease-in' frontend/src/ --include='*.tsx' --include='*.ts' 2>/dev/null | grep -v node_modules | grep -v '.next'

# Check for missing prefers-reduced-motion on animated elements
grep -rn 'transition-\|animate-' frontend/src/ --include='*.tsx' 2>/dev/null | grep -v 'reduced-motion' | grep -v node_modules
```

### Step 5: Polish Pass

Run ALL of these in sequence:

1. **`/impeccable polish`** — contrast verification, motion decisions, responsive check, anti-slop checklist
2. **`review-animations`** — brutal review against Emil's 10 non-negotiable standards. Flags `transition: all`, `scale(0)`, `ease-in`, non-GPU properties, missing reduced-motion, wrong transform-origin, symmetric timing. Default is flagging — approval is earned.
3. Fix any findings from either review
4. Re-run build to confirm clean

### Step 6: Report

Output final status:

```
## Design Complete

### Phases Executed: 0–12
### Files Created: N
### Build Status: PASS/FAIL
### Frontend URL: http://localhost:3000

### Pages Built:
[List all pages from phase plan, mark implemented vs Coming Soon]

### Animation Review: PASS/FAIL
[Number of findings from review-animations, fixed/blocked]

### Taste Review: PASS/FAIL
[Number of anti-slop findings, fixed/blocked]

### Next Steps:
1. cd frontend && npm run dev
2. Open http://localhost:3000
3. Test auth flow
4. Test chat with streaming
5. Verify all Coming Soon pages render
```

## Error Recovery

If any phase fails:
1. Read the error output
2. Fix the root cause (not the symptom)
3. Re-run build
4. Max 3 fix attempts per issue, then escalate to user

## Phase Quick Reference

| Phase | Name | What It Builds | Key Skills |
|-------|------|----------------|------------|
| 0 | Foundation | Scaffold, design system, shared UI | brainstorming, ui-ux-pro-max, impeccable, ui-styling |
| 1 | Auth + Layout | Login, register, app shell, sidebar | brainstorming, emil-design-eng, design-taste-frontend |
| 2 | Main Dashboard | System overview, quick actions, metrics | brainstorming, emil-design-eng, design-taste-frontend |
| 3 | Chat | Conversations, streaming, model selection | brainstorming, emil-design-eng, design-taste-frontend |
| 4 | Agents | Agent management, chat, run history | emil-design-eng, design-taste-frontend |
| 5 | System + Settings | Health monitoring, user settings | impeccable, ui-styling, design-taste-frontend |
| 6–11 | Future Features | Coming Soon placeholders | impeccable, ui-styling |
| 12 | Polish | Animations, a11y, responsive, final validation | ALL skills |

## Arguments Handling

- **Empty or `all`**: Run all phases 0–12
- **Number** (e.g., `3`): Start from that phase, run to completion
- **`resume`**: Detect current state, continue from next unbuilt phase
- **`phase N`**: Run only that specific phase
- **`validate`**: Skip implementation, just run build + lint + checks
- **`polish`**: Run only Phase 12 (polish pass)

## Skills Used (Complete List)

| Skill | Category | When | Purpose |
|-------|----------|------|---------|
| `cortex-repo-discovery` | Setup | Every run | Find repo root, set CWD |
| `brainstorming` | Planning | Phase 0, 1, 2, 3, 12 | Explore approaches, ask clarifying questions, present 2-3 options, get user approval before coding |
| `writing-plans` | Planning | Each phase | Bite-sized implementation plan with exact file paths, code, test commands, TDD when applicable |
| `ui-ux-pro-max` | Design | Phase 0, 1, 2, 5, 12 | Design intelligence — 67 styles, 161 palettes, 57 font pairings, UX guidelines, component patterns |
| `impeccable` | Craft | All phases | Design quality enforcement — contrast, typography, layout, anti-slop, production-grade code |
| `ui-styling` | Implementation | All phases | Tailwind CSS + shadcn/ui — accessible components, responsive layouts, dark mode, design system tokens |
| `emil-design-eng` | Animation | Phase 1, 2, 3, 4, 12 | **Primary animation authority** — Emil Kowalski's philosophy. Every animation must justify itself. 10 non-negotiable standards. Duration budgets. Anti-patterns. |
| `design-taste-frontend` | Taste | All phases | Anti-slop guard — catches gradient text, glassmorphism, identical cards, eyebrows, numbered sections, side-stripe borders |
| `review-animations` | Review | After any phase with motion | Brutal animation review against Emil's standards. Default to flagging. Approval is earned, not assumed. |
| `impeccable polish` | Polish | Phase 12 | Final quality pass — contrast, motion, responsive, anti-slop checklist |

## Animation Decision Flow

When building any interactive element, follow this flow:

```
Element needs animation?
    ↓
YES → What is the purpose? (spatial, state, feedback, explanation)
    ↓
Purpose justified? → NO → Don't animate. Done.
    ↓
YES → How often is this element seen?
    ↓
100+/day → No animation or minimal (opacity only)
Tens/day → Reduced motion (shorter, smaller)
Occasional → Standard (per Emil budgets)
Rare/first-time → Can have delight
    ↓
What properties to animate?
    ↓
ONLY transform + opacity. Never width/height/margin/padding.
    ↓
What easing?
    ↓
Enter: ease-out or custom curve. NEVER ease-in.
Exit: ease-in (faster out than in for deliberate actions)
    ↓
What duration?
    ↓
UI elements: <300ms. Per-element budgets in SKILL.md.
    ↓
Transform-origin correct?
    ↓
Dropdowns/popovers/tooltips: from trigger, NOT center.
Modals: center is OK.
    ↓
prefers-reduced-motion handled?
    ↓
YES → Ship it. Run review-animations after.
```

---

## Feedback Loop

**On entry:** Read `.claude/ecosystem/feedback.json`, filter last 10 entries where `command` matches this command name. If learnings exist, adapt behavior accordingly.

**On exit:** Append entry to `.claude/ecosystem/feedback.json`:
```json
{
  "timestamp": "<ISO-8601>",
  "command": "/project:design",
  "run_id": "<uuid>",
  "outcome": "success|failure|partial",
  "learnings": ["<what was discovered>"],
  "suggestions": ["<improvements for next run>"],
  "duration_ms": 0
}
```
