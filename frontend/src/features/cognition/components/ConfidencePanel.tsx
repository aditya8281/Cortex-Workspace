import type { ConfidenceResult } from "../api";

const riskStyles: Record<string, string> = {
  low: "bg-success/5 text-success border-success/20",
  medium: "bg-warning/5 text-warning border-warning/20",
  high: "bg-danger/5 text-danger border-danger/20",
  critical: "bg-danger/10 text-danger border-danger/20",
};

function ScoreRing({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const circumference = 2 * Math.PI * 36;
  const offset = circumference * (1 - score);

  let strokeColor = "stroke-text-muted";
  if (pct >= 70) strokeColor = "stroke-success";
  else if (pct >= 40) strokeColor = "stroke-warning";
  else strokeColor = "stroke-danger";

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg width="88" height="88" viewBox="0 0 80 80">
        <circle
          cx="40"
          cy="40"
          r="36"
          fill="none"
          stroke="currentColor"
          className="text-bg-surface"
          strokeWidth="5"
        />
        <circle
          cx="40"
          cy="40"
          r="36"
          fill="none"
          className={strokeColor}
          strokeWidth="5"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          transform="rotate(-90 40 40)"
        />
      </svg>
      <span className="absolute text-title font-medium text-text-primary">
        {pct}
      </span>
    </div>
  );
}

export function ConfidencePanel({
  result,
}: {
  result: ConfidenceResult;
}) {
  return (
    <div className="bg-bg-elevated rounded-lg border border-border-subtle p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start gap-4">
        <ScoreRing score={result.confidence} />
        <div className="min-w-0 flex-1">
          <p className="text-title font-medium text-text-primary">
            {result.task_type}
          </p>
          <div className="mt-1 flex items-center gap-2">
            <span
              className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${riskStyles[result.risk_level] ?? "bg-text-muted/10 text-text-muted border-border-subtle"}`}
            >
              {result.risk_level} risk
            </span>
          </div>
          <p className="mt-2 text-body text-text-secondary text-sm">
            {result.recommendation}
          </p>
        </div>
      </div>

      {result.factors.length > 0 && (
        <div className="mt-3">
          <p className="text-label uppercase text-text-muted tracking-wider text-[10px]">
            Factors
          </p>
          <ul className="mt-1 space-y-1">
            {result.factors.map((factor, i) => (
              <li
                key={i}
                className="flex items-center gap-2 text-sm text-text-secondary"
              >
                <span className="w-1 h-1 rounded-full bg-accent shrink-0" />
                {factor}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
