import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";
import type { ButtonHTMLAttributes } from "react";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 rounded-xl text-sm font-medium transition-all duration-200 ease-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cortex-accent/40 focus-visible:ring-offset-0 disabled:pointer-events-none disabled:opacity-50 active:scale-[0.98] transform-gpu hover:-translate-y-0.5 hover:shadow-lg",
  {
    variants: {
      variant: {
        default:
          "bg-gradient-to-r from-cortex-accent via-sky-400 to-cyan-400 text-cortex-bg shadow-cortex-accent/20 hover:brightness-110",
        secondary:
          "border border-cortex-border bg-cortex-elevated/70 text-cortex-text hover:border-cortex-accent/30 hover:bg-white/10",
        ghost:
          "text-cortex-muted hover:bg-white/6 hover:text-cortex-text",
        destructive:
          "border border-red-500/25 bg-red-500/10 text-red-200 hover:border-red-400/40 hover:bg-red-500/20 hover:text-red-100",
      },
      size: {
        default: "h-9 px-4 py-2",
        sm: "h-8 rounded-lg px-3 text-xs",
        lg: "h-11 rounded-xl px-6",
        icon: "h-9 w-9",
      },
    },
    defaultVariants: { variant: "default", size: "default" },
  },
);

export type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & VariantProps<typeof buttonVariants>;

export function Button({ className, variant, size, ...props }: ButtonProps) {
  return <button className={cn(buttonVariants({ variant, size }), className)} {...props} />;
}
