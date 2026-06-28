# Awareness Dashboard Design Spec

## Overview

Three-page Awareness system: `/awareness` (overview dashboard), `/awareness/repos` (repository management), `/awareness/indexing` (configuration). Maps 24 backend endpoints across 7 sub-domains to real UI.

## Pages

### 1. /awareness — Overview Dashboard

**Purpose:** System at a glance — device, environment, health, project.

**Layout:** Summary card grid (2x2 desktop, stacked mobile).

**Cards:**

1. **Device Card** — hostname, OS, CPU model/cores, total/available RAM, disk total/used, Python version. Color-coded RAM/disk bars. Last checked timestamp.
2. **Environment Card** — Safe environment variables (filtered list). System paths. Working directory.
3. **Health Card** — Status indicator (healthy/degraded/error), indexing active flag, watched count, last scan time.
4. **Project Card** — Last scanned project: type, name, frameworks, has_tests/has_ci/has_docker badges. "Scan Project" button to trigger `GET /awareness/project/scan?project_path=...`.

**Header:** "Awareness" title, subtitle "System awareness and repository management".

**Actions:** "Scan Project" button triggers project detection with path input.

### 2. /awareness/repos — Repository Management

**Purpose:** CRUD, indexing, graph building for repositories.

**Layout:** List view with add button.

**Header:** "Repositories" title, "Add Repository" button.

**Repo List Items:**
- Repo name (bold)
- Path (mono, muted)
- Primary language badge
- Status dot (pending/indexing/indexed/error)
- File count + chunk count
- Last indexed timestamp
- Actions: Index, Build Graph, View Graph, Delete

**Add Repository Modal:**
- Name input
- Path input with validation
- Submit creates via `POST /awareness/repos`

**Index Status:**
- Click "Index" triggers `POST /awareness/repos/{id}/index`
- Shows inline progress: files scanned, indexed, pending, errors
- Status polling via `GET /awareness/repos/{id}/status`

**Graph View:**
- Click "View Graph" opens `GET /awareness/repos/{id}/graph`
- Simple node/edge display (CSS-based, no library)
- Click node shows context via `GET /awareness/repos/{id}/graph/node/{node_id}`

**Delete:**
- Confirmation modal
- Calls `DELETE /awareness/repos/{id}`

### 3. /awareness/indexing — Configuration

**Purpose:** Manage indexing rules and preview.

**Layout:** Form-based config editor.

**Sections:**
1. **Include Paths** — list of paths to index
2. **Exclude Paths** — list of paths to skip
3. **Include Patterns** — glob patterns to include
4. **Exclude Patterns** — glob patterns to exclude
5. **Settings** — max file size, follow symlinks, sync enabled, sync interval, priority

**Actions:**
- "Save" saves via `PUT /awareness/indexing/config`
- "Preview" shows what would be indexed via `POST /awareness/indexing/preview?repo_path=...`

**Preview Results:**
- Files that would be indexed
- Files that would be skipped
- Estimated time

## API Client

The existing `features/awareness/api.ts` already covers all endpoints with correct types. No changes needed to the API layer — it was already built correctly.

## Components to Create

```
frontend/src/features/awareness/
├── page.tsx                    # Overview dashboard
├── repos/
│   └── page.tsx               # Repository management
├── indexing/
│   └── page.tsx               # Configuration editor
└── components/
    ├── DeviceCard.tsx          # Device info card
    ├── EnvironmentCard.tsx     # Environment vars card
    ├── HealthCard.tsx          # Health status card
    ├── ProjectCard.tsx         # Project detection card
    ├── RepoListItem.tsx        # Repository list item
    ├── AddRepoModal.tsx        # Add repository modal
    ├── IndexProgress.tsx       # Indexing progress display
    ├── GraphView.tsx           # Knowledge graph display
    └── IndexingConfigForm.tsx  # Config editor form
```

Route pages:
```
frontend/src/app/awareness/page.tsx           → re-export
frontend/src/app/awareness/repos/page.tsx     → re-export
frontend/src/app/awareness/indexing/page.tsx  → re-export
```

## Sidebar Update

Add "Awareness" nav link between "Models" and "System":
```typescript
{ name: "Awareness", href: "/awareness", icon: "eye" },
```

Icon: eye (SVG).

## State Management

- Overview: Component-local state, fetches on mount
- Repos: Component-local state, CRUD operations
- Indexing: Component-local state, form state

## Error Handling

- Each card handles its own errors independently
- Repo operations show inline error messages
- Indexing shows error count in status

## Loading States

- Card skeletons for overview
- List skeleton for repos
- Form disabled state while saving

## Responsive

- Desktop: 2x2 card grid for overview
- Tablet: 2-column grid
- Mobile: Stacked cards
- Repo list: Full width on all sizes

## Accessibility

- Cards use `role="article"` with `aria-label`
- Status dots have `aria-label` for state
- Form inputs have proper labels
- Focus-visible rings on all interactive elements
- Keyboard navigation in repo list

## Anti-Slop Compliance

- No transition-all, h-screen, gradient text, glassmorphism
- No identical card grids (each card has unique content/layout)
- No eyebrows or numbered sections
- Side-stripe borders: none
- Geist font throughout, JetBrains Mono for code/paths

## Files Summary

| Action | File |
|--------|------|
| Create | `features/awareness/page.tsx` |
| Create | `features/awareness/repos/page.tsx` |
| Create | `features/awareness/indexing/page.tsx` |
| Create | `features/awareness/components/DeviceCard.tsx` |
| Create | `features/awareness/components/EnvironmentCard.tsx` |
| Create | `features/awareness/components/HealthCard.tsx` |
| Create | `features/awareness/components/ProjectCard.tsx` |
| Create | `features/awareness/components/RepoListItem.tsx` |
| Create | `features/awareness/components/AddRepoModal.tsx` |
| Create | `features/awareness/components/IndexProgress.tsx` |
| Create | `features/awareness/components/GraphView.tsx` |
| Create | `features/awareness/components/IndexingConfigForm.tsx` |
| Create | `app/awareness/page.tsx` |
| Create | `app/awareness/repos/page.tsx` |
| Create | `app/awareness/indexing/page.tsx` |
| Modify | `shared/layout/Sidebar.tsx` |
| **Total** | **15 created, 1 modified** |
