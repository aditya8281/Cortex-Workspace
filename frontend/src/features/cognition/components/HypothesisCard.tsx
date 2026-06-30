import type { Hypothesis } from "../api";

const statusStyles: Record<string, string> = {
  active: "bg-accent/10 text-accent",
  confirmed: "bg-success/5 text-success",
  rejected: "bg-danger/5 text-danger",
  superseded: "bg-text-muted/10 text-text-muted",
};

function ConfidenceBar({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  let color = "bg-text-muted";
  if (pct >= 70) color = "bg-success";
  else if (pct >= 40) color = "bg-warning";
  else if (pct >= 20) color = "bg-danger";

  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 rounded-full bg-bg-surface overflow-hidden">
        <div
          className={`h-full rounded-full ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="font-mono text-xs text-text-muted tabular-nums">
        {pct}%
      </span>
    </div>
  );
}

export function HypothesisCard({
  hypothesis,
}: {
  hypothesis: Hypothesis;
}) {
  return (
    <div className="bg-bg-elevated rounded-lg border border-border-subtle p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between gap-3">
        <p className="text-title font-medium text-text-primary min-w-0 flex-1 line-clamp-3">
          {hypothesis.hypothesis}
        </p>
        <span
          className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium shrink-0 ${statusStyles[hypothesis.status] ?? "bg-text-muted/10 text-text-muted"}`}
        >
          {hypothesis.status}
        </span>
      </div>

      <div className="mt-3">
        <ConfidenceBar value={hypothesis.confidence} />
      </div>

      {hypothesis.evidence_for.length > 0 && (
        <div className="mt-3">
          <p className="text-label uppercase text-text-muted tracking-wider text-[10px]">
            Evidence For
          </p>
          <ul className="mt-1 space-y-1">
            {hypothesis.evidence_for.map((e, i) => (
              <li
                key={i}
                className="flex items-start gap-2 text-sm text-success"
              >
                <span className="mt-0.5 shrink-0">+</span>
                <span className="text-text-secondary">{e.text}</span>
                <span className="ml-auto font-mono text-xs text-text-muted shrink-0">
                  w:{e.weight.toFixed(1)}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {hypothesis.evidence_against.length > 0 && (
        <div className="mt-2">
          <p className="text-label uppercase text-text-muted tracking-wider text-[10px]">
            Evidence Against
          </p>
          <ul className="mt-1 space-y-1">
            {hypothesis.evidence_against.map((e, i) => (
              <li
                key={i}
                className="flex items-start gap-2 text-sm text-danger"
              >
                <span className="mt-0.5 shrink-0">-</span>
                <span className="text-text-secondary">{e.text}</span>
                <span className="ml-auto font-mono text-xs text-text-muted shrink-0">
                  w:{e.weight.toFixed(1)}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="mt-3 flex items-center gap-4 text-xs text-text-muted">
        <span className="font-mono">#{hypothesis.id}</span>
        {hypothesis.source && (
          <span className="text-text-secondary">{hypothesis.source}</span>
        )}
        <span className="font-mono">
          {new Date(hypothesis.created_at).toLocaleDateString()}
        </span>
      </div>
    </div>
  );
}
