# Fix: Registration Modal Bugs

**Commit:** `d025c67` — `fix: registration modal bugs — validation race, positioning, a11y, error handling`

## Summary

Fixed 11 bugs across `app/auth/page.tsx`, `src/shared/ui/Input.tsx`, and `app/auth/signup/page.test.tsx`. All fixes preserve existing layout, design, form logic, validation, and API calls.

## Files Modified

- `frontend/app/auth/page.tsx` — 10 fixes
- `frontend/src/shared/ui/Input.tsx` — 1 fix
- `frontend/app/auth/signup/page.test.tsx` — test updated for new behavior

## Fixes Applied

### Critical

1. **Step connector positioning** — Added `relative` to the connector `<div>` so the `absolute`-positioned gray background track renders correctly.
2. **Username validation race** — Set `usernameStatus` to `"checking"` immediately when `username` changes (before the 400ms debounce), preventing stale status from being used.
3. **Null assertion on `data.user!`** — Added null checks before calling `login(data.user)` in both `handleRegister` and `handleLogin`. Shows error if user data is missing.

### Medium

4. **Block "checking" in validateStep** — Added guard: if `usernameStatus === "checking"`, validation fails with "Still checking username availability...".
5. **Reset all form fields on mode switch** — `switchMode()` now resets all 13 form state variables (username, password, confirm, full name, nickname, bio, ghUsername, ghToken, vaultPassword, vaultConfirm, storageRoot, storageCustom, usernameStatus).
6. **GitHub connection error handling** — `catch {}` replaced with `catch { setError("GitHub connection failed..."); }`. `ghToken` is now trimmed before passing to `apiConnectGitHub`.
7. **Password toggle tabIndex** — Changed from `tabIndex={-1}` to `tabIndex={0}` so the button is keyboard-accessible.
8. **ARIA on step indicator** — Added `role="tablist"` to step container, `role="tab"` and `aria-selected` to each step circle.
9. **role="alert" on errors** — Both login and register error `<p>` tags now have `role="alert"` for screen reader announcements.
10. **Bio label association** — Added `htmlFor="bio"` to label and `id="bio"` to textarea.

### Low

11. **Removed unused `Steps` import** — Deleted `import Steps from "../../src/shared/ui/Steps";`.

## Test Update

Updated `app/auth/signup/page.test.tsx` to wait for the username availability check to resolve (the "Checking availability..." text to disappear) before clicking "Continue", matching the new behavior where "checking" status blocks step progression.

## Build & Test Results

- **Build:** ✅ Compiled successfully (warnings are pre-existing, unrelated to this change)
- **Tests:** ✅ 9/9 passed (3 test files)
