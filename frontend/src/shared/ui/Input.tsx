"use client";

import { forwardRef, type InputHTMLAttributes } from "react";
import { cn } from "@/shared/lib/utils";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, id, ...props }, ref) => {
    const inputId = id || label?.toLowerCase().replace(/\s+/g, "-");

    return (
      <div className="flex flex-col gap-1.5">
        {label && (
          <label
            htmlFor={inputId}
            className="text-xs font-medium text-text-secondary"
          >
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={inputId}
          className={cn(
            "h-11 rounded-md border border-border-default bg-bg-surface px-3 text-sm text-text-primary",
            "placeholder:text-text-muted",
            "motion-safe:transition-colors motion-safe:duration-150 ease-out",
            "focus:border-border-input-focus focus:shadow-[0_0_0_2px_rgba(211,47,47,0.12)] focus:outline-none",
            "disabled:pointer-events-none disabled:opacity-40",
            error && "border-danger focus:border-danger focus:shadow-[0_0_0_2px_rgba(239,68,68,0.12)]",
            className,
          )}
          {...props}
        />
        {error && <p className="text-xs text-danger">{error}</p>}
      </div>
    );
  },
);

Input.displayName = "Input";
