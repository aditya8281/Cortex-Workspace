"use client";

/**
 * Steps — Horizontal step progress indicator for wizards.
 * Shows numbered steps with active/completed states.
 */

export default function Steps({ steps, current }) {
  return (
    <div className="flex items-center gap-0">
      {steps.map((step, i) => {
        const isActive = i === current;
        const isDone = i < current;
        return (
          <div key={i} className="flex items-center">
            <div className="flex items-center gap-2">
              <div
                className={[
                  "h-7 w-7 rounded-full flex items-center justify-center text-xs font-mono font-medium transition-all duration-300 shrink-0",
                  isDone
                    ? "bg-accent text-white shadow-[0_0_8px_rgba(6,182,212,0.3)]"
                    : isActive
                    ? "bg-accent/20 text-accent border border-accent/40"
                    : "bg-bg-surface text-text-muted border border-border",
                ].join(" ")}
              >
                {isDone ? (
                  <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                ) : (
                  i + 1
                )}
              </div>
              <span
                className={[
                  "text-xs font-medium transition-colors hidden sm:block",
                  isActive ? "text-text" : isDone ? "text-accent" : "text-text-muted",
                ].join(" ")}
              >
                {step}
              </span>
            </div>
            {i < steps.length - 1 && (
              <div
                className={[
                  "h-px w-8 sm:w-12 mx-2 transition-colors duration-300",
                  isDone ? "bg-accent/40" : "bg-border",
                ].join(" ")}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
