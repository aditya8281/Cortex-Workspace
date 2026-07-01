Last updated: 2026-07-01

# Product

## Register

product

## Users

Developers and power users running a local-first AI brain ecosystem on their machine. They are technically sophisticated, privacy-conscious, and expect their tools to be fast, reliable, and non-intrusive. They interact with CORTEX while working — in code, in conversation, in knowledge management — not as a separate activity.

## Product Purpose

CORTEX is a local-first machine intelligence layer — a persistent AI brain that lives on your machine and grows with you. It provides persistent understanding, memory, reasoning, and agency. The goal is to transform a computer from a tool you operate into a companion that understands you.

CORTEX is not a chatbot, not a repo assistant, not a RAG platform, not a model wrapper. It is an entire cognition layer with memory, reasoning, and agency.

Success means: the interface disappears into the task. Users feel like they are interacting with the current state of their machine's intelligence, not opening another application.

## Status

| Area | State |
|------|-------|
| Backend API | 200+ REST + 3 WebSocket endpoints across 10 domain routers — production-ready |
| Auth + Vault | Production-quality — JWT + Argon2, Fernet encryption |
| Agent System | Agent loop, run manager, stall detection, verifier, compactor |
| Memory System | Episodic, semantic, working memory with graph search |
| Intelligence | Model catalog, providers, variants, benchmarks |
| LLM Integration | llama.cpp + Ollama with provider abstraction |
| Awareness | Device, file, project, repo detection + health monitoring |
| Privacy | Consent, audit, access control, RBAC/ABAC |
| Backend code | 425 Python files, 46,733 LoC |
| Frontend code | 17 page files, 76 feature components, 25 shared components, 17,348 LoC |
| Tests | 194 files, 21,784 LoC, 2,077 tests |
| Docs | 32 documentation files |
| Commits | 739 |

## Brand Personality

**Calm, Precise, Intelligent.**

The interface should feel like a calm AI companion — refined, approachable, and alive. It is spatial, persistent, and always aware. It does not demand attention; it earns trust through consistent, reliable behavior.

Voice: plain, direct, technical. No marketing speak. No AI clichés. No decoration for its own sake.

## Anti-references

**Do NOT look like:**
- ChatGPT, Claude.ai — generic chat interfaces. CORTEX is not a chatbot.
- Jupyter, VS Code — developer tools. CORTEX is not a code editor.
- Notion, Linear — cloud productivity SaaS. CORTEX is local-first.
- Any IDE, dashboard, file explorer, or productivity SaaS.
- MacOS Dock clones — the Neural Hub dock is glass, centered, and mode-aware, not a taskbar.

**Do NOT use:**
- Homepage as a conversation screen.
- "AI magic" aesthetics: purple gradients, sparkles, neon glows.
- Chatbot-style layouts or conversation-first UI patterns.
- Identical card grids — same-sized cards with icon + heading + text, repeated endlessly.
- Sidebar navigation with text labels (replaced by glass dock in Neural Hub redesign).
- Bounce, elastic, or spring easings on any UI element.

**Instead, feel like:** An Operating Intelligence Layer — calm, spatial, persistent, always aware. Users interact with the current state of their machine's intelligence, not an app.

## Design Principles

1. **Intelligence, not interface.** Show the current state of your machine's knowledge. Every screen should reveal what CORTEX knows, not what CORTEX can do.
2. **Calm is a feature.** Reduce noise, not add decoration. Sparse, purposeful, never overwhelming.
3. **Earned familiarity.** A user fluent in Linear, Figma, or Raycast should sit down and trust this interface without pausing at every subtly-off component.
4. **Motion serves state.** Every animation conveys feedback, reveals hierarchy, or signals change. Nothing decorative.
5. **Local-first trust.** Privacy is visible. Encryption status, data ownership, vault state — these are features, not settings.

## Layout Architecture (Neural Hub)

The frontend uses a **Neural Hub** layout replacing the legacy sidebar:

- **NeuralRibbon** (top): System status bar — health indicator, active model, TPS, VRAM, version. Fixed position, z-sticky.
- **Hub page** (home): Greeting → search bar (⌘K trigger) → widget grid. Auth-gated; unauthenticated users redirect to `/auth`.
- **Mode pages** (10 modes): Chat, Search, Brain, Vault, Models, Code, Utility, Settings, Systems, Profile. Each accessed via dock or command palette.
- **Dock** (bottom): Floating glass-morphism bar with 10 mode icons + profile avatar. Auto-hides in mode view after 3s; always visible on hub. Keyboard shortcuts: ⌘1–⌘0.
- **Command palette** (⌘K overlay): Fuzzy search over all modes + navigation commands. Arrow key navigation, group headers.
- **Mode stack:** Navigation context tracks up to 5 levels deep. Silent drop of oldest entry when exceeded. Back button pops mode stack.
- **Auth flow:** `AuthProvider` bootstraps via `GET /me`. Auto token refresh on 401. Redirect to `/auth` if unauthenticated.

## Keyboard Ergonomics

| Shortcut | Action |
|----------|--------|
| ⌘1 | Chat |
| ⌘2 | Search |
| ⌘3 | Brain |
| ⌘4 | Vault |
| ⌘5 | Models |
| ⌘6 | Code |
| ⌘7 | Utility |
| ⌘8 | Settings |
| ⌘9 | Systems |
| ⌘0 | Profile |
| ⌘K | Toggle command palette |
| ⎋ | Close command palette / back |
| ↑↓ | Navigate command palette |

## Design System
See `DESIGN.md` for the complete visual token system (colors, typography, elevation, components, motion, do's and don'ts).

## Accessibility & Inclusion

- WCAG AA compliance: 4.5:1 contrast, keyboard navigation, visible focus states, semantic HTML, ARIA labels.
- Mandatory `prefers-reduced-motion` support for all animations (backgrounds, graph effects, particles, transitions, pulses).
- Accessibility built into the design system from the start, not retrofitted.
- High-contrast UI throughout.
