"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/shared/auth/AuthProvider";
import { Skeleton } from "@/shared/ui/Skeleton";
import { tools, workflows, type ToolExecution, type Workflow, type ExecutionStats } from "./api";
import { ToolRegistryPanel } from "./components/ToolRegistryPanel";
import { ToolExecutionCard } from "./components/ToolExecutionCard";
import { WorkflowCard } from "./components/WorkflowCard";
import { WorkflowBuilder } from "./components/WorkflowBuilder";

// ── Tab definitions ──────────────────────────────────────────────────────────

type TabKey = "registry" | "execute" | "workflows";

const TABS: { key: TabKey; label: string }[] = [
  { key: "registry", label: "Tool Registry" },
  { key: "execute", label: "Tool Execution" },
  { key: "workflows", label: "Workflows" },
];

// ── Main page ────────────────────────────────────────────────────────────────

export default function ExecutionPage() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();

  const [activeTab, setActiveTab] = useState<TabKey>("registry");

  // ── Auth redirect ───────────────────────────────────────────────────────

  useEffect(() => {
    if (!authLoading && !user) {
      router.replace("/auth");
    }
  }, [authLoading, user, router]);

  // ── Loading skeleton ────────────────────────────────────────────────────

  if (authLoading || !user) {
    return (
        <div className="max-w-5xl mx-auto space-y-6">
          <div className="space-y-1">
            <Skeleton className="h-6 w-32" />
            <Skeleton className="h-4 w-56" />
          </div>
          <div className="flex gap-2">
            <Skeleton className="h-9 w-28" />
            <Skeleton className="h-9 w-28" />
            <Skeleton className="h-9 w-28" />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="bg-bg-elevated rounded-lg border border-border-subtle p-4 space-y-3">
                <Skeleton className="h-4 w-28" />
                <Skeleton className="h-3 w-16" />
                <Skeleton className="h-3 w-full" />
                <Skeleton className="h-3 w-3/4" />
              </div>
            ))}
          </div>
        </div>
    );
  }

  return (
      <div className="max-w-5xl mx-auto space-y-6 animate-fade-in">
        {/* Page header */}
        <div>
          <h1 className="text-headline font-semibold text-text-primary">Execution</h1>
          <p className="mt-1 text-sm text-text-secondary">
            Manage tools, execute operations, and orchestrate workflows.
          </p>
        </div>

        {/* Tab bar */}
        <div className="flex gap-2 border-b border-border-subtle pb-px" role="tablist">
          {TABS.map((tab) => (
            <button
              key={tab.key}
              role="tab"
              aria-selected={activeTab === tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`px-4 py-2 text-sm font-medium rounded-t-md motion-safe:transition-colors -mb-px ${
                activeTab === tab.key
                  ? "bg-bg-elevated border border-border-subtle border-b-bg-elevated text-text-primary"
                  : "text-text-muted hover:text-text-secondary"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab panels */}
        <div role="tabpanel">
          {activeTab === "registry" && <RegistryTab />}
          {activeTab === "execute" && <ExecuteTab />}
          {activeTab === "workflows" && <WorkflowsTab />}
        </div>
      </div>
  );
}

// ── Registry Tab ─────────────────────────────────────────────────────────────

function RegistryTab() {
  const [stats, setStats] = useState<ExecutionStats | null>(null);

  useEffect(() => {
    tools.getStats().then(setStats).catch(() => {});
  }, []);

  return (
    <div className="space-y-6">
      {/* Stats bar */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard label="Total Executions" value={stats.total} />
          <StatCard label="Success Rate" value={`${(stats.success_rate * 100).toFixed(1)}%`} />
          <StatCard label="Failed" value={stats.failed} variant="danger" />
          <StatCard label="Avg Duration" value={`${stats.average_duration_ms.toFixed(0)}ms`} />
        </div>
      )}

      {/* Tool registry */}
      <div>
        <span className="text-label uppercase text-text-muted tracking-wider text-[11px]">
          Available Tools
        </span>
        <div className="mt-3">
          <ToolRegistryPanel />
        </div>
      </div>
    </div>
  );
}

function StatCard({
  label,
  value,
  variant,
}: {
  label: string;
  value: string | number;
  variant?: "danger" | "success";
}) {
  const valueColor =
    variant === "danger"
      ? "text-danger"
      : variant === "success"
        ? "text-success"
        : "text-text-primary";

  return (
    <div className="bg-bg-elevated rounded-lg border border-border-subtle p-4 space-y-1">
      <span className="text-label uppercase text-text-muted tracking-wider text-[11px]">
        {label}
      </span>
      <p className={`text-title font-medium ${valueColor}`}>{value}</p>
    </div>
  );
}

// ── Execute Tab ──────────────────────────────────────────────────────────────

function ExecuteTab() {
  const [toolName, setToolName] = useState("");
  const [params, setParams] = useState("{}");
  const [executing, setExecuting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Execution history (accumulated locally; no server list endpoint)
  const [executions, setExecutions] = useState<ToolExecution[]>([]);

  const handleExecute = async () => {
    if (!toolName.trim()) {
      setError("Tool name is required");
      return;
    }
    let parsed: Record<string, unknown> = {};
    try {
      parsed = JSON.parse(params);
    } catch {
      setError("Invalid JSON in parameters");
      return;
    }
    setError(null);
    setExecuting(true);
    try {
      const result = await tools.execute(toolName.trim(), parsed);
      setExecutions((prev) => [result, ...prev]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Execution failed");
    } finally {
      setExecuting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Execute form */}
      <div className="bg-bg-elevated rounded-lg border border-border-subtle p-4 space-y-4">
        <span className="text-label uppercase text-text-muted tracking-wider text-[11px]">
          Execute Tool
        </span>
        <div className="flex items-end gap-3 flex-wrap">
          <div className="flex-1 min-w-[200px] space-y-1">
            <label className="text-xs text-text-muted">Tool Name</label>
            <input
              type="text"
              value={toolName}
              onChange={(e) => setToolName(e.target.value)}
              placeholder="e.g. filesystem.read"
              className="w-full px-3 py-2 rounded-md text-sm font-mono bg-bg-surface border border-border-subtle text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent/60"
            />
          </div>
          <div className="flex-1 min-w-[200px] space-y-1">
            <label className="text-xs text-text-muted">Parameters (JSON)</label>
            <input
              type="text"
              value={params}
              onChange={(e) => setParams(e.target.value)}
              placeholder='{"key": "value"}'
              className="w-full px-3 py-2 rounded-md text-sm font-mono bg-bg-surface border border-border-subtle text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent/60"
            />
          </div>
          <button
            onClick={handleExecute}
            disabled={executing}
            className="px-3 py-2 rounded-md text-sm font-medium bg-accent text-void hover:bg-accent/90 disabled:opacity-50"
          >
            {executing ? "Running..." : "Execute"}
          </button>
        </div>
        {error && (
          <div className="rounded border border-danger/20 bg-danger/5 p-3">
            <p className="text-sm text-danger">{error}</p>
          </div>
        )}
      </div>

      {/* Execution history */}
      <div className="space-y-3">
        <span className="text-label uppercase text-text-muted tracking-wider text-[11px]">
          Execution History
        </span>

        {executions.length === 0 && (
          <div className="text-center py-12 text-text-muted text-sm">
            No executions yet. Run a tool above to see results here.
          </div>
        )}

        {executions.map((exec) => (
          <ToolExecutionCard key={exec.id} execution={exec} />
        ))}
      </div>
    </div>
  );
}

// ── Workflows Tab ────────────────────────────────────────────────────────────

function WorkflowsTab() {
  const [workflowsList, setWorkflowsList] = useState<Workflow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showBuilder, setShowBuilder] = useState(false);
  const [runningId, setRunningId] = useState<number | null>(null);

  const loadWorkflows = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await workflows.list({ limit: 50 });
      setWorkflowsList(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load workflows");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadWorkflows();
  }, [loadWorkflows]);

  const handleRun = async (id: number) => {
    setRunningId(id);
    try {
      const updated = await workflows.run(id);
      setWorkflowsList((prev) => prev.map((w) => (w.id === id ? updated : w)));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to run workflow");
    } finally {
      setRunningId(null);
    }
  };

  const handleCancel = async (id: number) => {
    try {
      const updated = await workflows.cancel(id);
      setWorkflowsList((prev) => prev.map((w) => (w.id === id ? updated : w)));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to cancel workflow");
    }
  };

  return (
    <div className="space-y-6">
      {/* Actions */}
      <div className="flex items-center justify-between">
        <span className="text-label uppercase text-text-muted tracking-wider text-[11px]">
          Workflows
        </span>
        <div className="flex items-center gap-2">
          <button
            onClick={loadWorkflows}
            disabled={loading}
            className="px-3 py-1.5 rounded-md text-sm font-medium bg-bg-surface border border-border-subtle text-text-primary hover:bg-bg-hover disabled:opacity-50"
          >
            {loading ? "Loading..." : "Refresh"}
          </button>
          <button
            onClick={() => setShowBuilder(!showBuilder)}
            className="px-3 py-1.5 rounded-md text-sm font-medium bg-accent text-void hover:bg-accent/90"
          >
            {showBuilder ? "Cancel" : "Create Workflow"}
          </button>
        </div>
      </div>

      {/* Builder */}
      {showBuilder && (
        <div className="bg-bg-elevated rounded-lg border border-border-subtle p-4">
          <WorkflowBuilder
            onCreated={() => {
              loadWorkflows();
              setShowBuilder(false);
            }}
          />
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="rounded border border-danger/20 bg-danger/5 p-3 flex items-center justify-between">
          <p className="text-sm text-danger">{error}</p>
          <button
            onClick={() => { setError(null); loadWorkflows(); }}
            className="px-3 py-1.5 rounded-md text-sm font-medium bg-bg-surface border border-border-subtle text-text-primary hover:bg-bg-hover"
          >
            Retry
          </button>
        </div>
      )}

      {/* Loading skeletons */}
      {loading && (
        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="bg-bg-elevated rounded-lg border border-border-subtle p-4 space-y-3">
              <div className="flex items-center justify-between">
                <Skeleton className="h-4 w-40" />
                <Skeleton className="h-5 w-20 rounded" />
              </div>
              <Skeleton className="h-3 w-64" />
              <Skeleton className="h-3 w-32" />
            </div>
          ))}
        </div>
      )}

      {/* Empty */}
      {!loading && !error && workflowsList.length === 0 && (
        <div className="text-center py-12 text-text-muted text-sm">
          No workflows yet. Create one to get started.
        </div>
      )}

      {/* Workflow list */}
      {!loading && workflowsList.length > 0 && (
        <div className="space-y-3">
          {workflowsList.map((wf) => (
            <WorkflowCard
              key={wf.id}
              workflow={wf}
              onRun={handleRun}
              onCancel={handleCancel}
              isRunning={runningId === wf.id}
            />
          ))}
        </div>
      )}
    </div>
  );
}
