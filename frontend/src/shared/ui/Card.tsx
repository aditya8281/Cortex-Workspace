"use client";

import { type HTMLAttributes, type ReactNode } from "react";
import { cn } from "../../lib/utils";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  hover?: boolean;
  glass?: boolean;
  children: ReactNode;
}

export default function Card({ hover, glass, className, children, ...props }: CardProps) {
  return (
    <div
      className={cn(
        "rounded-xl border border-border-subtle bg-bg-elevated shadow-card transition-all duration-300",
        glass && "glass-panel",
        hover && "hover:border-border-accent hover:shadow-glow hover:-translate-y-0.5 cursor-pointer active:translate-y-0 active:scale-[0.995]",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}
