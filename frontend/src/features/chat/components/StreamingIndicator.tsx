"use client";

import { cn } from "@/shared/lib/utils";

/**
 * Neural Shimmer — Cortex-branded streaming indicator.
 *
 * Animated SVG waveform (EEG trace) with a gradient sweep overlay.
 * The wave morphs between organic neural patterns while a subtle
 * cyan shimmer sweeps across the bubble — the brain is thinking.
 */
export function StreamingIndicator({ centered }: { centered?: boolean }) {
  return (
    <div
      className={cn(
        centered
          ? "flex w-full justify-center"
          : "flex w-full justify-start motion-safe:animate-fade-in",
        "motion-safe:animate-neural-fade-in",
      )}
      role="status"
      aria-label="Generating response"
    >
      <div className="relative overflow-hidden rounded-xl max-w-[200px] w-full">
        {/* Bubble shell */}
        <div
          className={cn(
            "rounded-xl border border-accent-cyan/15 bg-accent-cyan-muted/8 backdrop-blur-xl",
            "px-4 py-3",
          )}
        >
          {/* Waveform SVG — EEG-style trace */}
          <svg
            viewBox="0 0 120 24"
            className="h-5 w-full"
            preserveAspectRatio="none"
            aria-hidden="true"
          >
            <defs>
              <linearGradient id="neural-shimmer-grad" x1="0" y1="0" x2="1" y2="0">
                <stop offset="0%" stopColor="var(--accent-cyan)" stopOpacity="0" />
                <stop offset="40%" stopColor="var(--accent-cyan)" stopOpacity="0.6" />
                <stop offset="60%" stopColor="var(--accent-cyan)" stopOpacity="1" />
                <stop offset="100%" stopColor="var(--accent-cyan)" stopOpacity="0" />
              </linearGradient>
            </defs>
            {/* Baseline */}
            <line x1="0" y1="12" x2="120" y2="12" stroke="var(--accent-cyan)" strokeOpacity="0.08" strokeWidth="0.5" />
            {/* Waveform — morphs between 3 organic shapes */}
            <path
              d="M0,12 C8,12 10,4 16,4 C22,4 24,12 28,12 C32,12 34,20 40,20 C46,20 48,12 52,12 C56,12 58,6 64,6 C70,6 72,12 76,12 C80,12 82,18 88,18 C94,18 96,12 100,12 C104,12 108,8 112,8 C116,8 118,12 120,12"
              fill="none"
              stroke="url(#neural-shimmer-grad)"
              strokeWidth="1.5"
              strokeLinecap="round"
            >
              <animate
                attributeName="d"
                dur="2s"
                repeatCount="indefinite"
                values="
                  M0,12 C8,12 10,4 16,4 C22,4 24,12 28,12 C32,12 34,20 40,20 C46,20 48,12 52,12 C56,12 58,6 64,6 C70,6 72,12 76,12 C80,12 82,18 88,18 C94,18 96,12 100,12 C104,12 108,8 112,8 C116,8 118,12 120,12;
                  M0,12 C8,12 10,8 16,8 C22,8 24,16 28,16 C32,16 34,6 40,6 C46,6 48,12 52,12 C56,12 58,18 64,18 C70,18 72,8 76,8 C80,8 82,14 88,14 C94,14 96,6 100,6 C104,6 108,12 112,12 C116,12 118,8 120,8;
                  M0,12 C8,12 10,6 16,6 C22,6 24,14 28,14 C32,14 34,8 40,8 C46,8 48,16 52,16 C56,16 58,10 64,10 C70,10 72,14 76,14 C80,14 82,6 88,6 C94,6 96,14 100,14 C104,14 108,8 112,8 C116,8 118,12 120,12;
                  M0,12 C8,12 10,4 16,4 C22,4 24,12 28,12 C32,12 34,20 40,20 C46,20 48,12 52,12 C56,12 58,6 64,6 C70,6 72,12 76,12 C80,12 82,18 88,18 C94,18 96,12 100,12 C104,12 108,8 112,8 C116,8 118,12 120,12"
              />
            </path>
          </svg>
        </div>
        {/* Shimmer sweep overlay */}
        <div className="shimmer-sweep absolute inset-0 pointer-events-none" aria-hidden="true" />
      </div>
    </div>
  );
}
