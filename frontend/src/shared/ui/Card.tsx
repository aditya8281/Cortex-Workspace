"use client";

import { type HTMLAttributes, forwardRef } from "react";
import { cn } from "@/shared/lib/utils";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  hover?: boolean;
}

export const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ className, hover = false, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          "rounded-lg border border-border-subtle bg-bg-elevated p-4",
          "shadow-card transition-colors duration-150 ease-out",
          hover &&
            "hover:border-accent/20 hover:shadow-elevated hover:-translate-y-0.5 transition-shadow duration-150",
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
