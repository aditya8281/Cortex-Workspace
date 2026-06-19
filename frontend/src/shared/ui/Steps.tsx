"use client";

interface StepsProps {
  steps: string[];
  current: number;
}

export default function Steps({ steps, current }: StepsProps) {
  const progress = steps.length > 1 ? (current / (steps.length - 1)) * 100 : 0;

  return (
    <div className="w-full">
      <div className="flex items-center w-full">
        {steps.map((step, i) => {
          const isActive = i === current;
          const isDone = i < current;
          return (
            <div key={i} className="flex items-center flex-1 min-w-0 last:flex-none">
              <div className="flex items-center gap-1.5 min-w-0">
                <div
                  className={[
                    "h-6 w-6 rounded-full flex items-center justify-center text-[11px] font-mono font-medium transition-all duration-300 shrink-0",
                    isDone
                      ? "bg-accent text-white shadow-[0_0_8px_rgba(6,182,212,0.3)]"
                      : isActive
                      ? "bg-accent/20 text-accent border border-accent/40 shadow-[0_0_12px_rgba(6,182,212,0.15)]"
                      : "bg-bg-surface text-text-muted border border-border",
                  ].join(" ")}
                >
                  {isDone ? (
                    <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                    </svg>
                  ) : (
                    i + 1
                  )}
                </div>
                <span
                  className={[
                    "text-[11px] font-medium transition-colors truncate hidden sm:inline-block",
                    isActive ? "text-text" : isDone ? "text-accent" : "text-text-muted",
                  ].join(" ")}
                >
                  {step}
                </span>
              </div>
              {i < steps.length - 1 && (
                <div
                  className={[
                    "h-px flex-1 mx-1.5 transition-colors duration-300 shrink-0 min-w-[12px]",
                    isDone ? "bg-accent/40" : "bg-border",
                  ].join(" ")}
                />
              )}
            </div>
          );
        })}
      </div>
      <div className="mt-2 h-[3px] w-full rounded-full bg-bg-surface overflow-hidden">
        <div
          className="h-full rounded-full bg-gradient-to-r from-accent/60 to-accent transition-all duration-500 ease-out"
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
}
