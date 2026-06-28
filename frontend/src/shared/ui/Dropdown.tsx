"use client";

import { type ReactNode, useState, useRef, useEffect, useCallback } from "react";
import { cn } from "@/shared/lib/utils";

interface DropdownItem {
  label: string;
  onClick: () => void;
  destructive?: boolean;
  disabled?: boolean;
}

interface DropdownProps {
  trigger: ReactNode;
  items: DropdownItem[];
  align?: "left" | "right";
}

export function Dropdown({ trigger, items, align = "left" }: DropdownProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  const close = useCallback(() => setOpen(false), []);

  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) close();
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open, close]);

  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") close();
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [open, close]);

  return (
    <div ref={ref} className="relative inline-flex">
      <div onClick={() => setOpen((o) => !o)} className="cursor-pointer">
        {trigger}
      </div>
      {open && (
        <div
          className={cn(
            "absolute z-50 mt-1.5 min-w-[160px] rounded-lg border border-border-default bg-bg-elevated py-1 shadow-elevated",
            "animate-fade-in-scale origin-top-left",
            align === "right" ? "right-0" : "left-0",
          )}
          role="menu"
        >
          {items.map((item) => (
            <button
              key={item.label}
              onClick={() => {
                if (!item.disabled) {
                  item.onClick();
                  close();
                }
              }}
              disabled={item.disabled}
              className={cn(
                "flex w-full items-center px-3 py-2 text-sm text-left transition-colors duration-150",
                item.disabled
                  ? "cursor-not-allowed text-text-muted"
                  : item.destructive
                    ? "text-danger hover:bg-danger/10"
                    : "text-text-primary hover:bg-bg-hover",
              )}
              role="menuitem"
            >
              {item.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
