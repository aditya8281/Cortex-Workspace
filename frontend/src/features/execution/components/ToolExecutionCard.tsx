"use client";

import type { ToolExecution } from "../api";

function statusBadge(status: string) {
  const map: Record<string, string> = {
    completed: "bg-success/10 text-success",
    pending: "bg-warning/10 text-warning",
    running: "bg-accent/10 text-accent",
    failed: "bg-danger/10 text-danger",
  };
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${map[status] ?? "bg-bg-surface text-text-muted"}`}
    >
      {status}
    </span>
  );
}

function formatDuration(ms: number | null) {
  if (ms === null || ms === undefined) return "—";
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(2)}s`;
}

function formatTimestamp(iso: string | null) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString();
}

function JsonBlock({ label, data }: { label: string; data: unknown }) {
  if (data === null || data === undefined) return null;
  return (
    <div className="space-y-1">
      <span className="text-label uppercase text-text-muted tracking-wider text-[11px]">
        {label}
      </span>
      <pre className="font-mono text-sm text-text-secondary bg-bg-surface rounded p-3 overflow-x-auto max-h-48 overflow-y-auto">
        {JSON.stringify(data, null, 2)}
      </pre>
    </div>
  );
}

interface ToolExecutionCardProps {
  execution: ToolExecution;
}

export function ToolExecutionCard({ execution }: ToolExecutionCardProps) {
  return (
    <div className="bg-bg-elevated rounded-lg border border-border-subtle p-4 space-y-3 hover:shadow-md motion-safe:transition-shadow">
      {/* Header */}
      <div className="flex items-center justify-between gap-3">
        <div className="min-w-0">
          <h4 className="text-title font-medium text-text-primary truncate">
            {execution.tool_name}
          </h4>
          <p className="text-body text-text-secondary text-xs mt-0.5">
            ID {execution.id}
            {execution.workflow_id !== null && (
              <> &middot; Workflow {execution.workflow_id}</>
            )}
          </p>
        </div>
        {statusBadge(execution.status)}
      </div>

      {/* Meta */}
      <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-text-secondary">
        <span>
          <span className="text-text-muted">Duration:</span>{" "}
          {formatDuration(execution.duration_ms)}
        </span>
        <span>
          <span className="text-text-muted">Started:</span>{" "}
          {formatTimestamp(execution.started_at)}
        </span>
        <span>
          <span className="text-text-muted">Completed:</span>{" "}
          {formatTimestamp(execution.completed_at)}
        </span>
        {execution.retry_count > 0 && (
          <span>
            <span className="text-text-muted">Retries:</span>{" "}
            {execution.retry_count}
          </span>
        )}
      </div>

      {/* Parameters */}
      <JsonBlock label="Parameters" data={execution.parameters} />

      {/* Result */}
      <JsonBlock label="Result" data={execution.result} />

      {/* Error */}
      {execution.error_message && (
        <div className="rounded border border-danger/20 bg-danger/5 p-3">
          <span className="text-label uppercase text-danger tracking-wider text-[11px]">
            {execution.error_type ?? "Error"}
          </span>
          <p className="text-body text-danger mt-1 text-sm">
            {execution.error_message}
          </p>
        </div>
      )}
    </div>
  );
}
