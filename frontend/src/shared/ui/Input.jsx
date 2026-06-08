"use client";

/**
 * Input — Clean input with label and optional error state.
 */
import { forwardRef } from "react";

const Input = forwardRef(function Input(
  { label, error, className = "", ...props },
  ref
) {
  return (
    <div className="grid gap-1.5">
      {label && (
        <label className="text-xs font-medium text-text-secondary">
          {label}
        </label>
      )}
      <input
        ref={ref}
        className={[
          "h-10 w-full rounded-md bg-bg-surface border border-border px-3 text-sm text-text",
          "placeholder:text-text-muted outline-none transition-colors duration-150",
          "focus:border-accent/40 focus:ring-1 focus:ring-accent/20",
          error && "border-error/50 focus:border-error/50 focus:ring-error/20",
          className,
        ].join(" ")}
        {...props}
      />
      {error && (
        <p className="text-xs text-error">{error}</p>
      )}
    </div>
  );
});

export default Input;
