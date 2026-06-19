# Cortex Frontend Redesign — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the entire Cortex frontend with a cinematic, AI-native "Neural Dark" interface featuring spring-physics animations, 3D effects, command palette, and a responsive adaptive layout.

**Architecture:** Next.js 15 App Router with framer-motion for animations, react-three-fiber for 3D landing hero, Radix UI primitives for accessible components, cmdk for command palette, and sonner for toasts. All built on a monochrome dark canvas with electric cyan accent.

**Tech Stack:** Next.js 15, React 19, TypeScript, Tailwind CSS 3.4, framer-motion, lucide-react, @radix-ui/react-dialog, @radix-ui/react-dropdown-menu, @radix-ui/react-tooltip, cmdk, sonner, three, @react-three/fiber, @react-three/drei, clsx, tailwind-merge

## Status

**Completed:** All 17 tasks implemented and committed. Neural Dark frontend is live.

**Post-Task Fixes:** Additional bug fixes applied after initial implementation (see "Post-Task Fixes" section below).

**Final Build:** Passes `npm run build`, `npm run lint`, and `npm run test -- --run`.

**Commit Range:** `56aec7e` → `5d4df6e` (23 commits total including post-task fixes)

## Global Constraints

- Next.js 15.3+ with App Router (file-system routing)
- React 19.1+
- TypeScript 5.8+ strict mode
- Tailwind CSS 3.4 with custom design tokens
- Dark mode only (hardcoded `className="dark"`)
- All API contracts unchanged (cortexApi.ts preserved)
- Auth flow unchanged (httpOnly cookies, JWT)
- Must pass `npm run build`, `npm run lint`, `npm run test`
- Responsive: 375px / 768px / 1024px / 1440px
- `prefers-reduced-motion` support required

---

## Phase 1: Foundation

### Task 1: Install Dependencies & Configure Utilities

**Files:**
- Modify: `frontend/package.json`
- Create: `frontend/src/lib/utils.ts`
- Create: `frontend/src/lib/motion.ts`

**Interfaces:**
- Produces: `cn()` utility function, `motionVariants` constants

- [x] **Step 1: Install all new dependencies** `56aec7e`

- [x] **Step 2: Create cn() utility** `56aec7e`

- [x] **Step 3: Create motion variants** `56aec7e`

- [x] **Step 4: Verify build** `56aec7e`

- [x] **Step 5: Commit** `56aec7e`

---

### Task 2: Update Design Tokens & Global Styles

**Files:**
- Modify: `frontend/src/shared/design/tokens.ts`
- Modify: `frontend/app/globals.css`
- Modify: `frontend/tailwind.config.ts`

**Interfaces:**
- Consumes: Nothing
- Produces: Updated token system, new CSS utility classes

- [x] **Step 1: Update design tokens** `39be089`

- [x] **Step 2: Update Tailwind config** `39be089`

- [x] **Step 3: Update global CSS** `39be089`

- [x] **Step 4: Verify build** `39be089`

- [x] **Step 5: Commit** `39be089`

---

### Task 3: Update Root Layout with Geist Font

**Files:**
- Modify: `frontend/app/layout.tsx`

**Interfaces:**
- Consumes: tokens from Task 2
- Produces: Updated root layout with Geist font

- [x] **Step 1: Update root layout** `cac4bb1`

- [x] **Step 2: Download Geist font** `cac4bb1`

- [x] **Step 3: Verify build** `cac4bb1`

- [x] **Step 4: Commit** `cac4bb1`

---

## Phase 2: Core UI Components

### Task 4: Build New Button Component

**Files:**
- Modify: `frontend/src/shared/ui/Button.tsx`

**Interfaces:**
- Consumes: `cn()` from `src/lib/utils`
- Produces: `<Button>` component with primary/secondary/ghost/danger variants, sizes, loading state, glow effect

- [x] **Step 1: Replace Button component** `63ccb9d`

- [x] **Step 2: Run Button test** `63ccb9d`

- [x] **Step 3: Verify build** `63ccb9d`

- [x] **Step 4: Commit** `63ccb9d`

---

### Task 5: Build New Input Component

**Files:**
- Modify: `frontend/src/shared/ui/Input.tsx`

**Interfaces:**
- Consumes: `cn()` from `src/lib/utils`
- Produces: `<Input>` component with floating label, focus glow, error state, password toggle

- [x] **Step 1: Replace Input component** `ea08ec5`

- [x] **Step 2: Verify build** `ea08ec5`

- [x] **Step 3: Commit** `ea08ec5`

---

### Task 6: Build New Card, Badge, Skeleton, Tooltip, Modal, Dropdown, Toast Components

**Files:**
- Modify: `frontend/src/shared/ui/Card.tsx`
- Create: `frontend/src/shared/ui/Badge.tsx`
- Create: `frontend/src/shared/ui/Skeleton.tsx`
- Create: `frontend/src/shared/ui/Tooltip.tsx`
- Create: `frontend/src/shared/ui/Modal.tsx`
- Create: `frontend/src/shared/ui/Dropdown.tsx`
- Create: `frontend/src/shared/ui/Toast.tsx`
- Create: `frontend/src/lib/utils.ts` (already created in Task 1)

**Interfaces:**
- Consumes: `cn()` from `src/lib/utils`
- Produces: All reusable UI components

- [x] **Step 1: Update Card component** `c53f400`

- [x] **Step 2: Create Badge component** `c53f400`

- [x] **Step 3: Create Skeleton component** `c53f400`

- [x] **Step 4: Create Tooltip component** `c53f400`

- [x] **Step 5: Create Modal component** `c53f400`

- [x] **Step 6: Create Dropdown component** `c53f400`

- [x] **Step 7: Create Toast component** `c53f400`

- [x] **Step 8: Verify build** `c53f400`

- [x] **Step 9: Commit** `c53f400`

---

### Task 7: Build Animation Wrapper Components

**Files:**
- Create: `frontend/src/shared/ui/PageTransition.tsx`
- Create: `frontend/src/shared/ui/StaggerChildren.tsx`
- Create: `frontend/src/shared/ui/GlowOrb.tsx`

**Interfaces:**
- Consumes: framer-motion, `cn()` from `src/lib/utils`
- Produces: Reusable animation wrapper components

- [x] **Step 1: Create PageTransition component** `f4a496e`

- [x] **Step 2: Create StaggerChildren component** `f4a496e`

- [x] **Step 3: Create GlowOrb component** `f4a496e`

- [x] **Step 4: Verify build** `f4a496e`

- [x] **Step 5: Commit** `f4a496e`

---

## Phase 3: Layout System

### Task 8: Build New DashboardShell with Adaptive Navigation

**Files:**
- Modify: `frontend/src/shared/layout/DashboardShell.tsx`

**Interfaces:**
- Consumes: `useAuth()`, `getProfilePhotoUrl()`, `cn()`, framer-motion
- Produces: Responsive layout with collapsible sidebar (desktop), bottom nav (mobile)

- [x] **Step 1: Replace DashboardShell** `3260836`

- [x] **Step 2: Verify build** `3260836`

- [x] **Step 3: Commit** `3260836`

---

## Phase 4: Page Redesigns

### Task 9: Redesign Landing Page

**Files:**
- Modify: `frontend/app/page.tsx`

**Interfaces:**
- Consumes: framer-motion, lucide-react, GlowOrb, StaggerChildren
- Produces: Immersive hero with animated particle network, feature cards

- [x] **Step 1: Replace landing page** `da7e178`

- [x] **Step 2: Verify build** `da7e178`

- [x] **Step 3: Commit** `da7e178`

---

### Task 10: Redesign Auth Page

**Files:**
- Modify: `frontend/app/auth/page.tsx`

**Interfaces:**
- Consumes: All UI components (Button, Input, Card, Steps, PasswordStrength, Modal)
- Produces: Redesigned auth with split layout, animated wizard

- [x] **Step 1: Replace auth page** `1a2ecdd`

- [x] **Step 2: Verify build** `1a2ecdd`

- [x] **Step 3: Commit** `1a2ecdd`

---

### Task 11: Redesign Dashboard Page

**Files:**
- Modify: `frontend/app/app/page.tsx`

**Interfaces:**
- Consumes: DashboardShell, Card, Badge, Button, PageTransition, StaggerChildren
- Produces: Command center dashboard with stat cards, quick actions, activity

- [x] **Step 1: Replace dashboard page** `c843721`

- [x] **Step 2: Verify build** `c843721`

- [x] **Step 3: Commit** `c843721`

---

### Task 12: Redesign Vault Page

**Files:**
- Modify: `frontend/app/vault/page.tsx`
- Modify: `frontend/app/vault/VaultLayout.tsx`
- Modify: `frontend/app/vault/VaultSidebar.tsx`
- Modify: `frontend/app/vault/VaultToolbar.tsx`
- Modify: `frontend/app/vault/VaultFileList.tsx`
- Modify: `frontend/app/vault/VaultLockScreen.tsx`
- Modify: `frontend/app/vault/VaultModals.tsx`
- Modify: `frontend/app/vault/VaultProperties.tsx`
- Modify: `frontend/app/vault/useVaultState.ts`

**Interfaces:**
- Consumes: All UI components, framer-motion
- Produces: Redesigned vault with glass panels, smooth animations

- [x] **Step 1: Redesign VaultLockScreen** `fe76c9d`

- [x] **Step 2: Redesign VaultSidebar** `fe76c9d`

- [x] **Step 3: Redesign VaultToolbar** `fe76c9d`

- [x] **Step 4: Redesign VaultFileList** `fe76c9d`

- [x] **Step 5: Redesign VaultProperties** `fe76c9d`

- [x] **Step 6: Redesign VaultModals** `fe76c9d`

- [x] **Step 7: Redesign VaultLayout** `fe76c9d`

- [x] **Step 8: Verify build** `fe76c9d`

- [x] **Step 9: Commit** `fe76c9d`

---

### Task 13: Redesign Memory, Profile, Settings, Admin Pages

**Files:**
- Modify: `frontend/app/memory/page.tsx`
- Modify: `frontend/app/profile/page.tsx`
- Modify: `frontend/app/settings/page.tsx`
- Modify: `frontend/app/admin/page.tsx`

**Interfaces:**
- Consumes: DashboardShell, all UI components, framer-motion
- Produces: Redesigned secondary pages

- [x] **Step 1: Redesign Memory page** `0e1633e`

- [x] **Step 2: Redesign Profile page** `0e1633e`

- [x] **Step 3: Redesign Settings page** `0e1633e`

- [x] **Step 4: Redesign Admin page** `0e1633e`

- [x] **Step 5: Verify build** `0e1633e`

- [x] **Step 6: Commit** `0e1633e`

---

## Phase 5: Command Palette & Integration

### Task 14: Build Command Palette

**Files:**
- Create: `frontend/src/shared/ui/CommandPalette.tsx`
- Modify: `frontend/src/shared/layout/DashboardShell.tsx` (add ⌘K trigger)

**Interfaces:**
- Consumes: cmdk, framer-motion, lucide-react
- Produces: ⌘K command palette with search across all pages

- [x] **Step 1: Create CommandPalette component** `5fea4e6`

- [x] **Step 2: Add ⌘K trigger to DashboardShell** `5fea4e6`

- [x] **Step 3: Verify build** `5fea4e6`

- [x] **Step 4: Commit** `5fea4e6`

---

### Task 15: Integrate Toast Notifications

**Files:**
- Modify: `frontend/app/layout.tsx` (add ToastProvider)
- Modify: `frontend/src/shared/auth/AuthProvider.tsx` (add toast on login/logout)

**Interfaces:**
- Consumes: ToastProvider from `src/shared/ui/Toast`
- Produces: Toast notifications for auth events

- [x] **Step 1: Add ToastProvider to root layout** `85f7d87`

- [x] **Step 2: Add toast notifications to AuthProvider** `85f7d87`

- [x] **Step 3: Verify build** `85f7d87`

- [x] **Step 4: Commit** `85f7d87`

---

## Phase 6: Testing & Polish

### Task 16: Update Tests and Fix Build Issues

**Files:**
- Modify: `frontend/src/shared/ui/Button.test.tsx` (update for new variants)
- Modify: `frontend/app/auth/login/page.test.tsx` (update selectors)
- Modify: `frontend/app/auth/signup/page.test.tsx` (update selectors)

**Interfaces:**
- Consumes: All updated components
- Produces: Passing test suite

- [x] **Step 1: Update Button test** `311e58b`

- [x] **Step 2: Update auth tests** `311e58b`

- [x] **Step 3: Run all tests** `311e58b`

- [x] **Step 4: Run lint** `311e58b`

- [x] **Step 5: Run build** `311e58b`

- [x] **Step 6: Commit** `311e58b`

---

### Task 17: Final Polish — Accessibility, Responsive, Reduced Motion

**Files:**
- Modify: `frontend/app/globals.css` (add prefers-reduced-motion)
- Modify: `frontend/src/shared/layout/DashboardShell.tsx` (mobile polish)
- Modify: Various page files (final responsive adjustments)

**Interfaces:**
- Consumes: All components
- Produces: Production-ready, accessible, responsive application

- [x] **Step 1: Add prefers-reduced-motion support** `3253d02`

- [x] **Step 2: Add skip-to-content link** `3253d02`

- [x] **Step 3: Verify all focus rings visible** `3253d02`

- [x] **Step 4: Test responsive breakpoints** `3253d02`

- [x] **Step 5: Final build + test** `3253d02`

- [x] **Step 6: Commit** `3253d02`

---

## Post-Task Fixes

Additional bug fixes applied after the initial 17-task implementation.

### Backend Auth: Cookie Fallback `d938c08`
- Added cookie-based auth fallback to `get_current_user` and CSRF validation
- Ensures requests with cookies (no Authorization header) are properly authenticated

### Frontend Auth: Cookie Forwarding & Token Refresh `15a6316`
- Cookie forwarding in API proxy for authenticated requests
- Token refresh logic for expired JWTs
- Type fixes for auth-related interfaces

### Register Modal: Validation & UX Fixes `d025c67`
- Fixed validation race condition in multi-step form
- Fixed modal positioning on smaller viewports
- Added accessibility attributes (aria-labels, focus management)
- Improved error handling with user-friendly messages

### CLI: Command Stubs & Syntax Fixes `5d4df6e`
- Added command stubs for new CLI commands
- Fixed syntax errors in command parsing

### Design System Documentation `3ff6b29`
- Updated DESIGN.md to reflect Neural Dark theme tokens and conventions

---

## Final Validation

| Check | Result |
|-------|--------|
| `npm run build` | Pass |
| `npm run lint` | Pass |
| `npm run test -- --run` | Pass |
| All 17 tasks committed | `56aec7e` → `3253d02` |
| Post-task fixes committed | `d938c08` → `5d4df6e` |
| Total commits | 23 |
