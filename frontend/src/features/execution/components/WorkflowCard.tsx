"use client";

import { useState } from "react";
import { workflows, type Workflow, type WorkflowStep } from "../api";

function statusBadge(status: string) {
  const map: Record<string, string> = {
    completed: "bg-success/10 text-success",
    running: "bg-accent/10 text-accent",
    pending: "bg-warning/10 text-warning",
    failed: "bg-danger/10 text-danger",
    cancelled: "bg-bg-surface text-text-muted",
  };
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${map[status] ?? "bg-bg-surface text-text-muted"}`}
    >
      {status}
    </span>
  );
}

function stepStatusIcon(status: string | undefined) {
  if (!status) return <span className="w-2 h-2 rounded-full bg-bg-surface inline-block" />;
  const map: Record<string, string> = {
    completed: "bg-success",
    running: "bg-accent motion-safe:animate-pulse",
    pending: "bg-warning",
    failed: "bg-danger",
  };
  return (
    <span className={`w-2 h-2 rounded-full inline-block ${map[status] ?? "bg-bg-surface"}`} />
  );
}

function formatDuration(ms: number | null) {
  if (ms === null || ms === undefined) return null;
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(2)}s`;
}

interface WorkflowCardProps {
  workflow: Workflow;
  onRun?: (id: number) => void;
  onCancel?: (id: number) => void;
  isRunning?: boolean;
}

export function WorkflowCard({
  workflow,
  onRun,
  onCancel,
  isRunning,
}: WorkflowCardProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="bg-bg-elevated rounded-lg border border-border-subtle hover:shadow-md motion-safe:transition-shadow">
      {/* Header */}
      <div className="p-4 cursor-pointer" onClick={() => setExpanded(!expanded)}>
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <h4 className="text-title font-medium text-text-primary truncate">
                {workflow.name}
              </h4>
              {statusBadge(workflow.status)}
            </div>
            {workflow.description && (
              <p className="text-body text-text-secondary text-xs mt-1 line-clamp-1">
                {workflow.description}
              </p>
            )}
          </div>
          <svg
            className={`w-4 h-4 text-text-muted shrink-0 motion-safe:transition-transform ${expanded ? "rotate-180" : ""}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
          </svg>
        </div>

        {/* Summary row */}
        <div className="flex items-center gap-4 mt-3 text-xs text-text-secondary">
          <span>{workflow.steps.length} steps</span>
          <span>Step {workflow.current_step} / {workflow.steps.length}</span>
          {workflow.run_count > 0 && <span>{workflow.run_count} runs</span>}
          {workflow.total_duration_ms !== null && (
            <span>{formatDuration(workflow.total_duration_ms)}</span>
          )}
        </div>
      </div>

      {/* Expanded detail */}
      {expanded && (
        <div className="border-t border-border-subtle p-4 space-y-4">
          {/* Actions */}
          <div className="flex items-center gap-2">
            {workflow.status !== "running" && onRun && (
              <button
                onClick={() => onRun(workflow.id)}
                disabled={isRunning}
                className="px-3 py-1.5 rounded-md text-sm font-medium bg-accent text-void hover:bg-accent/90 disabled:opacity-50"
              >
                Run
              </button>
            )}
            {workflow.status === "running" && onCancel && (
              <button
                onClick={() => onCancel(workflow.id)}
                className="px-3 py-1.5 rounded-md text-sm font-medium bg-danger/10 text-danger border border-danger/20 hover:bg-danger/20"
              >
                Cancel
              </button>
            )}
            <button
              onClick={() => onRun?.(workflow.id)}
              disabled
              className="px-3 py-1.5 rounded-md text-sm font-medium bg-bg-surface border border-border-subtle text-text-primary hover:bg-bg-hover opacity-50 cursor-not-allowed"
              title="Duplicate (coming soon)"
            >
              Duplicate
            </button>
          </div>

          {/* Steps */}
          <div className="space-y-2">
            <span className="text-label uppercase text-text-muted tracking-wider text-[11px]">
              Steps
            </span>
            <div className="space-y-2">
              {workflow.steps.map((step, idx) => (
                <StepRow key={idx} step={step} index={idx} />
              ))}
            </div>
          </div>

          {/* Error */}
          {workflow.error_message && (
            <div className="rounded border border-danger/20 bg-danger/5 p-3">
              <span className="text-label uppercase text-danger tracking-wider text-[11px]">
                Error
              </span>
              <p className="text-body text-danger mt-1 text-sm">
                {workflow.error_message}
              </p>
            </div>
          )}

          {/* Timestamps */}
          <div className="flex items-center gap-4 text-xs text-text-muted">
            <span>Created: {new Date(workflow.created_at).toLocaleString()}</span>
            {workflow.last_run && (
              <span>Last run: {new Date(workflow.last_run).toLocaleString()}</span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function StepRow({ step, index }: { step: WorkflowStep; index: number }) {
  return (
    <div className="flex items-start gap-3 bg-bg-surface rounded p-3">
      <div className="flex flex-col items-center gap-1 pt-0.5">
        <span className="text-xs text-text-muted font-mono">{index + 1}</span>
        {stepStatusIcon(step.status)}
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="font-mono text-sm text-text-primary">{step.tool}</span>
          {step.status && (
            <span className="text-xs text-text-muted">{step.status}</span>
          )}
        </div>
        {step.params && Object.keys(step.params).length > 0 && (
          <pre className="font-mono text-xs text-text-secondary mt-1 bg-bg-elevated rounded p-2 overflow-x-auto max-h-24 overflow-y-auto">
            {JSON.stringify(step.params, null, 2)}
          </pre>
        )}
        {step.error && (
          <p className="text-xs text-danger mt-1">{step.error}</p>
        )}
        {step.result && (
          <pre className="font-mono text-xs text-success/80 mt-1 bg-success/5 rounded p-2 overflow-x-auto max-h-24 overflow-y-auto">
            {JSON.stringify(step.result, null, 2)}
          </pre>
        )}
        {step.depends_on && step.depends_on.length > 0 && (
          <span className="text-[11px] text-text-muted mt-1 inline-block">
            Depends on: {step.depends_on.join(", ")}
          </span>
        )}
      </div>
    </div>
  );
}
