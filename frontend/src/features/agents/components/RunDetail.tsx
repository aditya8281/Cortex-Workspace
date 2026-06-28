"use client";

import { Card } from "@/shared/ui/Card";
import { Badge } from "@/shared/ui/Badge";
import type { AgentRun, AgentStep } from "../api";

const statusVariant: Record<string, "default" | "success" | "warning" | "danger"> = {
  pending: "warning",
  running: "default",
  completed: "success",
  failed: "danger",
};

export function RunDetail({
  run,
  steps,
}: {
  run: AgentRun;
  steps: AgentStep[];
}) {
  return (
    <div className="space-y-4">
      <Card className="p-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-title font-semibold text-text-primary">
            Run #{run.id}
          </h3>
          <Badge variant={statusVariant[run.status] ?? "default"}>
            {run.status}
          </Badge>
        </div>
        <div className="space-y-2 text-sm">
          <div>
            <span className="text-text-muted">Input: </span>
            <span className="text-text-primary">{run.input}</span>
          </div>
          {run.output && (
            <div>
              <span className="text-text-muted">Output: </span>
              <span className="text-text-primary">{run.output}</span>
            </div>
          )}
          {run.error && (
            <div>
              <span className="text-danger">Error: </span>
              <span className="text-danger">{run.error}</span>
            </div>
          )}
          <div className="text-xs text-text-muted font-mono">
            {run.token_usage.toLocaleString()} tokens
          </div>
        </div>
      </Card>

      {steps.length > 0 && (
        <Card className="p-4">
          <h4 className="text-sm font-medium text-text-primary mb-3">Steps</h4>
          <div className="space-y-3">
            {steps.map((step) => (
              <div
                key={step.id}
                className="rounded-lg border border-border-subtle p-3"
              >
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs font-mono text-text-muted">
                    #{step.step_number}
                  </span>
                  {step.tool_name && (
                    <Badge variant="default">{step.tool_name}</Badge>
                  )}
                  <Badge
                    variant={
                      step.status === "completed"
                        ? "success"
                        : step.status === "failed"
                          ? "danger"
                          : "default"
                    }
                  >
                    {step.status}
                  </Badge>
                </div>
                {step.reasoning && (
                  <p className="text-xs text-text-secondary mt-1">
                    {step.reasoning}
                  </p>
                )}
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}
