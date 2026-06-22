# Frontend Audit Report — Cortex

Generated: 2026-06-22

---

## Summary

| Metric | Value |
| --- | --- |
| Pages | 13 |
| Sub-components | 35+ |
| Shared UI components | 20 |
| Design tokens | Follows DESIGN.md (Warm Neural Dark) |
| TypeScript types | 742 lines |
| Auth pattern | All pages check `useAuth()` → redirect to `/auth` |
| Animation pattern | framer-motion spring physics throughout |

---

## Per-Page Audit

### 1. Landing Page — `/` (`app/page.tsx`)

| Feature | Status | Notes |
| --- | --- | --- |
| Typewriter tagline | ✅ Complete | 60ms per char, blinking cursor |
| Feature cards (4) | ✅ Complete | Scroll-reveal with 3D tilt on hover |
| NeuralNetwork background | ✅ Complete | Animated SVG nodes/edges |
| CTA → `/auth` | ✅ Complete | "Get Started" + "Sign In" buttons |
| Design system compliance | ✅ | Uses `text-gradient-accent`, `glass-panel`, spring physics |
| Mobile responsive | ✅ | Grid cols adjust for sm/md/lg |

**Quality:** High. Clean, polished, on-brand. No issues found.

---

### 2. Auth Page — `/auth` (`app/auth/page.tsx`)

| Feature | Status | Notes |
| --- | --- | --- |
| Login form | ✅ Complete | Username + password, CSRF token |
| Registration wizard (4 steps) | ✅ Complete | Credentials → Profile → Skills → Complete |
| Password strength indicator | ✅ | Uses `PasswordStrength` component |
| Step validation | ✅ | Per-step validation before advancing |
| Form error display | ✅ | Per-field errors + toast |
| Redirect on success | ✅ | → `/app` dashboard |
| Design system compliance | ✅ | Uses `Steps`, `Input`, `Button`, `Card` |

**Quality:** High. 4-step wizard is well-structured. No issues found.

---

### 3. Dashboard — `/app` (`app/app/page.tsx`)

| Feature | Status | Notes |
| --- | --- | --- |
| User avatar + welcome | ✅ | Shows profile photo or icon fallback |
| Metric rings (CPU/RAM/Disk/GPU) | ✅ | `MetricRing` component with live WebSocket data |
| WebSocket live metrics | ✅ | `useSystemWebSocket` with HTTP fallback |
| Activity tab | ✅ | Recent system logs |
| Processes tab | ✅ | Sortable table with PID/CPU/Memory/Status |
| Insights tab | ✅ | Vault status, memory count, agent count, member since |
| SyncStatus indicator | ✅ | Shows sync state inline |
| Auth guard | ✅ | Redirects to `/auth` if not logged in |

**Quality:** High. WebSocket + HTTP fallback is robust. Activity tab could benefit from filtering/search but functional.

---

### 4. Search — `/search` (`app/search/page.tsx`)

| Feature | Status | Notes |
| --- | --- | --- |
| Unified search input | ✅ | Large, prominent search bar |
| AI-powered answer | ✅ | Calls `searchApi.answer()`, fallback to client-side synthesis |
| Result cards | ✅ | File path, score badge, content snippet |
| Source type icons | ✅ | Code/Document/Brain icons per result type |
| Empty state | ✅ | Helpful message when no results |
| Loading state | ✅ | Skeleton/shimmer during search |
| NeuralNetwork background | ✅ | Low intensity |

**Quality:** High. Clean search experience. AI answer with fallback is well-handled.

---

### 5. Agents — `/agents` (`app/agents/page.tsx`)

| Feature | Status | Notes |
| --- | --- | --- |
| Agent list | ✅ | Cards with name, description, model, status |
| Create new agent | ✅ | Opens `AgentEditor` modal |
| Edit agent | ✅ | Same `AgentEditor` with pre-filled fields |
| Delete agent | ✅ | With confirmation |
| Agent chat | ✅ | `AgentChat` component with SSE streaming |
| Run history | ✅ | Expandable step-by-step breakdown |
| Available models dropdown | ✅ | Fetches downloaded models |
| Tool selection | ✅ | search, read_file, write_file, list_files |
| SSE streaming for responses | ✅ | Real-time step status updates |
| Auth guard | ✅ | Redirects if not logged in |

**Quality:** High. `AgentEditor` has clean form with model/tool selection. `AgentChat` shows step execution with status icons. Well-structured.

---

### 6. Chat — `/chat` (`app/chat/page.tsx`)

| Feature | Status | Notes |
| --- | --- | --- |
| Conversation list sidebar | ✅ | Create, switch, delete conversations |
| Message history | ✅ | Load messages per conversation |
| SSE streaming responses | ✅ | Real-time token-by-token display |
| Source references | ✅ | File path badges per message |
| Model selector | ✅ | Dropdown of available models |
| Markdown rendering | ✅ | Uses `MarkdownRenderer` component |
| Abort/cancel generation | ✅ | `AbortController` ref |
| Auto-scroll | ✅ | Scrolls to bottom on new messages |
| Auth guard | ✅ | Redirects if not logged in |

**Quality:** High. Full-featured chat with streaming, sources, and model selection. Well-implemented.

---

### 7. Vault — `/vault` (`app/vault/page.tsx`)

| Feature | Status | Notes |
| --- | --- | --- |
| Lock screen | ✅ | `VaultLockScreen` — password entry |
| Unlock flow | ✅ | Derives key, decrypts vault |
| File listing | ✅ | `VaultFileList` with columns |
| Folder navigation | ✅ | `useVaultNavigation` hook |
| File upload | ✅ | Drag-and-drop + file picker |
| File download/decrypt | ✅ | On-demand decryption |
| File delete | ✅ | With confirmation |
| File preview | ✅ | `useVaultPreview` hook |
| Properties panel | ✅ | `VaultProperties` component |
| Toolbar | ✅ | `VaultToolbar` with actions |
| Sidebar | ✅ | `VaultSidebar` with path tree |
| Layout management | ✅ | `VaultLayout` for structure |
| Modals | ✅ | `VaultModals` for create/rename/etc |
| View modes | ✅ | Grid/list toggle via `useVaultView` |
| Selection state | ✅ | Multi-select via `useVaultSelection` |
| CRUD operations | ✅ | `useVaultCrud` hook |
| UI state management | ✅ | `useVaultUI` hook |
| Core state | ✅ | `useVaultCore` hook |
| Auth guard | ✅ | Redirects if not logged in |

**Quality:** Excellent. Most thoroughly decomposed page in the app. 7 custom hooks, clean separation of concerns. No issues found.

---

### 8. Memory — `/memory` (`app/memory/page.tsx`)

| Feature | Status | Notes |
| --- | --- | --- |
| Memory list | ✅ | Cards with title, category, tags |
| Semantic search | ✅ | `MemorySearch` with semantic toggle |
| Category filtering | ✅ | Color-coded category chips |
| Graph view | ✅ | Network visualization with `categoryNodeColors` |
| List view | ✅ | Table/card layout |
| Learning view | ✅ | Trending/decay visualization |
| Memory editor | ✅ | `MemoryEditor` modal — create/edit |
| Memory detail | ✅ | `MemoryDetail` modal — view/delete |
| Folder sync management | ✅ | `SyncStatusData`, `SyncJobData` states |
| Add watched path | ✅ | Dialog with repo path, embedding model, sync toggle |
| Initial scan progress | ✅ | Progress bar per watched path |
| Sync status display | ✅ | Real-time sync status via `syncApi` |
| Long-term memory section | ✅ | Decay visualization, search |
| NeuralNetwork background | ✅ | Medium intensity |
| Auth guard | ✅ | Redirects if not logged in |

**Quality:** High. Complex page with many features. Good state management. Graph/list/learning view toggle is well-implemented.

---

### 9. Models — `/models` (`app/models/ModelsPage.tsx`)

| Feature | Status | Notes |
| --- | --- | --- |
| Hardware overview | ✅ | `HardwareBar` component |
| Workload recommendations | ✅ | `RecommendedRow` with hardware-aware picks |
| Search/filter | ✅ | `SearchBar` with size filter (<3B, 3-8B, 8-14B, 14B+) |
| Category sections | ✅ | `CategorySection` — Code, Reasoning, Agents, Vision, etc |
| Model cards | ✅ | `ModelCard` with download/status actions |
| Download queue panel | ✅ | `DownloadQueuePanel` with active/queued/failed |
| Installed models panel | ✅ | `InstalledModelsPanel` |
| Model detail page | ✅ | `app/models/[id]/` for individual model view |
| WebSocket live progress | ✅ | `useSystemWebSocket` for download progress |
| Auth guard | ✅ | Redirects if not logged in |

**Quality:** High. Well-decomposed with dedicated sub-components. Hardware-aware recommendations are a strong feature.

---

### 10. Downloads — `/downloads` (`app/downloads/DownloadManagerPage.tsx`)

| Feature | Status | Notes |
| --- | --- | --- |
| Download queue display | ✅ | Active, queued, completed, failed sections |
| Progress tracking | ✅ | WebSocket for live progress |
| Pause/resume | ✅ | Action buttons per job |
| Retry failed | ✅ | Retry button |
| Cancel download | ✅ | Cancel button |
| ETA display | ✅ | `formatEta()` helper |
| Byte formatting | ✅ | `formatBytes()` helper |
| Auth guard | ✅ | Redirects if not logged in |

**Quality:** Good. Functional download manager. Could benefit from batch actions but core features complete.

---

### 11. Profile — `/profile` (`app/profile/page.tsx`)

| Feature | Status | Notes |
| --- | --- | --- |
| Avatar upload/crop | ✅ | Camera icon, file input, upload to `/api/v1/me/profile/photo` |
| Avatar removal | ✅ | Remove button with confirmation |
| Full name, nickname, bio | ✅ | Text inputs with save |
| Programming languages | ✅ | Tag input |
| Frameworks | ✅ | Tag input |
| Current projects | ✅ | Dynamic list with name + description |
| Contribution style | ✅ | Text input |
| Social links | ✅ | Twitter, LinkedIn, Website inputs |
| GitHub connection | ✅ | Username + token, connect/disconnect |
| Save with loading state | ✅ | `profileLoading`, `profileSaved` states |
| Auth guard | ✅ | Redirects if not logged in |

**Quality:** High. Comprehensive profile page with GitHub integration. Well-structured with clear sections.

---

### 12. Settings — `/settings` (`app/settings/page.tsx`)

| Feature | Status | Notes |
| --- | --- | --- |
| Account info display | ✅ | Username, role, user ID, storage root |
| Edit profile link | ✅ | → `/profile` |
| Preferences — accent color | ✅ | 4 color swatches (cyan/purple/green/amber) |
| Preferences — font size | ✅ | sm/md/lg toggle |
| Preferences — sidebar default | ✅ | expanded/collapsed toggle |
| Save preferences | ✅ | With loading + success feedback |
| Indexing configuration | ✅ | `IndexingConfigForm` — include/exclude paths, patterns, max file size, symlinks, sync interval |
| Indexing preview | ✅ | Preview path before saving |
| Indexing status | ✅ | Shows current indexing status |
| Delete account | ✅ | 2-step confirmation (click → password → permanent delete) |
| Auth guard | ✅ | Redirects if not logged in |

**Quality:** High. Well-organized with clear sections. 2-step account deletion is good UX. `IndexingConfigForm` is thorough.

---

### 13. Admin — `/admin` (`app/admin/page.tsx`)

| Feature | Status | Notes |
| --- | --- | --- |
| User list | ✅ | Table with avatar, name, email, role, joined date |
| Search users | ✅ | Filter by name/username/email |
| Promote to admin | ✅ | With confirmation |
| Demote from admin | ✅ | With confirmation |
| Delete user | ✅ | With confirmation |
| Admin role check | ✅ | Redirects non-admins to `/app` |
| Refresh user list | ✅ | Manual refresh button |
| Auth guard | ✅ | Redirects if not logged in |

**Quality:** Good. Functional admin panel. Could benefit from pagination for large user lists but sufficient for current scale.

---

## Design System Compliance

| Token | Used | Notes |
| --- | --- | --- |
| `bg-void` | ✅ | Base canvas on all pages |
| `bg-elevated` | ✅ | Cards, panels |
| `bg-surface` | ✅ | Interactive surfaces |
| `border-subtle` | ✅ | Hairline borders throughout |
| `text` / `text-secondary` / `text-muted` | ✅ | Consistent 3-tier text hierarchy |
| `accent` | ✅ | Cyan accent on all interactive elements |
| `glass-panel` | ✅ | Sidebar, cards |
| `text-gradient-accent` | ✅ | Landing page, headings |
| `micro-label` | ✅ | Uppercase mono labels |
| `focus-ring` | ✅ | Focus states on inputs/buttons |
| Spring animations | ✅ | framer-motion throughout |
| NeuralNetwork bg | ✅ | Landing, search, memory, models |

**Verdict:** Consistent design system usage across all pages. No rogue colors, fonts, or patterns detected.

---

## Shared Component Usage

| Component | Used By |
| --- | --- |
| `DashboardShell` | All authenticated pages |
| `Card` | All pages |
| `Button` | All pages with actions |
| `Input` | Auth, profile, settings, admin, vault |
| `Badge` | Agents, chat, memory, vault |
| `Modal` | Vault, memory, agents |
| `NeuralNetwork` | Landing, search, memory, models |
| `MetricRing` | Dashboard |
| `TabGroup` | Dashboard |
| `Skeleton` | Downloads, models |
| `Dropdown` | Chat, agents |
| `Tooltip` | Various |
| `ErrorBoundary` | Page-level error boundaries |
| `PageTransition` | Memory |
| `PasswordStrength` | Auth |
| `Steps` | Auth wizard |
| `StaggerChildren` | Various |
| `CollapsiblePanel` | Settings, memory |

---

## Issues Found

### Critical
None.

### Medium
1. **Memory page is 1310 lines** — should be decomposed into smaller sub-components (graph view, sync management, learning view are large inline blocks).

### Low
1. **Search page** — no keyboard shortcut (Cmd+K) for quick search from other pages.
2. **Chat page** — conversation list sidebar could show last message preview (currently just title).
3. **Admin page** — no pagination for user list (fine at current scale).
4. **Downloads page** — no batch cancel/retry for multiple failed downloads.
5. **Settings page** — accent color preference is saved but not applied globally (no CSS variable update).

---

## Recommendations

1. **Memory page decomposition** — Extract graph view, sync management, and learning view into separate components to reduce the 1310-line monolith.
2. **Global keyboard shortcuts** — Add Cmd+K command palette for quick navigation (already have `CommandPalette.tsx` in shared/ui but not wired up).
3. **Accent color persistence** — Wire the settings accent color preference to actually update CSS variables.
4. **Chat conversation previews** — Show last message snippet in conversation list.
5. **Download batch operations** — Add select-all + batch cancel/retry for failed downloads.

---

## Verdict

**Overall Quality: HIGH**

All 13 pages are functional, well-structured, and consistent with the Warm Neural Dark design system. The vault page is exceptionally well-decomposed with 7 custom hooks. The main area for improvement is the memory page size (1310 lines). All pages have proper auth guards, loading states, error handling, and use the shared component library consistently.
