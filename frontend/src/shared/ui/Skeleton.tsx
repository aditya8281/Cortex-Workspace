import { cn } from "../../lib/utils";

interface SkeletonProps {
  className?: string;
}

export default function Skeleton({ className }: SkeletonProps) {
  return (
    <div
      className={cn(
        "rounded-xl bg-bg-surface shimmer-bg",
        className
      )}
    />
  );
}
