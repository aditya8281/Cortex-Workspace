"use client";

import { type ReactNode } from "react";
import { cn } from "@/shared/lib/utils";

interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: ReactNode;
  className?: string;
}

export function EmptyState({
  icon,
  title,
  description,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center px-6 py-16 text-center animate-fade-in",
        className,
      )}
    >
      {icon && (
        <div className="mb-4 text-text-muted/40 animate-fade-in-scale">{icon}</div>
      )}
      <h3 className="text-headline font-semibold text-text-primary mb-1">
        {title}
      </h3>
      {description && (
        <p className="text-sm text-text-secondary max-w-sm mt-0.5">{description}</p>
      )}
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}
