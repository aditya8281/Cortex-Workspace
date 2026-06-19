import type { HTMLAttributes, ReactNode } from "react";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  className?: string;
  children?: ReactNode;
  hover?: boolean;
  glass?: boolean;
}

export default function Card({
  className = "",
  children,
  hover = false,
  glass = false,
  ...props
}: CardProps) {
  return (
    <div
      className={[
        "rounded-lg border shadow-card transition-all duration-200",
        glass
          ? "glass-panel"
          : "bg-bg-card border-border",
        hover && "hover:border-accent/20 hover:shadow-glow hover:-translate-y-px cursor-pointer",
        hover && "active:translate-y-0 active:scale-[0.995]",
        className,
      ].join(" ")}
      {...props}
    >
      {children}
    </div>
  );
}
