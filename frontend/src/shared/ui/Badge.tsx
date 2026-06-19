import { type ReactNode } from "react";
import { cn } from "../../lib/utils";

interface BadgeProps {
  variant?: "default" | "accent" | "success" | "warning" | "danger";
  children: ReactNode;
  className?: string;
}

export default function Badge({ variant = "default", className, children }: BadgeProps) {
  const variants = {
    default: "bg-bg-surface text-text-secondary border-border-subtle",
    accent: "bg-accent-faint text-accent border-accent/20",
    success: "bg-success-muted text-success border-success/20",
    warning: "bg-warning-muted text-warning border-warning/20",
    danger: "bg-error-muted text-error border-error/20",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-[10px] font-mono font-medium uppercase tracking-wider border",
        variants[variant],
        className
      )}
    >
      {children}
    </span>
  );
}
