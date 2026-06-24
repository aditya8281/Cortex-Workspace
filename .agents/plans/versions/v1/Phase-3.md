# V1 Phase 3: CLI Completion + Bug Fixes + Docs

**Duration estimate:** 3-5 days
**Dependencies:** Phase 1 complete (daemon running, CLI can connect)
**Risk:** Low — mechanical implementation work

---

## Goals

Implement all 15 CLI command stubs. Fix all 5 council-discovered bugs. Clean up documentation to match actual codebase state. Target: 50+ new tests across CLI and bug fixes.

## Deliverables

1. 15 working CLI commands (daemon, agent, search, config, vault, memory)
2. 5 bug fixes (dead code, SSRF bypass, command blocking, sync/async, token estimation)
3. Documentation cleanup (CLAUDE.md, architecture diagram, test count)
4. 50+ new tests (CLI + bug fixes)
5. Feature flag removed (old agent path deprecated)

## Architectural Changes

No new architecture. CLI connects to daemon via HTTP (existing API). Bug fixes are localized changes.

## Backend Changes

### New Files

| File | Purpose |
|------|---------|
| `tests/test_cli_daemon.py` | CLI daemon commands tests |
| `tests/test_cli_agent.py` | CLI agent commands tests |
| `tests/test_cli_search.py` | CLI search commands tests |
| `tests/test_cli_config.py` | CLI config commands tests |
| `tests/test_cli_vault.py` | CLI vault commands tests |
| `tests/test_cli_memory.py` | CLI memory commands tests |
| `tests/test_security_fixes.py` | Bug fix regression tests |

### Modified Files

| File | Change |
|------|--------|
| `cli/src/commands/daemon.ts` | Implement start, stop, status, logs |
| `cli/src/commands/agent.ts` | Implement run, chat, list, cancel |
| `cli/src/commands/search.ts` | Implement search |
| `cli/src/commands/index.ts` | Implement run, status |
| `cli/src/commands/config.ts` | Implement set, get, list |
| `cli/src/commands/vault.ts` | Implement lock, unlock, status |
| `cli/src/commands/memory.ts` | Implement remember, recall, forget, status (NEW command) |
| `backend/app/agents/tools.py` | Remove dead `_REQUIRES_APPROVAL` for write_file |
| `backend/app/agents/tools/security.py` | Block curl/wget in exec_command, broader pattern blocking |
| `backend/app/services/embedding_service.py` | Fix sync/async: use `loop.run_in_executor()` when event loop exists |
| `CLAUDE.md` | Fix middleware/ reference, test count, architecture diagram |
| `docs/ROADMAP.md` | Align with version numbering |

### Bug Fixes (Detailed)

**Bug 1: write_file dead code**
- Remove `write_file` from `_REQUIRES_APPROVAL` set
- Either register in new @tool system (if needed) or remove entirely
- Verify no code path references the dead approval check

**Bug 2: SSRF bypass via exec_command**
- Add URL filtering to exec_command output
- Or block `curl`/`wget` in BLOCKED_PATTERNS
- Better: add output filtering that detects internal IP responses

**Bug 3: Command blocking bypass**
- Replace exact pattern matching with regex: `pip.*install`, `npm.*install`
- Add `pip3`, `npx`, `python -m pip` to blocked patterns
- Consider allowlist approach for high-security mode

**Bug 4: Embedding sync/async mismatch**
```python
# BEFORE (broken in async context):
def get_embedding(text):
    return asyncio.run(embed_model.encode(text))

# AFTER (works everywhere):
async def get_embedding(text):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, embed_model.encode, text)
```

**Bug 5: Token estimation**
- Install tiktoken
- Replace `len(text) // 4` with `len(encoding.encode(text))`
- Add fallback if tiktoken unavailable

## Frontend Changes

**No frontend changes in this phase.**

## Memory Changes

**No memory changes.**

## Retrieval Changes

**No retrieval changes.**

## Agent Changes

Feature flag removed. Old Planner→Executor path deprecated. New loop is the default. All existing agent tests now run against new loop only.

## Dependencies

| Dependency | Action |
|-----------|--------|
| tiktoken | Already added in Phase 2 |
| Commander.js | Already scaffolded, implementing stubs |
| Node.js fetch | For CLI → daemon HTTP calls |

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| CLI tests require running daemon | Medium | Medium | Mock HTTP responses. Integration tests separate. |
| Bug fixes change behavior | Low | Medium | Regression tests for each fix. |
| Documentation cleanup breaks links | Low | Low | Verify all cross-references. |

## Exit Criteria

- [ ] All 15 CLI commands return correct results + JSON output
- [ ] `cortexd start/stop/status/logs` works via CLI
- [ ] `cortex agent run/chat/list/cancel` works via CLI
- [ ] `cortex search "query"` returns results
- [ ] `cortex config set/get/list` manages configuration
- [ ] `cortex vault lock/unlock/status` manages vault
- [ ] `cortex memory remember/recall/forget/status` manages memory
- [ ] Bug 1: write_file dead code removed
- [ ] Bug 2: SSRF bypass via exec_command fixed
- [ ] Bug 3: Command blocking bypass fixed
- [ ] Bug 4: Embedding sync/async mismatch fixed
- [ ] Bug 5: Token estimation uses tiktoken
- [ ] CLAUDE.md updated (middleware/, test count, architecture)
- [ ] ROADMAP.md aligned with version numbering
- [ ] 50+ new tests pass
- [ ] All 341+ existing tests pass
- [ ] Feature flag removed (old path deprecated)
- [ ] `make lint` + `make format` clean
- [ ] `make build` succeeds (backend + frontend)
