# Privacy & Trust Pages Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Three-page Privacy system — overview dashboard, audit log viewer, consent management — mapping 24 non-vault endpoints to real UI.

**Architecture:** Split into 3 route pages under `/privacy`. Components in `features/privacy/components/`. New API client needed.

**Tech Stack:** Next.js 15 App Router, React 19, TypeScript, Tailwind CSS.

## Global Constraints

- Dark-only. All colors from DESIGN.md tokens.
- Font: Geist (`font-sans`), JetBrains Mono (`font-mono`).
- No `transition-all`, `h-screen`, gradient text, glassmorphism, side-stripe borders.
- Accessibility: WCAG AA 4.5:1, `prefers-reduced-motion`, focus-visible rings, 44px min touch targets.
- Toggle switches: `role="switch"`, `aria-checked`.
- Cards: `role="article"`, `aria-label`.

## Backend Endpoints

| Sub-domain | Endpoints | Path |
|-----------|-----------|------|
| Access Control | check, roles, permissions, assignRole, removeRole | `/privacy/access/*` |
| Audit | logs, count, activity | `/privacy/audit/*` |
| Consent | list, check, grant, revoke | `/privacy/consent/*` |
| Export | create, process, verify | `/privacy/export/*` |
| Settings | usageStats, sync, storage, updates, getSettings, updateSettings, refreshCatalogue | `/privacy/settings/*` |
| Transparency | explain, templates | `/privacy/transparency/*` |

---

## File Structure

```
frontend/src/
├── features/privacy/
│   ├── api.ts                          # NEW — API client
│   ├── page.tsx                        # Overview dashboard
│   ├── audit/
│   │   └── page.tsx                    # Audit log viewer
│   ├── consent/
│   │   └── page.tsx                    # Consent management
│   └── components/
│       ├── AccessControlCard.tsx        # Roles + permissions
│       ├── ConsentCard.tsx              # Consent with toggles
│       ├── StorageCard.tsx              # Storage usage
│       ├── ExportCard.tsx               # Data export
│       ├── AuditLogItem.tsx             # Single audit entry
│       └── ConsentToggle.tsx            # Reusable toggle
├── app/privacy/
│   ├── page.tsx                        # Route → re-export
│   ├── audit/page.tsx                  # Route → re-export
│   └── consent/page.tsx                # Route → re-export
└── shared/layout/Sidebar.tsx           # Add Privacy nav link
```

---

### Task 1: Privacy API Client

**Files:**
- Create: `frontend/src/features/privacy/api.ts`

- [ ] **Step 1: Create API client**

```typescript
"use client";

import { apiFetch } from "@/shared/api/client";

// ── Types ───────────────────────────────────────────────────────────────

export interface AccessCheck {
  has_access: boolean;
  roles: string[];
  permissions: string[];
}

export interface AuditLogEntry {
  id: number;
  action: string;
  resource_type: string;
  resource_id: string | null;
  user_id: string | null;
  ip_address: string | null;
  timestamp: string;
  details: Record<string, unknown> | null;
  success: boolean;
  error_message: string | null;
}

export interface ConsentItem {
  id: number;
  scope: string;
  description: string;
  granted: boolean;
  granted_at: string | null;
  revoked_at: string | null;
}

export interface StorageInfo {
  total_bytes: number;
  vault_bytes: number;
  database_bytes: number;
}

// ── Access Control ───────────────────────────────────────────────────────

export const accessControl = {
  check: () => apiFetch<AccessCheck>("/privacy/access/check"),
  roles: () => apiFetch<string[]>("/privacy/access/roles"),
  permissions: () => apiFetch<string[]>("/privacy/access/permissions"),
};

// ── Audit ────────────────────────────────────────────────────────────────

export const audit = {
  logs: (params?: { action?: string; user?: string; limit?: number; offset?: number }) => {
    const searchParams = new URLSearchParams();
    if (params?.action) searchParams.set("action", params.action);
    if (params?.user) searchParams.set("user", params.user);
    if (params?.limit) searchParams.set("limit", String(params.limit));
    if (params?.offset) searchParams.set("offset", String(params.offset));
    const qs = searchParams.toString();
    return apiFetch<{ logs: AuditLogEntry[]; total: number }>(`/privacy/audit/logs${qs ? `?${qs}` : ""}`);
  },
};

// ── Consent ──────────────────────────────────────────────────────────────

export const consent = {
  list: () => apiFetch<ConsentItem[]>("/privacy/consent/list"),
  check: (scope: string) => apiFetch<{ granted: boolean }>(`/privacy/consent/check?scope=${scope}`),
  grant: (scope: string) => apiFetch<{ granted: boolean }>("/privacy/consent/grant", { method: "POST", body: { scope } }),
  revoke: (scope: string) => apiFetch<{ revoked: boolean }>("/privacy/consent/revoke", { method: "POST", body: { scope } }),
};

// ── Export ────────────────────────────────────────────────────────────────

export const dataExport = {
  create: () => apiFetch<{ export_id: string; status: string }>("/privacy/export/create", { method: "POST" }),
  verify: (exportId: string) => apiFetch<{ status: string; file_url?: string }>(`/privacy/export/verify?export_id=${exportId}`),
};

// ── Storage ──────────────────────────────────────────────────────────────

export const storage = {
  usage: () => apiFetch<StorageInfo>("/privacy/settings/usageStats"),
};

// ── Settings ─────────────────────────────────────────────────────────────

export const privacySettings = {
  getSettings: () => apiFetch<Record<string, unknown>>("/privacy/settings/getSettings"),
  updateSettings: (data: Record<string, unknown>) => apiFetch<void>("/privacy/settings/updateSettings", { method: "POST", body: data }),
};
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/features/privacy/
git commit -m "feat(privacy): create API client for privacy endpoints"
```

---

### Task 2: Sidebar + Route Pages

**Files:**
- Modify: `frontend/src/shared/layout/Sidebar.tsx`
- Create: `frontend/src/app/privacy/page.tsx`
- Create: `frontend/src/app/privacy/audit/page.tsx`
- Create: `frontend/src/app/privacy/consent/page.tsx`

- [ ] **Step 1: Add Privacy to Sidebar**

Add `{ name: "Privacy", href: "/privacy", icon: "shield" }` after Settings. Add shield SVG to iconMap:

```typescript
shield: (
  <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.5">
    <path d="M9 1.5L2.5 4.5v4c0 4.5 3.5 7.5 6.5 8.5 3-1 6.5-4 6.5-8.5v-4L9 1.5z" />
  </svg>
),
```

- [ ] **Step 2: Create route pages**

```tsx
// frontend/src/app/privacy/page.tsx
export { default } from "@/features/privacy/page";
```

```tsx
// frontend/src/app/privacy/audit/page.tsx
export { default } from "@/features/privacy/audit/page";
```

```tsx
// frontend/src/app/privacy/consent/page.tsx
export { default } from "@/features/privacy/consent/page";
```

- [ ] **Step 3: Build + commit**

```bash
cd frontend && npm run build 2>&1 | grep -E 'Compiled|error|Failed'
git add frontend/src/shared/layout/Sidebar.tsx frontend/src/app/privacy/
git commit -m "feat(privacy): add sidebar nav link and route pages"
```

---

### Task 3: ConsentToggle + ConsentCard + AccessControlCard + StorageCard + ExportCard

**Files:**
- Create: `frontend/src/features/privacy/components/ConsentToggle.tsx`
- Create: `frontend/src/features/privacy/components/ConsentCard.tsx`
- Create: `frontend/src/features/privacy/components/AccessControlCard.tsx`
- Create: `frontend/src/features/privacy/components/StorageCard.tsx`
- Create: `frontend/src/features/privacy/components/ExportCard.tsx`

- [ ] **Step 1: Create ConsentToggle**

```tsx
"use client";

import { useState } from "react";
import { consent as consentApi } from "../api";

interface ConsentToggleProps {
  scope: string;
  initialGranted: boolean;
  onToggle: (scope: string, granted: boolean) => void;
}

export function ConsentToggle({ scope, initialGranted, onToggle }: ConsentToggleProps) {
  const [granted, setGranted] = useState(initialGranted);
  const [saving, setSaving] = useState(false);

  const handleToggle = async () => {
    setSaving(true);
    try {
      if (granted) {
        await consentApi.revoke(scope);
        setGranted(false);
        onToggle(scope, false);
      } else {
        await consentApi.grant(scope);
        setGranted(true);
        onToggle(scope, true);
      }
    } catch {
      setGranted(granted); // revert
    } finally {
      setSaving(false);
    }
  };

  return (
    <button
      role="switch"
      aria-checked={granted}
      aria-label={`${granted ? "Revoke" : "Grant"} consent for ${scope}`}
      onClick={handleToggle}
      disabled={saving}
      className={`relative inline-flex h-5 w-9 flex-shrink-0 cursor-pointer rounded-full transition-colors duration-150 focus-visible:ring-2 focus-visible:ring-accent/50 focus-visible:outline-none disabled:opacity-50 ${
        granted ? "bg-accent" : "bg-bg-surface border border-border-default"
      }`}
    >
      <span
        className={`pointer-events-none inline-block h-4 w-4 rounded-full bg-white shadow-sm transition-transform duration-150 ease-out ${
          granted ? "translate-x-4" : "translate-x-0.5"
        } mt-0.5`}
      />
    </button>
  );
}
```

- [ ] **Step 2: Create ConsentCard**

```tsx
"use client";

import { useState, useEffect } from "react";
import { consent as consentApi } from "../api";
import type { ConsentItem } from "../api";
import { Card } from "@/shared/ui/Card";
import { Button } from "@/shared/ui/Button";

export function ConsentCard() {
  const [items, setItems] = useState<ConsentItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    consentApi.list().then(setItems).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const handleToggle = (scope: string, granted: boolean) => {
    setItems((prev) => prev.map((item) =>
      item.scope === scope ? { ...item, granted, granted_at: granted ? new Date().toISOString() : item.granted_at, revoked_at: granted ? null : new Date().toISOString() } : item
    ));
  };

  const handleGrantAll = async () => {
    for (const item of items) {
      if (!item.granted) {
        await consentApi.grant(item.scope).catch(() => {});
      }
    }
    setItems((prev) => prev.map((item) => ({ ...item, granted: true, granted_at: new Date().toISOString(), revoked_at: null })));
  };

  const handleRevokeAll = async () => {
    for (const item of items) {
      if (item.granted) {
        await consentApi.revoke(item.scope).catch(() => {});
      }
    }
    setItems((prev) => prev.map((item) => ({ ...item, granted: false, granted_at: null, revoked_at: new Date().toISOString() })));
  };

  if (loading) {
    return <Card className="p-4 animate-pulse"><div className="space-y-3">{Array.from({ length: 3 }).map((_, i) => <div key={i} className="h-10 rounded bg-bg-surface" />)}</div></Card>;
  }

  return (
    <Card className="p-4" role="article" aria-label="Consent status">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-text-primary">Consent</h3>
        <div className="flex gap-1.5">
          <Button size="sm" variant="ghost" onClick={handleGrantAll}>Grant All</Button>
          <Button size="sm" variant="ghost" className="text-danger" onClick={handleRevokeAll}>Revoke All</Button>
        </div>
      </div>
      <p className="text-xs text-text-muted mb-3">{items.filter((i) => i.granted).length} / {items.length} granted</p>
      <div className="space-y-2 text-xs">
        {items.slice(0, 4).map((item) => (
          <div key={item.scope} className="flex items-center justify-between">
            <span className="text-text-secondary">{item.scope}</span>
            <span className={`text-xs ${item.granted ? "text-success" : "text-text-muted"}`}>{item.granted ? "Granted" : "Revoked"}</span>
          </div>
        ))}
        {items.length > 4 && <p className="text-text-muted">+{items.length - 4} more</p>}
      </div>
    </Card>
  );
}
```

- [ ] **Step 3: Create AccessControlCard**

```tsx
"use client";

import { useState, useEffect } from "react";
import { accessControl } from "../api";
import { Card } from "@/shared/ui/Card";
import { Badge } from "@/shared/ui/Badge";
import { Button } from "@/shared/ui/Button";
import Link from "next/link";

export function AccessControlCard() {
  const [data, setData] = useState<{ roles: string[]; permissions: string[] } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([accessControl.roles().catch(() => []), accessControl.permissions().catch(() => [])])
      .then(([roles, permissions]) => setData({ roles, permissions }))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <Card className="p-4 animate-pulse"><div className="h-5 w-1/2 rounded bg-bg-surface" /></Card>;
  }

  return (
    <Card className="p-4" role="article" aria-label="Access control">
      <h3 className="text-sm font-semibold text-text-primary mb-3">Access Control</h3>
      <div className="space-y-2">
        <div>
          <p className="text-xs text-text-muted mb-1.5">Roles</p>
          <div className="flex flex-wrap gap-1.5">
            {data?.roles?.map((role) => <Badge key={role} variant="default">{role}</Badge>)}
            {(!data?.roles || data.roles.length === 0) && <span className="text-xs text-text-muted">No roles assigned</span>}
          </div>
        </div>
        <p className="text-xs text-text-muted">{data?.permissions?.length ?? 0} permissions</p>
      </div>
    </Card>
  );
}
```

- [ ] **Step 4: Create StorageCard**

```tsx
"use client";

import { useState, useEffect } from "react";
import { storage } from "../api";
import type { StorageInfo } from "../api";
import { Card } from "@/shared/ui/Card";

function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B";
  const gb = bytes / (1024 * 1024 * 1024);
  if (gb >= 1) return `${gb.toFixed(1)} GB`;
  const mb = bytes / (1024 * 1024);
  return `${mb.toFixed(0)} MB`;
}

export function StorageCard() {
  const [data, setData] = useState<StorageInfo | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    storage.usage().then(setData).catch(() => {}).finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <Card className="p-4 animate-pulse"><div className="h-5 w-1/2 rounded bg-bg-surface" /></Card>;
  }

  const vaultPercent = data && data.total_bytes > 0 ? Math.round((data.vault_bytes / data.total_bytes) * 100) : 0;
  const dbPercent = data && data.total_bytes > 0 ? Math.round((data.database_bytes / data.total_bytes) * 100) : 0;

  return (
    <Card className="p-4" role="article" aria-label="Storage usage">
      <h3 className="text-sm font-semibold text-text-primary mb-3">Storage</h3>
      {data ? (
        <div className="space-y-2 text-xs">
          <p className="text-text-secondary">{formatBytes(data.total_bytes)} total</p>
          <div className="space-y-1.5">
            <div>
              <div className="flex justify-between mb-0.5"><span className="text-text-muted">Vault</span><span className="text-text-secondary">{formatBytes(data.vault_bytes)}</span></div>
              <div className="h-1 rounded-full bg-bg-surface overflow-hidden">
                <div className="h-full rounded-full bg-accent transition-[width] duration-300" style={{ width: `${vaultPercent}%` }} />
              </div>
            </div>
            <div>
              <div className="flex justify-between mb-0.5"><span className="text-text-muted">Database</span><span className="text-text-secondary">{formatBytes(data.database_bytes)}</span></div>
              <div className="h-1 rounded-full bg-bg-surface overflow-hidden">
                <div className="h-full rounded-full bg-accent transition-[width] duration-300" style={{ width: `${dbPercent}%` }} />
              </div>
            </div>
          </div>
        </div>
      ) : (
        <p className="text-xs text-text-muted">Storage info unavailable</p>
      )}
    </Card>
  );
}
```

- [ ] **Step 5: Create ExportCard**

```tsx
"use client";

import { useState } from "react";
import { dataExport } from "../api";
import { Card } from "@/shared/ui/Card";
import { Button } from "@/shared/ui/Button";

export function ExportCard() {
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<string | null>(null);

  const handleExport = async () => {
    setLoading(true);
    setStatus(null);
    try {
      const result = await dataExport.create();
      setStatus(`Export ${result.export_id}: ${result.status}`);
    } catch {
      setStatus("Export failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="p-4" role="article" aria-label="Data export">
      <h3 className="text-sm font-semibold text-text-primary mb-3">Data Export</h3>
      <p className="text-xs text-text-muted mb-3">Export all your data from CORTEX</p>
      <Button size="sm" onClick={handleExport} disabled={loading}>{loading ? "Exporting..." : "Export Data"}</Button>
      {status && <p className="text-xs text-text-muted mt-2">{status}</p>}
    </Card>
  );
}
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/features/privacy/components/
git commit -m "feat(privacy): add ConsentToggle, ConsentCard, AccessControlCard, StorageCard, ExportCard"
```

---

### Task 4: Privacy Overview Page

**Files:**
- Create: `frontend/src/features/privacy/page.tsx`

- [ ] **Step 1: Create overview page**

```tsx
"use client";

import { useAuth } from "@/shared/auth/AuthProvider";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { AppShell } from "@/shared/layout/AppShell";
import { AccessControlCard } from "./components/AccessControlCard";
import { ConsentCard } from "./components/ConsentCard";
import { StorageCard } from "./components/StorageCard";
import { ExportCard } from "./components/ExportCard";

export default function PrivacyPage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) router.push("/auth");
  }, [user, loading, router]);

  if (loading || !user) return null;

  return (
    <AppShell>
      <div className="max-w-5xl space-y-6">
        <div>
          <h1 className="text-headline font-semibold text-text-primary">Privacy & Trust</h1>
          <p className="text-sm text-text-secondary mt-1">Data privacy, access control, and consent management</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <AccessControlCard />
          <ConsentCard />
          <StorageCard />
          <ExportCard />
        </div>
      </div>
    </AppShell>
  );
}
```

- [ ] **Step 2: Build + commit**

```bash
cd frontend && npm run build 2>&1 | grep -E 'Compiled|error|Failed'
git add frontend/src/features/privacy/page.tsx
git commit -m "feat(privacy): add overview dashboard page"
```

---

### Task 5: AuditLogItem + Audit Log Page

**Files:**
- Create: `frontend/src/features/privacy/components/AuditLogItem.tsx`
- Create: `frontend/src/features/privacy/audit/page.tsx`

- [ ] **Step 1: Create AuditLogItem**

```tsx
"use client";

import { useState } from "react";
import type { AuditLogEntry } from "../api";
import { Badge } from "@/shared/ui/Badge";

const actionColors: Record<string, string> = {
  create: "text-success",
  read: "text-success",
  login: "text-success",
  logout: "text-warning",
  update: "text-warning",
  delete: "text-danger",
};

function relativeTime(timestamp: string): string {
  const diff = Date.now() - new Date(timestamp).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "Just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

export function AuditLogItem({ entry }: { entry: AuditLogEntry }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="py-3 border-b border-border-subtle last:border-0">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <Badge variant={entry.success ? "success" : "danger"}>{entry.action}</Badge>
          <span className="text-xs text-text-secondary truncate">{entry.resource_type}{entry.resource_id ? ` / ${entry.resource_id}` : ""}</span>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          {entry.ip_address && <span className="text-[10px] text-text-muted font-mono">{entry.ip_address}</span>}
          <span className="text-[10px] text-text-muted" title={new Date(entry.timestamp).toLocaleString()}>{relativeTime(entry.timestamp)}</span>
        </div>
      </div>
      {entry.error_message && (
        <button onClick={() => setExpanded(!expanded)} className="text-[10px] text-danger mt-1 hover:underline cursor-pointer">
          {expanded ? entry.error_message : "Show error"}
        </button>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Create Audit page**

```tsx
"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/shared/auth/AuthProvider";
import { useRouter } from "next/navigation";
import { AppShell } from "@/shared/layout/AppShell";
import { Card } from "@/shared/ui/Card";
import { Button } from "@/shared/ui/Button";
import { Input } from "@/shared/ui/Input";
import { EmptyState } from "@/shared/ui/EmptyState";
import { audit } from "../api";
import type { AuditLogEntry } from "../api";
import { AuditLogItem } from "../components/AuditLogItem";

const ACTIONS = ["", "login", "logout", "create", "read", "update", "delete"];

export default function AuditPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [loadingLogs, setLoadingLogs] = useState(true);
  const [offset, setOffset] = useState(0);
  const [actionFilter, setActionFilter] = useState("");
  const [userFilter, setUserFilter] = useState("");
  const limit = 25;

  useEffect(() => {
    if (!loading && !user) router.push("/auth");
  }, [user, loading, router]);

  const loadLogs = async (reset = false) => {
    setLoadingLogs(true);
    const newOffset = reset ? 0 : offset;
    try {
      const res = await audit.logs({ action: actionFilter || undefined, user: userFilter || undefined, limit, offset: newOffset });
      setLogs(reset ? res.logs : [...logs, ...res.logs]);
      setTotal(res.total);
      if (reset) setOffset(0);
    } catch {
      // ignore
    } finally {
      setLoadingLogs(false);
    }
  };

  useEffect(() => { loadLogs(true); }, [actionFilter, userFilter]);

  if (loading || !user) return null;

  return (
    <AppShell>
      <div className="max-w-4xl space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-headline font-semibold text-text-primary">Audit Log</h1>
            <p className="text-sm text-text-secondary mt-1">{total} entries</p>
          </div>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap gap-3">
          <select value={actionFilter} onChange={(e) => setActionFilter(e.target.value)} className="h-9 rounded-md border border-border-default bg-bg-surface px-3 text-xs text-text-secondary focus-visible:ring-2 focus-visible:ring-accent/50 focus-visible:outline-none">
            {ACTIONS.map((a) => <option key={a} value={a}>{a || "All Actions"}</option>)}
          </select>
          <Input placeholder="Filter by user" value={userFilter} onChange={(e) => setUserFilter(e.target.value)} className="w-48" />
        </div>

        <Card className="divide-y divide-border-subtle">
          {logs.length === 0 && !loadingLogs ? (
            <EmptyState title="No audit logs found" description="No entries match your filters" />
          ) : (
            logs.map((entry) => <AuditLogItem key={entry.id} entry={entry} />)
          )}
        </Card>

        {logs.length < total && (
          <div className="flex justify-center">
            <Button variant="ghost" onClick={() => { setOffset(offset + limit); loadLogs(false); }} disabled={loadingLogs}>
              {loadingLogs ? "Loading..." : "Load More"}
            </Button>
          </div>
        )}
      </div>
    </AppShell>
  );
}
```

- [ ] **Step 3: Build + commit**

```bash
cd frontend && npm run build 2>&1 | grep -E 'Compiled|error|Failed'
git add frontend/src/features/privacy/components/AuditLogItem.tsx frontend/src/features/privacy/audit/page.tsx
git commit -m "feat(privacy): add AuditLogItem and audit log viewer page"
```

---

### Task 6: Consent Management Page

**Files:**
- Create: `frontend/src/features/privacy/consent/page.tsx`

- [ ] **Step 1: Create consent page**

```tsx
"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/shared/auth/AuthProvider";
import { useRouter } from "next/navigation";
import { AppShell } from "@/shared/layout/AppShell";
import { Card } from "@/shared/ui/Card";
import { Button } from "@/shared/ui/Button";
import { EmptyState } from "@/shared/ui/EmptyState";
import { consent as consentApi } from "../api";
import type { ConsentItem } from "../api";
import { ConsentToggle } from "../components/ConsentToggle";

export default function ConsentPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [items, setItems] = useState<ConsentItem[]>([]);
  const [loadingItems, setLoadingItems] = useState(true);

  useEffect(() => {
    if (!loading && !user) router.push("/auth");
  }, [user, loading, router]);

  useEffect(() => {
    consentApi.list().then(setItems).catch(() => {}).finally(() => setLoadingItems(false));
  }, []);

  const handleToggle = (scope: string, granted: boolean) => {
    setItems((prev) => prev.map((item) =>
      item.scope === scope ? { ...item, granted, granted_at: granted ? new Date().toISOString() : item.granted_at, revoked_at: granted ? null : new Date().toISOString() } : item
    ));
  };

  const handleGrantAll = async () => {
    for (const item of items) {
      if (!item.granted) await consentApi.grant(item.scope).catch(() => {});
    }
    setItems((prev) => prev.map((item) => ({ ...item, granted: true, granted_at: new Date().toISOString(), revoked_at: null })));
  };

  const handleRevokeAll = async () => {
    for (const item of items) {
      if (item.granted) await consentApi.revoke(item.scope).catch(() => {});
    }
    setItems((prev) => prev.map((item) => ({ ...item, granted: false, granted_at: null, revoked_at: new Date().toISOString() })));
  };

  if (loading || !user) return null;

  return (
    <AppShell>
      <div className="max-w-3xl space-y-6">
        <div>
          <h1 className="text-headline font-semibold text-text-primary">Consent Management</h1>
          <p className="text-sm text-text-secondary mt-1">Control what data is collected and how it&apos;s used</p>
        </div>

        <div className="flex gap-2">
          <Button size="sm" onClick={handleGrantAll}>Grant All</Button>
          <Button size="sm" variant="ghost" className="text-danger" onClick={handleRevokeAll}>Revoke All</Button>
        </div>

        {loadingItems ? (
          <div className="space-y-3">
            {Array.from({ length: 4 }).map((_, i) => <div key={i} className="h-16 rounded-lg bg-bg-elevated animate-pulse" />)}
          </div>
        ) : items.length === 0 ? (
          <EmptyState title="No consent preferences" description="Consent items will appear here when configured" />
        ) : (
          <Card className="divide-y divide-border-subtle">
            {items.map((item) => (
              <div key={item.scope} className="flex items-center justify-between p-4">
                <div className="min-w-0 flex-1 mr-4">
                  <p className="text-sm font-medium text-text-primary">{item.scope}</p>
                  <p className="text-xs text-text-muted mt-0.5">{item.description}</p>
                  {item.granted_at && <p className="text-[10px] text-text-muted mt-1">Granted: {new Date(item.granted_at).toLocaleString()}</p>}
                  {item.revoked_at && <p className="text-[10px] text-text-muted mt-1">Revoked: {new Date(item.revoked_at).toLocaleString()}</p>}
                </div>
                <ConsentToggle scope={item.scope} initialGranted={item.granted} onToggle={handleToggle} />
              </div>
            ))}
          </Card>
        )}
      </div>
    </AppShell>
  );
}
```

- [ ] **Step 2: Build + commit**

```bash
cd frontend && npm run build 2>&1 | grep -E 'Compiled|error|Failed'
git add frontend/src/features/privacy/consent/page.tsx
git commit -m "feat(privacy): add consent management page"
```

---

### Task 7: Final Build Validation

- [ ] **Step 1: Full build**

```bash
cd frontend && npm run build 2>&1 | tail -20
```

- [ ] **Step 2: Verify sidebar has Privacy link**

```bash
grep -n 'Privacy\|Awareness\|Models\|Dashboard' frontend/src/shared/layout/Sidebar.tsx
```

- [ ] **Step 3: Verify toggle accessibility**

```bash
grep -n 'role="switch"\|aria-checked\|aria-label' frontend/src/features/privacy/components/ConsentToggle.tsx
```

---

## Summary

| Task | What It Builds | Files |
|------|---------------|-------|
| 1 | Privacy API client | 1 created |
| 2 | Sidebar + route pages | 1 modified, 3 created |
| 3 | 5 component cards | 5 created |
| 4 | Overview page | 1 created |
| 5 | AuditLogItem + Audit page | 2 created |
| 6 | Consent page | 1 created |
| 7 | Final validation | 0 |
| **Total** | | **12 created, 1 modified** |
