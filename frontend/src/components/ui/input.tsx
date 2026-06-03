import { cn } from "@/lib/utils";
import type { InputHTMLAttributes } from "react";

export function Input({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={cn(
        "flex h-9 w-full rounded-lg border border-cortex-border bg-cortex-elevated px-3 py-1 text-sm text-cortex-text placeholder:text-cortex-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cortex-accent/40",
        className,
      )}
      {...props}
    />
  );
}
