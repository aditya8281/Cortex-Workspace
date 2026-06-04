import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";
import type { HTMLAttributes } from "react";

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-[11px] font-medium tracking-wide transition-all duration-200 ease-out",
  {
    variants: {
      variant: {
        default: "border-cortex-border/80 bg-cortex-elevated/80 text-cortex-text",
        accent: "border-cortex-accent/30 bg-cortex-accent-soft text-cortex-accent shadow-sm",
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
