# Fix CLI Report

**Date:** 2026-06-19
**Status:** DONE

## Summary

Fixed the broken CLI at `/home/adi/Desktop/Cortex-Workspace/cli/` by creating all 15 missing command stub files, fixing syntax errors in `index.ts`, and adding project configuration files.

## Files Created

### Configuration Files
- `cli/package.json` — Node.js package config with commander dependency
- `cli/tsconfig.json` — TypeScript config (ES2022, NodeNext module, strict mode)

### Command Stubs (`cli/src/commands/`)
1. `init.ts` — `runInit()`
2. `install.ts` — `runInstall()`
3. `build.ts` — `runBuild()`
4. `start.ts` — `runStart(options: { profile?: string; detach?: boolean })`
5. `dev.ts` — `runDev(options: { profile?: string })`
6. `setup.ts` — `runSetup()`
7. `doctor.ts` — `runDoctor(options: { fix?: boolean })`
8. `stop.ts` — `runStop()`
9. `logs.ts` — `runLogs(service: string | undefined, options: { follow?: boolean; lines?: string })`
10. `migrate.ts` — `runMigrate(direction: string)`
11. `backup.ts` — `runBackup(name: string | undefined, options: { full?: boolean })`
12. `status.ts` — `runStatus(options: { json?: boolean })`
13. `registry.ts` — `runRegistry(action: string, skill: string | undefined)`
14. `deploy.ts` — `runDeploy(options: { target?: string; env?: string })`
15. `update.ts` — `runUpdate()`

## Bugs Fixed in `index.ts`

The existing `index.ts` had syntax errors in 5 command definitions where `.description=` was used instead of `.description()`:
- Line 86: `migrate` command
- Line 92: `backup` command
- Line 99: `deploy` command
- Line 106: `update` command
- Line 111: `registry` command

All imports were also updated to include `.js` extensions for NodeNext module resolution.

## Verification

- `npx tsc --noEmit` — passes with zero errors
- All 15 command stubs export the expected function signatures matching what `index.ts` imports and passes to commander
- Each stub prints "not yet implemented" and returns gracefully

## Function Signatures Reference

| Command    | First arg              | Second arg (options)                                   |
|------------|------------------------|--------------------------------------------------------|
| init       | —                      | —                                                      |
| install    | —                      | —                                                      |
| build      | —                      | —                                                      |
| start      | —                      | `{ profile?: string; detach?: boolean }`               |
| dev        | —                      | `{ profile?: string }`                                 |
| setup      | —                      | —                                                      |
| doctor     | —                      | `{ fix?: boolean }`                                    |
| stop       | —                      | —                                                      |
| logs       | `service?: string`     | `{ follow?: boolean; lines?: string }`                 |
| migrate    | `direction: string`    | —                                                      |
| backup     | `name?: string`        | `{ full?: boolean }`                                   |
| status     | —                      | `{ json?: boolean }`                                   |
| registry   | `action: string`       | `skill?: string` (3rd arg from commander)              |
| deploy     | —                      | `{ target?: string; env?: string }`                    |
| update     | —                      | —                                                      |
