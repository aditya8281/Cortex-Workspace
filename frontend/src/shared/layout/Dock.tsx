"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useGSAP } from "@gsap/react";
import gsap from "gsap";
import { cn } from "@/shared/lib/utils";
import { ChatIcon, SearchIcon, BrainIcon, VaultIcon, ModelsIcon, CodeIcon, UtilityIcon, SettingsIcon, SystemsIcon, ProfileIcon, HomeIcon } from "@/shared/ui/icons";

gsap.registerPlugin(useGSAP);

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
  const containerRef = useRef<HTMLDivElement>(null);
  const dockInnerRef = useRef<HTMLDivElement>(null);
  const itemsRef = useRef<(HTMLButtonElement | null)[]>([]);
  const lastVisible = useRef(visible);

  // ── Entrance stagger on mount ──────────────────────────────────────
  useGSAP(() => {
    // Stagger items in from below
    gsap.fromTo(
      itemsRef.current.filter(Boolean),
      { y: 16, opacity: 0, scale: 0.9 },
      {
        y: 0, opacity: 1, scale: 1,
        duration: 0.4,
        stagger: { from: "center", each: 0.035 },
        ease: "power3.out",
      },
    );
    // Dock glass container fade-in
    gsap.fromTo(
      dockInnerRef.current,
      { opacity: 0 },
      { opacity: 1, duration: 0.5, delay: 0.2, ease: "power2.out" },
    );
  }, { scope: containerRef });

  // ── Auto-hide animation (GSAP instead of CSS) ──────────────────────
  useEffect(() => {
    if (!containerRef.current) return;
    const el = containerRef.current;

    if (visible) {
      gsap.to(el, {
        y: 0,
        opacity: 1,
        duration: 0.3,
        ease: "power3.out",
        overwrite: "auto",
        onStart: () => el.classList.remove("pointer-events-none"),
      });
    } else {
      gsap.to(el, {
        y: 8,
        opacity: 0,
        duration: 0.25,
        ease: "power2.out",
        overwrite: "auto",
        onComplete: () => el.classList.add("pointer-events-none"),
      });
    }

    lastVisible.current = visible;
  }, [visible]);

  // ── Active-mode pulse ──────────────────────────────────────────────
  useEffect(() => {
    const idx = DOCK_ITEMS.findIndex((i) => i.id === activeMode);
    if (idx < 0) return;
    const btn = itemsRef.current[idx];
    if (!btn) return;
    // Brief scale pulse on active change
    gsap.fromTo(btn, { scale: 1 }, { scale: 1.08, duration: 0.15, yoyo: true, repeat: 1, ease: "power2.out" });
  }, [activeMode]);

  // ── Keyboard: ⌘1-⌘0 + ⌘H for hub ────────────────────────────────────
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (!e.metaKey || e.altKey || e.ctrlKey) return;

      // ⌘H → hub
      if (e.key === "h" || e.key === "H") {
        e.preventDefault();
        onModeChange("hub");
        return;
      }

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
      ref={containerRef}
      className="fixed bottom-3 left-1/2 z-dock -translate-x-1/2"
      style={{ willChange: "transform, opacity" }}
      role="navigation"
      aria-label="Mode dock"
    >
      <div
        ref={dockInnerRef}
        className={cn(
          "flex items-center gap-0.5",
          "rounded-2xl border border-border-default",
          "bg-bg-glass backdrop-blur-2xl",
          "px-2 py-1.5",
          "shadow-[0_8px_32px_rgba(0,0,0,0.5)]",
        )}
      >
        {/* Hub/home button — standalone, no keyboard shortcut */}
        <button
          onClick={() => onModeChange("hub")}
          className={cn(
            "flex h-9 w-9 items-center justify-center rounded-full",
            "motion-safe:transition-all motion-safe:duration-150",
            activeMode === "hub"
              ? "bg-accent-cyan/20 text-accent-cyan"
              : "text-text-muted hover:text-text-primary hover:bg-bg-surface/50",
          )}
          aria-label="Home — Hub"
          title="Hub (⌘H)"
          style={{ opacity: 0 }}
        >
          <HomeIcon size={17} />
        </button>

        <div className="mx-1.5 h-5 w-px bg-border-default/50" />

        {DOCK_ITEMS.map((item, i) => {
          const isActive = activeMode === item.id;
          const isHovered = hoveredItem === item.id;
          const Icon = MODE_ICONS[item.id];

          return (
            <button
              key={item.id}
              ref={(el) => { itemsRef.current[i] = el; }}
              onClick={() => onModeChange(item.id)}
              onMouseEnter={() => setHoveredItem(item.id)}
              onMouseLeave={() => setHoveredItem(null)}
              className={cn(
                "relative flex h-10 w-10 items-center justify-center rounded-xl",
                "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-border-input-focus",
                isActive
                  ? [
                      "bg-accent-red-muted text-accent-red",
                      "shadow-red motion-safe:animate-glow-pulse-red",
                      "after:absolute after:bottom-0.5 after:left-1/2 after:-translate-x-1/2",
                      "after:h-0.5 after:w-4 after:rounded-full after:bg-accent-red",
                    ]
                  : [
                      "text-text-secondary",
                      "hover:bg-accent-red-muted/50 hover:text-text-primary",
                    ],
              )}
              title={`${item.label} (⌘${item.shortcut})`}
              aria-current={isActive ? "page" : undefined}
              aria-label={`${item.label} mode — ⌘${item.shortcut}`}
              style={{ opacity: 0 }}
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
