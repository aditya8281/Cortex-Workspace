# Task 16: Update Tests and Fix Build Issues

## Status: DONE

## Summary

Build was already passing. Fixed 3 failing test files to match the redesigned auth page structure:

1. **`app/auth/login/page.test.tsx`** — Updated selectors for the split-layout auth page:
   - `"Cortex"` heading now appears twice (desktop panel + mobile header) → use `getAllByText`
   - `"Welcome back"` text no longer exists → replaced with `/Local-first/` regex check (also appears multiple times)

2. **`app/auth/signup/page.test.tsx`** — Updated selectors for the new wizard flow:
   - Step labels are now split across two `<span>` elements instead of one text node (`"Step 1 of 4 — Account"` → just `"Account"`)
   - Added `waitFor` for form placeholders before interaction (AnimatePresence transition delay)
   - Changed step indicators to wait for actual form content (`"Skip for now"`, `"Vault password"`) instead of step labels

## Test Results
- **9/9 tests passing** (Button: 2, Login: 4, Signup: 3)
- Build: ✅ passes
- Lint: ✅ no errors (only pre-existing `react-hooks/set-state-in-effect` warnings)

## Commit
- `311e58b` — fix: update tests and fix build issues for redesign
