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
3. **Read `.claude/skills/design/SKILL.md`** — load full phase plan
4. **`brainstorming`** — if significant design decisions needed for current phase
5. **`writing-plans`** — create implementation plan for current phase
6. **`impeccable`** — enforce design quality during implementation
7. **`emil-design-eng`** — animation decisions for interactive elements
8. **`design-taste-frontend`** — anti-slop guard
9. **`frontend-design`** — grounding in subject matter

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
  2. Create all files for this phase
  3. Run: cd frontend && npm run build
  4. If build fails: fix errors, re-run build
  5. Commit: "feat(frontend): Phase N — [phase name]"
  6. Report: files created, build status
  7. Continue to next phase
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
# The grep below uses generic patterns — adjust for your project's tokens
grep -rn 'font-inter\|text-primary\|text-secondary\|text-muted\|bg-surface\|bg-elevated\|rounded-xl\|100vh' frontend/src/ --include='*.tsx' --include='*.ts' 2>/dev/null | grep -v node_modules | grep -v '.next'
```

### Step 5: Polish Pass

Run `/impeccable polish` for final quality:
- Contrast verification
- Motion decisions
- Responsive check
- Anti-slop checklist

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

| Phase | Name | What It Builds |
|-------|------|----------------|
| 0 | Foundation | Scaffold, design system, shared UI |
| 1 | Auth + Layout | Login, register, app shell, sidebar |
| 2 | Main Dashboard | System overview, quick actions, metrics |
| 3 | Chat | Conversations, streaming, model selection |
| 4 | Agents | Agent management, chat, run history |
| 5 | System + Settings | Health monitoring, user settings |
| 6–11 | Future Features | Coming Soon placeholders |
| 12 | Polish | Animations, a11y, responsive, final validation |

## Arguments Handling

- **Empty or `all`**: Run all phases 0–12
- **Number** (e.g., `3`): Start from that phase, run to completion
- **`resume`**: Detect current state, continue from next unbuilt phase
- **`phase N`**: Run only that specific phase
- **`validate`**: Skip implementation, just run build + lint + checks
- **`polish`**: Run only Phase 12 (polish pass)

## Skills Used

| Skill | When | Purpose |
|-------|------|---------|
| `cortex-repo-discovery` | Every run | Find repo root |
| `brainstorming` | Phase 0, 3 | Design decisions for layout, chat UX |
| `writing-plans` | Each phase | Create implementation plan |
| `impeccable` | During implementation | Design quality enforcement |
| `emil-design-eng` | Phase 3, 4 | Animation decisions for chat, agents |
| `design-taste-frontend` | All phases | Anti-slop guard |
| `frontend-design` | Phase 0, 1 | Ground design in subject |
