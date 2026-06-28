"use client";

import { Card } from "@/shared/ui/Card";
import { Badge } from "@/shared/ui/Badge";
import type { AgentRun } from "../api";

const statusVariant: Record<string, "default" | "success" | "warning" | "danger"> = {
  pending: "warning",
  running: "default",
  completed: "success",
  failed: "danger",
};

export function RunHistory({
  runs,
  onSelect,
}: {
  runs: AgentRun[];
  onSelect: (run: AgentRun) => void;
}) {
  if (!runs.length) {
    return (
      <Card className="p-6 text-center">
        <p className="text-sm text-text-muted">No runs yet</p>
      </Card>
    );
  }

  return (
    <Card className="divide-y divide-border-subtle">
      {runs.map((run) => (
        <button
          key={run.id}
          onClick={() => onSelect(run)}
          className="flex w-full items-start gap-3 px-4 py-3 text-left hover:bg-bg-hover transition-colors duration-150"
        >
          <Badge variant={statusVariant[run.status] ?? "default"}>
            {run.status}
          </Badge>
          <div className="flex-1 min-w-0">
            <p className="text-sm text-text-primary truncate">{run.input}</p>
            {run.agent_name && (
              <p className="text-xs text-text-muted mt-0.5">{run.agent_name}</p>
            )}
          </div>
          <div className="text-right flex-shrink-0">
            <span className="text-xs text-text-muted font-mono">
              {run.token_usage.toLocaleString()} tok
            </span>
          </div>
        </button>
      ))}
    </Card>
  );
}
