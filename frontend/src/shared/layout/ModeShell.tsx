"use client";

import { type ReactNode } from "react";
import { cn } from "@/shared/lib/utils";

// ── Props ─────────────────────────────────────────────────────────────
interface ModeShellProps {
  /** Emoji icon for the mode */
  icon: string;
  /** Human-readable mode name */
  name: string;
  /** When true, header shows "Back to Hub" with navigation stack
   *  When false, header shows "Dashboard" or top-level label */
  isNested?: boolean;
  /** Callback for the back button */
  onBack?: () => void;
  /** Optional actions rendered in the top-right */
  actions?: ReactNode;
  /** Main content */
  children: ReactNode;
}

// ── Component ─────────────────────────────────────────────────────────
export function ModeShell({
  icon,
  name,
  isNested = false,
  onBack,
  actions,
  children,
}: ModeShellProps) {
  return (
    <div className="flex h-full flex-col bg-bg-base">
      {/* ── Mode top bar ─────────────────────────────────────────── */}
      <header
        className={cn(
          "flex h-11 items-center gap-2.5",
          "border-b border-border-subtle",
          "px-4",
          "flex-shrink-0",
        )}
      >
        {/* Back button */}
        {isNested && onBack && (
          <button
            onClick={onBack}
            className={cn(
              "flex items-center gap-1.5",
              "text-sm font-medium text-text-secondary",
              "hover:text-text-primary",
              "motion-safe:transition-colors motion-safe:duration-150",
            )}
          >
            <svg
              width="16"
              height="16"
              viewBox="0 0 16 16"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M10 2L4 8l6 6" />
            </svg>
            Back
          </button>
        )}

        {/* Separator when back is shown */}
        {isNested && onBack && (
          <span className="text-border-default text-sm">·</span>
        )}

        {/* Icon + name */}
        <span className="text-lg leading-none" aria-hidden="true">
          {icon}
        </span>
        <h1 className="text-sm font-semibold text-text-primary">{name}</h1>

        {/* Spacer */}
        <div className="flex-1" />

        {/* Actions menu */}
        {actions && (
          <div className="flex items-center gap-1">{actions}</div>
        )}
      </header>

      {/* ── Content area ─────────────────────────────────────────── */}
      <main className="flex-1 overflow-y-auto">{children}</main>
    </div>
  );
}
