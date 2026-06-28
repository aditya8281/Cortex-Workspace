"use client";

import { cn } from "@/shared/lib/utils";

type StatusColor = "accent" | "success" | "warning" | "danger";

interface StatusDotProps {
  color?: StatusColor;
  pulse?: boolean;
  className?: string;
}

const colorStyles: Record<StatusColor, string> = {
  accent: "bg-accent",
  success: "bg-success",
  warning: "bg-warning",
  danger: "bg-danger",
};

export function StatusDot({
  color = "success",
  pulse = false,
  className,
}: StatusDotProps) {
  return (
    <span className={cn("relative flex h-2 w-2", className)}>
      {pulse && (
        <span
          className={cn(
            "absolute inline-flex h-full w-full animate-pulse-dot rounded-full opacity-75",
            colorStyles[color],
          )}
        />
      )}
      <span
        className={cn(
          "relative inline-flex h-2 w-2 rounded-full",
          colorStyles[color],
        )}
      />
    </span>
  );
}
