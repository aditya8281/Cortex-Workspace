"use client";

import { type ReactNode } from "react";
import { cn } from "@/shared/lib/utils";
import { AppShell } from "@/shared/layout/AppShell";

interface ComingSoonProps {
  title: string;
  description: string;
  version: string;
  icon?: ReactNode;
  className?: string;
}

export function ComingSoon({
  title,
  description,
  version,
  icon,
  className,
}: ComingSoonProps) {
  return (
    <AppShell>
      <div
        className={cn(
          "flex flex-col items-center justify-center px-6 py-24 text-center max-w-lg mx-auto",
          className,
        )}
      >
        {icon && (
          <div className="mb-5 flex h-14 w-14 items-center justify-center rounded-xl bg-bg-surface text-text-muted">
            {icon}
          </div>
        )}
        <h1 className="text-headline font-semibold text-text-primary mb-2">
          {title}
        </h1>
        <p className="text-sm text-text-secondary mb-4 leading-relaxed max-w-sm">
          {description}
        </p>
        <span className="inline-flex items-center rounded-full bg-accent/10 px-3 py-1 text-xs font-mono font-semibold text-accent">
          {version}
        </span>
      </div>
    </AppShell>
  );
}
