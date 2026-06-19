"use client";

import { useEffect, useCallback, useState } from "react";
import { useRouter } from "next/navigation";
import { Command } from "cmdk";
import { motion, AnimatePresence } from "framer-motion";
import {
  LayoutDashboard,
  Lock,
  Brain,
  Bot,
  User,
  Settings,
  Shield,
  Search,
} from "lucide-react";

interface CommandPaletteProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const pages = [
  { label: "Dashboard", href: "/app", icon: LayoutDashboard },
  { label: "Search", href: "/search", icon: Search },
  { label: "Agents", href: "/agents", icon: Bot },
  { label: "Vault", href: "/vault", icon: Lock },
  { label: "Memory", href: "/memory", icon: Brain },
  { label: "Profile", href: "/profile", icon: User },
  { label: "Settings", href: "/settings", icon: Settings },
  { label: "Admin", href: "/admin", icon: Shield },
];

export default function CommandPalette({ open, onOpenChange }: CommandPaletteProps) {
  const router = useRouter();
  const [search, setSearch] = useState("");

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        onOpenChange(!open);
      }
      if (e.key === "Escape" && open) {
        onOpenChange(false);
      }
    },
    [open, onOpenChange]
  );

  useEffect(() => {
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [handleKeyDown]);

  useEffect(() => {
    if (!open) setSearch("");
  }, [open]);

  function handleSelect(href: string) {
    onOpenChange(false);
    setSearch("");
    router.push(href);
  }

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.15 }}
          className="fixed inset-0 z-[100] flex items-start justify-center pt-[20vh]"
        >
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-void/80 backdrop-blur-sm"
            onClick={() => onOpenChange(false)}
          />

          {/* Dialog */}
          <motion.div
            initial={{ opacity: 0, scale: 0.96, y: -10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.96, y: -10 }}
            transition={{ type: "spring", damping: 25, stiffness: 300 }}
            className="relative w-full max-w-lg mx-4 rounded-2xl border border-border-subtle bg-bg-elevated/95 backdrop-blur-xl shadow-modal overflow-hidden"
          >
            <Command loop shouldFilter={true}>
              <div className="flex items-center gap-3 px-4 border-b border-border-subtle">
                <Search className="h-4 w-4 text-text-muted shrink-0" />
                <Command.Input
                  value={search}
                  onValueChange={setSearch}
                  placeholder="Search pages..."
                  className="flex-1 h-12 bg-transparent text-sm text-text placeholder:text-text-muted outline-none"
                />
                <kbd className="hidden sm:inline-flex items-center gap-1 rounded-md border border-border-subtle bg-bg-surface px-1.5 py-0.5 text-[10px] font-mono text-text-muted">
                  ESC
                </kbd>
              </div>

              <Command.List className="max-h-[300px] overflow-y-auto p-2">
                <Command.Empty className="py-8 text-center text-sm text-text-muted">
                  No results found.
                </Command.Empty>

                <Command.Group heading="Pages" className="text-[10px] font-mono uppercase tracking-wider text-text-muted px-2 py-1.5">
                  {pages.map((page) => {
                    const Icon = page.icon;
                    return (
                      <Command.Item
                        key={page.href}
                        value={page.label}
                        onSelect={() => handleSelect(page.href)}
                        className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm text-text-secondary cursor-pointer transition-colors data-[selected=true]:bg-accent-faint data-[selected=true]:text-accent outline-none"
                      >
                        <Icon className="h-4 w-4 shrink-0" />
                        <span>{page.label}</span>
                        <span className="ml-auto text-[10px] font-mono text-text-muted">
                          {page.href}
                        </span>
                      </Command.Item>
                    );
                  })}
                </Command.Group>
              </Command.List>

              <div className="flex items-center justify-between px-4 py-2.5 border-t border-border-subtle">
                <div className="flex items-center gap-2 text-[10px] text-text-muted font-mono">
                  <span className="inline-flex items-center gap-1">
                    <kbd className="rounded border border-border-subtle bg-bg-surface px-1 py-0.5">↑↓</kbd>
                    Navigate
                  </span>
                  <span className="inline-flex items-center gap-1">
                    <kbd className="rounded border border-border-subtle bg-bg-surface px-1 py-0.5">↵</kbd>
                    Select
                  </span>
                </div>
              </div>
            </Command>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
