"use client";

import { type HTMLAttributes, forwardRef } from "react";
import { cn } from "@/shared/lib/utils";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  hover?: boolean;
  glass?: boolean;
}

export const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ className, hover = false, glass = false, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          "rounded-lg border border-border-subtle",
          glass
            ? "bg-bg-widget backdrop-blur-2xl"
            : "bg-bg-elevated",
          hover
            ? "shadow-card motion-safe:transition-all motion-safe:duration-200 ease-out hover:border-border-input-focus/50 hover:shadow-elevated hover:-translate-y-px"
            : "motion-safe:transition-colors motion-safe:duration-150",
          className,
        )}
        {...props}
      >
        {children}
      </div>
    );
  },
);

Card.displayName = "Card";
