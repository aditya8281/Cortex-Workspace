# CRITICAL RULES - MUST FOLLOW

## RESPONSES

- Keep responses concise and to the point - unless the user asks otherwise

## ECOSYSTEM INTEGRATION

This repository uses a multi-agent development ecosystem. All agents must follow these rules:

### Workflow Rules

1. **Skill Discovery:** Before any task, search for existing skills. Use `superpowers:brainstorming`, `superpowers:writing-plans`, `superpowers:test-driven-development`, `superpowers:systematic-debugging`, `code-review`, `simplify`, and other available skills. Never skip skill discovery.
2. **Brainstorming:** Use `superpowers:brainstorming` skill before any design work. Present design, get approval, write spec, then implement.
3. **Planning:** Use `superpowers:writing-plans` skill after design approval. Create implementation plan with explicit steps.
4. **Implementation:** Follow TDD when applicable. Commit after each logical unit. Run `make lint` + `make format` after each commit.
5. **Testing:** Run `make test` (backend) and `cd frontend && npm test` (frontend) before every push. No regressions.
6. **Validation:** Pre-commit hooks run automatically. Run `make check` before push.
7. **Review:** Use `code-review` skill for correctness, `simplify` for quality. Address all P0/P1 findings.
8. **Documentation:** Update relevant docs when changing APIs, schemas, security patterns, or architecture.
9. **Completion:** All tests pass, lint clean, build succeeds, docs updated, ADR created if architectural decision.
10. **Skill Creation:** When a reusable workflow is identified, create a skill. Skills are a normal part of Cortex development.

### Skill Usage Rules

- **Always check for applicable skills** before any task. The skill list is in system-reminder messages.
- **Use skills in priority order:** Process skills first (brainstorming, systematic-debugging), then implementation skills.
- **Never skip skills** because a task "seems simple." Every task goes through the appropriate workflow.
- **Skills are mandatory** when they apply. Do not rationalize skipping them.
- **Skill-first rule:** Before performing any significant task, determine whether an existing skill can improve the process.
- **Skill gap detection:** During execution, continuously evaluate: Is this repetitive? Likely to happen again? Cortex-specific? Difficult enough to benefit from standardization? If yes, create a skill improvement candidate.
- **Skill evolution:** When a skill is used, review its effectiveness, output quality, missing steps, and friction points. Improve the skill.

### Clarification Rules

**Agent MUST ask human when:**
- Decision is irreversible (schema migrations, breaking API changes, security policy)
- Multiple valid paths exist with different trade-offs
- Scope is ambiguous or requirements are missing
- Change affects >2 subsystems
- New technology or pattern not in current stack is proposed

**Agent MAY proceed without asking when:**
- Task is well-defined with explicit acceptance criteria
- Following established codebase patterns
- Mechanical changes (typos, formatting, imports)
- Updating existing tests or documentation

See [docs/guides/governance.md](docs/guides/governance.md) for full governance rules.
See [`.agents/plans/IMPLEMENTATION_STEPS.md`](.agents/plans/IMPLEMENTATION_STEPS.md) for workflow details.

## PLANNING MODE

- Always ask clarifying questions
- Never assume design, tech stack or features
- Use deep-dive sub-agents to assist with research
- Use deep-dive sub-agents to review the different aspects of your plan before presenting to the user

## CHANGE / EDIT MODE

- Never implement features yourself when possible - use sub-agents!
- Identify changes from the plan that can be implemented in parallel, and use sub-agents to implement the features efficiently
- When using sub-agents to implement features, act as a coordinator only
- Use the best model for the task - premium models for complex tasks (like coding) and mid-tier models for simpler tasks, like documentation
- After completing features (large or small), always run commands like lint, type check and next build to check code quality

## DATABASE SCHEMA CHANGES

- Whenever you make changes to the database schema, ALWAYS run alembic revision + alembic upgrade head
- NEVER use drizzle (this project uses SQLAlchemy + Alembic, not Drizzle)
- Alembic migrations live in `migrations/versions/` — use descriptive filenames with a sequential prefix
- Always define both `upgrade()` and `downgrade()` in migrations
- Use `op.execute()` for DDL and `op.bulk_insert()` for seed data in migrations
- Test migrations with `make db-reset` before committing

## TESTING

- Use any testing tools, libraries available to the project for testing your changes
- Never assume your changes simply work, always test!
- If the project does not have any testing tools, scripts, MCP tools, skills, etc. available for testing, ask the user whether testing should be skipped.

## UI DESIGN

- Always follow the UI design system when creating or reviewing components or pages.
- When doing update or new Design integration always brainstorm and ask relevant question about design choices if needed.
- Design System: @DESIGN.md

## SECURITY PATTERNS

- **Ownership checks:** Every user-scoped endpoint MUST verify `resource.user_id == current_user.id` before returning or mutating data. Never trust client-provided user IDs.
- **IDOR prevention:** Use dependency injection (`get_current_user`) to resolve the authenticated user. Query resources with `user_id` filter, not just resource ID.
- **Path traversal:** Vault and file operations MUST sanitize paths — reject any path containing `..` or absolute paths outside the allowed root.
- **Authentication:** All `/api/v1/*` endpoints require auth unless explicitly marked otherwise. Use `Depends(get_current_user)` from `backend.app.core.db` or `backend.app.api.deps`.
- **Rate limiting:** Auth endpoints have stricter rate limits. General endpoints use global rate limiting.
- **CSRF:** Double-submit cookie pattern. API endpoints with explicit auth (Bearer token or session cookie) are exempt.

## API DESIGN PATTERNS

- **Route ordering:** Specific routes must be registered before parameterized routes to avoid shadowing (e.g., `/models/installed` before `/models/{model_id}`).
- **Response models:** Always use `response_model=` on endpoint decorators for automatic OpenAPI schema generation and response validation.
- **Dependency injection:** Use `Depends(get_db)` for database sessions and `Depends(get_current_user)` for auth. Never manually instantiate sessions in route handlers.
- **Error handling:** Use `HTTPException` with appropriate status codes. 404 for not found, 403 for forbidden, 409 for conflicts.
- **Pydantic schemas:** Define request/response schemas in `backend/app/schemas/`. Use `BaseModel` with explicit field types. Never use `dict` for structured responses.
- **Router organization:** Each domain gets its own router file in `backend/app/api/v1/`. Include it in `backend/app/api/router.py` with appropriate prefix and tags.
