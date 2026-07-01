"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { cn } from "@/shared/lib/utils";

// ── Dock item definition ──────────────────────────────────────────────
interface DockItem {
  id: string;
  icon: string;
  label: string;
  shortcut: string; // "1" through "0"
}

const DOCK_ITEMS: DockItem[] = [
  { id: "chat", icon: "💬", label: "Chat", shortcut: "1" },
  { id: "search", icon: "🔍", label: "Search", shortcut: "2" },
  { id: "brain", icon: "🧠", label: "Brain", shortcut: "3" },
  { id: "vault", icon: "🔐", label: "Vault", shortcut: "4" },
  { id: "models", icon: "📚", label: "Models", shortcut: "5" },
  { id: "code", icon: "📐", label: "Code", shortcut: "6" },
  { id: "utility", icon: "🛠️", label: "Utility", shortcut: "7" },
  { id: "settings", icon: "⚙️", label: "Settings", shortcut: "8" },
  { id: "systems", icon: "🖥️", label: "Systems", shortcut: "9" },
  { id: "profile", icon: "👤", label: "Profile", shortcut: "0" },
];

// ── Props ─────────────────────────────────────────────────────────────
interface DockProps {
  activeMode: string;
  onModeChange: (modeId: string) => void;
  visible: boolean;
}

// ── Component ─────────────────────────────────────────────────────────
export function Dock({ activeMode, onModeChange, visible }: DockProps) {
  const [hoveredItem, setHoveredItem] = useState<string | null>(null);

  // Keyboard: ⌘1–⌘0 → switch mode
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (!e.metaKey || e.altKey || e.ctrlKey) return;
      const idx = parseInt(e.key, 10);
      if (idx >= 1 && idx <= 9) {
        e.preventDefault();
        onModeChange(DOCK_ITEMS[idx - 1].id);
      } else if (e.key === "0") {
        e.preventDefault();
        onModeChange("profile");
      }
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onModeChange]);

  // ── Render ──────────────────────────────────────────────────────────
  return (
    <div
      className={cn(
        // Positioning — fixed at bottom center
        "fixed bottom-3 left-1/2 z-dock -translate-x-1/2",
        "motion-safe:transition-all motion-safe:duration-300 motion-safe:ease-out",
        visible
          ? "translate-y-0 opacity-100"
          : "translate-y-4 opacity-0 pointer-events-none",
      )}
      role="navigation"
      aria-label="Mode dock"
    >
      {/* Dock tray — glass background */}
      <div
        className={cn(
          "flex items-center gap-0.5",
          "rounded-2xl border border-border-default",
          "bg-bg-glass backdrop-blur-2xl",
          "px-2 py-1.5",
          "shadow-[0_8px_32px_rgba(0,0,0,0.5)]",
          "motion-safe:transition-shadow motion-safe:duration-200",
        )}
      >
        {/* Mode icons */}
        {DOCK_ITEMS.map((item) => {
          const isActive = activeMode === item.id;
          const isHovered = hoveredItem === item.id;

          return (
            <button
              key={item.id}
              onClick={() => onModeChange(item.id)}
              onMouseEnter={() => setHoveredItem(item.id)}
              onMouseLeave={() => setHoveredItem(null)}
              className={cn(
                // Base shape
                "relative flex h-10 w-10 items-center justify-center rounded-xl text-lg",
                "motion-safe:transition-all motion-safe:duration-150 motion-safe:ease-out",
                "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-border-input-focus",
                // Default state
                isActive
                  ? [
                      "bg-accent-red-muted text-accent-red",
                      "shadow-red",
                      "after:absolute after:bottom-0.5 after:left-1/2 after:-translate-x-1/2",
                      "after:h-0.5 after:w-4 after:rounded-full after:bg-accent-red",
                    ]
                  : [
                      "text-text-secondary",
                      "hover:bg-accent-red-muted/50 hover:text-text-primary",
                      "hover:shadow-cyan/30",
                    ],
              )}
              title={`${item.label} (⌘${item.shortcut})`}
              aria-current={isActive ? "page" : undefined}
              aria-label={`${item.label} mode — ⌘${item.shortcut}`}
            >
              <span className={cn(
                "inline-block leading-none",
                isActive && "scale-105",
                isHovered && !isActive && "scale-105",
                "motion-safe:transition-transform motion-safe:duration-150",
              )}>
                {item.icon}
              </span>

              {/* Tooltip — appears above the icon on hover */}
              <span
                className={cn(
                  "absolute -top-8 left-1/2 -translate-x-1/2",
                  "whitespace-nowrap rounded-md px-2 py-1",
                  "bg-bg-elevated border border-border-default",
                  "text-xs font-medium text-text-primary",
                  "motion-safe:transition-all motion-safe:duration-100",
                  isHovered
                    ? "opacity-100 translate-y-0"
                    : "opacity-0 translate-y-1 pointer-events-none",
                )}
                role="tooltip"
              >
                <span className="flex items-center gap-1.5">
                  {item.label}
                  <span className="text-text-muted font-mono text-[10px]">
                    ⌘{item.shortcut}
                  </span>
                </span>
              </span>
            </button>
          );
        })}

        {/* Spacer + user avatar */}
        <div className="ml-1.5 border-l border-border-default pl-1.5">
          <button
            onClick={() => onModeChange("profile")}
            className={cn(
              "flex h-9 w-9 items-center justify-center rounded-full",
              "text-sm font-semibold",
              "motion-safe:transition-all motion-safe:duration-150",
              activeMode === "profile"
                ? "bg-accent-red text-white shadow-red"
                : "bg-accent-red-muted/30 text-accent-red hover:bg-accent-red-muted/60",
            )}
            aria-label="Profile"
            title="Profile"
          >
            👤
          </button>
        </div>
      </div>
    </div>
  );
}
