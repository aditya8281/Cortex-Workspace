"use client";

import { type ReactNode, useState, useRef, useCallback } from "react";
import { cn } from "@/shared/lib/utils";

interface TooltipProps {
  content: string;
  children: ReactNode;
  side?: "top" | "bottom";
}

export function Tooltip({ content, children, side = "top" }: TooltipProps) {
  const [visible, setVisible] = useState(false);
  const timeoutRef = useRef<ReturnType<typeof setTimeout>>(null);

  const show = useCallback(() => {
    clearTimeout(timeoutRef.current!);
    timeoutRef.current = setTimeout(() => setVisible(true), 400);
  }, []);

  const hide = useCallback(() => {
    clearTimeout(timeoutRef.current!);
    setVisible(false);
  }, []);

  return (
    <div className="relative inline-flex" onMouseEnter={show} onMouseLeave={hide}>
      {children}
      {visible && (
        <div
          className={cn(
            "absolute z-50 whitespace-nowrap rounded-md bg-bg-elevated px-2.5 py-1 text-xs text-text-primary shadow-elevated",
            "pointer-events-none animate-fade-in",
            side === "top" ? "bottom-full mb-2" : "top-full mt-2",
          )}
          role="tooltip"
        >
          {content}
        </div>
      )}
    </div>
  );
}
