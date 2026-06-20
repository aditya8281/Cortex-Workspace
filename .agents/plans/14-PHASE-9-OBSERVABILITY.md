# Phase 9: Observability & Monitoring

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Full visibility into system health, agent performance, retrieval quality, and resource usage. Dashboards for everything.

**Architecture:** Metrics collection pipeline, health check aggregation, dashboard UI with real-time updates.

**Tech Stack:** Python 3.12+, Prometheus metrics (existing), Next.js 15

---

## Task 1: Metrics Collector Service

**Files:**
- Create: `backend/app/services/metrics_collector.py`
- Modify: `backend/app/api/router.py`

### Step 1.1: Create MetricsCollector singleton

Create `backend/app/services/metrics_collector.py`:

```python
"""Thread-safe in-memory metrics collector with periodic PostgreSQL flush."""

from __future__ import annotations

import atexit
import time
import threading
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from backend.app.core.logging import get_logger

logger = get_logger(__name__)


class MetricsCollector:
    """Singleton metrics collector — thread-safe, accumulates counters in memory,
    flushes to PostgreSQL every FLUSH_INTERVAL seconds."""

    _instance: MetricsCollector | None = None
    _lock = threading.Lock()

    FLUSH_INTERVAL = 300  # 5 minutes

    def __new__(cls) -> MetricsCollector:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        self._data_lock = threading.Lock()
        self._start_time = time.time()
        self._flush_thread: threading.Thread | None = None
        self._shutdown = False

        # ── Counters ─────────────────────────────────────────────
        self._counters: dict[str, float] = defaultdict(float)

        # ── Histograms (agent runs, search latency, etc.) ────────
        self._histograms: dict[str, list[float]] = defaultdict(list)
        self._histogram_max = 1000  # bound memory per histogram

        # ── Gauges ───────────────────────────────────────────────
        self._gauges: dict[str, float] = {}

        self._start_flush_thread()
        atexit.register(self.shutdown)

    # ── Counter API ──────────────────────────────────────────────

    def increment(self, name: str, value: float = 1.0) -> None:
        with self._data_lock:
            self._counters[name] += value

    def decrement(self, name: str, value: float = 1.0) -> None:
        with self._data_lock:
            self._counters[name] -= value

    def get_counter(self, name: str) -> float:
        with self._data_lock:
            return self._counters.get(name, 0.0)

    # ── Gauge API ────────────────────────────────────────────────

    def set_gauge(self, name: str, value: float) -> None:
        with self._data_lock:
            self._gauges[name] = value

    def get_gauge(self, name: str) -> float:
        with self._data_lock:
            return self._gauges.get(name, 0.0)

    # ── Histogram API ────────────────────────────────────────────

    def observe(self, name: str, value: float) -> None:
        with self._data_lock:
            hist = self._histograms[name]
            hist.append(value)
            if len(hist) > self._histogram_max:
                hist.pop(0)

    def get_histogram(self, name: str) -> dict[str, float]:
        with self._data_lock:
            values = list(self._histograms.get(name, []))
        if not values:
            return {"count": 0, "avg": 0.0, "min": 0.0, "max": 0.0, "p50": 0.0, "p95": 0.0, "p99": 0.0}
        values.sort()
        n = len(values)
        return {
            "count": n,
            "avg": sum(values) / n,
            "min": values[0],
            "max": values[-1],
            "p50": values[int(n * 0.5)],
            "p95": values[int(n * 0.95)] if n >= 20 else values[-1],
            "p99": values[int(n * 0.99)] if n >= 100 else values[-1],
        }

    # ── Convenience: Agent metrics ───────────────────────────────

    def record_agent_run(self, success: bool, duration_ms: float, tokens_used: int = 0) -> None:
        with self._data_lock:
            self._counters["agent.runs.total"] += 1
            if success:
                self._counters["agent.runs.success"] += 1
            else:
                self._counters["agent.runs.failure"] += 1
            self._histograms["agent.run.duration_ms"].append(duration_ms)
            if len(self._histograms["agent.run.duration_ms"]) > self._histogram_max:
                self._histograms["agent.run.duration_ms"].pop(0)
            self._counters["agent.tokens.total"] += tokens_used

    # ── Convenience: Search metrics ──────────────────────────────

    def record_search(self, latency_ms: float, result_count: int) -> None:
        with self._data_lock:
            self._counters["search.queries.total"] += 1
            self._histograms["search.latency_ms"].append(latency_ms)
            if len(self._histograms["search.latency_ms"]) > self._histogram_max:
                self._histograms["search.latency_ms"].pop(0)
            self._counters["search.results.total"] += result_count

    # ── Convenience: Indexing metrics ────────────────────────────

    def record_indexing(self, files_indexed: int, sync_time_ms: float, errors: int = 0) -> None:
        with self._data_lock:
            self._counters["indexing.files.total"] += files_indexed
            self._counters["indexing.errors.total"] += errors
            self._histograms["indexing.sync_time_ms"].append(sync_time_ms)
            if len(self._histograms["indexing.sync_time_ms"]) > self._histogram_max:
                self._histograms["indexing.sync_time_ms"].pop(0)

    # ── Convenience: Memory metrics ──────────────────────────────

    def record_memory_entry(self) -> None:
        with self._data_lock:
            self._counters["memory.entries.total"] += 1

    def record_memory_search(self, hit: bool, latency_ms: float) -> None:
        with self._data_lock:
            self._counters["memory.searches.total"] += 1
            if hit:
                self._counters["memory.hits.total"] += 1
            self._histograms["memory.search.latency_ms"].append(latency_ms)
            if len(self._histograms["memory.search.latency_ms"]) > self._histogram_max:
                self._histograms["memory.search.latency_ms"].pop(0)

    # ── Convenience: LLM metrics ─────────────────────────────────

    def record_llm_call(self, tokens_used: int, latency_ms: float, error: bool = False) -> None:
        with self._data_lock:
            self._counters["llm.calls.total"] += 1
            self._counters["llm.tokens.total"] += tokens_used
            if error:
                self._counters["llm.errors.total"] += 1
            self._histograms["llm.latency_ms"].append(latency_ms)
            if len(self._histograms["llm.latency_ms"]) > self._histogram_max:
                self._histograms["llm.latency_ms"].pop(0)

    # ── Snapshot (for API) ───────────────────────────────────────

    def snapshot(self) -> dict[str, Any]:
        """Return a point-in-time snapshot of all metrics."""
        with self._data_lock:
            uptime = time.time() - self._start_time
            counters = dict(self._counters)
            gauges = dict(self._gauges)
            histograms = {}
            for name, values in self._histograms.items():
                vals = sorted(values)
                n = len(vals)
                histograms[name] = {
                    "count": n,
                    "avg": sum(vals) / n if n else 0.0,
                    "min": vals[0] if n else 0.0,
                    "max": vals[-1] if n else 0.0,
                    "p50": vals[int(n * 0.5)] if n else 0.0,
                    "p95": vals[int(n * 0.95)] if n and n >= 20 else (vals[-1] if n else 0.0),
                    "p99": vals[int(n * 0.99)] if n and n >= 100 else (vals[-1] if n else 0.0),
                }
        return {
            "uptime_seconds": round(uptime, 1),
            "counters": counters,
            "gauges": gauges,
            "histograms": histograms,
            "collected_at": datetime.now(timezone.utc).isoformat(),
        }

    # ── Flush to PostgreSQL ──────────────────────────────────────

    def _start_flush_thread(self) -> None:
        self._flush_thread = threading.Thread(target=self._flush_loop, daemon=True, name="metrics-flush")
        self._flush_thread.start()

    def _flush_loop(self) -> None:
        while not self._shutdown:
            time.sleep(self.FLUSH_INTERVAL)
            self._flush_to_db()

    def _flush_to_db(self) -> None:
        try:
            from backend.app.db.session import SessionLocal
            from sqlalchemy import text

            snapshot = self.snapshot()
            counters = snapshot["counters"]
            histograms = snapshot["histograms"]
            uptime = snapshot["uptime_seconds"]

            db = SessionLocal()
            try:
                db.execute(
                    text(
                        """
                        INSERT INTO metrics_snapshots (uptime_seconds, counters, histograms, created_at)
                        VALUES (:uptime, :counters, :histograms, :ts)
                        """
                    ),
                    {
                        "uptime": uptime,
                        "counters": str(dict(counters)),
                        "histograms": str(dict(histograms)),
                        "ts": datetime.now(timezone.utc),
                    },
                )
                db.commit()
                logger.info("metrics_flushed counters=%d histograms=%d", len(counters), len(histograms))
            finally:
                db.close()
        except Exception as exc:
            logger.warning("metrics_flush_failed: %s", exc)

    def shutdown(self) -> None:
        self._shutdown = True
        if self._flush_thread and self._flush_thread.is_alive():
            self._flush_thread.join(timeout=3)
        logger.info("metrics_collector_shutdown")


def get_metrics_collector() -> MetricsCollector:
    """Public accessor — always returns the same singleton."""
    return MetricsCollector()
```

### Step 1.2: Register health dashboard router

Modify `backend/app/api/router.py` — add the health dashboard import and route:

```python
from backend.app.api.v1.health_dashboard import router as health_dashboard_router
```

Add after the existing health_router include:

```python
api_router.include_router(health_dashboard_router, tags=["Health Dashboard"])
```

**Full modified `backend/app/api/router.py`:**

```python
from fastapi import APIRouter

from backend.app.api.metrics import router as metrics_router
from backend.app.api.v1.agents import router as agents_router
from backend.app.api.v1.github import router as github_router
from backend.app.api.v1.health import router as health_router
from backend.app.api.v1.health_dashboard import router as health_dashboard_router
from backend.app.api.v1.notifications import router as notifications_router
from backend.app.api.v1.profile import router as profile_router
from backend.app.api.v1.repository import router as repository_router
from backend.app.api.v1.search import router as search_router
from backend.app.api.v1.system import router as system_router
from backend.app.api.v1.users import router as users_router
from backend.app.api.v1.vault import router as vault_router

api_router = APIRouter()

api_router.include_router(health_router, tags=["Health"])

api_router.include_router(users_router, tags=["Users"])

api_router.include_router(profile_router, prefix="/me/profile", tags=["Profile"])

api_router.include_router(github_router, prefix="/me/github", tags=["GitHub"])

api_router.include_router(vault_router, prefix="/me/vault", tags=["Vault"])

api_router.include_router(metrics_router, tags=["Metrics"])

api_router.include_router(notifications_router, prefix="/notifications", tags=["Notifications"])

api_router.include_router(system_router, tags=["System"])

api_router.include_router(health_dashboard_router, tags=["Health Dashboard"])

api_router.include_router(search_router, tags=["Search"])

api_router.include_router(repository_router, tags=["Repository"])

api_router.include_router(agents_router, tags=["Agents"])
```

### Step 1.3: Commit

```bash
git add backend/app/services/metrics_collector.py backend/app/api/router.py
git commit -m "feat: thread-safe metrics collector singleton with periodic DB flush"
```

---

## Task 2: System Health API

**Files:**
- Create: `backend/app/api/v1/health_dashboard.py`

### Step 2.1: Create health dashboard endpoint

Create `backend/app/api/v1/health_dashboard.py`:

```python
"""Aggregated health dashboard endpoint."""

from __future__ import annotations

import time

import psutil
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, get_db
from backend.app.core.logging import get_logger
from backend.app.core.system_info import get_disk_info, get_gpu_info, get_ram_info
from backend.app.models.user import User
from backend.app.services.health_service import HealthService
from backend.app.services.metrics_collector import get_metrics_collector

logger = get_logger(__name__)

router = APIRouter()

_start_time = time.time()


def _check_redis() -> dict:
    """Check Redis connectivity."""
    try:
        import redis

        from backend.app.core.config import settings

        r = redis.from_url(settings.REDIS_URL, socket_timeout=2)
        info = r.info("memory")
        return {
            "status": "healthy",
            "connected": True,
            "used_memory_human": info.get("used_memory_human", "unknown"),
            "used_memory_bytes": info.get("used_memory", 0),
        }
    except Exception as exc:
        return {"status": "unhealthy", "connected": False, "error": str(exc)}


def _check_qdrant() -> dict:
    """Check Qdrant vector DB connectivity."""
    try:
        from qdrant_client import QdrantClient

        client = QdrantClient(host="localhost", port=6333, timeout=3)
        collections = client.get_collections()
        return {
            "status": "healthy",
            "connected": True,
            "collections_count": len(collections.collections),
        }
    except Exception as exc:
        return {"status": "unhealthy", "connected": False, "error": str(exc)}


def _check_llm() -> dict:
    """Check LLM provider status (basic reachability)."""
    try:
        import httpx

        # Try local Ollama first
        resp = httpx.get("http://localhost:11434/api/tags", timeout=3)
        if resp.status_code == 200:
            data = resp.json()
            models = [m.get("name", "") for m in data.get("models", [])]
            return {
                "status": "healthy",
                "provider": "ollama",
                "models": models[:10],
                "models_loaded": len(models),
            }
    except Exception:
        pass

    return {
        "status": "unknown",
        "provider": "none",
        "models": [],
        "models_loaded": 0,
    }


@router.get("/health/dashboard")
async def get_health_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Aggregated system health: system resources, service status, agent metrics, indexing, LLM."""
    collector = get_metrics_collector()
    uptime = time.time() - _start_time

    # ── System resources ─────────────────────────────────────────
    cpu_percent = psutil.cpu_percent(interval=0.1)
    ram = get_ram_info()
    ram_used = ram["total_gb"] - ram["available_gb"]
    gpu = get_gpu_info()
    disk_path = (
        current_user.storage_root
        if hasattr(current_user, "storage_root") and current_user.storage_root
        else "."
    )
    disk = get_disk_info(disk_path)

    # ── Service health ───────────────────────────────────────────
    db_healthy = HealthService.check_database()
    redis_info = _check_redis()
    qdrant_info = _check_qdrant()
    llm_info = _check_llm()

    # ── Metrics snapshot ─────────────────────────────────────────
    snapshot = collector.snapshot()
    counters = snapshot["counters"]
    histograms = snapshot["histograms"]

    agent_runs = counters.get("agent.runs.total", 0)
    agent_success = counters.get("agent.runs.success", 0)
    agent_failure = counters.get("agent.runs.failure", 0)
    agent_success_rate = (
        round((agent_success / agent_runs) * 100, 1) if agent_runs > 0 else 0.0
    )

    search_queries = counters.get("search.queries.total", 0)
    search_latencies = histograms.get("search.latency_ms", {})
    search_avg_latency = search_latencies.get("avg", 0.0)

    indexing_files = counters.get("indexing.files.total", 0)
    indexing_errors = counters.get("indexing.errors.total", 0)

    memory_entries = counters.get("memory.entries.total", 0)
    memory_searches = counters.get("memory.searches.total", 0)
    memory_hits = counters.get("memory.hits.total", 0)
    memory_hit_rate = (
        round((memory_hits / memory_searches) * 100, 1) if memory_searches > 0 else 0.0
    )

    llm_calls = counters.get("llm.calls.total", 0)
    llm_tokens = counters.get("llm.tokens.total", 0)
    llm_errors = counters.get("llm.errors.total", 0)
    llm_latencies = histograms.get("llm.latency_ms", {})
    llm_avg_latency = llm_latencies.get("avg", 0.0)

    # ── Overall status ───────────────────────────────────────────
    services = {
        "database": {"status": "healthy" if db_healthy else "unhealthy"},
        "redis": {"status": redis_info["status"], "used_memory_human": redis_info.get("used_memory_human")},
        "qdrant": {"status": qdrant_info["status"], "collections_count": qdrant_info.get("collections_count", 0)},
        "llm": {"status": llm_info["status"], "provider": llm_info.get("provider"), "models_loaded": llm_info.get("models_loaded", 0)},
    }
    all_healthy = all(s["status"] == "healthy" for s in services.values())
    overall = "healthy" if all_healthy else "degraded"

    return {
        "overall_status": overall,
        "uptime_seconds": round(uptime, 1),
        "system": {
            "cpu_percent": cpu_percent,
            "ram_total_gb": ram["total_gb"],
            "ram_used_gb": round(ram_used, 2),
            "ram_percent": round((ram_used / ram["total_gb"]) * 100, 1) if ram["total_gb"] > 0 else 0,
            "gpu_name": gpu.get("name", "No GPU detected"),
            "gpu_type": gpu.get("type", ""),
            "disk_total_gb": disk["total_gb"],
            "disk_used_gb": disk["used_gb"],
            "disk_percent": disk["percent"],
        },
        "services": services,
        "agents": {
            "total_runs": int(agent_runs),
            "successful_runs": int(agent_success),
            "failed_runs": int(agent_failure),
            "success_rate_percent": agent_success_rate,
            "avg_duration_ms": histograms.get("agent.run.duration_ms", {}).get("avg", 0.0),
            "total_tokens_used": int(counters.get("agent.tokens.total", 0)),
        },
        "search": {
            "total_queries": int(search_queries),
            "avg_latency_ms": round(search_avg_latency, 2),
            "total_results": int(counters.get("search.results.total", 0)),
        },
        "indexing": {
            "total_files_indexed": int(indexing_files),
            "total_errors": int(indexing_errors),
            "avg_sync_time_ms": histograms.get("indexing.sync_time_ms", {}).get("avg", 0.0),
        },
        "memory": {
            "total_entries": int(memory_entries),
            "total_searches": int(memory_searches),
            "total_hits": int(memory_hits),
            "hit_rate_percent": memory_hit_rate,
        },
        "llm": {
            "provider": llm_info.get("provider", "none"),
            "models_loaded": llm_info.get("models_loaded", 0),
            "models": llm_info.get("models", []),
            "total_calls": int(llm_calls),
            "total_tokens_used": int(llm_tokens),
            "total_errors": int(llm_errors),
            "avg_latency_ms": round(llm_avg_latency, 2),
        },
    }
```

### Step 2.2: Commit

```bash
git add backend/app/api/v1/health_dashboard.py backend/app/api/router.py
git commit -m "feat: aggregated health dashboard API endpoint"
```

---

## Task 3: Health Dashboard Frontend

**Files:**
- Create: `frontend/app/health/page.tsx`
- Modify: `frontend/src/shared/layout/DashboardShell.tsx`
- Modify: `frontend/src/shared/types.ts`
- Modify: `frontend/src/shared/auth/cortexApi.ts`

### Step 3.1: Add TypeScript types

Modify `frontend/src/shared/types.ts` — add at end of file:

```typescript
// ── Health Dashboard ─────────────────────────────────────────────

export interface HealthDashboard {
  overall_status: "healthy" | "degraded" | "unhealthy";
  uptime_seconds: number;
  system: {
    cpu_percent: number;
    ram_total_gb: number;
    ram_used_gb: number;
    ram_percent: number;
    gpu_name: string;
    gpu_type: string;
    disk_total_gb: number;
    disk_used_gb: number;
    disk_percent: number;
  };
  services: {
    database: { status: string };
    redis: { status: string; used_memory_human?: string };
    qdrant: { status: string; collections_count?: number };
    llm: { status: string; provider?: string; models_loaded?: number };
  };
  agents: {
    total_runs: number;
    successful_runs: number;
    failed_runs: number;
    success_rate_percent: number;
    avg_duration_ms: number;
    total_tokens_used: number;
  };
  search: {
    total_queries: number;
    avg_latency_ms: number;
    total_results: number;
  };
  indexing: {
    total_files_indexed: number;
    total_errors: number;
    avg_sync_time_ms: number;
  };
  memory: {
    total_entries: number;
    total_searches: number;
    total_hits: number;
    hit_rate_percent: number;
  };
  llm: {
    provider: string;
    models_loaded: number;
    models: string[];
    total_calls: number;
    total_tokens_used: number;
    total_errors: number;
    avg_latency_ms: number;
  };
}
```

### Step 3.2: Add API function

Modify `frontend/src/shared/auth/cortexApi.ts` — add at end of file:

```typescript
// ── Health Dashboard endpoints ────────────────────────────────────

import type { HealthDashboard } from "../types";

export async function apiHealthDashboard(): Promise<HealthDashboard> {
  return request<HealthDashboard>("GET", "/api/v1/health/dashboard");
}
```

### Step 3.3: Create health dashboard page

Create `frontend/app/health/page.tsx`:

```tsx
"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { useAuth } from "../../src/shared/auth/AuthProvider";
import { apiHealthDashboard } from "../../src/shared/auth/cortexApi";
import DashboardShell from "../../src/shared/layout/DashboardShell";
import Card from "../../src/shared/ui/Card";
import Button from "../../src/shared/ui/Button";
import { cn } from "../../src/lib/utils";
import {
  Activity,
  Cpu,
  MemoryStick,
  HardDrive,
  Monitor,
  Database,
  Wifi,
  Search,
  Bot,
  Brain,
  RefreshCw,
  Loader2,
  Zap,
  Clock,
  CheckCircle,
  XCircle,
  AlertTriangle,
} from "lucide-react";
import type { HealthDashboard } from "../../src/shared/types";

function StatusDot({ status }: { status: string }) {
  return (
    <span
      className={cn(
        "inline-block h-2.5 w-2.5 rounded-full shrink-0",
        status === "healthy"
          ? "bg-green-500 shadow-[0_0_6px_rgba(34,197,94,0.4)]"
          : status === "degraded"
            ? "bg-amber-500 shadow-[0_0_6px_rgba(245,158,11,0.4)]"
            : "bg-red-500 shadow-[0_0_6px_rgba(239,68,68,0.4)]"
      )}
    />
  );
}

function SystemCard({
  icon: Icon,
  label,
  value,
  sub,
  color,
}: {
  icon: React.ElementType;
  label: string;
  value: string | number;
  sub?: string;
  color: string;
}) {
  return (
    <Card className="p-4">
      <div className="flex items-center gap-2 mb-3">
        <div className={cn("h-8 w-8 rounded-lg flex items-center justify-center", color)}>
          <Icon className="h-4 w-4" />
        </div>
        <span className="text-xs text-text-muted">{label}</span>
      </div>
      <p className="text-2xl font-semibold text-text font-mono">{value}</p>
      {sub && <p className="text-[11px] text-text-muted mt-1">{sub}</p>}
    </Card>
  );
}

function ServiceRow({
  name,
  status,
  detail,
}: {
  name: string;
  status: string;
  detail?: string;
}) {
  return (
    <div className="flex items-center justify-between py-3 px-5 hover:bg-bg-hover/50 transition-colors">
      <div className="flex items-center gap-3">
        <StatusDot status={status} />
        <span className="text-sm text-text">{name}</span>
      </div>
      <div className="flex items-center gap-3">
        {detail && <span className="text-xs text-text-muted font-mono">{detail}</span>}
        <span
          className={cn(
            "text-[10px] font-mono font-medium uppercase tracking-wider px-2.5 py-1 rounded-full",
            status === "healthy"
              ? "bg-green-500/10 text-green-400 border border-green-500/15"
              : status === "degraded"
                ? "bg-amber-500/10 text-amber-400 border border-amber-500/15"
                : "bg-red-500/10 text-red-400 border border-red-500/15"
          )}
        >
          {status}
        </span>
      </div>
    </div>
  );
}

function MetricRow({
  label,
  value,
  icon: Icon,
}: {
  label: string;
  value: string | number;
  icon?: React.ElementType;
}) {
  return (
    <div className="flex items-center justify-between py-2">
      <span className="text-xs text-text-muted flex items-center gap-2">
        {Icon && <Icon className="h-3.5 w-3.5" />}
        {label}
      </span>
      <span className="text-sm text-text font-mono">{value}</span>
    </div>
  );
}

function formatUptime(seconds: number): string {
  const d = Math.floor(seconds / 86400);
  const h = Math.floor((seconds % 86400) / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  if (d > 0) return `${d}d ${h}h ${m}m`;
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m`;
}

function formatTokens(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return String(n);
}

export default function HealthPage() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
  const [data, setData] = useState<HealthDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  useEffect(() => {
    if (!authLoading && !user) router.replace("/auth");
    if (!authLoading && user && user.role !== "admin") router.replace("/app");
  }, [user, authLoading, router]);

  const fetchDashboard = useCallback(async () => {
    try {
      setError("");
      const result = await apiHealthDashboard();
      setData(result);
      setLastRefresh(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load health data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!user || user.role !== "admin") return;
    fetchDashboard();
    const interval = setInterval(fetchDashboard, 15000);
    return () => clearInterval(interval);
  }, [user, fetchDashboard]);

  if (authLoading || !user || user.role !== "admin") return null;

  const stagger = {
    animate: { transition: { staggerChildren: 0.06 } },
  };
  const item = {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    transition: { type: "spring" as const, damping: 25, stiffness: 200 },
  };

  return (
    <DashboardShell>
      <div className="max-w-6xl mx-auto space-y-6 animate-fade-in">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold text-text">System Health</h1>
            <p className="text-sm text-text-muted mt-1">
              Real-time monitoring dashboard
              {data && (
                <span className="ml-2 font-mono text-[10px]">
                  &middot; Uptime: {formatUptime(data.uptime_seconds)}
                </span>
              )}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-[10px] text-text-muted font-mono">
              {lastRefresh.toLocaleTimeString()}
            </span>
            <Button variant="ghost" size="sm" onClick={fetchDashboard}>
              <RefreshCw className={cn("h-3.5 w-3.5", loading && "animate-spin")} />
              Refresh
            </Button>
          </div>
        </div>

        {error && (
          <div className="px-4 py-3 text-sm text-error bg-error/10 rounded-xl border border-error/10 flex items-center gap-2">
            <AlertTriangle className="h-4 w-4" />
            {error}
          </div>
        )}

        {loading && !data ? (
          <div className="flex flex-col items-center justify-center py-20 gap-3">
            <Loader2 className="h-8 w-8 text-accent animate-spin" />
            <p className="text-sm text-text-muted">Loading health data...</p>
          </div>
        ) : data ? (
          <motion.div variants={stagger} initial="initial" animate="animate" className="space-y-6">
            {/* Overall Status */}
            <motion.div {...item}>
              <Card
                gradient
                className={cn(
                  "p-5 border",
                  data.overall_status === "healthy"
                    ? "border-green-500/20"
                    : data.overall_status === "degraded"
                      ? "border-amber-500/20"
                      : "border-red-500/20"
                )}
              >
                <div className="flex items-center gap-3">
                  <StatusDot status={data.overall_status} />
                  <span className="text-sm font-medium text-text capitalize">
                    System {data.overall_status}
                  </span>
                  <span className="text-xs text-text-muted font-mono">
                    {data.uptime_seconds > 0 ? formatUptime(data.uptime_seconds) : "Just started"}
                  </span>
                </div>
              </Card>
            </motion.div>

            {/* System Resources */}
            <motion.div {...item}>
              <h2 className="text-sm font-medium text-text mb-3 flex items-center gap-2">
                <Monitor className="h-4 w-4 text-text-muted" />
                System Resources
              </h2>
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                <SystemCard
                  icon={Cpu}
                  label="CPU"
                  value={`${data.system.cpu_percent}%`}
                  color="bg-accent/10 text-accent"
                />
                <SystemCard
                  icon={MemoryStick}
                  label="RAM"
                  value={`${data.system.ram_percent}%`}
                  sub={`${data.system.ram_used_gb} / ${data.system.ram_total_gb} GB`}
                  color="bg-purple-500/10 text-purple-400"
                />
                <SystemCard
                  icon={HardDrive}
                  label="Disk"
                  value={`${data.system.disk_percent}%`}
                  sub={`${data.system.disk_used_gb} / ${data.system.disk_total_gb} GB`}
                  color="bg-amber-500/10 text-amber-400"
                />
                <SystemCard
                  icon={Monitor}
                  label="GPU"
                  value={data.system.gpu_name}
                  sub={data.system.gpu_type || undefined}
                  color="bg-green-500/10 text-green-400"
                />
              </div>
            </motion.div>

            {/* Service Status */}
            <motion.div {...item}>
              <h2 className="text-sm font-medium text-text mb-3 flex items-center gap-2">
                <Wifi className="h-4 w-4 text-text-muted" />
                Service Status
              </h2>
              <Card className="overflow-hidden divide-y divide-border">
                <ServiceRow
                  name="PostgreSQL"
                  status={data.services.database.status}
                />
                <ServiceRow
                  name="Redis"
                  status={data.services.redis.status}
                  detail={data.services.redis.used_memory_human}
                />
                <ServiceRow
                  name="Qdrant"
                  status={data.services.qdrant.status}
                  detail={
                    data.services.qdrant.collections_count !== undefined
                      ? `${data.services.qdrant.collections_count} collections`
                      : undefined
                  }
                />
                <ServiceRow
                  name="LLM Provider"
                  status={data.services.llm.status}
                  detail={
                    data.services.llm.provider
                      ? `${data.services.llm.provider} (${data.services.llm.models_loaded} models)`
                      : undefined
                  }
                />
              </Card>
            </motion.div>

            {/* Agent Performance */}
            <motion.div {...item}>
              <h2 className="text-sm font-medium text-text mb-3 flex items-center gap-2">
                <Bot className="h-4 w-4 text-text-muted" />
                Agent Performance
              </h2>
              <Card className="p-5">
                <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
                  <div>
                    <p className="text-xs text-text-muted mb-1">Total Runs</p>
                    <p className="text-xl font-semibold text-text font-mono">
                      {data.agents.total_runs}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-text-muted mb-1">Success Rate</p>
                    <p className="text-xl font-semibold font-mono">
                      <span
                        className={cn(
                          data.agents.success_rate_percent >= 90
                            ? "text-green-400"
                            : data.agents.success_rate_percent >= 70
                              ? "text-amber-400"
                              : "text-red-400"
                        )}
                      >
                        {data.agents.success_rate_percent}%
                      </span>
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-text-muted mb-1">Avg Duration</p>
                    <p className="text-xl font-semibold text-text font-mono">
                      {data.agents.avg_duration_ms.toFixed(0)}ms
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-text-muted mb-1">Successful</p>
                    <p className="text-xl font-semibold text-green-400 font-mono flex items-center gap-1">
                      <CheckCircle className="h-4 w-4" />
                      {data.agents.successful_runs}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-text-muted mb-1">Failed</p>
                    <p className="text-xl font-semibold text-red-400 font-mono flex items-center gap-1">
                      <XCircle className="h-4 w-4" />
                      {data.agents.failed_runs}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-text-muted mb-1">Tokens Used</p>
                    <p className="text-xl font-semibold text-text font-mono">
                      {formatTokens(data.agents.total_tokens_used)}
                    </p>
                  </div>
                </div>
              </Card>
            </motion.div>

            {/* Search & Indexing & Memory */}
            <motion.div {...item} className="grid grid-cols-1 lg:grid-cols-3 gap-4">
              <Card className="p-5">
                <h3 className="text-sm font-medium text-text mb-3 flex items-center gap-2">
                  <Search className="h-4 w-4 text-text-muted" />
                  Search
                </h3>
                <MetricRow label="Total Queries" value={data.search.total_queries} />
                <MetricRow label="Avg Latency" value={`${data.search.avg_latency_ms.toFixed(1)}ms`} />
                <MetricRow label="Total Results" value={data.search.total_results} />
              </Card>

              <Card className="p-5">
                <h3 className="text-sm font-medium text-text mb-3 flex items-center gap-2">
                  <Activity className="h-4 w-4 text-text-muted" />
                  Indexing
                </h3>
                <MetricRow label="Files Indexed" value={data.indexing.total_files_indexed} />
                <MetricRow label="Errors" value={data.indexing.total_errors} icon={XCircle} />
                <MetricRow label="Avg Sync Time" value={`${data.indexing.avg_sync_time_ms.toFixed(0)}ms`} />
              </Card>

              <Card className="p-5">
                <h3 className="text-sm font-medium text-text mb-3 flex items-center gap-2">
                  <Brain className="h-4 w-4 text-text-muted" />
                  Memory
                </h3>
                <MetricRow label="Total Entries" value={data.memory.total_entries} />
                <MetricRow label="Search Queries" value={data.memory.total_searches} />
                <MetricRow
                  label="Hit Rate"
                  value={`${data.memory.hit_rate_percent}%`}
                  icon={Zap}
                />
              </Card>
            </motion.div>

            {/* LLM Status */}
            <motion.div {...item}>
              <h2 className="text-sm font-medium text-text mb-3 flex items-center gap-2">
                <Zap className="h-4 w-4 text-text-muted" />
                LLM Status
              </h2>
              <Card className="p-5">
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                  <div>
                    <p className="text-xs text-text-muted mb-1">Provider</p>
                    <p className="text-lg font-semibold text-text capitalize">{data.llm.provider}</p>
                  </div>
                  <div>
                    <p className="text-xs text-text-muted mb-1">Models Loaded</p>
                    <p className="text-lg font-semibold text-text font-mono">{data.llm.models_loaded}</p>
                  </div>
                  <div>
                    <p className="text-xs text-text-muted mb-1">Total Calls</p>
                    <p className="text-lg font-semibold text-text font-mono">{data.llm.total_calls}</p>
                  </div>
                  <div>
                    <p className="text-xs text-text-muted mb-1">Tokens Used</p>
                    <p className="text-lg font-semibold text-text font-mono">{formatTokens(data.llm.total_tokens_used)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-text-muted mb-1">Errors</p>
                    <p className="text-lg font-semibold font-mono">
                      <span className={data.llm.total_errors > 0 ? "text-red-400" : "text-green-400"}>
                        {data.llm.total_errors}
                      </span>
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-text-muted mb-1">Avg Latency</p>
                    <p className="text-lg font-semibold text-text font-mono">
                      {data.llm.avg_latency_ms.toFixed(0)}ms
                    </p>
                  </div>
                  {data.llm.models.length > 0 && (
                    <div className="col-span-2">
                      <p className="text-xs text-text-muted mb-1">Available Models</p>
                      <div className="flex flex-wrap gap-1.5 mt-1">
                        {data.llm.models.map((model) => (
                          <span
                            key={model}
                            className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-bg-elevated border border-border-subtle text-text-secondary"
                          >
                            {model}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </Card>
            </motion.div>
          </motion.div>
        ) : null}
      </div>
    </DashboardShell>
  );
}
```

### Step 3.4: Add Health nav item to DashboardShell

Modify `frontend/src/shared/layout/DashboardShell.tsx`:

1. Add `Activity` to the lucide-react imports (line 18):

```typescript
import {
  LayoutDashboard,
  Lock,
  Brain,
  Bot,
  User,
  Settings,
  Menu,
  LogOut,
  Shield,
  Search,
  Bell,
  Activity,
} from "lucide-react";
```

2. Add the Health nav item to `accountNavItems` array (after Settings, before closing bracket):

```typescript
const accountNavItems = [
  { label: "Vault", href: "/vault", icon: Lock },
  { label: "Memory", href: "/memory", icon: Brain },
  { label: "Profile", href: "/profile", icon: User },
  { label: "Settings", href: "/settings", icon: Settings },
];
```

Change the `accountNavItems` definition to conditionally include Health (admin only). Since `accountNavItems` is a const outside the component, we add Health as a separate admin-only item after the admin button in the sidebar. Replace the admin-only button block in the sidebar nav (appears twice — desktop and tablet) with:

```tsx
{user?.role === "admin" && (
  <>
    <button
      onClick={() => router.push("/admin")}
      className={cn(
        "relative flex items-center gap-3 w-full px-3 py-2.5 rounded-xl text-sm transition-all duration-200",
        pathname === "/admin"
          ? "text-accent font-medium shadow-[0_0_20px_rgba(6,182,212,0.08)]"
          : "text-text-secondary hover:bg-bg-hover hover:text-text hover:shadow-[0_0_15px_rgba(6,182,212,0.04)]"
      )}
    >
      {pathname === "/admin" && (
        <motion.div
          layoutId="sidebar-active"
          className="absolute inset-0 rounded-xl bg-accent-faint border border-accent/15"
          transition={{ type: "spring", damping: 25, stiffness: 300 }}
        />
      )}
      {pathname === "/admin" && (
        <span className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-[3px] rounded-full bg-accent shadow-[0_0_6px_rgba(6,182,212,0.6)] animate-pulse-dot" />
      )}
      <Shield className={cn("h-5 w-5 shrink-0 relative z-10 transition-all duration-200", pathname === "/admin" && "drop-shadow-[0_0_4px_rgba(6,182,212,0.4)]")} />
      <span className="relative z-10 whitespace-nowrap flex-1 text-left">Admin</span>
    </button>
    <button
      onClick={() => router.push("/health")}
      className={cn(
        "relative flex items-center gap-3 w-full px-3 py-2.5 rounded-xl text-sm transition-all duration-200",
        pathname === "/health"
          ? "text-accent font-medium shadow-[0_0_20px_rgba(6,182,212,0.08)]"
          : "text-text-secondary hover:bg-bg-hover hover:text-text hover:shadow-[0_0_15px_rgba(6,182,212,0.04)]"
      )}
    >
      {pathname === "/health" && (
        <motion.div
          layoutId="sidebar-active"
          className="absolute inset-0 rounded-xl bg-accent-faint border border-accent/15"
          transition={{ type: "spring", damping: 25, stiffness: 300 }}
        />
      )}
      {pathname === "/health" && (
        <span className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-[3px] rounded-full bg-accent shadow-[0_0_6px_rgba(6,182,212,0.6)] animate-pulse-dot" />
      )}
      <Activity className={cn("h-5 w-5 shrink-0 relative z-10 transition-all duration-200", pathname === "/health" && "drop-shadow-[0_0_4px_rgba(6,182,212,0.4)]")} />
      <span className="relative z-10 whitespace-nowrap flex-1 text-left">Health</span>
    </button>
  </>
)}
```

This block appears in 3 places in the DashboardShell (desktop sidebar ~line 205, tablet sidebar ~line 372, and the mobile bottom tab bar does not include admin items). Update the desktop and tablet sidebar blocks identically.

### Step 3.5: Build check

```bash
cd /home/adi/Desktop/Cortex-Workspace/frontend && npx next build
```

### Step 3.6: Commit

```bash
git add frontend/app/health/page.tsx frontend/src/shared/layout/DashboardShell.tsx frontend/src/shared/types.ts frontend/src/shared/auth/cortexApi.ts
git commit -m "feat: health dashboard page with real-time system metrics (admin only)"
```

---

## Exit Criteria

- [ ] `MetricsCollector` singleton collects agent, search, indexing, memory, and LLM metrics
- [ ] Metrics flush to PostgreSQL every 5 minutes via background thread
- [ ] `GET /api/v1/health/dashboard` returns aggregated system + service + metrics data
- [ ] `/health` page displays system resources, service status, agent/search/indexing/memory/LLM health
- [ ] Health nav item appears in sidebar for admin users only
- [ ] Dashboard auto-refreshes every 15 seconds
- [ ] All code compiles and builds clean
