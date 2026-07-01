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
            ? "shadow-card transition-all duration-200 ease-out hover:border-border-input-focus/50 hover:shadow-elevated hover:-translate-y-px"
            : "transition-colors duration-150",
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
