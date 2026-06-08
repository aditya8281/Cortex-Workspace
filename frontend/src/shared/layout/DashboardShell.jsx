/**
 * Dashboard shell — Post-auth layout with header.
 * Header: CORTEX branding (left), avatar menu (right).
 * Main content area is empty — to be built later.
 */
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../auth/AuthProvider";

export default function DashboardShell({ children }) {
  const router = useRouter();
  const { user, logout } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);

  const initials = (user?.full_name || user?.username || "?")
    .charAt(0)
    .toUpperCase();

  return (
    <div className="min-h-screen flex flex-col bg-bg">
      {/* ── Header ──────────────────────────────────────────────── */}
      <header className="h-14 border-b border-border flex items-center justify-between px-5 shrink-0">
        {/* Left: Brand */}
        <button
          onClick={() => router.push("/app")}
          className="flex items-center gap-2 group"
        >
          <div className="h-1.5 w-1.5 rounded-full bg-accent shadow-[0_0_8px_rgba(6,182,212,0.4)] group-hover:shadow-[0_0_12px_rgba(6,182,212,0.6)] transition-shadow" />
          <span className="font-mono text-[11px] tracking-[0.2em] uppercase text-text-secondary group-hover:text-text transition-colors">
            Cortex
          </span>
        </button>

        {/* Right: Avatar */}
        <div className="relative">
          <button
            onClick={() => setMenuOpen((v) => !v)}
            className="h-8 w-8 rounded-full bg-bg-elevated border border-border
                       flex items-center justify-center text-xs font-medium text-accent
                       hover:border-accent/30 transition-colors"
          >
            {user?.profile_photo ? (
              <img
                src={`${process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1"}/me/profile/photo`}
                alt=""
                className="h-full w-full rounded-full object-cover"
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

      {/* ── Main content (empty — to be built later) ─────────────── */}
      <main className="flex-1 p-6">
        {children}
      </main>
    </div>
  );
}
