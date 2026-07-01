"use client";

export function StreamingIndicator() {
  return (
    <div className="flex w-full justify-start">
      <div className="flex items-center gap-1.5 rounded-xl border border-accent-cyan/20 bg-accent-cyan-muted/10 backdrop-blur-xl px-4 py-3 border-l-2 border-l-accent-cyan">
        <span className="h-1.5 w-1.5 rounded-full bg-accent-cyan animate-pulse-dot" />
        <span className="h-1.5 w-1.5 rounded-full bg-accent-cyan animate-pulse-dot [animation-delay:200ms]" />
        <span className="h-1.5 w-1.5 rounded-full bg-accent-cyan animate-pulse-dot [animation-delay:400ms]" />
      </div>
    </div>
  );
}
