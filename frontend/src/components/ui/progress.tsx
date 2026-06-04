import { cn } from "@/lib/utils";

type ProgressProps = {
  value: number;
  className?: string;
  label?: string;
};

export function Progress({ value, className, label }: ProgressProps) {
  const clamped = Math.min(100, Math.max(0, value));
  return (
    <div className={cn("space-y-1.5", className)}>
      {label && (
        <div className="flex justify-between text-xs text-cortex-muted">
          <span>{label}</span>
          <span>{Math.round(clamped)}%</span>
        </div>
      )}
      <div className="h-2 overflow-hidden rounded-full bg-cortex-elevated/80">
        <div
          className="h-full rounded-full bg-gradient-to-r from-cortex-accent via-sky-400 to-cyan-400 transition-all duration-300 animate-shimmer"
          style={{ width: `${clamped}%` }}
        />
      </div>
    </div>
  );
}
