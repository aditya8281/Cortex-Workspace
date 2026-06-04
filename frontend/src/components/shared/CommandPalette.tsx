"use client";

import React, { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { useDispatch, useSelector } from "react-redux";
import type { RootState } from "@/state/store";
import { toggleCommandPalette } from "@/state/slices/ui";
import { clearMessages } from "@/state/slices/chat";
import { syncService as apiSyncService } from "@/services/api/sync";
import { useAuth } from "@/hooks/useAuth";
import { 
  Search, MessageSquare, Brain, RefreshCw, Cpu, Settings, LogOut, Trash2, ArrowRight
} from "lucide-react";

interface PaletteItem {
  icon: React.ComponentType<any>;
  label: string;
  category: "Navigation" | "System Commands";
  action: () => void;
  shortcut?: string;
}

export function CommandPalette() {
  const dispatch = useDispatch();
  const router = useRouter();
  const { logout } = useAuth();
  
  const isOpen = useSelector((state: RootState) => state.ui.commandPaletteOpen);
  const [search, setSearch] = useState("");
  const [activeIndex, setActiveIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  // Close palette helper
  const closePalette = () => {
    if (isOpen) {
      dispatch(toggleCommandPalette());
    }
  };

  // Keyboard shortcut Ctrl+K / Cmd+K listener
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "k") {
        e.preventDefault();
        dispatch(toggleCommandPalette());
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [dispatch]);

  // Focus input on open
  useEffect(() => {
    if (isOpen) {
      setSearch("");
      setActiveIndex(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [isOpen]);

  const items: PaletteItem[] = [
    // Navigation
    {
      icon: MessageSquare,
      label: "Go to Chat Interface",
      category: "Navigation",
      action: () => {
        router.push("/dashboard/chat");
        closePalette();
      }
    },
    {
      icon: Brain,
      label: "Go to Memory Vault",
      category: "Navigation",
      action: () => {
        router.push("/dashboard/memory");
        closePalette();
      }
    },
    {
      icon: Cpu,
      label: "Go to Model Management",
      category: "Navigation",
      action: () => {
        router.push("/dashboard/models");
        closePalette();
      }
    },
    {
      icon: RefreshCw,
      label: "Go to Workspace Sync",
      category: "Navigation",
      action: () => {
        router.push("/dashboard/sync");
        closePalette();
      }
    },
    {
      icon: Search,
      label: "Go to Context Search",
      category: "Navigation",
      action: () => {
        router.push("/dashboard/search");
        closePalette();
      }
    },
    {
      icon: Settings,
      label: "Go to Configuration Settings",
      category: "Navigation",
      action: () => {
        router.push("/dashboard/settings");
        closePalette();
      }
    },
    // System Commands
    {
      icon: RefreshCw,
      label: "Trigger Full Workspace Sync",
      category: "System Commands",
      shortcut: "SYNC",
      action: async () => {
        closePalette();
        try {
          await apiSyncService.triggerSync();
          alert("Workspace sync successfully triggered!");
        } catch (err) {
          alert("Failed to trigger sync: " + err);
        }
      }
    },
    {
      icon: Trash2,
      label: "Clear All Conversations",
      category: "System Commands",
      shortcut: "CLEAR",
      action: () => {
        dispatch(clearMessages());
        closePalette();
      }
    },
    {
      icon: LogOut,
      label: "Logout of Cortex AI Workspace",
      category: "System Commands",
      action: () => {
        logout();
        router.push("/login");
        closePalette();
      }
    }
  ];

  // Filter items
  const filtered = items.filter(item => 
    item.label.toLowerCase().includes(search.toLowerCase()) || 
    item.category.toLowerCase().includes(search.toLowerCase())
  );

  // Key navigation inside list
  const handleListKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActiveIndex(prev => (prev + 1) % filtered.length);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActiveIndex(prev => (prev - 1 + filtered.length) % filtered.length);
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (filtered[activeIndex]) {
        filtered[activeIndex].action();
      }
    } else if (e.key === "Escape") {
      e.preventDefault();
      closePalette();
    }
  };

  if (!isOpen) return null;

  return (
    <div 
      className="fixed inset-0 z-50 flex items-start justify-center pt-24 px-4 bg-slate-950/60 backdrop-blur-[4px] transition-all animate-fade-in"
      onClick={closePalette}
    >
      <div 
        className="w-full max-w-xl bg-slate-900/95 border border-cyan-500/30 rounded-xl overflow-hidden shadow-[0_0_40px_rgba(6,182,212,0.15)] flex flex-col max-h-[420px]"
        onClick={e => e.stopPropagation()}
        onKeyDown={handleListKeyDown}
      >
        {/* Search Input Bar */}
        <div className="flex items-center gap-3 px-4 py-3.5 border-b border-slate-800/80 bg-slate-900/40">
          <Search className="text-slate-400 shrink-0" size={18} />
          <input
            ref={inputRef}
            type="text"
            placeholder="Type a command or route name..."
            className="w-full bg-transparent text-slate-100 text-sm focus:outline-none placeholder-slate-500 font-sans"
            value={search}
            onChange={e => {
              setSearch(e.target.value);
              setActiveIndex(0);
            }}
          />
          <span className="text-[10px] bg-slate-800 border border-slate-700 px-1.5 py-0.5 rounded text-slate-500 font-mono tracking-wider shadow-inner">
            ESC
          </span>
        </div>

        {/* List of items */}
        <div className="flex-1 overflow-y-auto p-2 space-y-3 scrollbar-thin">
          {filtered.length === 0 ? (
            <div className="py-8 text-center text-xs text-slate-500 font-mono">
              NO MATCHES FOUND FOR &quot;{search}&quot;
            </div>
          ) : (
            // Group by Category
            ["Navigation", "System Commands"].map((cat) => {
              const catItems = filtered.filter(i => i.category === cat);
              if (catItems.length === 0) return null;
              
              return (
                <div key={cat} className="space-y-1">
                  <div className="text-[10px] font-mono tracking-widest text-slate-500 uppercase px-3 py-1">
                    {cat}
                  </div>
                  {catItems.map((item) => {
                    const globalIdx = filtered.indexOf(item);
                    const isSelected = globalIdx === activeIndex;
                    
                    return (
                      <button
                        key={item.label}
                        onClick={item.action}
                        onMouseEnter={() => setActiveIndex(globalIdx)}
                        className={`w-full text-left flex items-center justify-between px-3 py-2.5 rounded-lg transition-all duration-100 ${
                          isSelected 
                            ? "bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 shadow-[inset_0_1px_1px_rgba(255,255,255,0.05)]" 
                            : "border border-transparent text-slate-300 hover:text-slate-200"
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <item.icon size={16} className={isSelected ? "text-cyan-400" : "text-slate-400"} />
                          <span className="text-xs font-medium font-sans">{item.label}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          {item.shortcut && (
                            <span className="text-[9px] bg-slate-800/80 px-1.5 py-0.5 rounded text-slate-400 font-mono border border-slate-700/50">
                              {item.shortcut}
                            </span>
                          )}
                          {isSelected && <ArrowRight size={12} className="text-cyan-400 animate-pulse" />}
                        </div>
                      </button>
                    );
                  })}
                </div>
              );
            })
          )}
        </div>

        {/* Footer */}
        <div className="bg-slate-950/80 border-t border-slate-800/60 px-4 py-2 flex items-center justify-between text-[10px] font-mono text-slate-500">
          <div className="flex gap-4">
            <span>↑↓ NAVIGATION</span>
            <span>ENTER EXECUTE</span>
          </div>
          <span>CORTEX OS v0.1.0</span>
        </div>
      </div>
    </div>
  );
}
