"use client";

import { cn } from "@/shared/lib/utils";

type StatusColor = "accent" | "success" | "warning" | "danger";
type StatusSize = "xs" | "sm" | "md" | "lg";

interface StatusDotProps {
  color?: StatusColor;
  size?: StatusSize;
  pulse?: boolean;
  className?: string;
}

const colorStyles: Record<StatusColor, string> = {
  accent: "bg-accent",
  success: "bg-success",
  warning: "bg-warning",
  danger: "bg-danger",
};

const sizeStyles: Record<StatusSize, { dot: string; pulse: string; wrapper: string }> = {
  xs: { dot: "h-1.5 w-1.5", pulse: "h-1.5 w-1.5", wrapper: "h-1.5 w-1.5" },
  sm: { dot: "h-2 w-2", pulse: "h-2 w-2", wrapper: "h-2 w-2" },
  md: { dot: "h-2.5 w-2.5", pulse: "h-2.5 w-2.5", wrapper: "h-2.5 w-2.5" },
  lg: { dot: "h-3.5 w-3.5", pulse: "h-3.5 w-3.5", wrapper: "h-3.5 w-3.5" },
};

export function StatusDot({
  color = "success",
  size = "sm",
  pulse = false,
  className,
}: StatusDotProps) {
  const s = sizeStyles[size];
  return (
    <span className={cn("relative flex", s.wrapper, className)}>
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
          "relative inline-flex rounded-full",
          s.dot,
          colorStyles[color],
        )}
      />
    </span>
  );
}
