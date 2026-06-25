# Command Guide

## Using Commands

Type `/project:<name>` to invoke any command.

## Commands

### Autonomous
| Command | Purpose | When to Use |
|---------|---------|-------------|
| `/project:cortex` | Full development iteration | Start a development session — walks away |

### Prompt Generation
| Command | Purpose | When to Use |
|---------|---------|-------------|
| `/project:prompt` | Generate ecosystem-aware prompts | Before any work, to get a high-quality prompt |

### Expert Commands
| Command | Purpose | When to Use |
|---------|---------|-------------|
| `/project:audit` | Deep code audit | Find bugs, dead code, integration issues |
| `/project:review` | Code quality review | Before push or merge |
| `/project:verify` | Run verification suite | Check tests, lint, build pass |
| `/project:release` | Release readiness | Before releasing a version/phase |
| `/project:architecture` | Architecture alignment | Before big architectural changes |
| `/project:challenge` | Adversarial review | Before major decisions |
| `/project:health` | Repository health | Weekly or before milestones |
| `/project:ideas` | Innovation discovery | Weekly or during planning |
| `/project:improve` | Ecosystem improvement | Weekly or after significant work |
| `/project:reflect` | Reflection framework | Before completing any major task |
| `/project:feature-gap` | Roadmap vs codebase | During planning or phase transitions |

## Typical Workflows

### Quick development session
`/project:cortex` → walks away

### Before a big decision
`/project:challenge` → review findings → decide

### Weekly maintenance
`/project:health` → `/project:ideas` → `/project:improve`

### Before release
`/project:release` → fix blockers → `/project:verify`

### Need a prompt for complex work
`/project:prompt` → review generated prompt → use it

## Priority Order
1. `/project:cortex` — does everything autonomously
2. `/project:prompt` — generates ecosystem-aware prompts
3. Everything else — focused expert tools
