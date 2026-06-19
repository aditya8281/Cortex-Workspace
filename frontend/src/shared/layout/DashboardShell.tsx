"use client";

import { useState, useEffect, useRef, type ReactNode } from "react";
import { useRouter, usePathname } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { useAuth } from "../auth/AuthProvider";
import { getProfilePhotoUrl } from "../auth/cortexApi";
import { cn } from "../../lib/utils";
import {
  LayoutDashboard,
  Lock,
  Brain,
  User,
  Settings,
  Menu,
  ChevronLeft,
  LogOut,
  Shield,
  Search,
} from "lucide-react";
import CommandPalette from "../ui/CommandPalette";

interface DashboardShellProps {
  children: ReactNode;
}

const navItems = [
  { label: "Dashboard", href: "/app", icon: LayoutDashboard },
  { label: "Vault", href: "/vault", icon: Lock },
  { label: "Memory", href: "/memory", icon: Brain },
  { label: "Profile", href: "/profile", icon: User },
  { label: "Settings", href: "/settings", icon: Settings },
];

const bottomNavItems = [
  { label: "Dashboard", href: "/app", icon: LayoutDashboard },
  { label: "Vault", href: "/vault", icon: Lock },
  { label: "Memory", href: "/memory", icon: Brain },
  { label: "Profile", href: "/profile", icon: User },
  { label: "Settings", href: "/settings", icon: Settings },
];

export default function DashboardShell({ children }: DashboardShellProps) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const [sidebarExpanded, setSidebarExpanded] = useState(true);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [photoFailed, setPhotoFailed] = useState(false);
  const [breakpoint, setBreakpoint] = useState<"mobile" | "tablet" | "desktop">("desktop");
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);
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

  const initials = (user?.full_name || user?.username || "?")
    .charAt(0)
    .toUpperCase();

  const isDesktop = breakpoint === "desktop";
  const isTablet = breakpoint === "tablet";
  const isMobile = breakpoint === "mobile";

  const sidebarWidth = isDesktop ? (sidebarExpanded ? 240 : 64) : 0;

  return (
    <div className="min-h-screen flex bg-bg">
      {/* ── Desktop Sidebar ────────────────────────────────────── */}
      {isDesktop && (
        <motion.aside
          className="fixed left-0 top-0 z-30 h-full flex flex-col border-r border-border-subtle bg-bg-surface"
          animate={{ width: sidebarWidth }}
          transition={{ type: "spring", damping: 25, stiffness: 200 }}
        >
          {/* Logo */}
          <div className="h-14 shrink-0 flex items-center border-b border-border-subtle overflow-hidden">
            <div className="flex items-center gap-3 px-4 w-full">
              <div className="h-1.5 w-1.5 rounded-full bg-accent shadow-[0_0_8px_rgba(6,182,212,0.4)] shrink-0" />
              <AnimatePresence>
                {sidebarExpanded && (
                  <motion.span
                    initial={{ opacity: 0, width: 0 }}
                    animate={{ opacity: 1, width: "auto" }}
                    exit={{ opacity: 0, width: 0 }}
                    transition={{ duration: 0.2 }}
                    className="font-mono text-[11px] tracking-[0.2em] uppercase text-text-secondary whitespace-nowrap overflow-hidden"
                  >
                    Cortex
                  </motion.span>
                )}
              </AnimatePresence>
            </div>
          </div>

          {/* Nav Items */}
          <nav className="flex-1 overflow-y-auto p-3 space-y-1">
            {navItems.map((item) => {
              const isActive = pathname === item.href;
              const Icon = item.icon;
              return (
                <button
                  key={item.href}
                  onClick={() => router.push(item.href)}
                  className={cn(
                    "relative flex items-center gap-3 w-full rounded-xl text-sm transition-colors duration-200",
                    sidebarExpanded ? "px-3 py-2.5" : "justify-center px-0 py-2.5",
                    isActive
                      ? "text-accent font-medium"
                      : "text-text-secondary hover:bg-bg-hover hover:text-text"
                  )}
                >
                  {isActive && (
                    <motion.div
                      layoutId="sidebar-active"
                      className="absolute inset-0 rounded-xl bg-accent-faint border border-accent/15"
                      transition={{ type: "spring", damping: 25, stiffness: 300 }}
                    />
                  )}
                  <Icon className="h-5 w-5 shrink-0 relative z-10" />
                  <AnimatePresence>
                    {sidebarExpanded && (
                      <motion.span
                        initial={{ opacity: 0, width: 0 }}
                        animate={{ opacity: 1, width: "auto" }}
                        exit={{ opacity: 0, width: 0 }}
                        transition={{ duration: 0.2 }}
                        className="relative z-10 whitespace-nowrap overflow-hidden"
                      >
                        {item.label}
                      </motion.span>
                    )}
                  </AnimatePresence>
                </button>
              );
            })}
            {user?.role === "admin" && (
              <button
                onClick={() => router.push("/admin")}
                className={cn(
                  "relative flex items-center gap-3 w-full rounded-xl text-sm transition-colors duration-200",
                  sidebarExpanded ? "px-3 py-2.5" : "justify-center px-0 py-2.5",
                  pathname === "/admin"
                    ? "text-accent font-medium"
                    : "text-text-secondary hover:bg-bg-hover hover:text-text"
                )}
              >
                {pathname === "/admin" && (
                  <motion.div
                    layoutId="sidebar-active"
                    className="absolute inset-0 rounded-xl bg-accent-faint border border-accent/15"
                    transition={{ type: "spring", damping: 25, stiffness: 300 }}
                  />
                )}
                <Shield className="h-5 w-5 shrink-0 relative z-10" />
                <AnimatePresence>
                  {sidebarExpanded && (
                    <motion.span
                      initial={{ opacity: 0, width: 0 }}
                      animate={{ opacity: 1, width: "auto" }}
                      exit={{ opacity: 0, width: 0 }}
                      transition={{ duration: 0.2 }}
                      className="relative z-10 whitespace-nowrap overflow-hidden"
                    >
                      Admin
                    </motion.span>
                  )}
                </AnimatePresence>
              </button>
            )}
          </nav>

          {/* Collapse Toggle */}
          <div className="p-3 border-t border-border-subtle">
            <button
              onClick={() => setSidebarExpanded((v) => !v)}
              className="flex items-center justify-center w-full rounded-xl py-2.5 text-text-muted hover:text-text-secondary hover:bg-bg-hover transition-colors"
              aria-label={sidebarExpanded ? "Collapse sidebar" : "Expand sidebar"}
            >
              <motion.div
                animate={{ rotate: sidebarExpanded ? 0 : 180 }}
                transition={{ duration: 0.2 }}
              >
                <ChevronLeft className="h-4 w-4" />
              </motion.div>
            </button>
          </div>
        </motion.aside>
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
                  {navItems.map((item) => {
                    const isActive = pathname === item.href;
                    const Icon = item.icon;
                    return (
                      <button
                        key={item.href}
                        onClick={() => router.push(item.href)}
                        className={cn(
                          "relative flex items-center gap-3 w-full px-3 py-2.5 rounded-xl text-sm transition-colors duration-200",
                          isActive
                            ? "text-accent font-medium"
                            : "text-text-secondary hover:bg-bg-hover hover:text-text"
                        )}
                      >
                        {isActive && (
                          <motion.div
                            layoutId="tablet-sidebar-active"
                            className="absolute inset-0 rounded-xl bg-accent-faint border border-accent/15"
                            transition={{ type: "spring", damping: 25, stiffness: 300 }}
                          />
                        )}
                        <Icon className="h-5 w-5 shrink-0 relative z-10" />
                        <span className="relative z-10">{item.label}</span>
                      </button>
                    );
                  })}
                  {user?.role === "admin" && (
                    <button
                      onClick={() => router.push("/admin")}
                      className={cn(
                        "relative flex items-center gap-3 w-full px-3 py-2.5 rounded-xl text-sm transition-colors duration-200",
                        pathname === "/admin"
                          ? "text-accent font-medium"
                          : "text-text-secondary hover:bg-bg-hover hover:text-text"
                      )}
                    >
                      {pathname === "/admin" && (
                        <motion.div
                          layoutId="tablet-sidebar-active"
                          className="absolute inset-0 rounded-xl bg-accent-faint border border-accent/15"
                          transition={{ type: "spring", damping: 25, stiffness: 300 }}
                        />
                      )}
                      <Shield className="h-5 w-5 shrink-0 relative z-10" />
                      <span className="relative z-10">Admin</span>
                    </button>
                  )}
                </nav>
              </motion.aside>
            </>
          )}
        </AnimatePresence>
      )}

      {/* ── Main area ─────────────────────────────────────────── */}
      <div
        className="flex-1 flex flex-col min-h-screen transition-all duration-300"
        style={{ marginLeft: isDesktop ? sidebarWidth : 0 }}
      >
        {/* ── Header ──────────────────────────────────────────── */}
        <header className="glass-panel h-14 flex items-center justify-between px-5 shrink-0 sticky top-0 z-20">
          {/* Left: Menu button + Brand */}
          <div className="flex items-center gap-3">
            {(isTablet || isMobile) && (
              <button
                onClick={() => setMobileSidebarOpen((v) => !v)}
                className="h-8 w-8 rounded-lg flex items-center justify-center text-text-secondary hover:bg-bg-hover hover:text-text transition-colors"
                aria-label="Toggle sidebar"
              >
                <Menu className="h-5 w-5" />
              </button>
            )}
            {isDesktop && (
              <button
                onClick={() => setSidebarExpanded((v) => !v)}
                className="h-8 w-8 rounded-lg flex items-center justify-center text-text-secondary hover:bg-bg-hover hover:text-text transition-colors lg:hidden"
                aria-label="Toggle sidebar"
              >
                <Menu className="h-5 w-5" />
              </button>
            )}
            <button
              onClick={() => router.push("/app")}
              className="flex items-center gap-2 group"
            >
              <div className="h-1.5 w-1.5 rounded-full bg-accent shadow-[0_0_8px_rgba(6,182,212,0.4)] group-hover:shadow-[0_0_12px_rgba(6,182,212,0.6)] transition-shadow" />
              <span className="font-mono text-[11px] tracking-[0.2em] uppercase text-text-secondary group-hover:text-text transition-colors">
                Cortex
              </span>
            </button>
          </div>

          {/* Right: Search + Avatar */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setCommandPaletteOpen(true)}
              className="h-8 px-3 rounded-lg flex items-center gap-2 text-text-muted hover:text-text-secondary hover:bg-bg-hover transition-colors text-xs font-mono border border-border-subtle"
            >
              <Search className="h-3.5 w-3.5" />
              <span className="hidden sm:inline">Search...</span>
              <kbd className="hidden sm:inline-flex items-center gap-0.5 rounded border border-border-subtle bg-bg-surface px-1 py-0.5 text-[9px] text-text-muted ml-1">
                ⌘K
              </kbd>
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
        <main className={cn("flex-1 p-6", isMobile && "pb-24")}>
          {children}
        </main>
      </div>

      <CommandPalette open={commandPaletteOpen} onOpenChange={setCommandPaletteOpen} />

      {/* ── Mobile Bottom Tab Bar ──────────────────────────────── */}
      {isMobile && (
        <nav className="fixed bottom-0 left-0 right-0 z-30 glass-panel-strong border-t border-border-subtle">
          <div className="flex items-center justify-around h-16">
            {bottomNavItems.map((item) => {
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
