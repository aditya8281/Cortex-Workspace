# Frontend Auth Fixes Report

## Changes Made

### 1. API Proxy Cookie Forwarding & DELETE Body (`app/api/[...path]/route.ts`)
- Added `Cookie` header forwarding from incoming requests to backend
- Removed `DELETE` from body exclusion list so DELETE requests can carry body payloads
- Refactored headers into a typed `proxyHeaders` object for clarity

### 2. Token Refresh Flow (`src/shared/auth/AuthProvider.tsx`)
- Added `apiRefresh` import from cortexApi
- Implemented automatic token refresh on 401 during bootstrap:
  - `apiGetMe()` → if 401, call `apiRefresh("")` (backend reads refresh token from cookie)
  - If refresh succeeds, retry `apiGetMe()`
  - If refresh fails, fall through to session clear + error toast

### 3. MemoryListResponse Pagination Fields (`src/shared/types.ts`)
- Added optional `total`, `offset`, and `limit` fields to `MemoryListResponse` interface

### 4. Logout (No Change Needed)
- `apiLogout("")` with empty string now works correctly because the proxy forwards cookies, allowing the backend's `_get_refresh_token()` to find the `cortex_refresh` cookie

## Verification

- **TypeScript:** `npx tsc --noEmit` — clean, no errors
- **Lint:** `next lint` — only pre-existing warnings (none from changes)
- **Tests:** `vitest run` — 9/9 passed (3 test files)
- **Build:** `next build` — fails with pre-existing module resolution errors for `/` and `/app` (unrelated to changes)

## Build Failure Note
The `next build` failure is pre-existing: `Cannot find module for page: /` and `/app`. This is a Next.js 15 module resolution issue unrelated to these changes. Pages exist at `app/page.tsx` and `app/app/page.tsx`.
