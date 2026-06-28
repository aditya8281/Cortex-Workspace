# Privacy & Trust Pages Design Spec

## Overview

Three-page Privacy system: `/privacy` (overview dashboard), `/privacy/audit` (audit log viewer), `/privacy/consent` (consent management). Maps backend privacy endpoints to real UI.

Vault already has its own page at `/vault`. This covers the remaining privacy sub-domains.

## Backend Endpoints

| Sub-domain | Endpoints | Count |
|-----------|-----------|-------|
| Vault | unlock, lock, status, files, upload, preview, download, delete, rename, move, metadata, createFolder, search, export, changePassword | Already at /vault |
| Access Control | check, roles, permissions, assignRole, removeRole | 5 |
| Audit | logs, count, activity | 3 |
| Consent | list, check, grant, revoke | 4 |
| Export | create, process, verify | 3 |
| Settings | usageStats, sync, storage, updates, getSettings, updateSettings, refreshCatalogue | 7 |
| Transparency | explain, templates | 2 |

**Total non-vault endpoints:** 24

## Pages

### 1. /privacy — Overview Dashboard

**Purpose:** Privacy status at a glance — access control, consent status, storage, export.

**Layout:** Summary card grid (2×2 desktop).

**Cards:**

1. **Access Control Card** — Current user's roles, permission count. "Manage Roles" link to access control details.
2. **Consent Card** — Number of consents granted vs total. Toggle switches for each consent scope. Quick grant/revoke.
3. **Storage Card** — Total storage used, breakdown by type (vault, database). Visual bar chart.
4. **Data Export Card** — Last export status. "Export Data" button triggers export flow.

**Header:** "Privacy & Trust" title, subtitle "Data privacy, access control, and consent management".

**Actions:**
- "Export Data" button → triggers `POST /privacy/export/create`
- "Sync Models" button → triggers `POST /privacy/models/sync`

### 2. /privacy/audit — Audit Log Viewer

**Purpose:** View and filter audit logs.

**Layout:** Filterable table/list.

**Header:** "Audit Log" title, total count badge.

**Filters:**
- Action filter (dropdown: all, login, logout, create, update, delete, etc.)
- User filter (text input)
- Date range (start/end date inputs)

**Log List Items:**
- Timestamp (relative: "2 hours ago")
- Action badge (color-coded: green for read, blue for create, yellow for update, red for delete)
- Resource type + ID
- IP address
- Success/failure indicator
- Error details (expandable)

**Pagination:** "Load More" button or infinite scroll.

**Empty state:** "No audit logs found" with filter reset button.

### 3. /privacy/consent — Consent Management

**Purpose:** View and manage consent preferences.

**Layout:** List of consent items with toggle switches.

**Header:** "Consent Management" title, subtitle "Control what data is collected and how it's used".

**Consent List:**
- Consent scope name (bold)
- Description (muted text)
- Toggle switch (on/off)
- Granted date (when toggled on)
- Revoked date (when toggled off)

**Actions:**
- Toggle switch calls `POST /privacy/consent/grant` or `POST /privacy/consent/revoke`
- "Grant All" button
- "Revoke All" button

**Empty state:** "All consent preferences are managed here" with info text.

## Components

```
frontend/src/features/privacy/
├── page.tsx                    # Overview dashboard
├── audit/
│   └── page.tsx               # Audit log viewer
├── consent/
│   └── page.tsx               # Consent management
└── components/
    ├── AccessControlCard.tsx   # Roles + permissions summary
    ├── ConsentCard.tsx         # Consent status with toggles
    ├── StorageCard.tsx         # Storage usage breakdown
    ├── ExportCard.tsx          # Data export action
    ├── AuditLogItem.tsx        # Single audit log entry
    └── ConsentToggle.tsx       # Reusable consent toggle
```

Route pages:
```
frontend/src/app/privacy/page.tsx           → re-export
frontend/src/app/privacy/audit/page.tsx     → re-export
frontend/src/app/privacy/consent/page.tsx   → re-export
```

## Sidebar Update

Add "Privacy" nav link between "Settings" and end of nav:
```typescript
{ name: "Privacy", href: "/privacy", icon: "shield" },
```

Icon: shield (SVG).

## State Management

- Overview: Component-local state per card
- Audit: Component-local state with filter params
- Consent: Component-local state with optimistic toggles

## Error Handling

- Each card handles its own errors independently
- Audit filters show "No results" on empty
- Consent toggles revert on failure

## Loading States

- Card skeletons for overview
- Table skeleton for audit list
- Toggle disabled while saving

## Responsive

- Desktop: 2×2 card grid for overview
- Tablet: 2-column grid
- Mobile: Stacked cards
- Audit table: Card layout on mobile (hide less important columns)

## Accessibility

- Cards use `role="article"` with `aria-label`
- Toggle switches have `role="switch"` with `aria-checked`
- Audit log items have proper semantic structure
- Focus-visible rings on all interactive elements
- Keyboard navigation in consent list

## Anti-Slop Compliance

- No transition-all, h-screen, gradient text, glassmorphism
- No identical card grids (each card has unique content)
- No eyebrows or numbered sections
- Geist font throughout, JetBrains Mono for timestamps/codes

## Files Summary

| Action | File |
|--------|------|
| Create | `features/privacy/page.tsx` |
| Create | `features/privacy/audit/page.tsx` |
| Create | `features/privacy/consent/page.tsx` |
| Create | `features/privacy/components/AccessControlCard.tsx` |
| Create | `features/privacy/components/ConsentCard.tsx` |
| Create | `features/privacy/components/StorageCard.tsx` |
| Create | `features/privacy/components/ExportCard.tsx` |
| Create | `features/privacy/components/AuditLogItem.tsx` |
| Create | `features/privacy/components/ConsentToggle.tsx` |
| Create | `app/privacy/page.tsx` |
| Create | `app/privacy/audit/page.tsx` |
| Create | `app/privacy/consent/page.tsx` |
| Modify | `shared/layout/Sidebar.tsx` |
| **Total** | **12 created, 1 modified** |
