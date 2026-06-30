import type { ErrorAnalysis } from "../api";

const severityStyles: Record<string, string> = {
  critical: "bg-danger/10 text-danger border-danger/20",
  high: "bg-danger/5 text-danger border-danger/20",
  medium: "bg-warning/5 text-warning border-warning/20",
  low: "bg-text-muted/10 text-text-muted border-border-subtle",
};

export function ErrorAnalysisCard({
  analysis,
}: {
  analysis: ErrorAnalysis;
}) {
  return (
    <div
      className={`rounded-lg border p-4 ${severityStyles[analysis.severity] ?? "bg-bg-elevated border-border-subtle"} hover:shadow-md transition-shadow`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <p className="text-title font-medium text-text-primary">
            {analysis.error_type}
          </p>
          {analysis.error_message && (
            <p className="mt-1 text-body text-text-secondary line-clamp-2 font-mono text-sm">
              {analysis.error_message}
            </p>
          )}
        </div>
        <span
          className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium shrink-0 ${severityStyles[analysis.severity] ?? "bg-text-muted/10 text-text-muted"}`}
        >
          {analysis.severity}
        </span>
      </div>

      {analysis.root_cause && (
        <div className="mt-3">
          <p className="text-label uppercase text-text-muted tracking-wider text-[10px]">
            Root Cause
          </p>
          <p className="mt-0.5 text-body text-text-secondary text-sm">
            {analysis.root_cause}
          </p>
        </div>
      )}

      {analysis.resolution && (
        <div className="mt-2">
          <p className="text-label uppercase text-text-muted tracking-wider text-[10px]">
            Resolution
          </p>
          <p className="mt-0.5 text-body text-text-secondary text-sm">
            {analysis.resolution}
          </p>
        </div>
      )}

      {analysis.prevention && (
        <div className="mt-2">
          <p className="text-label uppercase text-text-muted tracking-wider text-[10px]">
            Prevention
          </p>
          <p className="mt-0.5 text-body text-text-secondary text-sm">
            {analysis.prevention}
          </p>
        </div>
      )}

      <div className="mt-3 flex items-center gap-4 text-xs text-text-muted">
        <span className="font-mono">#{analysis.id}</span>
        <span className="font-mono">
          {new Date(analysis.created_at).toLocaleDateString()}
        </span>
        {analysis.resolved ? (
          <span className="text-success">Resolved</span>
        ) : (
          <span className="text-warning">Open</span>
        )}
      </div>
    </div>
  );
}
