"use client";

import { useEffect, useRef } from "react";

interface IndexProgressProps {
  /** Current progress value (0-100). If undefined, fetches from API. */
  progress: number;
  /** Current status label (e.g. "indexing", "indexed", "error"). */
  status: string;
}

/**
 * Inline progress bar for index operations.
 * Renders a labeled progress bar with status text.
 * Does NOT poll — parent is responsible for providing updated progress.
 */
export function IndexProgress({ progress, status }: IndexProgressProps) {
  const normalized = Math.min(Math.max(Math.round(progress), 0), 100);
  const isComplete = status === "indexed" || status === "error";
  const isActive =
    !isComplete && (status === "indexing" || status === "starting" || status === "");
  const barRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isComplete && barRef.current) {
      // Ensure the bar fills to 100% on completion
      barRef.current.style.width = "100%";
    }
  }, [isComplete]);

  return (
    <div className="space-y-1" role="progressbar" aria-valuenow={normalized} aria-valuemin={0} aria-valuemax={100}>
      <div className="flex items-center justify-between text-xs text-text-secondary">
        <span>
          {isComplete
            ? status === "error"
              ? "Indexing failed"
              : "Indexing complete"
            : isActive
              ? "Indexing..."
              : status}
        </span>
        <span>{normalized}%</span>
      </div>
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-bg-surface">
        <div
          ref={barRef}
          className={`h-full rounded-full bg-accent motion-safe:transition-[width] duration-300 ease-out ${
            isActive ? "animate-pulse-subtle" : ""
          }`}
          style={{ width: `${normalized}%` }}
        />
      </div>
    </div>
  );
}
