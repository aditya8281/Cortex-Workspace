"use client";

import { type ReactNode } from "react";
import { cn } from "@/shared/lib/utils";

// ── Props ─────────────────────────────────────────────────────────────
interface HubWidgetProps {
  icon: string;
  label: string;
  children: ReactNode;
  onClick: () => void;
  isActive?: boolean;
  glowColor?: "red" | "cyan";
  className?: string;
}

// ── Component ─────────────────────────────────────────────────────────
export function HubWidget({
  icon,
  label,
  children,
  onClick,
  isActive = false,
  glowColor = "cyan",
  className,
}: HubWidgetProps) {
  return (
    <button
      onClick={onClick}
      className={cn(
        // Base glass card
        "group relative flex flex-col rounded-2xl border p-4 text-left",
        "bg-bg-widget backdrop-blur-2xl",
        "motion-safe:transition-all motion-safe:duration-200 motion-safe:ease-out",
        // Default border
        "border-border-subtle",
        // Hover
        "hover:border-border-default hover:-translate-y-0.5",
        glowColor === "red"
          ? "hover:shadow-red"
          : "hover:shadow-cyan",
        // Active state glow
        isActive && (glowColor === "red" ? "shadow-red" : "shadow-cyan"),
        // Focus
        "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-border-input-focus",
        className,
      )}
    >
      {/* Active glow indicator — thin line at top edge */}
      {isActive && (
        <span
          className={cn(
            "absolute -top-px left-4 right-4 h-px rounded-full",
            glowColor === "red" ? "bg-accent-red" : "bg-accent-cyan",
          )}
        />
      )}

      {/* Header */}
      <div className="mb-2.5 flex items-center gap-2">
        <span className="text-xl leading-none" aria-hidden="true">{icon}</span>
        <span className="text-xs font-semibold uppercase tracking-widest text-text-secondary">
          {label}
        </span>
      </div>

      {/* Preview content — children fill the body */}
      <div className="flex-1 space-y-1 text-xs text-text-muted">
        {children}
      </div>

      {/* Subtle "enter" hint at bottom-right on hover */}
      <span
        className={cn(
          "absolute bottom-2 right-3 text-[10px] font-mono text-text-muted",
          "opacity-0 group-hover:opacity-40",
          "motion-safe:transition-opacity motion-safe:duration-200",
        )}
      >
        ⌘{/* shortcut placeholder — filled by parent */}→
      </span>
    </button>
  );
}
