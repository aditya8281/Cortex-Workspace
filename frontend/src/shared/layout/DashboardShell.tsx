"use client";

import { useState, useEffect, useRef, type ReactNode } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { useAuth } from "../auth/AuthProvider";
import { getProfilePhotoUrl, apiListNotifications, apiVaultStatus, apiListMemory } from "../auth/cortexApi";
import { cn } from "../../lib/utils";
import {
  LayoutDashboard,
  Lock,
  Brain,
  Bot,
  User,
  Settings,
  Menu,
  LogOut,
  Shield,
  Search,
  Bell,
} from "lucide-react";
import CommandPalette from "../ui/CommandPalette";

interface DashboardShellProps {
  children: ReactNode;
}

const workNavItems = [
  { label: "Dashboard", href: "/app", icon: LayoutDashboard },
  { label: "Search", href: "/search", icon: Search },
  { label: "Agents", href: "/agents", icon: Bot },
];

const accountNavItems = [
  { label: "Vault", href: "/vault", icon: Lock },
  { label: "Memory", href: "/memory", icon: Brain },
  { label: "Profile", href: "/profile", icon: User },
  { label: "Settings", href: "/settings", icon: Settings },
];

const SIDEBAR_WIDTH = 240;

export default function DashboardShell({ children }: DashboardShellProps) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [photoFailed, setPhotoFailed] = useState(false);
  const [breakpoint, setBreakpoint] = useState<"mobile" | "tablet" | "desktop">("desktop");
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [vaultLocked, setVaultLocked] = useState(true);
  const [memoryCount, setMemoryCount] = useState(0);
  const prevUserIdRef = useRef(user?.id);
  const menuRef = useRef<HTMLDivElement>(null);

  if (prevUserIdRef.current !== user?.id) {
    prevUserIdRef.current = user?.id;
    if (photoFailed) setPhotoFailed(false);
  }

  useEffect(() => {
    function handleResize() {
      const w = window.innerWidth;
      if (w < 768) setBreakpoint("mobile");
      else if (w < 1024) setBreakpoint("tablet");
      else setBreakpoint("desktop");
    }
    handleResize();
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  useEffect(() => {
    if (breakpoint !== "desktop") {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setMobileSidebarOpen(false);
    }
  }, [breakpoint]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setMobileSidebarOpen(false);
  }, [pathname]);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false);
      }
    }
    if (menuOpen) {
      document.addEventListener("mousedown", handleClickOutside);
      return () => document.removeEventListener("mousedown", handleClickOutside);
    }
  }, [menuOpen]);

  useEffect(() => {
    if (!user) return;
    apiListNotifications(1, true).then((data) => setUnreadCount(data.unread_count)).catch(() => {});
    apiVaultStatus().then((data) => setVaultLocked(data.locked)).catch(() => {});
    apiListMemory({ limit: 1 }).then((data) => setMemoryCount(data.total ?? data.count)).catch(() => {});
  }, [user]);

  const initials = (user?.full_name || user?.username || "?")
    .charAt(0)
    .toUpperCase();

  const isDesktop = breakpoint === "desktop";
  const isTablet = breakpoint === "tablet";
  const isMobile = breakpoint === "mobile";

  return (
    <div className="min-h-screen flex bg-transparent">
      {/* ── Desktop Sidebar ────────────────────────────────────── */}
      {isDesktop && (
        <aside
          className="fixed left-0 top-0 z-30 h-full flex flex-col border-r border-border-subtle glass-panel-strong"
          style={{ width: SIDEBAR_WIDTH }}
        >
          {/* Logo */}
          <div className="h-14 shrink-0 flex items-center border-b border-border-subtle">
            <div className="flex items-center gap-3 px-4 w-full">
              <div className="h-1.5 w-1.5 rounded-full bg-accent shadow-[0_0_8px_rgba(6,182,212,0.4)] shrink-0" />
              <span className="font-mono text-[11px] tracking-[0.2em] uppercase text-text-secondary whitespace-nowrap">
                Cortex
              </span>
            </div>
          </div>

          {/* Nav Items */}
          <nav className="flex-1 overflow-y-auto p-3 space-y-1">
            {/* Work Group */}
            <div className="px-3 mb-1">
              <span className="micro-label">Work</span>
            </div>
            {workNavItems.map((item) => {
              const isActive = pathname === item.href;
              const Icon = item.icon;
              return (
                <button
                  key={item.href}
                  onClick={() => router.push(item.href)}
                  className={cn(
                    "relative flex items-center gap-3 w-full px-3 py-2.5 rounded-xl text-sm transition-all duration-200",
                    isActive
                      ? "text-accent font-medium shadow-[0_0_20px_rgba(6,182,212,0.08)]"
                      : "text-text-secondary hover:bg-bg-hover hover:text-text hover:shadow-[0_0_15px_rgba(6,182,212,0.04)]"
                  )}
                >
                  {isActive && (
                    <motion.div
                      layoutId="sidebar-active"
                      className="absolute inset-0 rounded-xl bg-accent-faint border border-accent/15"
                      transition={{ type: "spring", damping: 25, stiffness: 300 }}
                    />
                  )}
                  {isActive && (
                    <span className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-[3px] rounded-full bg-accent shadow-[0_0_6px_rgba(6,182,212,0.6)] animate-pulse-dot" />
                  )}
                  <Icon className={cn("h-5 w-5 shrink-0 relative z-10 transition-all duration-200", isActive && "drop-shadow-[0_0_4px_rgba(6,182,212,0.4)]")} />
                  <span className="relative z-10 whitespace-nowrap flex-1 text-left">{item.label}</span>
                </button>
              );
            })}

            {/* Divider */}
            <div className="mx-3 my-2 h-px bg-gradient-to-r from-transparent via-border-subtle to-transparent" />

            {/* You Group */}
            <div className="px-3 mb-1">
              <span className="micro-label">You</span>
            </div>
            {accountNavItems.map((item) => {
              const isActive = pathname === item.href;
              const Icon = item.icon;
              return (
                <button
                  key={item.href}
                  onClick={() => router.push(item.href)}
                  className={cn(
                    "relative flex items-center gap-3 w-full px-3 py-2.5 rounded-xl text-sm transition-all duration-200",
                    isActive
                      ? "text-accent font-medium shadow-[0_0_20px_rgba(6,182,212,0.08)]"
                      : "text-text-secondary hover:bg-bg-hover hover:text-text hover:shadow-[0_0_15px_rgba(6,182,212,0.04)]"
                  )}
                >
                  {isActive && (
                    <motion.div
                      layoutId="sidebar-active"
                      className="absolute inset-0 rounded-xl bg-accent-faint border border-accent/15"
                      transition={{ type: "spring", damping: 25, stiffness: 300 }}
                    />
                  )}
                  {isActive && (
                    <span className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-[3px] rounded-full bg-accent shadow-[0_0_6px_rgba(6,182,212,0.6)] animate-pulse-dot" />
                  )}
                  <Icon className={cn("h-5 w-5 shrink-0 relative z-10 transition-all duration-200", isActive && "drop-shadow-[0_0_4px_rgba(6,182,212,0.4)]")} />
                  <span className="relative z-10 whitespace-nowrap flex-1 text-left">{item.label}</span>
                </button>
              );
            })}
            {user?.role === "admin" && (
              <button
                onClick={() => router.push("/admin")}
                className={cn(
                  "relative flex items-center gap-3 w-full px-3 py-2.5 rounded-xl text-sm transition-all duration-200",
                  pathname === "/admin"
                    ? "text-accent font-medium shadow-[0_0_20px_rgba(6,182,212,0.08)]"
                    : "text-text-secondary hover:bg-bg-hover hover:text-text hover:shadow-[0_0_15px_rgba(6,182,212,0.04)]"
                )}
              >
                {pathname === "/admin" && (
                  <motion.div
                    layoutId="sidebar-active"
                    className="absolute inset-0 rounded-xl bg-accent-faint border border-accent/15"
                    transition={{ type: "spring", damping: 25, stiffness: 300 }}
                  />
                )}
                {pathname === "/admin" && (
                  <span className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-[3px] rounded-full bg-accent shadow-[0_0_6px_rgba(6,182,212,0.6)] animate-pulse-dot" />
                )}
                <Shield className={cn("h-5 w-5 shrink-0 relative z-10 transition-all duration-200", pathname === "/admin" && "drop-shadow-[0_0_4px_rgba(6,182,212,0.4)]")} />
                <span className="relative z-10 whitespace-nowrap flex-1 text-left">Admin</span>
              </button>
            )}
          </nav>

          {/* Status Bar */}
          <div className="px-3 pt-2">
            <div className="h-px mb-2 bg-gradient-to-r from-transparent via-accent/15 to-transparent" />
            <button
              onClick={() => router.push("/vault")}
              className="flex items-center gap-2 w-full px-2 py-1.5 rounded-lg text-[12px] text-text-muted hover:bg-bg-hover hover:text-text-secondary transition-colors"
            >
              <span className={cn("w-[6px] h-[6px] rounded-full shrink-0", vaultLocked ? "bg-red-500 shadow-[0_0_6px_rgba(239,68,68,0.4)]" : "bg-green-500 shadow-[0_0_6px_rgba(34,197,94,0.4)]")} />
              <span>Vault: {vaultLocked ? "Locked" : "Unlocked"}</span>
            </button>
            <button
              onClick={() => router.push("/memory")}
              className="flex items-center gap-2 w-full px-2 py-1.5 rounded-lg text-[12px] text-text-muted hover:bg-bg-hover hover:text-text-secondary transition-colors"
            >
              <Brain className="w-3.5 h-3.5 shrink-0" />
              <span>Memory: <span className="text-accent font-mono text-[11px]">{memoryCount}</span> items</span>
            </button>
          </div>

          {/* User Card */}
          <div className="px-3 pb-2 pt-2">
            <div className="flex items-center gap-3 px-2 py-2 rounded-xl bg-bg-hover/50">
              <div className="relative shrink-0">
                <div className="h-8 w-8 rounded-full bg-accent flex items-center justify-center text-xs font-bold text-void overflow-hidden ring-2 ring-accent/20 shadow-[0_0_12px_rgba(6,182,212,0.2)]">
                  {user?.profile_photo && user?.id && !photoFailed ? (
                    <img src={getProfilePhotoUrl(user.id)} alt="" className="h-full w-full object-cover" onError={() => setPhotoFailed(true)} />
                  ) : initials}
                </div>
                <span className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-green-500 border-2 border-bg-surface" />
              </div>
              <div className="min-w-0">
                <p className="text-sm font-medium text-text truncate">{user?.full_name || user?.username}</p>
                <p className="text-[10px] text-text-muted truncate">@{user?.username}</p>
              </div>
            </div>
          </div>
        </aside>
      )}

      {/* ── Tablet Overlay Sidebar ─────────────────────────────── */}
      {isTablet && (
        <AnimatePresence>
          {mobileSidebarOpen && (
            <>
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.2 }}
                className="fixed inset-0 z-40 bg-void/60 backdrop-blur-sm"
                onClick={() => setMobileSidebarOpen(false)}
              />
              <motion.aside
                initial={{ x: -280 }}
                animate={{ x: 0 }}
                exit={{ x: -280 }}
                transition={{ type: "spring", damping: 25, stiffness: 200 }}
                className="fixed left-0 top-0 z-50 h-full w-[260px] flex flex-col border-r border-border-subtle bg-bg-surface backdrop-blur-xl"
              >
                {/* Logo */}
                <div className="h-14 shrink-0 flex items-center px-4 border-b border-border-subtle">
                  <div className="flex items-center gap-3">
                    <div className="h-1.5 w-1.5 rounded-full bg-accent shadow-[0_0_8px_rgba(6,182,212,0.4)]" />
                    <span className="font-mono text-[11px] tracking-[0.2em] uppercase text-text-secondary">
                      Cortex
                    </span>
                  </div>
                </div>

                {/* Nav Items */}
                <nav className="flex-1 overflow-y-auto p-3 space-y-1">
                  {/* Work Group */}
                  <div className="px-3 mb-1">
                    <span className="micro-label">Work</span>
                  </div>
                  {workNavItems.map((item) => {
                    const isActive = pathname === item.href;
                    const Icon = item.icon;
                    return (
                      <button
                        key={item.href}
                        onClick={() => router.push(item.href)}
                        className={cn(
                          "relative flex items-center gap-3 w-full px-3 py-2.5 rounded-xl text-sm transition-all duration-200",
                          isActive
                            ? "text-accent font-medium shadow-[0_0_20px_rgba(6,182,212,0.08)]"
                            : "text-text-secondary hover:bg-bg-hover hover:text-text hover:shadow-[0_0_15px_rgba(6,182,212,0.04)]"
                        )}
                      >
                        {isActive && (
                          <motion.div
                            layoutId="tablet-sidebar-active"
                            className="absolute inset-0 rounded-xl bg-accent-faint border border-accent/15"
                            transition={{ type: "spring", damping: 25, stiffness: 300 }}
                          />
                        )}
                        {isActive && (
                          <span className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-[3px] rounded-full bg-accent shadow-[0_0_6px_rgba(6,182,212,0.6)] animate-pulse-dot" />
                        )}
                        <Icon className={cn("h-5 w-5 shrink-0 relative z-10 transition-all duration-200", isActive && "drop-shadow-[0_0_4px_rgba(6,182,212,0.4)]")} />
                        <span className="relative z-10">{item.label}</span>
                      </button>
                    );
                  })}

                  {/* Divider */}
                  <div className="mx-3 my-2 h-px bg-gradient-to-r from-transparent via-border-subtle to-transparent" />

                  {/* You Group */}
                  <div className="px-3 mb-1">
                    <span className="micro-label">You</span>
                  </div>
                  {accountNavItems.map((item) => {
                    const isActive = pathname === item.href;
                    const Icon = item.icon;
                    return (
                      <button
                        key={item.href}
                        onClick={() => router.push(item.href)}
                        className={cn(
                          "relative flex items-center gap-3 w-full px-3 py-2.5 rounded-xl text-sm transition-all duration-200",
                          isActive
                            ? "text-accent font-medium shadow-[0_0_20px_rgba(6,182,212,0.08)]"
                            : "text-text-secondary hover:bg-bg-hover hover:text-text hover:shadow-[0_0_15px_rgba(6,182,212,0.04)]"
                        )}
                      >
                        {isActive && (
                          <motion.div
                            layoutId="tablet-sidebar-active"
                            className="absolute inset-0 rounded-xl bg-accent-faint border border-accent/15"
                            transition={{ type: "spring", damping: 25, stiffness: 300 }}
                          />
                        )}
                        {isActive && (
                          <span className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-[3px] rounded-full bg-accent shadow-[0_0_6px_rgba(6,182,212,0.6)] animate-pulse-dot" />
                        )}
                        <Icon className={cn("h-5 w-5 shrink-0 relative z-10 transition-all duration-200", isActive && "drop-shadow-[0_0_4px_rgba(6,182,212,0.4)]")} />
                        <span className="relative z-10">{item.label}</span>
                      </button>
                    );
                  })}
                  {user?.role === "admin" && (
                    <button
                      onClick={() => router.push("/admin")}
                      className={cn(
                        "relative flex items-center gap-3 w-full px-3 py-2.5 rounded-xl text-sm transition-all duration-200",
                        pathname === "/admin"
                          ? "text-accent font-medium shadow-[0_0_20px_rgba(6,182,212,0.08)]"
                          : "text-text-secondary hover:bg-bg-hover hover:text-text hover:shadow-[0_0_15px_rgba(6,182,212,0.04)]"
                      )}
                    >
                      {pathname === "/admin" && (
                        <motion.div
                          layoutId="tablet-sidebar-active"
                          className="absolute inset-0 rounded-xl bg-accent-faint border border-accent/15"
                          transition={{ type: "spring", damping: 25, stiffness: 300 }}
                        />
                      )}
                      {pathname === "/admin" && (
                        <span className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-[3px] rounded-full bg-accent shadow-[0_0_6px_rgba(6,182,212,0.6)] animate-pulse-dot" />
                      )}
                      <Shield className={cn("h-5 w-5 shrink-0 relative z-10 transition-all duration-200", pathname === "/admin" && "drop-shadow-[0_0_4px_rgba(6,182,212,0.4)]")} />
                      <span className="relative z-10">Admin</span>
                    </button>
                  )}
                </nav>

                {/* Status Bar */}
                <div className="px-3 pt-2">
                  <div className="h-px mb-2 bg-gradient-to-r from-transparent via-accent/15 to-transparent" />
                  <button
                    onClick={() => { router.push("/vault"); setMobileSidebarOpen(false); }}
                    className="flex items-center gap-2 w-full px-2 py-1.5 rounded-lg text-[12px] text-text-muted hover:bg-bg-hover hover:text-text-secondary transition-colors"
                  >
                    <span className={cn("w-[6px] h-[6px] rounded-full shrink-0", vaultLocked ? "bg-red-500 shadow-[0_0_6px_rgba(239,68,68,0.4)]" : "bg-green-500 shadow-[0_0_6px_rgba(34,197,94,0.4)]")} />
                    <span>Vault: {vaultLocked ? "Locked" : "Unlocked"}</span>
                  </button>
                  <button
                    onClick={() => { router.push("/memory"); setMobileSidebarOpen(false); }}
                    className="flex items-center gap-2 w-full px-2 py-1.5 rounded-lg text-[12px] text-text-muted hover:bg-bg-hover hover:text-text-secondary transition-colors"
                  >
                    <Brain className="w-3.5 h-3.5 shrink-0" />
                    <span>Memory: <span className="text-accent font-mono text-[11px]">{memoryCount}</span> items</span>
                  </button>
                </div>
              </motion.aside>
            </>
          )}
        </AnimatePresence>
      )}

      {/* ── Main area ─────────────────────────────────────────── */}
      <div
        className="flex-1 flex flex-col min-h-screen"
        style={{ marginLeft: isDesktop ? SIDEBAR_WIDTH : 0 }}
      >
        {/* ── Header ──────────────────────────────────────────── */}
        <header className="sticky top-0 z-30 h-14 flex items-center justify-between px-4 glass-panel border-b border-border-subtle shrink-0">
          <div className="flex items-center gap-3">
            {(isTablet || isMobile) && (
              <button
                onClick={() => setMobileSidebarOpen((v) => !v)}
                className="p-2 rounded-lg hover:bg-bg-hover text-text-secondary"
                aria-label="Toggle sidebar"
              >
                <Menu className="h-5 w-5" />
              </button>
            )}
            <Link href="/app" className="flex items-center gap-2 group">
              <div className="h-1.5 w-1.5 rounded-full bg-accent shadow-[0_0_8px_rgba(6,182,212,0.4)] group-hover:shadow-[0_0_12px_rgba(6,182,212,0.6)] transition-shadow" />
              <span className="font-semibold text-text hidden sm:inline">Cortex</span>
            </Link>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setCommandPaletteOpen(true)}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-border-subtle bg-bg-surface text-text-secondary text-sm hover:border-accent/20 hover:text-text transition-colors"
            >
              <Search size={14} />
              <span className="hidden sm:inline">Search</span>
              <kbd className="text-[10px] font-mono bg-bg-hover px-1.5 py-0.5 rounded">⌘K</kbd>
            </button>
            <button
              onClick={() => {/* TODO: open notifications panel */}}
              className="relative h-8 w-8 rounded-lg flex items-center justify-center text-text-secondary hover:bg-bg-hover hover:text-text transition-colors"
              aria-label="Notifications"
            >
              <Bell className="h-4 w-4" />
              {unreadCount > 0 && (
                <span className="absolute -top-0.5 -right-0.5 h-4 min-w-[16px] rounded-full bg-accent text-[9px] font-bold text-void flex items-center justify-center px-1">
                  {unreadCount > 9 ? "9+" : unreadCount}
                </span>
              )}
            </button>
            <div className="relative" ref={menuRef}>
              <button
                onClick={() => setMenuOpen((v) => !v)}
                className="h-8 w-8 rounded-full bg-bg-elevated border border-border-subtle
                           flex items-center justify-center text-xs font-medium text-accent
                           hover:border-accent/30 transition-colors overflow-hidden"
              >
                {user?.profile_photo && user?.id && !photoFailed ? (
                  <img
                    src={getProfilePhotoUrl(user.id)}
                    alt={`${user?.full_name || user?.username || "User"} avatar`}
                    className="h-full w-full object-cover"
                    onError={() => setPhotoFailed(true)}
                  />
                ) : (
                  initials
                )}
              </button>

              {/* Dropdown */}
              <AnimatePresence>
                {menuOpen && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.95, y: -4 }}
                    animate={{ opacity: 1, scale: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.95, y: -4 }}
                    transition={{ duration: 0.15, ease: "easeOut" }}
                    className="absolute right-0 top-full mt-1.5 z-50 w-52 rounded-xl bg-bg-elevated border border-border-subtle shadow-elevated py-1.5 overflow-hidden"
                  >
                    <div className="px-3.5 py-2.5 border-b border-border-subtle">
                      <p className="text-sm font-medium text-text truncate">
                        {user?.full_name || user?.username}
                      </p>
                      <p className="text-[11px] text-text-muted truncate">
                        @{user?.username}
                      </p>
                    </div>

                    <div className="py-1">
                      <button
                        onClick={() => {
                          setMenuOpen(false);
                          router.push("/profile");
                        }}
                        className="w-full text-left px-3.5 py-2 text-sm text-text-secondary hover:bg-bg-hover hover:text-text transition-colors flex items-center gap-2.5"
                      >
                        <User className="h-4 w-4" />
                        Profile
                      </button>
                      <button
                        onClick={() => {
                          setMenuOpen(false);
                          router.push("/settings");
                        }}
                        className="w-full text-left px-3.5 py-2 text-sm text-text-secondary hover:bg-bg-hover hover:text-text transition-colors flex items-center gap-2.5"
                      >
                        <Settings className="h-4 w-4" />
                        Settings
                      </button>
                      {user?.role === "admin" && (
                        <button
                          onClick={() => {
                            setMenuOpen(false);
                            router.push("/admin");
                          }}
                          className="w-full text-left px-3.5 py-2 text-sm text-text-secondary hover:bg-bg-hover hover:text-text transition-colors flex items-center gap-2.5"
                        >
                          <Shield className="h-4 w-4 text-accent" />
                          Admin
                        </button>
                      )}
                    </div>

                    <div className="border-t border-border-subtle pt-1 mt-1">
                      <button
                        onClick={() => {
                          setMenuOpen(false);
                          logout();
                        }}
                        className="w-full text-left px-3.5 py-2 text-sm text-text-secondary hover:bg-bg-hover hover:text-text transition-colors flex items-center gap-2.5"
                      >
                        <LogOut className="h-4 w-4" />
                        Sign out
                      </button>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>
        </header>

        {/* ── Main content ───────────────────────────────────── */}
        <main id="main-content" className={cn("flex-1 p-6", isMobile && "pb-24")}>
          {children}
        </main>
      </div>

      <CommandPalette open={commandPaletteOpen} onOpenChange={setCommandPaletteOpen} />

      {/* ── Mobile Bottom Tab Bar ──────────────────────────────── */}
      {isMobile && (
        <nav className="fixed bottom-0 left-0 right-0 z-30 glass-panel-strong border-t border-border-subtle">
          <div className="flex items-center justify-around h-16">
            {[...workNavItems, ...accountNavItems].map((item) => {
              const isActive = pathname === item.href;
              const Icon = item.icon;
              return (
                <button
                  key={item.href}
                  onClick={() => router.push(item.href)}
                  className={cn(
                    "flex flex-col items-center gap-1 px-3 py-1.5 rounded-lg transition-colors",
                    isActive
                      ? "text-accent"
                      : "text-text-muted hover:text-text-secondary"
                  )}
                >
                  <Icon className="h-5 w-5" />
                  <span className="text-[10px] font-medium">{item.label}</span>
                </button>
              );
            })}
          </div>
        </nav>
      )}
    </div>
  );
}
