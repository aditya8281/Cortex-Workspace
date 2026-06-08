/**
 * Root page — Landing page at /.
 * Redirects authenticated users to /app.
 */
"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { useAuth } from "../src/shared/auth/AuthProvider";

export default function RootPage() {
  const router = useRouter();
  const { user, loading } = useAuth();

  useEffect(() => {
    if (!loading && user) router.replace("/app");
  }, [user, loading, router]);

  if (loading) return null;

  return (
    <div className="min-h-screen flex flex-col">
      {/* ── Nav ─────────────────────────────────────────────────── */}
      <header className="flex items-center justify-between px-6 h-14 border-b border-border">
        <span className="font-mono text-xs tracking-widest text-text-secondary uppercase">
          Cortex
        </span>
        <button
          onClick={() => router.push("/auth")}
          className="text-sm text-text-secondary hover:text-text transition-colors"
        >
          Sign in
        </button>
      </header>

      {/* ── Hero ────────────────────────────────────────────────── */}
      <main className="flex-1 flex items-center justify-center px-6">
        <div className="max-w-xl text-center animate-fade-in">
          <div className="flex justify-center mb-6">
            <div className="h-2 w-2 rounded-full bg-accent shadow-[0_0_12px_rgba(6,182,212,0.4)]" />
          </div>

          <h1 className="text-4xl sm:text-5xl font-semibold tracking-tight text-text leading-tight">
            Your AI workspace,
            <br />
            <span className="text-accent">locally run.</span>
          </h1>

          <p className="mt-5 text-base text-text-secondary leading-relaxed max-w-md mx-auto">
            Cortex is a private, local-first platform for orchestrating AI models,
            managing memory, and building intelligent workflows — all on your machine.
          </p>

          <div className="mt-8 flex items-center justify-center gap-3">
            <button
              onClick={() => router.push("/auth")}
              className="h-11 px-6 rounded-lg bg-accent text-white text-sm font-medium
                         hover:bg-accent-hover active:scale-[0.98] transition-all shadow-glow"
            >
              Get started
            </button>
            <a
              href="https://github.com"
              target="_blank"
              rel="noreferrer"
              className="h-11 px-6 rounded-lg border border-border text-sm text-text-secondary
                         hover:bg-bg-hover hover:text-text transition-all inline-flex items-center"
            >
              View on GitHub
            </a>
          </div>
        </div>
      </main>

      {/* ── Footer ──────────────────────────────────────────────── */}
      <footer className="px-6 py-4 border-t border-border">
        <p className="text-center text-xs text-text-muted font-mono">
          Local-first · Private by default
        </p>
      </footer>
    </div>
  );
}
