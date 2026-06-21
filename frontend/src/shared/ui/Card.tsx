import { type HTMLAttributes, type ReactNode, forwardRef } from "react";
import { cn } from "@/lib/utils";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  hover?: boolean;
  glass?: boolean;
  gradient?: boolean;
  glow?: boolean;
}

const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ children, className, hover, glass, gradient, glow, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          "rounded-xl border border-border-subtle bg-bg-elevated",
          "shadow-card transition-all duration-200 ease-out",
          hover && [
            "cursor-pointer",
            "hover:border-accent/20 hover:shadow-glow",
            "hover:-translate-y-0.5",
            "active:scale-[0.98]",
          ],
          glass && "glass-panel",
          gradient && [
            "bg-gradient-to-br from-bg-elevated via-bg-surface to-bg-elevated",
            "before:absolute before:inset-0 before:rounded-xl before:opacity-0",
            "before:bg-gradient-to-br before:from-accent/5 before:to-transparent",
            "before:transition-opacity before:duration-300",
            "hover:before:opacity-100",
          ],
          glow && "shadow-glow hover:shadow-glow-strong",
          "relative overflow-hidden",
          className
        )}
        {...props}
      >
        {children}
      </div>
    );
  }
);

Card.displayName = "Card";

export { Card };
export default Card;
