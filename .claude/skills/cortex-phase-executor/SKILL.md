# cortex-phase-executor

Execute a single phase from a version plan. Reads the phase file, executes each task sequentially, validates, and marks progress.

## When to Use

When invoking /project:cortex, /project:next, or /project:phase. This is the core execution engine.

## Process

### 1. Load Phase Context

Read the phase plan file (e.g., `.agents/plans/versions/v1.02/P03.md`).

Parse:
- Phase objective
- Implementation tasks (Task 1 through Task N)
- Testing strategy
- Validation steps
- Definition of Done

### 2. Execute Tasks Sequentially

For each task in the phase plan:

#### 2a. Read Task Requirements
- Files to create/modify
- Interfaces (consumes/produces)
- Test criteria

#### 2b. TDD Cycle
1. Write the failing test
2. Run test to verify it fails
3. Implement the minimal code
4. Run test to verify it passes
5. Commit with descriptive message

#### 2c. Task Complete
- All tests passing
- Code implements the spec
- Commit created

### 3. Phase Validation

After all tasks complete:

```bash
make test
make lint
make format
```

If any check fails, fix before proceeding.

### 4. Update Progress

Read the version's progress.md.

Update the phase status from "Not started" to "Completed".

Set the completion timestamp.

### 5. Report

Output:
```
## Phase Complete: P0X — <name>

**Tasks Completed:** N/N
**Tests:** X passing
**Duration:** Xh Ym
**Next Phase:** P0X+1 — <name>

Run /project:next to continue.
```

## Error Handling

If a task fails:
1. Report the error
2. Show the failing test/command
3. Suggest fix
4. Wait for user confirmation before retrying

If validation fails:
1. Show which checks failed
2. Fix the issues
3. Re-run validation
4. Only proceed when all checks pass
