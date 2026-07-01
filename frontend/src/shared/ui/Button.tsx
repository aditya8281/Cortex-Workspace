"use client";

import { forwardRef, type ButtonHTMLAttributes } from "react";
import { cn } from "@/shared/lib/utils";

type ButtonVariant = "primary" | "ghost" | "danger" | "neural";
type ButtonSize = "sm" | "md" | "lg";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
}

const variantStyles: Record<ButtonVariant, string> = {
  primary:
    "bg-accent-red text-white shadow-sm hover:bg-accent-red/90 active:scale-[0.97] shadow-[0_1px_6px_-1px] shadow-accent-red/20",
  ghost:
    "bg-transparent text-text-secondary hover:bg-bg-surface hover:text-text-primary active:scale-[0.97]",
  danger:
    "bg-danger/10 text-danger hover:bg-danger/20 active:scale-[0.97]",
  neural:
    "bg-bg-surface text-accent hover:bg-accent/10 active:scale-[0.97] border border-accent/20",
};

const sizeStyles: Record<ButtonSize, string> = {
  sm: "h-8 px-3 text-xs",
  md: "h-11 px-4 text-sm min-h-[44px]",
  lg: "h-12 px-6 text-sm min-h-[44px]",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant = "primary",
      size = "md",
      loading,
      disabled,
      children,
      ...props
    },
    ref,
  ) => {
    return (
      <button
        ref={ref}
        className={cn(
          "inline-flex items-center justify-center gap-2 rounded-md font-medium",
          "transition-all duration-150 ease-out active:duration-75",
          "focus-visible:ring-2 focus-visible:ring-accent/50 focus-visible:outline-none",
          "disabled:pointer-events-none disabled:opacity-40",
          variantStyles[variant],
          sizeStyles[size],
          className,
        )}
        disabled={disabled || loading}
        {...props}
      >
        {loading && (
          <svg
            className="h-4 w-4 animate-spin"
            viewBox="0 0 24 24"
            fill="none"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="3"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
            />
          </svg>
        )}
        {children}
      </button>
    );
  },
);

Button.displayName = "Button";
