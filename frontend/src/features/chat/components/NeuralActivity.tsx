"use client";

import { cn } from "@/shared/lib/utils";

/**
 * NeuralActivity — animated neural network indicator.
 *
 * Replaces the subtle EEG waveform with a prominent neural-nexus motif:
 * pulsing nodes, firing connection lines, and a glowing gradient aura.
 * Three states: thinking (cyan), writing (emerald), using-tools (amber).
 * Pure SVG + CSS — no JS animation loop, no external deps.
 */
export function NeuralActivity({
  mode = "thinking",
}: {
  mode?: "thinking" | "writing" | "using-tools";
}) {
  const accentClass =
    mode === "thinking"
      ? "neural-accent-cyan"
      : mode === "writing"
        ? "neural-accent-emerald"
        : "neural-accent-amber";

  const label =
    mode === "thinking" ? "Thinking"
      : mode === "writing" ? "Writing"
        : "Using tools";

  return (
    <div
      role="status"
      aria-label={`Cortex is ${label.toLowerCase()}`}
      className={cn(
        "neural-container motion-safe:animate-neural-fade-in",
      )}
    >
      {/* Background glow aura — bleeds beyond container */}
      <div
        className={cn(
          "pointer-events-none absolute -inset-4 rounded-[2rem] opacity-20 blur-3xl",
          "motion-safe:animate-neural-pulse-aura",
          mode === "thinking" && "bg-accent-cyan",
          mode === "writing" && "bg-accent-emerald",
          mode === "using-tools" && "bg-accent-amber",
        )}
        aria-hidden="true"
      />

      {/* Shell */}
      <div
        className={cn(
          "relative rounded-2xl border px-5 py-4",
          "backdrop-blur-xl",
          mode === "thinking" && "border-accent-cyan/15 bg-accent-cyan-muted/8",
          mode === "writing" && "border-emerald-500/15 bg-emerald-500/8",
          mode === "using-tools" && "border-amber-500/15 bg-amber-500/8",
        )}
      >
        <div className="flex items-center gap-3">
          {/* ── Neural network SVG ────────────────────────────────── */}
          <svg
            viewBox="0 0 48 32"
            className={cn(
              "h-8 w-12 flex-shrink-0",
              accentClass,
            )}
            preserveAspectRatio="xMidYMid meet"
            aria-hidden="true"
          >
            <defs>
              <radialGradient id="neuron-glow-cyan" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stopColor="var(--accent-cyan)" stopOpacity="0.6" />
                <stop offset="100%" stopColor="var(--accent-cyan)" stopOpacity="0" />
              </radialGradient>
              <radialGradient id="neuron-glow-emerald" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stopColor="#34d399" stopOpacity="0.6" />
                <stop offset="100%" stopColor="#34d399" stopOpacity="0" />
              </radialGradient>
              <radialGradient id="neuron-glow-amber" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stopColor="#f59e0b" stopOpacity="0.6" />
                <stop offset="100%" stopColor="#f59e0b" stopOpacity="0" />
              </radialGradient>
              <filter id="neuron-glow-filter">
                <feGaussianBlur stdDeviation="1.5" result="blur" />
                <feMerge>
                  <feMergeNode in="blur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
            </defs>

            {/* Connection lines — animate stroke-dashoffset to simulate firing */}
            {/* Top tier */}
            <line x1="10" y1="6" x2="22" y2="12" stroke="currentColor" strokeWidth="0.8" strokeOpacity="0.25">
              <animate attributeName="strokeOpacity" values="0.25;0.6;0.25" dur="1.8s" repeatCount="indefinite" />
            </line>
            <line x1="22" y1="12" x2="38" y2="8" stroke="currentColor" strokeWidth="0.8" strokeOpacity="0.25">
              <animate attributeName="strokeOpacity" values="0.25;0.5;0.25" dur="2.1s" repeatCount="indefinite" />
            </line>
            <line x1="10" y1="6" x2="28" y2="6" stroke="currentColor" strokeWidth="0.5" strokeOpacity="0.15">
              <animate attributeName="strokeOpacity" values="0.15;0.4;0.15" dur="2.7s" repeatCount="indefinite" />
            </line>

            {/* Mid tier — dense connections */}
            <line x1="6" y1="14" x2="18" y2="18" stroke="currentColor" strokeWidth="0.8" strokeOpacity="0.25">
              <animate attributeName="strokeOpacity" values="0.25;0.7;0.25" dur="1.5s" repeatCount="indefinite" />
            </line>
            <line x1="18" y1="18" x2="34" y2="18" stroke="currentColor" strokeWidth="0.8" strokeOpacity="0.25">
              <animate attributeName="strokeOpacity" values="0.25;0.5;0.25" dur="2.3s" repeatCount="indefinite" />
            </line>
            <line x1="34" y1="18" x2="44" y2="14" stroke="currentColor" strokeWidth="0.8" strokeOpacity="0.2">
              <animate attributeName="strokeOpacity" values="0.2;0.55;0.2" dur="1.9s" repeatCount="indefinite" />
            </line>
            <line x1="6" y1="14" x2="28" y2="14" stroke="currentColor" strokeWidth="0.5" strokeOpacity="0.12">
              <animate attributeName="strokeOpacity" values="0.12;0.35;0.12" dur="3.1s" repeatCount="indefinite" />
            </line>
            <line x1="18" y1="18" x2="10" y2="26" stroke="currentColor" strokeWidth="0.6" strokeOpacity="0.2">
              <animate attributeName="strokeOpacity" values="0.2;0.45;0.2" dur="2.5s" repeatCount="indefinite" />
            </line>
            <line x1="34" y1="18" x2="40" y2="26" stroke="currentColor" strokeWidth="0.6" strokeOpacity="0.2">
              <animate attributeName="strokeOpacity" values="0.2;0.5;0.2" dur="2.0s" repeatCount="indefinite" />
            </line>

            {/* Cross tier */}
            <line x1="10" y1="6" x2="18" y2="18" stroke="currentColor" strokeWidth="0.5" strokeOpacity="0.15">
              <animate attributeName="strokeOpacity" values="0.15;0.4;0.15" dur="2.8s" repeatCount="indefinite" />
            </line>
            <line x1="22" y1="12" x2="34" y2="18" stroke="currentColor" strokeWidth="0.5" strokeOpacity="0.15">
              <animate attributeName="strokeOpacity" values="0.15;0.35;0.15" dur="3.2s" repeatCount="indefinite" />
            </line>

            {/* Nodes — with firing pulse animation */}
            {/* Row 1: top neurons (processing input) */}
            <circle cx="10" cy="6" r="2.8" fill="currentColor" fillOpacity="0.15" stroke="currentColor" strokeWidth="1" strokeOpacity="0.4">
              <animate attributeName="r" values="2.8;3.5;2.8" dur="1.8s" repeatCount="indefinite" />
              <animate attributeName="fillOpacity" values="0.15;0.4;0.15" dur="1.8s" repeatCount="indefinite" />
            </circle>
            <circle cx="28" cy="6" r="2" fill="currentColor" fillOpacity="0.1" stroke="currentColor" strokeWidth="0.8" strokeOpacity="0.3">
              <animate attributeName="fillOpacity" values="0.1;0.3;0.1" dur="2.7s" repeatCount="indefinite" />
            </circle>
            <circle cx="38" cy="8" r="2.2" fill="currentColor" fillOpacity="0.12" stroke="currentColor" strokeWidth="0.8" strokeOpacity="0.3">
              <animate attributeName="r" values="2.2;2.8;2.2" dur="2.1s" repeatCount="indefinite" />
              <animate attributeName="fillOpacity" values="0.12;0.35;0.12" dur="2.1s" repeatCount="indefinite" />
            </circle>

            {/* Row 2: mid neurons (processing) */}
            <circle cx="6" cy="14" r="2.5" fill="currentColor" fillOpacity="0.12" stroke="currentColor" strokeWidth="1" strokeOpacity="0.35">
              <animate attributeName="r" values="2.5;3.2;2.5" dur="1.5s" repeatCount="indefinite" />
              <animate attributeName="fillOpacity" values="0.12;0.45;0.12" dur="1.5s" repeatCount="indefinite" />
            </circle>
            <circle cx="28" cy="14" r="3" fill="currentColor" fillOpacity="0.2" filter="url(#neuron-glow-filter)">
              <animate attributeName="r" values="3;4;3" dur="2.3s" repeatCount="indefinite" />
              <animate attributeName="fillOpacity" values="0.2;0.5;0.2" dur="2.3s" repeatCount="indefinite" />
            </circle>
            <circle cx="44" cy="14" r="2.3" fill="currentColor" fillOpacity="0.15" stroke="currentColor" strokeWidth="0.8" strokeOpacity="0.3">
              <animate attributeName="fillOpacity" values="0.15;0.4;0.15" dur="1.9s" repeatCount="indefinite" />
            </circle>

            {/* Row 3: bottom neurons (integration/output) */}
            <circle cx="10" cy="26" r="2" fill="currentColor" fillOpacity="0.1" stroke="currentColor" strokeWidth="0.8" strokeOpacity="0.25">
              <animate attributeName="fillOpacity" values="0.1;0.3;0.1" dur="2.5s" repeatCount="indefinite" />
            </circle>
            <circle cx="24" cy="28" r="2.6" fill="currentColor" fillOpacity="0.18" filter="url(#neuron-glow-filter)">
              <animate attributeName="r" values="2.6;3.3;2.6" dur="2.0s" repeatCount="indefinite" />
              <animate attributeName="fillOpacity" values="0.18;0.45;0.18" dur="2.0s" repeatCount="indefinite" />
            </circle>
            <circle cx="40" cy="26" r="2" fill="currentColor" fillOpacity="0.12" stroke="currentColor" strokeWidth="0.8" strokeOpacity="0.25">
              <animate attributeName="fillOpacity" values="0.12;0.3;0.12" dur="2.8s" repeatCount="indefinite" />
            </circle>
          </svg>

          {/* ── Activity text + dots ───────────────────────────────── */}
          <div className="flex flex-col gap-0.5 min-w-0">
            <span
              className={cn(
                "text-sm font-medium tracking-tight",
                mode === "thinking" && "text-accent-cyan",
                mode === "writing" && "text-emerald-400",
                mode === "using-tools" && "text-amber-400",
              )}
            >
              {label}
            </span>

            {/* Animated dot sequence — shows activity rhythm */}
            <div className="flex items-center gap-1">
              <span className={cn(
                "inline-block h-1.5 w-1.5 rounded-full",
                "motion-safe:animate-neural-dot",
                mode === "thinking" && "bg-accent-cyan",
                mode === "writing" && "bg-emerald-400",
                mode === "using-tools" && "bg-amber-400",
              )} />
              <span className={cn(
                "inline-block h-1.5 w-1.5 rounded-full",
                "motion-safe:animate-neural-dot animation-delay-300",
                mode === "thinking" && "bg-accent-cyan",
                mode === "writing" && "bg-emerald-400",
                mode === "using-tools" && "bg-amber-400",
              )} />
              <span className={cn(
                "inline-block h-1.5 w-1.5 rounded-full",
                "motion-safe:animate-neural-dot animation-delay-600",
                mode === "thinking" && "bg-accent-cyan",
                mode === "writing" && "bg-emerald-400",
                mode === "using-tools" && "bg-amber-400",
              )} />
              <span className="ml-2 text-[10px] text-text-muted font-mono">
                {mode === "thinking" ? "processing" : mode === "writing" ? "generating" : "executing"}
              </span>
            </div>
          </div>

          {/* ── Right-side pulsing ring ────────────────────────────── */}
          <div className="relative ml-auto flex-shrink-0">
            <span
              className={cn(
                "block h-6 w-6 rounded-full border-2 motion-safe:animate-neural-pulse-ring",
                mode === "thinking" && "border-accent-cyan/40",
                mode === "writing" && "border-emerald-500/40",
                mode === "using-tools" && "border-amber-500/40",
              )}
            />
            <span
              className={cn(
                "absolute inset-0 block rounded-full",
                mode === "thinking" && "bg-accent-cyan/10",
                mode === "writing" && "bg-emerald-500/10",
                mode === "using-tools" && "bg-amber-500/10",
              )}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
