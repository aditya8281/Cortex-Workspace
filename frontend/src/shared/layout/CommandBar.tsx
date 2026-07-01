"use client";

import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { cn } from "@/shared/lib/utils";

import {
  BrainIcon,
  ChatIcon,
  CloseIcon,
  CodeIcon,
  HomeIcon,
  LightningIcon,
  ModelsIcon,
  ProfileIcon,
  SearchIcon,
  SettingsIcon,
  SystemsIcon,
  UtilityIcon,
  VaultIcon,
} from "@/shared/ui/icons";

// ── Command types ────────────────────────────────────────────────────
interface CommandGroup {
  label: string;
  items: CommandItem[];
}

interface CommandItem {
  id: string;
  icon: ReactNode;
  label: string;
  description?: string;
  shortcut?: string;
  action: () => void;
}

// ── Props ─────────────────────────────────────────────────────────────
interface CommandBarProps {
  onNavigate: (modeId: string) => void;
  goToHub: () => void;
  currentMode: string;
}

// ── Component ─────────────────────────────────────────────────────────
export function CommandBar({ onNavigate, goToHub, currentMode }: CommandBarProps) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [selectedIdx, setSelectedIdx] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);
  const selectedRef = useRef<HTMLButtonElement>(null);

  // ── Build command groups from context ─────────────────────────────
  const groups: CommandGroup[] = useMemo(() => {
    const modeCommands: CommandItem[] = [
      { id: "chat",    icon: <ChatIcon />,    label: "Chat",    description: "Conversation mode", shortcut: "⌘1", action: () => { onNavigate("chat"); setOpen(false); } },
      { id: "search",  icon: <SearchIcon />,  label: "Search",  description: "Search knowledge base", shortcut: "⌘2", action: () => { onNavigate("search"); setOpen(false); } },
      { id: "brain",   icon: <BrainIcon />,   label: "Brain",   description: "Memory & knowledge graph", shortcut: "⌘3", action: () => { onNavigate("brain"); setOpen(false); } },
      { id: "vault",   icon: <VaultIcon />,   label: "Vault",   description: "Encrypted storage", shortcut: "⌘4", action: () => { onNavigate("vault"); setOpen(false); } },
      { id: "models",  icon: <ModelsIcon />,  label: "Models",  description: "LLM management", shortcut: "⌘5", action: () => { onNavigate("models"); setOpen(false); } },
      { id: "code",    icon: <CodeIcon />,    label: "Code",    description: "Code intelligence", shortcut: "⌘6", action: () => { onNavigate("code"); setOpen(false); } },
      { id: "utility", icon: <UtilityIcon />, label: "Utility", description: "Tools & utilities", shortcut: "⌘7", action: () => { onNavigate("utility"); setOpen(false); } },
      { id: "settings",icon: <SettingsIcon />,label: "Settings",description: "App configuration", shortcut: "⌘8", action: () => { onNavigate("settings"); setOpen(false); } },
      { id: "systems", icon: <SystemsIcon />, label: "Systems", description: "System overview", shortcut: "⌘9", action: () => { onNavigate("systems"); setOpen(false); } },
      { id: "profile", icon: <ProfileIcon />, label: "Profile", description: "Your account", shortcut: "⌘0", action: () => { onNavigate("profile"); setOpen(false); } },
    ];

    const navCommands: CommandItem[] = [
      { id: "ask",      icon: <LightningIcon />, label: "Ask Cortex anything…", description: "Open chat with query", action: () => { onNavigate("chat"); setOpen(false); } },
      { id: "go-home",  icon: <HomeIcon />,     label: "Go to Hub",           description: "Return to home", action: () => { goToHub(); setOpen(false); } },
    ];

    const result: CommandGroup[] = [
      { label: "Navigation", items: navCommands },
    ];

    // If not on hub, add current mode context group
    // (future: mode-specific commands loaded from each mode)
    if (currentMode !== "hub") {
      result.push({
        label: "Context",
        items: [
          { id: "close-mode", icon: <CloseIcon />, label: "Close Mode", description: "Go back to previous mode", shortcut: "⎋", action: () => { onNavigate("hub"); setOpen(false); } },
        ],
      });
    }

    result.push({ label: "Modes", items: modeCommands });
    return result;
  }, [onNavigate, goToHub, currentMode]);

  // ── Flatten for search + keyboard nav ─────────────────────────────
  const flatItems = useMemo(() => {
    return groups.flatMap((g) => g.items);
  }, [groups]);

  const filtered = useMemo(() => {
    if (!query.trim()) return flatItems;
    const q = query.toLowerCase();
    // Simple fuzzy: match chars in order across label
    return flatItems.filter((item) => {
      const label = item.label.toLowerCase();
      const desc = (item.description ?? "").toLowerCase();
      // Direct substring match
      if (label.includes(q) || desc.includes(q)) return true;
      // Fuzzy char match
      let qi = 0;
      for (const ch of label) {
        if (ch === q[qi]) qi++;
        if (qi === q.length) return true;
      }
      return false;
    });
  }, [flatItems, query]);

  // Reset selection when results change
  useEffect(() => {
    setSelectedIdx(0);
  }, [query]);

  // Scroll selected into view
  useEffect(() => {
    if (selectedRef.current) {
      selectedRef.current.scrollIntoView({ block: "nearest" });
    }
  }, [selectedIdx]);

  // ── Open / close ────────────────────────────────────────────────
  const openBar = useCallback(() => {
    setOpen(true);
    setQuery("");
    setSelectedIdx(0);
    // Focus on next tick after render
    requestAnimationFrame(() => inputRef.current?.focus());
  }, []);

  const closeBar = useCallback(() => {
    setOpen(false);
    setQuery("");
    setSelectedIdx(0);
  }, []);

  // Global ⌘K listener
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      // ⌘K toggle
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        if (open) closeBar();
        else openBar();
        return;
      }

      if (!open) return;

      // Escape to close
      if (e.key === "Escape") {
        e.preventDefault();
        closeBar();
        return;
      }

      // Arrow navigation
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setSelectedIdx((prev) => (prev + 1) % filtered.length);
        return;
      }
      if (e.key === "ArrowUp") {
        e.preventDefault();
        setSelectedIdx((prev) => (prev - 1 + filtered.length) % filtered.length);
        return;
      }

      // Enter to select
      if (e.key === "Enter" && filtered.length > 0) {
        e.preventDefault();
        filtered[selectedIdx]?.action();
        return;
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [open, openBar, closeBar, filtered, selectedIdx]);

  // ── Render ──────────────────────────────────────────────────────────
  return (
    <div
      className={cn(
        "fixed inset-x-0 top-[72px] z-commandbar flex justify-center",
        "motion-safe:transition-all motion-safe:duration-200 motion-safe:ease-out",
        open
          ? "opacity-100 translate-y-0"
          : "opacity-0 -translate-y-2 pointer-events-none",
      )}
    >
      {/* Backdrop — dims background */}
      {open && (
        <div
          className="fixed inset-0 z-[-1] bg-black/30 backdrop-blur-sm"
          onClick={closeBar}
          aria-hidden="true"
        />
      )}

      {/* Glass dropdown */}
      <div
        className={cn(
          "w-full max-w-lg rounded-2xl border border-border-default",
          "bg-bg-glass backdrop-blur-2xl",
          "shadow-[0_16px_48px_rgba(0,0,0,0.6)]",
          "overflow-hidden",
          "motion-safe:animate-fade-in",
        )}
        role="dialog"
        aria-label="Command palette"
      >
        {/* ── Input ───────────────────────────────────────────── */}
        <div className="flex items-center gap-3 border-b border-border-subtle px-4 py-3">
          <LightningIcon className="text-text-muted" size={16} />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type a command or mode name…"
            className={cn(
              "flex-1 bg-transparent text-sm font-medium text-text-primary",
              "placeholder:text-text-muted",
              "outline-none border-none focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-border-input-focus",
            )}
            aria-label="Command search"
          />
          <span className="text-[10px] font-mono text-text-muted bg-bg-elevated px-1.5 py-0.5 rounded">
            ⎋
          </span>
        </div>

        {/* ── Results ─────────────────────────────────────────── */}
        <div
          ref={listRef}
          className="max-h-80 overflow-y-auto overscroll-contain py-2"
          role="listbox"
          aria-label="Commands"
        >
          {filtered.length === 0 && (
            <div className="px-4 py-6 text-center text-sm text-text-muted">
              No results for <span className="font-mono text-text-secondary">&ldquo;{query}&rdquo;</span>
            </div>
          )}

          {/* Render as flat list with group headers if unfiltered */}
          {query.trim()
            ? /* Flat when filtered */
              filtered.slice(0, 8).map((item, idx) => (
                <button
                  key={item.id}
                  ref={idx === selectedIdx ? selectedRef : undefined}
                  onClick={item.action}
                  onMouseEnter={() => setSelectedIdx(idx)}
                  className={cn(
                    "flex w-full items-center gap-3 px-4 py-2.5 text-left",
                    "motion-safe:transition-colors motion-safe:duration-100",
                    idx === selectedIdx ? "bg-accent-red-muted/40" : "hover:bg-bg-elevated/50",
                  )}
                  role="option"
                  aria-selected={idx === selectedIdx}
                >
                  <span className="flex items-center justify-center w-5 flex-shrink-0 text-text-secondary">{item.icon}</span>
                  <div className="flex-1 min-w-0">
                    <span className="text-sm font-medium text-text-primary block truncate">
                      {item.label}
                    </span>
                    {item.description && (
                      <span className="text-xs text-text-muted block truncate">
                        {item.description}
                      </span>
                    )}
                  </div>
                  {item.shortcut && (
                    <span className="text-[10px] font-mono text-text-muted flex-shrink-0">
                      {item.shortcut}
                    </span>
                  )}
                </button>
              ))
            : /* Grouped when empty query */
              groups.map((group) => {
                const groupStart = flatItems.indexOf(group.items[0]);
                return (
                  <div key={group.label}>
                    <div className="px-4 py-1.5 text-[10px] font-semibold uppercase tracking-widest text-text-muted">
                      {group.label}
                    </div>
                    {group.items.slice(0, 8).map((item, idx) => {
                      const globalIdx = groupStart + idx;
                      return (
                        <button
                          key={item.id}
                          ref={globalIdx === selectedIdx ? selectedRef : undefined}
                          onClick={item.action}
                          onMouseEnter={() => setSelectedIdx(globalIdx)}
                          className={cn(
                            "flex w-full items-center gap-3 px-4 py-2.5 text-left",
                            "motion-safe:transition-colors motion-safe:duration-100",
                            globalIdx === selectedIdx ? "bg-accent-red-muted/40" : "hover:bg-bg-elevated/50",
                          )}
                          role="option"
                          aria-selected={globalIdx === selectedIdx}
                        >
                          <span className="flex items-center justify-center w-5 flex-shrink-0 text-text-secondary">{item.icon}</span>
                          <div className="flex-1 min-w-0">
                            <span className="text-sm font-medium text-text-primary block truncate">
                              {item.label}
                            </span>
                            {item.description && (
                              <span className="text-xs text-text-muted block truncate">
                                {item.description}
                              </span>
                            )}
                          </div>
                          {item.shortcut && (
                            <span className="text-[10px] font-mono text-text-muted flex-shrink-0">
                              {item.shortcut}
                            </span>
                          )}
                        </button>
                      );
                    })}
                  </div>
                );
              })
          }
        </div>

        {/* ── Footer hint ─────────────────────────────────────── */}
        <div className="border-t border-border-subtle px-4 py-1.5 flex items-center gap-3 text-[10px] text-text-muted">
          <span>↑↓ Navigate</span>
          <span className="w-px h-3 bg-border-subtle" />
          <span>↵ Select</span>
          <span className="w-px h-3 bg-border-subtle" />
          <span>⎋ Close</span>
        </div>
      </div>
    </div>
  );
}
