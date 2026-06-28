"use client";

export function StreamingIndicator() {
  return (
    <div className="flex w-full justify-start">
      <div className="flex items-center gap-1.5 rounded-xl bg-bg-elevated px-4 py-3 rounded-bl-md">
        <span className="h-1.5 w-1.5 rounded-full bg-text-muted animate-pulse-dot" />
        <span className="h-1.5 w-1.5 rounded-full bg-text-muted animate-pulse-dot [animation-delay:200ms]" />
        <span className="h-1.5 w-1.5 rounded-full bg-text-muted animate-pulse-dot [animation-delay:400ms]" />
      </div>
    </div>
  );
}
