# Command Guide

## Using Commands

Type `/project:<name>` to invoke any command. All commands automatically discover the repository root — they work from any directory.

## Architecture

The Cortex ecosystem follows a **skill-first** hierarchy:

```
Commands (orchestrate)
    ↓
Skills (contain reusable intelligence)
    ↓
Hooks (enforce quality automatically)
```

Commands are thin orchestrators. They invoke skills from `.claude/skills/` rather than containing logic inline.

## Commands

### Orchestrators (design → improve → develop)

| Command | Purpose | When to Use |
|---------|---------|-------------|
| `/project:update` | Project evolution — turns high-level ideas into approved plans | New features, architecture changes, ambiguous requests |
| `/project:enhance_plan` | Planning ecosystem improvement — detects drift, fixes inconsistencies | After phases, when plans drift from reality |
| `/project:develop` | Development iteration orchestrator — decides next work, delegates, reflects | Start of session, after merge |
| `/project:cortex` | Full autonomous development iteration | Concrete task with clear scope |

### Specialist Commands

| Command | Purpose | When to Use |
|---------|---------|-------------|
| `/project:prompt` | Generate ecosystem-aware prompts | Before complex work, need structured spec |
| `/project:audit` | Deep code-level scan (runtime errors, dead code, integration issues) | Find bugs, dead code, integration issues |
| `/project:review` | Code quality review | Before push or merge |
| `/project:verify` | Run verification suite (tests, lint, format, hooks) | Pre-merge automated checks |
| `/project:release` | Release readiness check | Before releasing a version/phase |
| `/project:architecture` | Architecture alignment check | Before big architectural changes |
| `/project:challenge` | Adversarial review — stress-tests plans and specs | Before major decisions |
| `/project:health` | Repository health check | Weekly or before milestones |
| `/project:ideas` | Innovation and opportunity discovery | Weekly or during planning |
| `/project:improve` | Ecosystem self-improvement | Weekly or after significant work |
| `/project:reflect` | Reflection framework | Before completing any major task |
| `/project:feature-gap` | Roadmap vs codebase gap analysis | During planning or phase transitions |

## Typical Workflows

### Quick development session
`/project:develop` → delegates to `/project:cortex` → walks away

### New feature (ambiguous → approved → built)
`/project:update` → plan approved → `/project:develop` → `/project:cortex` → `/project:reflect` → `/project:verify`

### Before a big decision
`/project:challenge` → review findings → decide

### Weekly maintenance
`/project:health` → `/project:ideas` → `/project:improve`

### Before release
`/project:release` → fix blockers → `/project:verify`

### Planning review
`/project:enhance_plan` → review drift findings → fix inconsistencies → update plans

### Need a prompt for complex work
`/project:prompt` → review generated prompt → use it

## Priority Order

1. `/project:update` — design before implementation
2. `/project:enhance_plan` — keep plans aligned with reality
3. `/project:develop` — decide what to do next
4. `/project:cortex` — full autonomous implementation
5. `/project:prompt` — generate structured prompts
6. Everything else — focused specialist tools
