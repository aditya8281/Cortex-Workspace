# Redesign v0 — Neural Hub Implementation

**Document:** Redesign Overview
**Date:** 2026-07-01
**Type:** Frontend Redesign
**Complexity:** High (12 phases)

---

## Objective

Convert CORTEX from a sidebar-left dashboard application to a **Neural Hub** — a full-screen, immersive, command-driven interface with a floating dock, glass-morphism widgets, and 10 mode shells.

Every mode preserves state. Navigation is instant (150ms crossfade). The hub is the default view — live widgets showing real system data. Command bar (`⌘K`) reaches anything instantly.

---

## Design Source of Truth

`docs/design/redesign0.md` — this is the canonical reference. All implementation decisions follow it. Key divergence from existing `DESIGN.md`:

| Area | DESIGN.md | redesign0.md | Resolution |
|------|-----------|--------------|------------|
| Layout | Left sidebar (60px or 240px) | Bottom floating dock (56px) | redesign0 wins for the hub; sidebar content lives inside modes |
| Accent | Single cyan (#0ea5c9) | Dual: silk red + cyan | redesign0 wins — red for actions, cyan for AI |
| Glassmorphism | Banned | Used selectively (dock, hub widgets, auth cards) | redesign0 wins for these specific surfaces |
| Neural particles | Banned | Very dim background layer | redesign0 wins — always-on at ≤0.3 opacity |
| Typography | Same Geist + JetBrains Mono | Same | No conflict |
| Motion | Same easing philosophy | Extended with spring token | Compatible |

---

## Phase Overview

| Phase | Name | Status | Dependencies | Est. Time |
|-------|------|--------|--------------|-----------|
| **P01** | Design Tokens & Tailwind Config | 🔲 Not started | None | 1-2h |
| **P02** | Neural Hub Layout | 🔲 Not started | P01 | 3-4h |
| **P03** | Hub Landing Page | 🔲 Not started | P02 | 4-5h |
| **P04** | Mode Navigation System | 🔲 Not started | P02 | 2-3h |
| **P05** | Auth Pages | 🔲 Not started | P01, P03 | 1-2h |
| **P06** | Chat Mode | 🔲 Not started | P01, P02, P04 | 3-4h |
| **P07** | Search Mode | 🔲 Not started | P01, P02, P04 | 2-3h |
| **P08** | Brain Mode | 🔲 Not started | P01, P02, P04 | 2-3h |
| **P09** | Vault Mode | 🔲 Not started | P01, P02, P04 | 2-3h |
| **P10** | Remaining Modes (Models, Code, Utility, Settings, Systems, Profile) | 🔲 Not started | P01, P02, P04 | 4-5h |
| **P11** | Component Polish | 🔲 Not started | P01 | 2-3h |
| **P12** | Final Polish | 🔲 Not started | All | 1-2h |

**Total estimated: 27-37 hours**

---

## File Plan

### New Files
```
frontend/src/features/hub/page.tsx                    — Hub landing page
frontend/src/features/search/page.tsx                 — Search mode
frontend/src/features/brain/page.tsx                  — Brain/memory mode
frontend/src/features/vault/page.tsx                  — Vault mode
frontend/src/features/code/page.tsx                   — Code mode
frontend/src/features/utility/page.tsx                — Utility mode
frontend/src/features/profile/page.tsx                — Profile mode
frontend/src/shared/layout/NeuralHub.tsx              — Root hub layout
frontend/src/shared/layout/Dock.tsx                   — Floating bottom dock
frontend/src/shared/layout/NeuralRibbon.tsx           — Status ribbon
frontend/src/shared/layout/NeuralParticles.tsx        — Canvas particle bg
frontend/src/shared/layout/HubWidget.tsx              — Glass widget card
frontend/src/shared/layout/CommandBar.tsx             — ⌘K command bar
frontend/src/shared/layout/ModeShell.tsx              — Full-screen wrapper
frontend/src/shared/layout/ModeStack.tsx              — Navigation stack context
frontend/src/shared/layout/ModeView.tsx               — Mode router
frontend/src/shared/layout/HubGreeting.tsx            — Greeting display
```

### Modified Files
```
frontend/tailwind.config.ts                           — New colors, shadows, z-index
frontend/src/app/globals.css                          — CSS variables, animations
frontend/src/app/layout.tsx                           — NeuralHub provider
frontend/src/app/page.tsx                             — Hub page import
frontend/src/app/auth/page.tsx                        — Login redesign
frontend/src/app/auth/register/page.tsx               — Register redesign
frontend/src/features/chat/                           — Chat mode redesign
frontend/src/features/settings/page.tsx               — Settings refactor
frontend/src/features/system/page.tsx                 — Systems mode
frontend/src/features/models/page.tsx                 — ModelBook refactor
frontend/src/shared/ui/Card.tsx                       — Glass variant
frontend/src/shared/ui/Button.tsx                     — Red/cyan/ghost variants
frontend/src/shared/ui/Input.tsx                      — Redesigned input
frontend/src/shared/ui/Modal.tsx                      — Redesigned modal
frontend/src/shared/ui/Toast.tsx                      — Redesigned toast
frontend/src/shared/ui/Badge.tsx                      — Variants
frontend/src/shared/ui/Skeleton.tsx                   — Shimmer alignment
```

---

## Backend Reality Integration

| Mode | Backend Status | Frontend Behavior |
|------|---------------|-------------------|
| Chat | ✅ Full API | Live endpoints |
| Search | ✅ Default, 🔴 prefixes | Graceful empty state per prefix |
| Brain | 🟡 Partial (CRUD + health exist) | Show real data where available, "planned v1.09" for gaps |
| Vault | ✅ Full API | All encrypted CRUD |
| Models | 🟡 Ollama only | Show real catalog, coming-soon for HF |
| Code | 🔴 Only GitHub works | GitHub tab live, LSP/Skills/MCP tabs: "v1.12" |
| Utility | 🟢 Frontend-only | All local tools |
| Settings | 🟡 Partial | Read-only for service controls |
| Systems | 🟡 Partial | GPU conditional, no service start/stop |
| Profile | 🟡 Partial | Activity feed not built |

---

## Relation to Version Plans

This redesign runs **alongside** version v1.09–v1.14. It does not block them; it is a frontend layer that connects to backend APIs as they become available.

| Future Version | Redesign Impact |
|---------------|-----------------|
| v1.09 (Knowledge) | Unlocks Brain mode file watcher, graph viz, memory consolidation |
| v1.10 (Scheduler) | Enables Scheduled Actions in Utility mode |
| v1.11 (Web Search) | Unlocks Search mode /web prefix |
| v1.12 (Developer) | Unlocks Code mode LSP, AST, agent tools, skills |
| v1.13 (Utility) | Enables email/calendar/tasks in Utility mode |
| v1.14 (Advanced AI) | Deepens Chat/Brain reasoning visualization |

**Engineering note:** The redesign's mode architecture is designed so that new backend features slot into existing mode shells without structural changes. Each mode page is a self-contained component — when a v1.12 endpoint ships, the Code mode simply starts fetching real data instead of showing "coming in v1.12".

---

## Execution Order

1. **P01** — Foundation (must come first)
2. **P02 + P11** — Layout + component polish (can run in parallel)
3. **P03 + P04** — Hub page + navigation system (P03 needs P02, P04 needs P02)
4. **P05–P10** — Individual modes (can run in parallel once P02 + P04 exist)
5. **P12** — Final polish (everything else must be done)

---

## Definition of Done

- [ ] Sidebar replaced by floating dock with auto-hide
- [ ] Neural hub landing page with 2×5 live widget grid
- [ ] ⌘K command bar with fuzzy search
- [ ] All 10 modes wired through ModeStack navigation
- [ ] Mode state preserved across switches (scroll, input, tab)
- [ ] Auth pages with glass cards + neural particles
- [ ] Chat mode with slide-over conversation list + glass bubbles
- [ ] Search mode with prefix routing and graceful placeholders
- [ ] Brain, Vault, ModelBook, Code, Utility, Settings, Systems, Profile modes functional
- [ ] All UI components refactored to redesign0 tokens
- [ ] WCAG AA contrast verified on all surfaces
- [ ] `prefers-reduced-motion` respected everywhere
- [ ] Keyboard navigation: tab through all elements, ⌘K works, escape works
- [ ] All error states handled (loading, empty, error, offline)
- [ ] Build passes with zero errors
- [ ] No regressions in existing backend API connectivity
