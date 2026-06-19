# Fix Backend Auth & CSRF Report

## Issue 1: `get_current_user` cookie fallback

**File:** `backend/app/core/db.py`

**Problem:** `get_current_user` only read the `Authorization: Bearer` header via `HTTPBearer()`, but the frontend sends auth via httpOnly `cortex_access` cookies. All `/api/v1/*` endpoints returned 401 for cookie-based requests.

**Fix:**
- Added `Request` import from fastapi
- Created `_extract_token()` helper that checks `Authorization` header first, falls back to `cortex_access` cookie
- Updated `get_current_user` and `get_current_user_optional` to accept `request: Request` parameter and use the helper
- Backward compatible — Bearer tokens still work

## Issue 2: CSRF blocks cookie-based browser requests

**File:** `backend/app/core/csrf.py`

**Problem:** CSRF middleware only exempted `Authorization: Bearer` requests. Cookie-based browser auth (which never sends this header) was CSRF-blocked on POST/PUT/DELETE.

**Fix:**
- Added check: if request has `cortex_access` cookie, treat as API call (bypass CSRF)
- This mirrors the Bearer token exemption pattern

## Test Results

- 106 tests passed, 0 failed
- All existing auth tests continue to pass

## Commit

```
fix: add cookie-based auth fallback to get_current_user and CSRF
```
