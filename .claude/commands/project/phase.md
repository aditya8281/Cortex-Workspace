# /project:phase — Execute Specific Phase

Manually select and execute a specific phase from any version.

## Usage

```
/project:phase v1.02 P03
```

If no arguments: show available phases and let user select.

## Instructions

### 1. Discovery

Invoke `cortex-repo-discovery`.

### 2. Parse Arguments

If version and phase provided (e.g., `v1.02 P03`):
- Read `.agents/plans/versions/v1.02/P03.md`
- Execute via cortex-phase-executor

If no arguments:
- Read IMPLEMENTATION_STEPS.md
- Show all versions with phase status (from progress.md)
- Let user select

### 3. Execute

Auto-invoke `/project:cortex` with the selected version and phase.
