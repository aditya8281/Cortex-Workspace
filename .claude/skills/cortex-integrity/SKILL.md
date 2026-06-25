# cortex-integrity — Repository Integrity Analysis

Reusable skill that any Cortex command can invoke. Runs `IntegrityService` and returns findings.

## Invocation

Invoke via: `Skill(topic="cortex-integrity", args={mode: "full"})`

## Modes
- `quick` — structural analysis on changed files
- `incremental` — structural + transitive deps
- `full` — all available engines
- `verify` — structural + semantic
- `target` — specific paths/engines

## Output
Returns `IntegrityReport` with findings, metrics, and model.
