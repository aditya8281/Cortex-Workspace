# Feature Module Conventions — CORTEX Frontend

## Naming Conventions

| Item | Convention | Example |
|------|-----------|---------|
| Directory | lowercase singular | `memory/`, `search/`, `agents/` |
| Component files | PascalCase | `MemoryView.tsx`, `SearchResults.tsx` |
| Hook files | camelCase with `use` prefix | `useMemorySearch.ts` |
| Type files | camelCase | `types.ts` |
| API files | camelCase | `api.ts` |
| Test files | `<name>.test.ts` | `useMemorySearch.test.ts` |

## Export Rules

1. **Public API:** `index.ts` is the ONLY file other features import from.
2. **Internal imports:** Features may import from `@/shared/` but NOT from other `@/features/*/` directories.
3. **Type imports:** Always use `import type { X }` for type-only imports.
4. **Re-exports:** `index.ts` re-exports everything consumers need. No deep imports.

## Dependency Rules

1. **Features depend on shared, never on each other.** `features/memory/` cannot import from `features/search/`.
2. **Shared is the integration layer.** If two features need to share data, it goes in `shared/`.
3. **No circular dependencies.** Feature → Shared → Feature is forbidden.
4. **API layer isolation:** Feature `api.ts` wraps `shared/api/` calls. Features never call `apiClient` directly.

## File Structure Rules

1. **Minimum files per feature:** `index.ts`, `types.ts`, `api.ts` (3 files).
2. **Components directory:** Required if feature has UI. Empty `components/index.ts` if no components yet.
3. **Hooks directory:** Required if feature has state logic. Empty `hooks/index.ts` if no hooks yet.
4. **Tests directory:** Required. At minimum, a smoke test that verifies the feature module loads.

## Lazy Loading

1. **Every feature module is lazy-loaded** via `React.lazy()` in the router.
2. **Route definition** imports from `@/features/<feature>/index.ts`.
3. **No feature is eagerly imported** in the root layout (except shared providers).

## Code Style

1. **Functional components only** — no class components.
2. **Hooks for state** — no raw `useState` in components deeper than 1 level.
3. **Error boundaries** — each feature wraps its route in an error boundary.
4. **Suspense** — each lazy-loaded feature shows a skeleton during loading.
