Last updated: 2026-06-28

# Awareness Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Three-page Awareness system — overview dashboard, repository management, indexing configuration — mapping 24 backend endpoints to real UI.

**Architecture:** Split into 3 route pages under `/awareness`. Components in `features/awareness/components/`. API client already exists at `features/awareness/api.ts`.

**Tech Stack:** Next.js 15 App Router, React 19, TypeScript, Tailwind CSS (DESIGN.md tokens), existing shared UI.

## Global Constraints

- Dark-only. All colors from tailwind.config.ts tokens.
- Font: Geist (`font-sans`), JetBrains Mono (`font-mono`).
- No `transition-all`, `h-screen`, gradient text, glassmorphism, side-stripe borders.
- Accessibility: WCAG AA 4.5:1, `prefers-reduced-motion`, focus-visible rings, 44px min touch targets.
- Motion: hover 150ms, modal 250ms, ease-out-quart.
- All pages `"use client"`. API calls via `apiFetch`.

## Existing API Client

`frontend/src/features/awareness/api.ts` already covers ALL endpoints:
- `device.info()` → `GET /awareness/device/info`
- `environment.info()` → `GET /awareness/environment`
- `environment.paths()` → `GET /awareness/environment/paths`
- `files.scan(data)` → `POST /awareness/files/scan`
- `files.changes(params)` → `GET /awareness/files/changes`
- `files.summary()` → `GET /awareness/files/summary`
- `awarenessHealth.check()` → `GET /awareness/health`
- `awarenessHealth.status()` → `GET /awareness/health/status`
- `indexing.config()` → `GET /awareness/indexing/config`
- `indexing.saveConfig(data)` → `PUT /awareness/indexing/config`
- `indexing.preview(data)` → `POST /awareness/indexing/preview`
- `project.scan()` → `GET /awareness/project/scan`
- `repository.list()` → `GET /awareness/repos`
- `repository.create(data)` → `POST /awareness/repos`
- `repository.get(id)` → `GET /awareness/repos/{id}`
- `repository.update(id, data)` → `PUT /awareness/repos/{id}`
- `repository.delete(id)` → `DELETE /awareness/repos/{id}`
- `repository.index(id)` → `POST /awareness/repos/{id}/index`
- `repository.indexStatus(id)` → `GET /awareness/repos/{id}/status`
- `repository.scanAll()` → `POST /awareness/repos/scan`
- `repository.buildGraph(id)` → `POST /awareness/repos/{id}/graph`
- `repository.getGraph(id)` → `GET /awareness/repos/{id}/graph`
- `repository.graphNode(repoId, nodeId)` → `GET /awareness/repos/{repoId}/graph/node/{nodeId}`

---

## File Structure

```
frontend/src/
├── features/awareness/
│   ├── api.ts                          # EXISTING — no changes needed
│   ├── page.tsx                        # Overview dashboard
│   ├── repos/page.tsx                  # Repository management
│   ├── indexing/page.tsx               # Configuration editor
│   └── components/
│       ├── DeviceCard.tsx              # Device info card
│       ├── EnvironmentCard.tsx         # Environment vars card
│       ├── HealthCard.tsx              # Health status card
│       ├── ProjectCard.tsx             # Project detection card
│       ├── RepoListItem.tsx            # Repository list item
│       ├── AddRepoModal.tsx            # Add repository modal
│       ├── IndexProgress.tsx           # Indexing progress display
│       ├── GraphView.tsx               # Knowledge graph display
│       └── IndexingConfigForm.tsx      # Config editor form
├── app/awareness/
│   ├── page.tsx                        # Route → re-export
│   ├── repos/page.tsx                  # Route → re-export
│   └── indexing/page.tsx               # Route → re-export
└── shared/layout/Sidebar.tsx           # Add Awareness nav link
```

---

### Task 1: Sidebar + Route Pages

**Files:**
- Modify: `frontend/src/shared/layout/Sidebar.tsx`
- Create: `frontend/src/app/awareness/page.tsx`
- Create: `frontend/src/app/awareness/repos/page.tsx`
- Create: `frontend/src/app/awareness/indexing/page.tsx`

- [ ] **Step 1: Add Awareness to Sidebar**

Add `{ name: "Awareness", href: "/awareness", icon: "eye" }` between Models and System in the navigation array. Add eye SVG to iconMap:

```typescript
eye: (
  <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.5">
    <path d="M1 9s3-6 8-6 8 6 8 6-3 6-8 6-8-6-8-6z" />
    <circle cx="9" cy="9" r="2.5" />
  </svg>
),
```

- [ ] **Step 2: Create route pages**

Each is a one-line re-export:

```tsx
// frontend/src/app/awareness/page.tsx
export { default } from "@/features/awareness/page";
```

```tsx
// frontend/src/app/awareness/repos/page.tsx
export { default } from "@/features/awareness/repos/page";
```

```tsx
// frontend/src/app/awareness/indexing/page.tsx
export { default } from "@/features/awareness/indexing/page";
```

- [ ] **Step 3: Build check + commit**

```bash
cd frontend && npm run build 2>&1 | grep -E 'Compiled|error|Failed'
git add frontend/src/shared/layout/Sidebar.tsx frontend/src/app/awareness/
git commit -m "feat(awareness): add sidebar nav link and route pages"
```

---

### Task 2: DeviceCard + EnvironmentCard + HealthCard + ProjectCard

**Files:**
- Create: `frontend/src/features/awareness/components/DeviceCard.tsx`
- Create: `frontend/src/features/awareness/components/EnvironmentCard.tsx`
- Create: `frontend/src/features/awareness/components/HealthCard.tsx`
- Create: `frontend/src/features/awareness/components/ProjectCard.tsx`

- [ ] **Step 1: Create DeviceCard**

```tsx
"use client";

import { useState, useEffect } from "react";
import { device } from "../api";
import type { DeviceInfo } from "../api";
import { Card } from "@/shared/ui/Card";
import { StatusDot } from "@/shared/ui/StatusDot";

export function DeviceCard() {
  const [info, setInfo] = useState<DeviceInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    device.info().then(setInfo).catch((e) => setError(e.message)).finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <Card className="p-4 animate-pulse"><div className="space-y-3"><div className="h-5 w-1/2 rounded bg-bg-surface" /><div className="h-4 w-3/4 rounded bg-bg-surface" /><div className="h-4 w-2/3 rounded bg-bg-surface" /></div></Card>;
  }

  if (error) {
    return <Card className="p-4"><StatusDot color="danger" /><span className="text-sm text-danger ml-2">{error}</span></Card>;
  }

  if (!info) return null;

  const ramUsed = info.memory_total - info.memory_used;
  const ramPercent = info.memory_total > 0 ? Math.round((ramUsed / info.memory_total) * 100) : 0;
  const diskPercent = info.disk_total > 0 ? Math.round((info.disk_used / info.disk_total) * 100) : 0;

  return (
    <Card className="p-4" role="article" aria-label="Device information">
      <h3 className="text-sm font-semibold text-text-primary mb-3">Device</h3>
      <div className="space-y-2 text-xs">
        <div className="flex justify-between"><span className="text-text-muted">Hostname</span><span className="text-text-secondary font-mono">{info.hostname}</span></div>
        <div className="flex justify-between"><span className="text-text-muted">OS</span><span className="text-text-secondary">{info.os}</span></div>
        <div className="flex justify-between"><span className="text-text-muted">CPU</span><span className="text-text-secondary">{info.cpu}</span></div>
        <div className="flex justify-between"><span className="text-text-muted">Python</span><span className="text-text-secondary font-mono">{info.python_version}</span></div>

        {/* RAM bar */}
        <div className="pt-1">
          <div className="flex justify-between mb-1"><span className="text-text-muted">RAM</span><span className="text-text-secondary">{ramUsed.toFixed(1)} / {info.memory_total} GB</span></div>
          <div className="h-1.5 rounded-full bg-bg-surface overflow-hidden">
            <div className={`h-full rounded-full transition-[width] duration-300 ${ramPercent >= 85 ? "bg-danger" : ramPercent >= 70 ? "bg-warning" : "bg-success"}`} style={{ width: `${ramPercent}%` }} role="progressbar" aria-valuenow={ramPercent} aria-valuemin={0} aria-valuemax={100} />
          </div>
        </div>

        {/* Disk bar */}
        <div className="pt-1">
          <div className="flex justify-between mb-1"><span className="text-text-muted">Disk</span><span className="text-text-secondary">{info.disk_used} / {info.disk_total} GB</span></div>
          <div className="h-1.5 rounded-full bg-bg-surface overflow-hidden">
            <div className={`h-full rounded-full transition-[width] duration-300 ${diskPercent >= 85 ? "bg-danger" : diskPercent >= 70 ? "bg-warning" : "bg-success"}`} style={{ width: `${diskPercent}%` }} role="progressbar" aria-valuenow={diskPercent} aria-valuemin={0} aria-valuemax={100} />
          </div>
        </div>
      </div>
    </Card>
  );
}
```

- [ ] **Step 2: Create EnvironmentCard**

```tsx
"use client";

import { useState, useEffect } from "react";
import { environment } from "../api";
import { Card } from "@/shared/ui/Card";

export function EnvironmentCard() {
  const [env, setEnv] = useState<{ variables: Record<string, string>; paths: string[]; working_directory: string } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    environment.info().then(setEnv).catch(() => {}).finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <Card className="p-4 animate-pulse"><div className="space-y-3"><div className="h-5 w-1/2 rounded bg-bg-surface" /><div className="h-4 w-3/4 rounded bg-bg-surface" /></div></Card>;
  }

  if (!env) return null;

  const vars = Object.entries(env.variables).slice(0, 8);

  return (
    <Card className="p-4" role="article" aria-label="Environment information">
      <h3 className="text-sm font-semibold text-text-primary mb-3">Environment</h3>
      <div className="space-y-1.5 text-xs">
        <div className="flex justify-between"><span className="text-text-muted">Working Dir</span><span className="text-text-secondary font-mono truncate max-w-[180px]">{env.working_directory}</span></div>
        {vars.map(([key, value]) => (
          <div key={key} className="flex justify-between gap-2">
            <span className="text-text-muted truncate">{key}</span>
            <span className="text-text-secondary font-mono truncate text-right">{value}</span>
          </div>
        ))}
        {Object.keys(env.variables).length > 8 && (
          <p className="text-text-muted">+{Object.keys(env.variables).length - 8} more</p>
        )}
      </div>
    </Card>
  );
}
```

- [ ] **Step 3: Create HealthCard**

```tsx
"use client";

import { useState, useEffect } from "react";
import { awarenessHealth } from "../api";
import { Card } from "@/shared/ui/Card";
import { StatusDot } from "@/shared/ui/StatusDot";

export function HealthCard() {
  const [health, setHealth] = useState<{ status: string; indexing_active: boolean; watched_count: number; last_scan: string } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    awarenessHealth.check().then(setHealth).catch(() => {}).finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <Card className="p-4 animate-pulse"><div className="h-5 w-1/2 rounded bg-bg-surface" /></Card>;
  }

  const statusColor = health?.status === "healthy" ? "success" : health?.status === "degraded" ? "warning" : "danger";

  return (
    <Card className="p-4" role="article" aria-label="System health">
      <h3 className="text-sm font-semibold text-text-primary mb-3">Health</h3>
      {health ? (
        <div className="space-y-2 text-xs">
          <div className="flex items-center gap-2">
            <StatusDot color={statusColor as any} />
            <span className="text-text-secondary capitalize">{health.status}</span>
          </div>
          <div className="flex justify-between"><span className="text-text-muted">Indexing</span><span className="text-text-secondary">{health.indexing_active ? "Active" : "Inactive"}</span></div>
          <div className="flex justify-between"><span className="text-text-muted">Watched</span><span className="text-text-secondary">{health.watched_count} items</span></div>
          <div className="flex justify-between"><span className="text-text-muted">Last Scan</span><span className="text-text-secondary">{health.last_scan ? new Date(health.last_scan).toLocaleDateString() : "Never"}</span></div>
        </div>
      ) : (
        <p className="text-xs text-text-muted">Health check unavailable</p>
      )}
    </Card>
  );
}
```

- [ ] **Step 4: Create ProjectCard**

```tsx
"use client";

import { useState } from "react";
import { project } from "../api";
import { Card } from "@/shared/ui/Card";
import { Badge } from "@/shared/ui/Badge";
import { Button } from "@/shared/ui/Button";
import { Input } from "@/shared/ui/Input";

export function ProjectCard() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [path, setPath] = useState("");
  const [scanning, setScanning] = useState(false);

  const handleScan = async () => {
    if (!path.trim()) return;
    setScanning(true);
    try {
      const result = await project.scan();
      setData(result);
    } catch {
      // ignore
    } finally {
      setScanning(false);
    }
  };

  return (
    <Card className="p-4" role="article" aria-label="Project detection">
      <h3 className="text-sm font-semibold text-text-primary mb-3">Project</h3>
      {data ? (
        <div className="space-y-2 text-xs">
          <div className="flex justify-between"><span className="text-text-muted">Type</span><span className="text-text-secondary">{data.project_type}</span></div>
          <div className="flex justify-between"><span className="text-text-muted">Name</span><span className="text-text-secondary">{data.project_name}</span></div>
          <div className="flex gap-1.5 flex-wrap">
            {data.frameworks?.map((f: string) => <Badge key={f} variant="default">{f}</Badge>)}
          </div>
          <div className="flex gap-2 pt-1">
            {data.has_tests && <Badge variant="success">Tests</Badge>}
            {data.has_ci && <Badge variant="default">CI</Badge>}
            {data.has_docker && <Badge variant="default">Docker</Badge>}
          </div>
        </div>
      ) : (
        <div className="space-y-2">
          <p className="text-xs text-text-muted">Scan a project to detect its type and frameworks</p>
          <div className="flex gap-2">
            <Input placeholder="/path/to/project" value={path} onChange={(e) => setPath(e.target.value)} onKeyDown={(e) => e.key === "Enter" && handleScan()} />
            <Button size="sm" onClick={handleScan} disabled={scanning || !path.trim()}>{scanning ? "Scanning..." : "Scan"}</Button>
          </div>
        </div>
      )}
    </Card>
  );
}
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/awareness/components/
git commit -m "feat(awareness): add DeviceCard, EnvironmentCard, HealthCard, ProjectCard"
```

---

### Task 3: Overview Page

**Files:**
- Create: `frontend/src/features/awareness/page.tsx`

- [ ] **Step 1: Create overview page**

```tsx
"use client";

import { useAuth } from "@/shared/auth/AuthProvider";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { AppShell } from "@/shared/layout/AppShell";
import { DeviceCard } from "./components/DeviceCard";
import { EnvironmentCard } from "./components/EnvironmentCard";
import { HealthCard } from "./components/HealthCard";
import { ProjectCard } from "./components/ProjectCard";

export default function AwarenessPage() {
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
          <h1 className="text-headline font-semibold text-text-primary">Awareness</h1>
          <p className="text-sm text-text-secondary mt-1">System awareness and repository management</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <DeviceCard />
          <EnvironmentCard />
          <HealthCard />
          <ProjectCard />
        </div>
      </div>
    </AppShell>
  );
}
```

- [ ] **Step 2: Build check + commit**

```bash
cd frontend && npm run build 2>&1 | grep -E 'Compiled|error|Failed'
git add frontend/src/features/awareness/page.tsx
git commit -m "feat(awareness): add overview dashboard page"
```

---

### Task 4: AddRepoModal + RepoListItem + IndexProgress

**Files:**
- Create: `frontend/src/features/awareness/components/AddRepoModal.tsx`
- Create: `frontend/src/features/awareness/components/RepoListItem.tsx`
- Create: `frontend/src/features/awareness/components/IndexProgress.tsx`

- [ ] **Step 1: Create AddRepoModal**

```tsx
"use client";

import { useState } from "react";
import { repository } from "../api";
import { Modal } from "@/shared/ui/Modal";
import { Input } from "@/shared/ui/Input";
import { Button } from "@/shared/ui/Button";

interface AddRepoModalProps {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
}

export function AddRepoModal({ open, onClose, onCreated }: AddRepoModalProps) {
  const [name, setName] = useState("");
  const [path, setPath] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCreate = async () => {
    if (!name.trim() || !path.trim()) return;
    setLoading(true);
    setError(null);
    try {
      await repository.create({ name: name.trim(), path: path.trim() });
      setName("");
      setPath("");
      onCreated();
      onClose();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal open={open} onClose={onClose} title="Add Repository">
      <div className="space-y-4">
        <Input label="Name" placeholder="my-project" value={name} onChange={(e) => setName(e.target.value)} />
        <Input label="Path" placeholder="/path/to/repo" value={path} onChange={(e) => setPath(e.target.value)} onKeyDown={(e) => e.key === "Enter" && handleCreate()} />
        {error && <p className="text-xs text-danger">{error}</p>}
        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={onClose}>Cancel</Button>
          <Button onClick={handleCreate} disabled={loading || !name.trim() || !path.trim()}>{loading ? "Creating..." : "Add"}</Button>
        </div>
      </div>
    </Modal>
  );
}
```

- [ ] **Step 2: Create RepoListItem**

```tsx
"use client";

import { useState } from "react";
import { repository } from "../api";
import { Card } from "@/shared/ui/Card";
import { Badge } from "@/shared/ui/Badge";
import { Button } from "@/shared/ui/Button";
import { StatusDot } from "@/shared/ui/StatusDot";
import { IndexProgress } from "./IndexProgress";

interface Repo {
  id: number;
  repo_name: string;
  repo_path: string;
  primary_language: string | null;
  total_files: number;
  total_chunks: number;
  status: string;
  last_indexed_at: string | null;
}

interface RepoListItemProps {
  repo: Repo;
  onRefresh: () => void;
  onViewGraph: (repoId: number) => void;
}

export function RepoListItem({ repo, onRefresh, onViewGraph }: RepoListItemProps) {
  const [indexing, setIndexing] = useState(false);
  const [showProgress, setShowProgress] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const statusColor = repo.status === "indexed" ? "success" : repo.status === "indexing" ? "accent" : repo.status === "error" ? "danger" : "warning";

  const handleIndex = async () => {
    setIndexing(true);
    setShowProgress(true);
    try {
      await repository.index(repo.id);
      // Poll for status
      const poll = setInterval(async () => {
        try {
          const status = await repository.indexStatus(repo.id);
          if (status.status === "indexed" || status.status === "error") {
            clearInterval(poll);
            setIndexing(false);
            onRefresh();
          }
        } catch {
          clearInterval(poll);
          setIndexing(false);
        }
      }, 3000);
    } catch {
      setIndexing(false);
      setShowProgress(false);
    }
  };

  const handleDelete = async () => {
    setDeleting(true);
    try {
      await repository.delete(repo.id);
      onRefresh();
    } catch {
      setDeleting(false);
    }
  };

  return (
    <Card className="p-4" role="article" aria-label={`Repository ${repo.repo_name}`}>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="text-sm font-semibold text-text-primary">{repo.repo_name}</h3>
            <StatusDot color={statusColor as any} />
            {repo.primary_language && <Badge variant="default">{repo.primary_language}</Badge>}
          </div>
          <p className="text-xs text-text-muted font-mono truncate">{repo.repo_path}</p>
          <div className="flex items-center gap-3 mt-1.5 text-xs text-text-muted">
            <span>{repo.total_files} files</span>
            <span>{repo.total_chunks} chunks</span>
            {repo.last_indexed_at && <span>Last indexed: {new Date(repo.last_indexed_at).toLocaleDateString()}</span>}
          </div>
        </div>
        <div className="flex items-center gap-1.5 flex-shrink-0">
          <Button size="sm" variant="ghost" onClick={handleIndex} disabled={indexing}>{indexing ? "Indexing..." : "Index"}</Button>
          <Button size="sm" variant="ghost" onClick={() => onViewGraph(repo.id)}>Graph</Button>
          <Button size="sm" variant="ghost" className="text-danger hover:text-danger" onClick={handleDelete} disabled={deleting}>{deleting ? "..." : "Delete"}</Button>
        </div>
      </div>
      {showProgress && <IndexProgress repoId={repo.id} />}
    </Card>
  );
}
```

- [ ] **Step 3: Create IndexProgress**

```tsx
"use client";

import { useState, useEffect } from "react";
import { repository } from "../api";

interface IndexProgressProps {
  repoId: number;
}

export function IndexProgress({ repoId }: IndexProgressProps) {
  const [status, setStatus] = useState<any>(null);

  useEffect(() => {
    const poll = setInterval(async () => {
      try {
        const s = await repository.indexStatus(repoId);
        setStatus(s);
        if (s.status === "indexed" || s.status === "error") clearInterval(poll);
      } catch {
        clearInterval(poll);
      }
    }, 2000);
    return () => clearInterval(poll);
  }, [repoId]);

  if (!status) return null;

  const total = status.total_files || 1;
  const indexed = status.indexed || 0;
  const percent = Math.round((indexed / total) * 100);

  return (
    <div className="mt-3 space-y-1.5">
      <div className="h-1.5 rounded-full bg-bg-surface overflow-hidden">
        <div className="h-full rounded-full bg-accent transition-[width] duration-300" style={{ width: `${percent}%` }} role="progressbar" aria-valuenow={percent} aria-valuemin={0} aria-valuemax={100} />
      </div>
      <div className="flex justify-between text-xs text-text-muted">
        <span>{indexed}/{total} files indexed</span>
        <span>{status.errors || 0} errors</span>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/features/awareness/components/AddRepoModal.tsx frontend/src/features/awareness/components/RepoListItem.tsx frontend/src/features/awareness/components/IndexProgress.tsx
git commit -m "feat(awareness): add AddRepoModal, RepoListItem, IndexProgress"
```

---

### Task 5: GraphView + Repos Page

**Files:**
- Create: `frontend/src/features/awareness/components/GraphView.tsx`
- Create: `frontend/src/features/awareness/repos/page.tsx`

- [ ] **Step 1: Create GraphView**

```tsx
"use client";

import { useState, useEffect } from "react";
import { repository } from "../api";
import { Card } from "@/shared/ui/Card";
import { Button } from "@/shared/ui/Button";
import { EmptyState } from "@/shared/ui/EmptyState";

interface GraphViewProps {
  repoId: number;
  onClose: () => void;
}

export function GraphView({ repoId, onClose }: GraphViewProps) {
  const [graph, setGraph] = useState<{ nodes: any[]; edges: any[] } | null>(null);
  const [loading, setLoading] = useState(true);
  const [building, setBuilding] = useState(false);

  const loadGraph = async () => {
    setLoading(true);
    try {
      const g = await repository.getGraph(repoId);
      setGraph(g);
    } catch {
      setGraph(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadGraph(); }, [repoId]);

  const handleBuild = async () => {
    setBuilding(true);
    try {
      await repository.buildGraph(repoId);
      await loadGraph();
    } catch {
      // ignore
    } finally {
      setBuilding(false);
    }
  };

  return (
    <Card className="p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-text-primary">Knowledge Graph</h3>
        <div className="flex gap-2">
          <Button size="sm" onClick={handleBuild} disabled={building}>{building ? "Building..." : "Build Graph"}</Button>
          <Button size="sm" variant="ghost" onClick={onClose}>Close</Button>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-8"><div className="h-5 w-5 animate-spin rounded-full border-2 border-accent border-t-transparent" /></div>
      ) : graph && graph.nodes.length > 0 ? (
        <div className="space-y-3">
          <div className="flex gap-4 text-xs text-text-muted">
            <span>{graph.nodes.length} nodes</span>
            <span>{graph.edges.length} edges</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {graph.nodes.slice(0, 20).map((node: any) => (
              <div key={node.id} className="px-2.5 py-1 rounded-md bg-bg-surface text-xs text-text-secondary border border-border-subtle">
                {node.name || node.label || `Node ${node.id}`}
              </div>
            ))}
            {graph.nodes.length > 20 && <span className="text-xs text-text-muted">+{graph.nodes.length - 20} more</span>}
          </div>
        </div>
      ) : (
        <EmptyState title="No graph data" description="Build the graph to visualize repository structure" />
      )}
    </Card>
  );
}
```

- [ ] **Step 2: Create Repos page**

```tsx
"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/shared/auth/AuthProvider";
import { useRouter } from "next/navigation";
import { AppShell } from "@/shared/layout/AppShell";
import { Button } from "@/shared/ui/Button";
import { EmptyState } from "@/shared/ui/EmptyState";
import { repository } from "../api";
import { RepoListItem } from "../components/RepoListItem";
import { AddRepoModal } from "../components/AddRepoModal";
import { GraphView } from "../components/GraphView";

export default function ReposPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [repos, setRepos] = useState<any[]>([]);
  const [loadingRepos, setLoadingRepos] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [graphRepoId, setGraphRepoId] = useState<number | null>(null);

  useEffect(() => {
    if (!loading && !user) router.push("/auth");
  }, [user, loading, router]);

  const loadRepos = async () => {
    setLoadingRepos(true);
    try {
      const res = await repository.list();
      setRepos(res.repos);
    } catch {
      // ignore
    } finally {
      setLoadingRepos(false);
    }
  };

  useEffect(() => { loadRepos(); }, []);

  if (loading || !user) return null;

  return (
    <AppShell>
      <div className="max-w-4xl space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-headline font-semibold text-text-primary">Repositories</h1>
            <p className="text-sm text-text-secondary mt-1">Manage and index your code repositories</p>
          </div>
          <Button onClick={() => setShowAdd(true)}>Add Repository</Button>
        </div>

        {loadingRepos ? (
          <div className="space-y-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="h-20 rounded-lg bg-bg-elevated animate-pulse" />
            ))}
          </div>
        ) : repos.length === 0 ? (
          <EmptyState title="No repositories" description="Add a repository to start indexing your code" action={<Button onClick={() => setShowAdd(true)}>Add Repository</Button>} />
        ) : (
          <div className="space-y-3">
            {repos.map((repo) => (
              <RepoListItem key={repo.id} repo={repo} onRefresh={loadRepos} onViewGraph={setGraphRepoId} />
            ))}
          </div>
        )}

        {graphRepoId && <GraphView repoId={graphRepoId} onClose={() => setGraphRepoId(null)} />}

        <AddRepoModal open={showAdd} onClose={() => setShowAdd(false)} onCreated={loadRepos} />
      </div>
    </AppShell>
  );
}
```

- [ ] **Step 3: Build check + commit**

```bash
cd frontend && npm run build 2>&1 | grep -E 'Compiled|error|Failed'
git add frontend/src/features/awareness/components/GraphView.tsx frontend/src/features/awareness/repos/page.tsx
git commit -m "feat(awareness): add GraphView and repository management page"
```

---

### Task 6: IndexingConfigForm + Indexing Page

**Files:**
- Create: `frontend/src/features/awareness/components/IndexingConfigForm.tsx`
- Create: `frontend/src/features/awareness/indexing/page.tsx`

- [ ] **Step 1: Create IndexingConfigForm**

```tsx
"use client";

import { useState, useEffect } from "react";
import { indexing } from "../api";
import { Card } from "@/shared/ui/Card";
import { Input } from "@/shared/ui/Input";
import { Button } from "@/shared/ui/Button";

export function IndexingConfigForm() {
  const [config, setConfig] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [previewPath, setPreviewPath] = useState("");
  const [previewResult, setPreviewResult] = useState<any>(null);
  const [previewing, setPreviewing] = useState(false);

  useEffect(() => {
    indexing.config().then((res) => setConfig(res.config)).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const handleSave = async () => {
    if (!config) return;
    setSaving(true);
    try {
      await indexing.saveConfig(config);
    } catch {
      // ignore
    } finally {
      setSaving(false);
    }
  };

  const handlePreview = async () => {
    if (!previewPath.trim()) return;
    setPreviewing(true);
    try {
      const result = await indexing.preview({ directory: previewPath.trim() });
      setPreviewResult(result);
    } catch {
      setPreviewResult(null);
    } finally {
      setPreviewing(false);
    }
  };

  if (loading) {
    return <div className="space-y-4">{Array.from({ length: 3 }).map((_, i) => <div key={i} className="h-16 rounded-lg bg-bg-elevated animate-pulse" />)}</div>;
  }

  return (
    <div className="space-y-6">
      <Card className="p-5">
        <h3 className="text-sm font-semibold text-text-primary mb-4">Indexing Configuration</h3>
        <div className="space-y-4">
          <div>
            <label className="text-xs text-text-muted mb-1 block">Include Paths</label>
            <textarea className="w-full h-20 rounded-md border border-border-default bg-bg-surface px-3 py-2 text-sm text-text-secondary font-mono focus-visible:ring-2 focus-visible:ring-accent/50 focus-visible:outline-none resize-none" value={config?.include_paths?.join("\n") ?? ""} onChange={(e) => setConfig({ ...config, include_paths: e.target.value.split("\n").filter(Boolean) })} placeholder="One path per line" />
          </div>
          <div>
            <label className="text-xs text-text-muted mb-1 block">Exclude Paths</label>
            <textarea className="w-full h-20 rounded-md border border-border-default bg-bg-surface px-3 py-2 text-sm text-text-secondary font-mono focus-visible:ring-2 focus-visible:ring-accent/50 focus-visible:outline-none resize-none" value={config?.exclude_paths?.join("\n") ?? ""} onChange={(e) => setConfig({ ...config, exclude_paths: e.target.value.split("\n").filter(Boolean) })} placeholder="One path per line" />
          </div>
          <div>
            <label className="text-xs text-text-muted mb-1 block">Include Patterns</label>
            <textarea className="w-full h-16 rounded-md border border-border-default bg-bg-surface px-3 py-2 text-sm text-text-secondary font-mono focus-visible:ring-2 focus-visible:ring-accent/50 focus-visible:outline-none resize-none" value={config?.include_patterns?.join("\n") ?? ""} onChange={(e) => setConfig({ ...config, include_patterns: e.target.value.split("\n").filter(Boolean) })} placeholder="*.py, *.ts, etc." />
          </div>
          <div>
            <label className="text-xs text-text-muted mb-1 block">Exclude Patterns</label>
            <textarea className="w-full h-16 rounded-md border border-border-default bg-bg-surface px-3 py-2 text-sm text-text-secondary font-mono focus-visible:ring-2 focus-visible:ring-accent/50 focus-visible:outline-none resize-none" value={config?.exclude_patterns?.join("\n") ?? ""} onChange={(e) => setConfig({ ...config, exclude_patterns: e.target.value.split("\n").filter(Boolean) })} placeholder="node_modules, .git, etc." />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <Input label="Max File Size (bytes)" type="number" value={String(config?.max_file_size_bytes ?? 1000000)} onChange={(e) => setConfig({ ...config, max_file_size_bytes: parseInt(e.target.value) || 0 })} />
            <Input label="Sync Interval (seconds)" type="number" value={String(config?.sync_interval_seconds ?? 300)} onChange={(e) => setConfig({ ...config, sync_interval_seconds: parseInt(e.target.value) || 0 })} />
          </div>
          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2 text-xs text-text-secondary cursor-pointer">
              <input type="checkbox" checked={config?.follow_symlinks ?? false} onChange={(e) => setConfig({ ...config, follow_symlinks: e.target.checked })} className="h-3.5 w-3.5 rounded border-border-default bg-bg-surface accent-accent" />
              Follow symlinks
            </label>
            <label className="flex items-center gap-2 text-xs text-text-secondary cursor-pointer">
              <input type="checkbox" checked={config?.sync_enabled ?? true} onChange={(e) => setConfig({ ...config, sync_enabled: e.target.checked })} className="h-3.5 w-3.5 rounded border-border-default bg-bg-surface accent-accent" />
              Sync enabled
            </label>
          </div>
          <Button onClick={handleSave} disabled={saving}>{saving ? "Saving..." : "Save Configuration"}</Button>
        </div>
      </Card>

      <Card className="p-5">
        <h3 className="text-sm font-semibold text-text-primary mb-3">Preview Indexing</h3>
        <div className="flex gap-2 mb-3">
          <Input placeholder="/path/to/preview" value={previewPath} onChange={(e) => setPreviewPath(e.target.value)} onKeyDown={(e) => e.key === "Enter" && handlePreview()} />
          <Button size="sm" onClick={handlePreview} disabled={previewing || !previewPath.trim()}>{previewing ? "Previewing..." : "Preview"}</Button>
        </div>
        {previewResult && (
          <div className="text-xs text-text-secondary space-y-1">
            <p>Files to index: {previewResult.total_files ?? previewResult.files ?? 0}</p>
            {previewResult.estimated_time && <p>Estimated time: {previewResult.estimated_time}s</p>}
          </div>
        )}
      </Card>
    </div>
  );
}
```

- [ ] **Step 2: Create Indexing page**

```tsx
"use client";

import { useEffect } from "react";
import { useAuth } from "@/shared/auth/AuthProvider";
import { useRouter } from "next/navigation";
import { AppShell } from "@/shared/layout/AppShell";
import { IndexingConfigForm } from "../components/IndexingConfigForm";

export default function IndexingPage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) router.push("/auth");
  }, [user, loading, router]);

  if (loading || !user) return null;

  return (
    <AppShell>
      <div className="max-w-3xl space-y-6">
        <div>
          <h1 className="text-headline font-semibold text-text-primary">Indexing Configuration</h1>
          <p className="text-sm text-text-secondary mt-1">Configure how CORTEX indexes your files and repositories</p>
        </div>
        <IndexingConfigForm />
      </div>
    </AppShell>
  );
}
```

- [ ] **Step 3: Build check + commit**

```bash
cd frontend && npm run build 2>&1 | grep -E 'Compiled|error|Failed'
git add frontend/src/features/awareness/components/IndexingConfigForm.tsx frontend/src/features/awareness/indexing/page.tsx
git commit -m "feat(awareness): add IndexingConfigForm and indexing configuration page"
```

---

### Task 7: Final Build Validation

- [ ] **Step 1: Full build**

```bash
cd frontend && npm run build 2>&1 | tail -20
```

- [ ] **Step 2: Verify no forbidden patterns**

```bash
grep -rn 'transition-all\|h-screen\|glassmorphism\|gradient.*text' frontend/src/features/awareness/ --include='*.tsx' --include='*.ts' 2>/dev/null
```

- [ ] **Step 3: Verify Sidebar has all links**

```bash
grep -n 'Awareness\|Models\|Dashboard\|Chat\|Agents\|System\|Settings' frontend/src/shared/layout/Sidebar.tsx
```

---

## Summary

| Task | What It Builds | Files |
|------|---------------|-------|
| 1 | Sidebar + route pages | 1 modified, 3 created |
| 2 | 4 overview cards | 4 created |
| 3 | Overview page | 1 created |
| 4 | AddRepoModal + RepoListItem + IndexProgress | 3 created |
| 5 | GraphView + Repos page | 2 created |
| 6 | IndexingConfigForm + Indexing page | 2 created |
| 7 | Final validation | 0 |
| **Total** | | **15 created, 1 modified** |
