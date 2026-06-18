/**
 * Dashboard shell — Post-auth layout with header.
 * Header: CORTEX branding (left), avatar menu (right).
 */
"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../auth/AuthProvider";
import { getProfilePhotoUrl } from "../auth/cortexApi";

export default function DashboardShell({ children }) {
  const router = useRouter();
  const { user, logout } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  const [photoFailed, setPhotoFailed] = useState(false);

  // Reset photoFailed when user changes (e.g. logout/login different user)
  useEffect(() => setPhotoFailed(false), [user?.id]);

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
                       hover:border-accent/30 transition-colors overflow-hidden"
          >
            {user?.profile_photo && user?.id && !photoFailed ? (
              <img
                src={getProfilePhotoUrl(user.id)}
                alt=""
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

      {/* ── Main content ───────────────────────────────────────── */}
      <main className="flex-1 p-6">
        {children}
      </main>
    </div>
  );
}
