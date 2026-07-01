"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { cn } from "@/shared/lib/utils";
import { ChatIcon, SearchIcon, BrainIcon, VaultIcon, ModelsIcon, CodeIcon, UtilityIcon, SettingsIcon, SystemsIcon, ProfileIcon } from "@/shared/ui/icons";

// ── Icon component map ──────────────────────────────────────────────
const MODE_ICONS: Record<string, React.ComponentType<{className?: string; size?: number}>> = {
  chat: ChatIcon,
  search: SearchIcon,
  brain: BrainIcon,
  vault: VaultIcon,
  models: ModelsIcon,
  code: CodeIcon,
  utility: UtilityIcon,
  settings: SettingsIcon,
  systems: SystemsIcon,
  profile: ProfileIcon,
};

// ── Dock item definition ──────────────────────────────────────────────
interface DockItem {
  id: string;
  label: string;
  shortcut: string;
}

const DOCK_ITEMS: DockItem[] = [
  { id: "chat", label: "Chat", shortcut: "1" },
  { id: "search", label: "Search", shortcut: "2" },
  { id: "brain", label: "Brain", shortcut: "3" },
  { id: "vault", label: "Vault", shortcut: "4" },
  { id: "models", label: "Models", shortcut: "5" },
  { id: "code", label: "Code", shortcut: "6" },
  { id: "utility", label: "Utility", shortcut: "7" },
  { id: "settings", label: "Settings", shortcut: "8" },
  { id: "systems", label: "Systems", shortcut: "9" },
  { id: "profile", label: "Profile", shortcut: "0" },
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

  // Keyboard: ⌘1-⌘0
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

  return (
    <div
      className={cn(
        "fixed bottom-3 left-1/2 z-dock -translate-x-1/2",
        "motion-safe:transition-all motion-safe:duration-300 motion-safe:ease-out",
        visible
          ? "translate-y-0 opacity-100"
          : "translate-y-4 opacity-0 pointer-events-none",
      )}
      role="navigation"
      aria-label="Mode dock"
    >
      <div
        className={cn(
          "flex items-center gap-0.5",
          "rounded-2xl border border-border-default",
          "bg-bg-glass backdrop-blur-2xl",
          "px-2 py-1.5",
          "shadow-[0_8px_32px_rgba(0,0,0,0.5)]",
        )}
      >
        {DOCK_ITEMS.map((item) => {
          const isActive = activeMode === item.id;
          const isHovered = hoveredItem === item.id;
          const Icon = MODE_ICONS[item.id];

          return (
            <button
              key={item.id}
              onClick={() => onModeChange(item.id)}
              onMouseEnter={() => setHoveredItem(item.id)}
              onMouseLeave={() => setHoveredItem(null)}
              className={cn(
                "relative flex h-10 w-10 items-center justify-center rounded-xl",
                "motion-safe:transition-all motion-safe:duration-150 motion-safe:ease-out",
                "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-border-input-focus",
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
              {Icon && (
                <Icon
                  className={cn(
                    "inline-block",
                    isActive && "scale-110",
                    isHovered && !isActive && "scale-110",
                    "motion-safe:transition-transform motion-safe:duration-150",
                  )}
                  size={18}
                />
              )}

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

        <div className="ml-1.5 border-l border-border-default pl-1.5">
          <button
            onClick={() => onModeChange("profile")}
            className={cn(
              "flex h-9 w-9 items-center justify-center rounded-full",
              "motion-safe:transition-all motion-safe:duration-150",
              activeMode === "profile"
                ? "bg-accent-red text-white shadow-red"
                : "bg-accent-red-muted/30 text-accent-red hover:bg-accent-red-muted/60",
            )}
            aria-label="Profile"
            title="Profile"
          >
            <ProfileIcon size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}
