import { cn } from "@/lib/utils";
import type { InputHTMLAttributes } from "react";

export function Input({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={cn(
        "flex h-10 w-full rounded-xl border border-cortex-border/80 bg-cortex-elevated/80 px-3 py-1 text-sm text-cortex-text placeholder:text-cortex-muted/70 shadow-sm backdrop-blur-sm focus-visible:border-cortex-accent/40 focus-visible:ring-2 focus-visible:ring-cortex-accent/25 focus-visible:shadow-lg hover:border-cortex-border/90",
        className,
      )}
      {...props}
    />
  );
}
