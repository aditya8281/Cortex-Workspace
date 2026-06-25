# Skills Index

81 skills in `.claude/skills/`. Each has a `SKILL.md` entry point. Cortex-specific skills provide reusable intelligence for the command ecosystem.

---

## CORTEX-Specific

| Skill | Purpose | When to Use |
|-------|---------|-------------|
| cortex-repository-intelligence | Discover git state, version, repo structure | First step of every command |
| cortex-repo-discovery | Find repo root from any working directory | Universal command access |
| cortex-planning-ecosystem | Load all planning artifacts | Before planning analysis |
| cortex-system-validation | Run full validation pipeline (test, lint, format, hooks) | Before merge, after implementation |
| cortex-engineering-review | Review code for correctness, patterns, quality | Before push, after implementation |
| cortex-architecture-drift | Detect divergence between docs and code | Before release, architecture changes |
| cortex-adversarial-challenge | Stress-test plans/specs/implementations | Before major decisions, spec approval |
| cortex-post-reflection | Systematic reflection after completing work | Before merge, after implementation |
| cortex-repo-cleanup | Remove temp files, dead code, verify clean state | Before final commit, before merge |
| cortex-version-integration | Verify version readiness before merge | Before merge, release gate |
| cortex-repo-health-scan | Check hook/skill/tech debt/docs health | Weekly health check, before release |
| cortex-documentation-consistency | Cross-reference docs against codebase | Before release, after implementation |
| cortex-architecture-audit | Validate against 10 architecture principles | Before merge, after phase, architecture drift |
| cortex-health-review | Comprehensive health check | Weekly, before release, quality concerns |
| cortex-status | Report current development status | On entry, "what version are we on?" |

## Core Development

| Skill | Purpose | When to Use |
|-------|---------|-------------|
| brainstorming | Turn ideas into designs through dialogue | Before any design work |
| writing-plans | Write implementation plans | After design approval |
| tdd | Test-driven development | During implementation |
| subagent-driven-development | Multi-file implementation with subagents | Complex multi-file tasks |
| review | Code review | Before push |
| implement | Implementation guidance | During coding |
| diagnose-bugs | Find and fix bugs | When debugging |

## Design & Visual

| Skill | Purpose | When to Use |
|-------|---------|-------------|
| frontend-design | Frontend design system | Frontend work |
| design-an-interface | Interface design | New UI components |
| design-md | Design documentation | Documenting design decisions |
| design-motion-principles | Motion design | Animations, transitions |
| design-taste-frontend | Frontend taste evaluation | UI quality review |
| high-end-visual-design | Premium visual design | High-quality UI |
| industrial-brutalist-ui | Brutalist UI style | Alternative design approach |
| minimalist-ui | Minimalist UI style | Clean, simple UI |
| ui-ux-pro-max | Comprehensive UI/UX data | UI/UX research |
| brandkit | Brand identity | Branding work |
| stitch-design-taste | Design taste stitching | Combining design approaches |
| imagegen-frontend-mobile | Mobile image generation | Mobile UI assets |
| imagegen-frontend-web | Web image generation | Web UI assets |
| image-to-code | Convert images to code | Design-to-code workflow |

## Writing & Communication

| Skill | Purpose | When to Use |
|-------|---------|-------------|
| writing-beats | Writing rhythm and pacing | Content creation |
| writing-fragments | Writing fragments | Short-form content |
| writing-great-skills | How to write good skills | Creating new skills |
| writing-shape | Writing shape and structure | Document structure |
| edit-article | Article editing | Content editing |
| enhance-prompt | Prompt enhancement | AI prompt improvement |

## Architecture & Planning

| Skill | Purpose | When to Use |
|-------|---------|-------------|
| domain-modeling | Domain modeling | DDD, bounded contexts |
| decision-mapping | Decision mapping | Decision tracking |
| improve-codebase-architecture | Architecture improvement | Refactoring |
| request-refactor-plan | Refactoring plans | Before refactoring |
| codebase-design | Codebase design | System design |
| ubiquitous-language | Ubiquitous language | DDD terminology |

## Git & Workflow

| Skill | Purpose | When to Use |
|-------|---------|-------------|
| git-guardrails-claude-code | Git safety guards | Git operations |
| resolving-merge-conflicts | Merge conflict resolution | During merge conflicts |
| handoff | Work handoff | Switching contexts |
| to-issues | Convert to issues | Issue creation |
| to-prd | Convert to PRD | PRD creation |
| triage | Work triage | Classifying incoming work |

## Quality & Review

| Skill | Purpose | When to Use |
|-------|---------|-------------|
| grilling | Adversarial review | Challenging decisions |
| grill-me | Self-adversarial review | Self-critique |
| grill-with-docs | Document-based adversarial review | Review against docs |
| qa | Quality assurance | Testing, QA |
| scaffold-exercises | Scaffolding exercises | Practice, learning |

## Tools & Integration

| Skill | Purpose | When to Use |
|-------|---------|-------------|
| ai-sdk | AI SDK integration | AI/LLM work |
| fastapi | FastAPI patterns | Backend API work |
| postgresql-optimization | PostgreSQL optimization | Database performance |
| obsidian-vault | Obsidian vault integration | Knowledge management |
| setup-pre-commit | Pre-commit setup | Hook configuration |
| setup-matt-pocock-skills | Matt Pocock skills setup | Skill ecosystem setup |
| migrate-to-shoehorn | Migration to shoehorn | Tool migration |
| prototype | Prototyping | Quick prototypes |
| redesign-existing-projects | Redesign projects | UI redesign |

## Caveman Family

| Skill | Purpose | When to Use |
|-------|---------|-------------|
| caveman | Terse communication style | When activated via hook |
| caveman-commit | Terse commit messages | Committing |
| caveman-compress | Compress outputs | Token optimization |
| caveman-help | Caveman help | When stuck |
| caveman-review | Terse code review | Quick reviews |
| caveman-stats | Caveman statistics | Usage stats |
| cavecrew | Cavecrew collaboration | Multi-agent work |

## Meta & Discovery

| Skill | Purpose | When to Use |
|-------|---------|-------------|
| find-skills | Find applicable skills | Skill discovery |
| full-output-enforcement | Full output enforcement | When complete output needed |
| ask-matt | Ask Matt Pocock | Expert guidance |
| gpt-taste | GPT taste evaluation | AI taste assessment |
| teach | Teaching mode | Learning, instruction |
