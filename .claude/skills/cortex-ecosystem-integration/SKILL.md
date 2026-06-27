# cortex-ecosystem-integration

Unified skill that detects and applies all available ecosystem capabilities for any task. Every Cortex command invokes this skill to ensure maximum leverage of skills, hooks, MCP servers, and plugins.

## When to Use

At the START of every significant task. Before any implementation work begins. This is the "ensure nothing is missed" skill.

## Process

### 1. Skill Audit

Check ALL available skill families for applicable skills:

**Cortex Skills** (`.claude/skills/cortex-*`):
- `cortex-repo-discovery` — Find repo root
- `cortex-repository-intelligence` — Build repo state understanding
- `cortex-system-validation` — Full test/lint/build pipeline
- `cortex-integrity` — Import/dependency/structural scan
- `cortex-architecture-drift` — File placement and pattern compliance
- `cortex-documentation-consistency` — Docs match code
- `cortex-engineering-review` — Code quality analysis
- `cortex-adversarial-challenge` — Challenge assumptions
- `cortex-health-review` — Comprehensive health check
- `cortex-repo-health-scan` — Hooks, skills, tech debt
- `cortex-planning-ecosystem` — Planning improvement
- `cortex-phase-executor` — TDD implementation loop
- `cortex-progress-tracker` — Progress tracking
- `cortex-post-reflection` — Post-implementation reflection
- `cortex-repo-cleanup` — Repository hygiene
- `cortex-version-integration` — Version completion
- `cortex-status` — Current state reporting
- `cortex-architecture-audit` — Architecture compliance

**Superpowers Skills** (via Skill tool):
- `brainstorming` — Design exploration and decision-making
- `writing-plans` — Implementation plan creation
- `writing-skills` — Skill creation for repeated patterns
- `test-driven-development` — TDD discipline
- `systematic-debugging` — Bug investigation
- `executing-plans` — Plan execution with checkpoints
- `subagent-driven-development` — Fresh subagent per task
- `verification-before-completion` — Quality gates
- `requesting-code-review` — External review
- `receiving-code-review` — Process review feedback
- `finishing-a-development-branch` — Branch completion
- `using-git-worktrees` — Isolated workspaces
- `dispatching-parallel-agents` — Parallel work execution

### 2. MCP Server Detection

Check available MCP servers and their capabilities:

| Server | Capability | When to Use |
|--------|-----------|-------------|
| context7 | Library documentation | Any code involving React, Next.js, Tailwind, FastAPI, SQLAlchemy |
| sequential-thinking | Complex reasoning | Architectural decisions, multi-factor analysis |
| playwright | Browser automation | Visual testing, UI validation, screenshots |
| context-mode | Knowledge base | Session memory, batch analysis, code derivation |

**Action:** Before writing any code that uses a library, fetch its docs from context7. Before complex reasoning, use sequential-thinking. Before frontend merge, use playwright for visual validation.

### 3. Hook Activation Check

Verify all relevant hooks are active for the current task type:

| Hook | Triggers On | What It Checks |
|------|-------------|----------------|
| UI Review | `.tsx/.ts/.css` changes | Design tokens, glassmorphism, accessibility, responsive |
| Architecture | Structural changes | File placement, ownership, patterns |
| Code Quality | All code changes | Lint, formatting, style |
| Skill Discovery | Any task | Skill gaps, repeated patterns |
| Contract | API changes | Schema validation, route consistency |
| Completion Gate | Pre-merge | Tests, lint, build, docs |
| Docs Consistency | Doc changes | References, cross-links |
| Planning | Plan changes | Version tracking, phase plans |
| Decision Tracking | ADRs | Decision format, rationale |
| Repo Health | Periodic | Overall repository health |

**Action:** Ensure hooks are configured to run automatically. If a hook is missing for a common task pattern, create it.

### 4. Plugin Detection

Check available plugins:

- **Superpowers** — Skills marketplace with design patterns, TDD, code review
- **Caveman** — Mode management (full/lite/ultra), terse communication
- **Context Mode** — Knowledge base, sandboxed code execution, session memory

**Action:** Use plugin capabilities proactively. Don't wait for them to be invoked — apply them when they add value.

### 5. Skill Gap Detection

For the current task, identify:

1. **What skills exist** that could help?
2. **What patterns are being repeated** that could become skills?
3. **What hooks are missing** for quality enforcement?
4. **What MCP tools** could accelerate the work?

If a repeated pattern is detected (same workflow 2+ times):
- Note it in the session output
- After completing the current work, invoke `superpowers:writing-skills` to create a new skill
- Save to `.claude/skills/<skill-name>/SKILL.md`
- Log: "Created skill: <name> for <pattern>"

### 6. Frontend-Specific Integration

When ANY work touches `frontend/`:

**Before Design:**
- Invoke `superpowers:brainstorming` for design decisions
- Fetch latest docs from context7 (React 19, Next.js 15, Tailwind 3.4)
- Check `DESIGN.md` and `frontend/src/features/CONVENTIONS.md` for design system rules

**During Implementation:**
- Follow `frontend/src/features/CONVENTIONS.md` for feature module structure
- Use design tokens from `tokens.ts` — no hardcoded colors
- Use `cn()` utility for className merging
- Apply glassmorphism patterns consistently

**After Implementation:**
- UI Review hook validates design compliance
- Playwright hook validates build and visual regression
- Verify responsive design (desktop sidebar, tablet overlay, mobile tabs)

### 7. Output

Return a structured report:

```markdown
## Ecosystem Integration Report

### Applicable Skills
| Skill | Status | Action |
|-------|--------|--------|
| cortex-integrity | ✅ Available | Invoke quick scan |
| brainstorming | ✅ Available | Use for design decisions |
| writing-plans | ✅ Available | Create implementation plan |
| writing-skills | ⚠️ Gap detected | Create skill for <pattern> |

### MCP Servers
| Server | Status | Use Case |
|--------|--------|----------|
| context7 | ✅ Connected | Fetch React/Next.js docs |
| sequential-thinking | ✅ Connected | Complex reasoning |
| playwright | ✅ Connected | Visual testing |
| context-mode | ✅ Connected | Knowledge base |

### Hooks Active
| Hook | Status | Coverage |
|------|--------|----------|
| UI Review | ✅ Active | Frontend changes |
| Architecture | ✅ Active | Structural changes |
| Code Quality | ✅ Active | All code |

### Recommendations
- Create skill for: <detected repeated pattern>
- Add hook for: <missing quality gate>
- Use MCP for: <acceleration opportunity>
```

## Examples

```
Invoke cortex-ecosystem-integration before starting any significant task.
```

```
Invoke cortex-ecosystem-integration to detect available skills for frontend work.
```
