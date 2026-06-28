"use client";

import { cn } from "@/shared/lib/utils";

interface SkeletonProps {
  className?: string;
}

export function Skeleton({ className }: SkeletonProps) {
  return (
    <div
      className={cn(
        "shimmer-bg rounded-md",
        className,
      )}
      aria-hidden="true"
    />
  );
}
