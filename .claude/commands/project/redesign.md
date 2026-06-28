# /project:redesign — Frontend Redesign

Redesigns the CORTEX frontend using the Impeccable design system + supporting frontend skills. Two modes: **scoped** (given a direction) or **full** (bare command, runs all 8 phases).

## Modes

**Full:** `/project:redesign` — all 8 phases, all Impeccable commands + supporting skills.
**Scoped:** `/project:redesign <direction>` — only relevant phases/commands for that area.

---

## Execution

### Step 0: Setup

```bash
find_repo_root() {
    local dir="${1:-$(pwd)}"
    while [ "$dir" != "/" ]; do
        if [ -f "$dir/CLAUDE.md" ]; then echo "$dir"; return 0; fi
        dir=$(dirname "$dir")
    done
    echo "ERROR: No Cortex repo root found"
    return 1
}
ROOT=$(find_repo_root) && cd "$ROOT"

# Setup Impeccable context
node ~/.claude/skills/impeccable/scripts/context.mjs --target frontend/src/
```

If `NO_PRODUCT_MD` → run `/impeccable init` first.

### Step 1: Determine Mode

- **Direction provided** → Scoped. Route to relevant phases (see routing table in Step 4).
- **No direction** → Full. Run all 8 phases sequentially.

---

## Full Mode — 8 Phases

### PHASE 1: DIAGNOSE

> Know what we're fixing. Freeze current state before changing it.

**Commands:**
1. `/impeccable document` — Scan frontend, capture current visual system into DESIGN.md
2. `/impeccable critique` — Two-assessment UX review (Assessment A: design director, Assessment B: automated detectors)

**Skills:**
- `ui-ux-pro-max` — Read for design intelligence database (50+ styles, 161 palettes) to inform critique

**Output:** DESIGN.md baseline + `.impeccable/critique/snapshots/` backlog

---

### PHASE 2: FOUNDATION

> Typography, color, layout — the skeleton everything hangs on.

**Commands:**
3. `/impeccable typeset` — Typography system (product register: fixed rem scale, one family)
4. `/impeccable colorize` — Color palette (Restrained: accent ≤10%, semantic-first)
5. `/impeccable layout` — Spacing & structure (4pt scale, Grid for 2D, Flexbox for 1D)

**Skills:**
- `design-system` — Token architecture (primitive → semantic → component) informs typeset + colorize
- `ui-styling` — shadcn/ui + Tailwind patterns inform layout decisions

**Output:** Updated DESIGN.md + code changes in `frontend/src/`

---

### PHASE 3: BUILD

> Audit, motion, responsive, components.

**Commands:**
6. `/impeccable audit` — Technical quality: a11y, performance, theming (5 dimensions, scored 0-4)
7. `/impeccable animate` — Motion system (product: 150-250ms, conveys state, no page-load choreography)
8. `/impeccable adapt` — Responsive behavior (structural adaptation, not fluid typography)
9. `/impeccable craft` — Build component library + feature page layouts (multiple user gates)

**Skills:**
- `high-end-visual-design` — Premium component patterns (double-bezel, island buttons) informs craft
- `design-motion-principles` — Emil Kowalski (70%), Jakub Krehel (20%), Jhey Tompkins (10%) informs animate
- `ui-styling` — Implementation patterns for Tailwind + Radix + framer-motion integration

**Output:** Audit report + motion system + responsive system + component library + feature pages

---

### PHASE 4: POLISH

> Quality, onboarding, copy. Make it feel crafted, not assembled.

**Commands:**
10. `/impeccable polish` — Final quality pass (read critique snapshot as backlog)
11. `/impeccable onboard` — Empty states + first-run experience
12. `/impeccable clarify` — UX copy & labeling pass

**Skills:**
- `ui-ux-pro-max` — Empty state patterns and UX conventions from design intelligence DB
- `design-system` — Ensure all polish aligns to token architecture

**Output:** Polished code + empty states + consistent copy

---

### PHASE 5: WOW

> Delight and overdrive. Only after all foundations solid.

**Commands:**
13. `/impeccable delight` — 3-5 personality touches (product register: delight at specific moments, not pages)
14. `/impeccable overdrive` — Extraordinary hero moment (propose 2-3 directions, get pick, build, iterate in browser)

**Skills:**
- `high-end-visual-design` — Signature moments for overdrive
- `gpt-taste` — GSAP motion patterns, bento grids for delight
- `design-motion-principles` — Restraint vs controlled delight balance

**Output:** Delight moments + hero moment in `frontend/src/`

---

### PHASE 6: SYNTHESIZE

> Merge all decisions into one implementation-ready document.

**Read:** All Impeccable outputs — DESIGN.md, design.json, critique snapshots, code changes from phases 1-5.

**Write:** `docs/superpowers/specs/cortex-frontend-redesign-spec.md`

Must contain:
1. Product identity summary (from PRODUCT.md)
2. Design system tokens (from DESIGN.md frontmatter)
3. Component catalog (every component: props, states, variants)
4. Layout system (shell, sidebar, content, panels, responsive)
5. Motion system (every interaction → timing/easing)
6. Page templates (for each of 15 feature modules)
7. Empty states & onboarding (from command 11)
8. Copy guidelines (from command 12)
9. Delight moments (from command 13)
10. Overdrive spec (from command 14)
11. Accessibility requirements (from audit)
12. Anti-patterns (from DESIGN.md Do's and Don'ts)
13. File structure (where every component lives)

---

### PHASE 7: PLAN

> Implementation plan from the spec.

**Skill:** `superpowers:writing-plans`

Reads the spec from Phase 6. Produces `docs/superpowers/plans/cortex-frontend-redesign.md` with TDD tasks ordered by dependency.

Must cover:
1. Design system foundation (tokens, globals.css, tailwind config, font loading)
2. Core components (every component, one at a time)
3. Layout shell (sidebar, content area, panels, routing)
4. Feature modules (rebuild each of 15 modules against new design)
5. Motion integration (framer-motion at every interaction point)
6. Responsive pass (mobile/tablet breakpoints)
7. Accessibility audit (contrast, keyboard, focus, screen reader)
8. Empty states & onboarding (every module's empty/error/first-run)
9. Copy pass (all text updated)
10. Delight moments (3-5 personality touches)
11. Overdrive (hero moment)
12. Performance (bundle analysis, lazy loading, image optimization)

---

### PHASE 8: EXECUTE

> Build it.

**Skill:** `superpowers:subagent-driven-development`

Dispatches fresh subagent per task. Review between tasks.

**Validation after each:**
```bash
cd frontend && npm run build    # Must pass
cd frontend && npm test         # Must pass (if tests exist)
```

**Commit format:**
```
design(<area>): <what changed>
```

---

## Scoped Mode — Routing Table

Given a direction, run only relevant phases and their commands:

| Direction contains | Phases | Commands | Skills |
|--------------------|--------|----------|--------|
| typography, fonts, text, type | 2 | typeset | design-system |
| colors, palette, accent, dark mode | 2 | colorize | design-system |
| spacing, layout, grid, structure | 2 | layout | ui-styling |
| animation, motion, transition | 3 | animate | design-motion-principles |
| responsive, mobile, tablet | 3 | adapt | — |
| accessibility, a11y, contrast, keyboard | 3 | audit | — |
| components, buttons, inputs, cards, modals | 3 | craft | high-end-visual-design, ui-styling |
| loading, empty, error, onboarding | 4 | onboard | ui-ux-pro-max |
| copy, labels, text, placeholder, error message | 4 | clarify | — |
| personality, delight, micro-interaction | 5 | delight | gpt-taste, design-motion-principles |
| hero, extraordinary, wow, screenshot-worthy | 5 | overdrive | high-end-visual-design, gpt-taste |
| quality, polish, consistency, edge case | 4 | polish | design-system |
| design system, tokens, extract, catalog | 1 | document | design-system, ui-styling |
| performance, bundle, optimize | 3 | audit + optimize | — |
| security, hardening | — | harden | — |
| simplify, reduce, too complex | — | distill | — |
| make louder | — | bolder | high-end-visual-design |
| make subtler, too much | — | quieter | — |
| interaction, hover, gesture, focus | 3 | interaction-design | design-motion-principles |

**Ambiguous direction?** Run `/impeccable critique` first to diagnose, then route.

---

## Impeccable Commands Reference (28 total)

| Cmd | File | Phase | Purpose |
|-----|------|-------|---------|
| init | `reference/init.md` | Setup | Create PRODUCT.md + DESIGN.md |
| document | `reference/document.md` | 1 | Capture visual system |
| critique | `reference/critique.md` | 1 | Two-assessment UX review |
| typeset | `reference/typeset.md` | 2 | Typography system |
| colorize | `reference/colorize.md` | 2 | Color palette |
| layout | `reference/layout.md` | 2 | Spacing & structure |
| audit | `reference/audit.md` | 3 | Technical quality (a11y, perf) |
| animate | `reference/animate.md` | 3 | Motion system |
| adapt | `reference/adapt.md` | 3 | Responsive behavior |
| craft | `reference/craft.md` | 3 | Build with UX/UI quality |
| polish | `reference/polish.md` | 4 | Final quality pass |
| onboard | `reference/onboard.md` | 4 | First-run & empty states |
| clarify | `reference/clarify.md` | 4 | UX copy & labeling |
| delight | `reference/delight.md` | 5 | Personality touches |
| overdrive | `reference/overdrive.md` | 5 | Push past limits |
| brand | `reference/brand.md` | — | Brand register (not used: CORTEX is product) |
| product | `reference/product.md` | — | Product register (loaded by all commands) |
| shape | `reference/shape.md` | — | Design direction/shape brief |
| bolder | `reference/bolder.md` | — | Make louder |
| quieter | `reference/quieter.md` | — | Make subtler |
| harden | `reference/harden.md` | — | Security/performance |
| optimize | `reference/optimize.md` | — | Performance optimization |
| distill | `reference/distill.md` | — | Simplify |
| extract | `reference/extract.md` | — | Extract design system |
| live | `reference/live.md` | — | Live browser iteration |
| hooks | `reference/hooks.md` | — | Before-edit hooks |
| codex | `reference/codex.md` | — | Image generation |
| interaction-design | `reference/interaction-design.md` | — | Interaction patterns |

---

## Supporting Skills Map

| Skill | Phase | What it provides |
|-------|-------|-----------------|
| `ui-ux-pro-max` | 1, 4 | Design intelligence DB — 50+ styles, 161 palettes, empty state patterns |
| `design-system` | 2, 4 | Token architecture — primitive → semantic → component |
| `ui-styling` | 2, 3 | shadcn/ui + Tailwind + Radix integration patterns |
| `high-end-visual-design` | 3, 5 | Premium component patterns (double-bezel, island buttons) |
| `design-motion-principles` | 3, 5 | Emil/Jakub/Jhey designer perspectives |
| `gpt-taste` | 5 | GSAP motion, bento grids, controlled delight |
| `superpowers:brainstorming` | 7 | Design direction exploration (before plan if direction unclear) |
| `superpowers:writing-plans` | 7 | Implementation plan from spec |
| `superpowers:subagent-driven-development` | 8 | Task-by-task execution |

---

## Rules

- **Product register always.** Design serves the app, not the other way around.
- **Dark-only.** No light mode. Local-first tool.
- **One accent color.** Accent ≤10%. Reserved for primary action/selection/state.
- **No Inter.** Typography must have character. Check brand.md reflex-reject list.
- **No AI purple/blue gradients.** Banned.
- **No decorative animation.** Motion conveys state or gives feedback. 150-250ms.
- **Accessibility from day one.** 4.5:1 contrast, keyboard nav, focus states, reduced motion.
- **Mobile-aware.** Desktop-first but responsive. Touch targets ≥44x44px. No horizontal scroll. No 100vh.
- **Build before polish.** Never skip to delight without foundation.
- **Future-proof.** Must work for v1.06 (cognition), v1.07 (graph viz), v1.08 (environment), v1.11 (voice), v1.12 (code intel).
- **Max 3 fix attempts per issue** before escalating.
- **Frequent commits.** One commit per command completion.
