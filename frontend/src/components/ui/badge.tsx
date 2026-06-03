import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";
import type { HTMLAttributes } from "react";

const badgeVariants = cva(
  "inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium transition-colors",
  {
    variants: {
      variant: {
        default: "border-cortex-border bg-cortex-elevated text-cortex-text",
        accent: "border-cortex-accent/30 bg-cortex-accent-soft text-cortex-accent",
        success: "border-cortex-success/30 bg-cortex-success/10 text-cortex-success",
        warn: "border-cortex-warn/30 bg-cortex-warn/10 text-cortex-warn",
      },
    },
    defaultVariants: { variant: "default" },
  },
);

export function Badge({ className, variant, ...props }: HTMLAttributes<HTMLSpanElement> & VariantProps<typeof badgeVariants>) {
  return <span className={cn(badgeVariants({ variant }), className)} {...props} />;
}
