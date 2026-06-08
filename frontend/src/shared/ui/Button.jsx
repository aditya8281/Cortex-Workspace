"use client";

/**
 * Button — Clean, minimal button component.
 * Supports primary, secondary, ghost variants and loading state.
 */
import { forwardRef } from "react";

const variants = {
  primary:
    "bg-accent text-white hover:bg-accent-hover active:scale-[0.98] shadow-glow",
  secondary:
    "bg-bg-card text-text border border-border hover:bg-bg-hover active:scale-[0.98]",
  ghost:
    "bg-transparent text-text-secondary hover:text-text hover:bg-bg-hover",
};

const sizes = {
  sm: "h-8 px-3 text-xs",
  md: "h-10 px-4 text-sm",
  lg: "h-12 px-6 text-sm",
};

const Button = forwardRef(function Button(
  { variant = "primary", size = "md", loading, disabled, className = "", children, ...props },
  ref
) {
  return (
    <button
      ref={ref}
      disabled={disabled || loading}
      className={[
        "inline-flex items-center justify-center gap-2 rounded-md font-medium transition-all duration-150",
        "disabled:opacity-40 disabled:pointer-events-none",
        variants[variant],
        sizes[size],
        className,
      ].join(" ")}
      {...props}
    >
      {loading && (
        <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
      )}
      {children}
    </button>
  );
});

export default Button;
