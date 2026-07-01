import type { TaskPlan } from "../api";

const statusStyles: Record<string, string> = {
  pending: "bg-text-muted/10 text-text-muted",
  running: "bg-accent/10 text-accent",
  completed: "bg-success/5 text-success",
  failed: "bg-danger/5 text-danger",
  cancelled: "bg-warning/5 text-warning",
};

const stepStatusStyles: Record<string, string> = {
  pending: "bg-text-muted/10 text-text-muted",
  running: "bg-accent/10 text-accent",
  completed: "bg-success/5 text-success",
  failed: "bg-danger/5 text-danger",
  skipped: "bg-warning/5 text-warning",
};

export function TaskPlanCard({ plan }: { plan: TaskPlan }) {
  return (
    <div className="bg-bg-elevated rounded-lg border border-border-subtle p-4 hover:shadow-md motion-safe:transition-shadow">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <p className="text-title font-medium text-text-primary truncate">
            {plan.goal}
          </p>
          <div className="mt-1 flex items-center gap-2">
            <span className="font-mono text-xs text-text-muted">
              #{plan.id}
            </span>
            <span
              className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${statusStyles[plan.status] ?? "bg-text-muted/10 text-text-muted"}`}
            >
              {plan.status}
            </span>
            {plan.confidence != null && (
              <span className="font-mono text-xs text-text-muted">
                {Math.round(plan.confidence * 100)}%
              </span>
            )}
          </div>
        </div>
      </div>

      {plan.steps.length > 0 && (
        <div className="mt-3 space-y-1.5">
          <p className="text-label uppercase text-text-muted tracking-wider text-[10px]">
            Steps
          </p>
          <ul className="space-y-1">
            {plan.steps.map((step, i) => (
              <li
                key={i}
                className="flex items-start gap-2 text-sm text-text-secondary"
              >
                <span
                  className={`mt-0.5 inline-flex items-center justify-center w-5 h-5 rounded-full text-[10px] font-medium shrink-0 ${stepStatusStyles[step.status] ?? "bg-text-muted/10 text-text-muted"}`}
                >
                  {step.step}
                </span>
                <span className="min-w-0">
                  <span className="line-clamp-2">{step.description}</span>
                  {step.error && (
                    <span className="block mt-0.5 text-danger text-xs">
                      {step.error}
                    </span>
                  )}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="mt-3 flex items-center gap-4 text-xs text-text-muted font-mono">
        <span>{new Date(plan.created_at).toLocaleDateString()}</span>
        {plan.estimated_duration_ms != null && (
          <span>~{(plan.estimated_duration_ms / 1000).toFixed(1)}s est</span>
        )}
        {plan.actual_duration_ms != null && (
          <span>{(plan.actual_duration_ms / 1000).toFixed(1)}s actual</span>
        )}
      </div>
    </div>
  );
}
