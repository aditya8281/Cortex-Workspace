/**
 * Dashboard shell — Post-auth layout with header & collapsible sidebar.
 * Header: brand + hamburger (left), breadcrumb (center), avatar menu (right).
 * Sidebar: nav items with Heroicons, .nav-item class, active state via pathname.
 */
"use client";

import { useState, useRef, type ReactNode } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuth } from "../auth/AuthProvider";
import { getProfilePhotoUrl } from "../auth/cortexApi";

interface DashboardShellProps {
  children: ReactNode;
}

const navItems = [
  {
    label: "Dashboard",
    href: "/app",
    icon: (
      <svg className="h-5 w-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z" />
      </svg>
    ),
  },
  {
    label: "Vault",
    href: "/vault",
    icon: (
      <svg className="h-5 w-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v12m-3-2.818l.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.45-.22-2.003-.659-1.106-.879-1.106-2.303 0-3.182s2.9-.879 4.006 0l.415.33M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  },
  {
    label: "Memory",
    href: "/memory",
    icon: (
      <svg className="h-5 w-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 6.375c0 2.278-3.694 4.125-8.25 4.125S3.75 8.653 3.75 6.375m16.5 0c0-2.278-3.694-4.125-8.25-4.125S3.75 4.097 3.75 6.375m16.5 0v11.25c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125V6.375m16.5 0v3.75m-16.5-3.75v3.75m16.5 0v3.75C20.25 16.153 16.556 18 12 18s-8.25-1.847-8.25-4.125v-3.75m16.5 0c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125" />
      </svg>
    ),
  },
  {
    label: "Profile",
    href: "/profile",
    icon: (
      <svg className="h-5 w-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M17.982 18.725A7.488 7.488 0 0012 15.75a7.488 7.488 0 00-5.982 2.975m11.963 0a9 9 0 10-11.963 0m11.963 0A8.966 8.966 0 0112 21a8.966 8.966 0 01-5.982-2.275M15 9.75a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
    ),
  },
  {
    label: "Settings",
    href: "/settings",
    icon: (
      <svg className="h-5 w-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.324.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.26 1.431l-1.003.827c-.293.24-.438.613-.431.992a6.759 6.759 0 010 .255c-.007.378.138.75.43.99l1.005.828c.424.35.534.954.26 1.43l-1.298 2.247a1.125 1.125 0 01-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.57 6.57 0 01-.22.128c-.331.183-.581.495-.644.869l-.213 1.28c-.09.543-.56.941-1.11.941h-2.594c-.55 0-1.02-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 01-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 01-1.369-.49l-1.297-2.247a1.125 1.125 0 01.26-1.431l1.004-.827c.292-.24.437-.613.43-.992a6.932 6.932 0 010-.255c.007-.378-.138-.75-.43-.99l-1.004-.828a1.125 1.125 0 01-.26-1.43l1.297-2.247a1.125 1.125 0 011.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.087.22-.128.332-.183.582-.495.644-.869l.214-1.281z" />
        <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
    ),
  },
];

const breadcrumbLabels: Record<string, string> = {
  "/app": "Dashboard",
  "/vault": "Vault",
  "/memory": "Memory",
  "/profile": "Profile",
  "/settings": "Settings",
};

export default function DashboardShell({ children }: DashboardShellProps) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [photoFailed, setPhotoFailed] = useState(false);

  const prevUserIdRef = useRef(user?.id);
  if (prevUserIdRef.current !== user?.id) {
    prevUserIdRef.current = user?.id;
    if (photoFailed) setPhotoFailed(false);
  }

  const initials = (user?.full_name || user?.username || "?")
    .charAt(0)
    .toUpperCase();

  const breadcrumbLabel = breadcrumbLabels[pathname] || "Cortex";

  return (
    <div className="min-h-screen flex bg-bg">
      {/* ── Sidebar ─────────────────────────────────────────────── */}
      <aside
        className={`fixed left-0 top-0 z-30 h-full flex flex-col border-r border-border bg-bg-surface transition-all duration-200 ${
          sidebarOpen ? "w-56" : "w-0 border-r-0"
        }`}
      >
        <div className="h-14 shrink-0 flex items-center px-4 border-b border-border">
          <div className="flex items-center gap-2">
            <div className="h-1.5 w-1.5 rounded-full bg-accent shadow-[0_0_8px_rgba(6,182,212,0.4)]" />
            <span className="font-mono text-[11px] tracking-[0.2em] uppercase text-text-secondary">
              Cortex
            </span>
          </div>
        </div>

        <nav className="flex-1 overflow-y-auto p-3 space-y-1">
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            return (
              <button
                key={item.href}
                onClick={() => router.push(item.href)}
                className={`nav-item w-full text-left ${isActive ? "active" : ""}`}
              >
                {item.icon}
                <span className={sidebarOpen ? "" : "hidden"}>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </aside>

      {/* ── Main area ───────────────────────────────────────────── */}
      <div className={`flex-1 flex flex-col min-h-screen transition-all duration-200 ${sidebarOpen ? "ml-56" : "ml-0"}`}>
        {/* ── Header ────────────────────────────────────────────── */}
        <header className="glass-panel h-14 flex items-center justify-between px-5 shrink-0 sticky top-0 z-20">
          {/* Left: Hamburger + Brand */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen((v) => !v)}
              className="h-8 w-8 rounded-lg flex items-center justify-center text-text-secondary hover:bg-bg-hover hover:text-text transition-colors"
              aria-label="Toggle sidebar"
            >
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
              </svg>
            </button>
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

          {/* Center: Breadcrumb */}
          <div className="flex items-center gap-2 text-sm">
            <span className="text-text-muted">/</span>
            <span className="text-text-secondary font-medium">{breadcrumbLabel}</span>
          </div>

          {/* Right: Avatar */}
          <div className="relative">
            <button
              onClick={() => setMenuOpen((v) => !v)}
              className="h-8 w-8 rounded-full bg-bg-elevated border border-border
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
            {menuOpen && (
              <>
                <div
                  className="fixed inset-0 z-40"
                  onClick={() => setMenuOpen(false)}
                />
                <div className="absolute right-0 top-full mt-1.5 z-50 w-44 rounded-lg bg-bg-elevated border border-border shadow-lg py-1 animate-fade-in">
                  <div className="px-3 py-2 border-b border-border">
                    <p className="text-sm font-medium text-text truncate">
                      {user?.full_name || user?.username}
                    </p>
                    <p className="text-[11px] text-text-muted truncate">
                      @{user?.username}
                    </p>
                  </div>
                  <button
                    onClick={() => {
                      setMenuOpen(false);
                      router.push("/app");
                    }}
                    className="w-full text-left px-3 py-2 text-sm text-text-secondary hover:bg-bg-hover hover:text-text transition-colors"
                  >
                    Dashboard
                  </button>
                  {user?.role === "admin" && (
                    <button
                      onClick={() => {
                        setMenuOpen(false);
                        router.push("/admin");
                      }}
                      className="w-full text-left px-3 py-2 text-sm text-text-secondary hover:bg-bg-hover hover:text-text transition-colors flex items-center gap-2"
                    >
                      <svg className="h-3.5 w-3.5 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
                      </svg>
                      Admin
                    </button>
                  )}
                  <button
                    onClick={() => {
                      setMenuOpen(false);
                      router.push("/profile");
                    }}
                    className="w-full text-left px-3 py-2 text-sm text-text-secondary hover:bg-bg-hover hover:text-text transition-colors"
                  >
                    Profile
                  </button>
                  <button
                    onClick={() => {
                      setMenuOpen(false);
                      router.push("/vault");
                    }}
                    className="w-full text-left px-3 py-2 text-sm text-text-secondary hover:bg-bg-hover hover:text-text transition-colors"
                  >
                    Vault
                  </button>
                  <button
                    onClick={() => {
                      setMenuOpen(false);
                      router.push("/memory");
                    }}
                    className="w-full text-left px-3 py-2 text-sm text-text-secondary hover:bg-bg-hover hover:text-text transition-colors"
                  >
                    Memory
                  </button>
                  <button
                    onClick={() => {
                      setMenuOpen(false);
                      router.push("/settings");
                    }}
                    className="w-full text-left px-3 py-2 text-sm text-text-secondary hover:bg-bg-hover hover:text-text transition-colors"
                  >
                    Settings
                  </button>
                  <button
                    onClick={() => {
                      setMenuOpen(false);
                      logout();
                    }}
                    className="w-full text-left px-3 py-2 text-sm text-text-secondary hover:bg-bg-hover hover:text-text transition-colors"
                  >
                    Sign out
                  </button>
                </div>
              </>
            )}
          </div>
        </header>

        {/* ── Main content ─────────────────────────────────────── */}
        <main className="flex-1 p-6">
          {children}
        </main>
      </div>
    </div>
  );
}
