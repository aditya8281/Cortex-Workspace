"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useGSAP } from "@gsap/react";
import gsap from "gsap";
import { SplitText } from "gsap/SplitText";
import { useAuth } from "@/shared/auth/AuthProvider";
import { apiFetch } from "@/shared/api/client";
import { cn } from "@/shared/lib/utils";

gsap.registerPlugin(useGSAP, SplitText);

export default function LoginPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [shakeKey, setShakeKey] = useState(0);
  const cardRef = useRef<HTMLDivElement>(null);

  // GSAP entrance + shake + SplitText heading reveal
  useGSAP(() => {
    if (!cardRef.current) return;
    const mm = gsap.matchMedia();
    mm.add("(prefers-reduced-motion: no-preference)", () => {
      // Entrance: scale + fade
      gsap.from(cardRef.current, { scale: 0.92, opacity: 0, duration: 0.4, ease: "power3.out" });

      // SplitText: "Welcome back" character reveal
      const heading = cardRef.current!.querySelector("h1");
      if (heading) {
        const split = new SplitText(heading, { type: "chars" });
        gsap.set(split.chars, { opacity: 0, y: 12 });
        gsap.to(split.chars, {
          y: 0,
          opacity: 1,
          duration: 0.35,
          stagger: { each: 0.03, from: "start" },
          ease: "power3.out",
          delay: 0.2,
          onComplete: () => split.revert(),
        });
      }
    });
    return () => mm.revert();
  }, { scope: cardRef });

  // GSAP shake on error (replaces CSS keyframe)
  useEffect(() => {
    if (!error || !cardRef.current) return;
    const mm = gsap.matchMedia();
    mm.add("(prefers-reduced-motion: no-preference)", () => {
      gsap.to(cardRef.current, {
        keyframes: [
          { x: -6, duration: 0.06 },
          { x: 6, duration: 0.06 },
          { x: -4, duration: 0.06 },
          { x: 4, duration: 0.06 },
          { x: -2, duration: 0.06 },
          { x: 2, duration: 0.06 },
          { x: 0, duration: 0.06 },
        ],
        ease: "power2.out",
      });
    });
    return () => mm.revert();
  }, [error, shakeKey]);

  // Already logged in
  useEffect(() => {
    if (!loading && user) router.replace("/");
  }, [user, loading, router]);

  if (loading || user) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await apiFetch("/auth/login", {
        method: "POST",
        body: { username, password },
      });
      // Full reload so AuthProvider re-mounts
      window.location.href = "/";
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
      setShakeKey((k) => k + 1); // trigger shake
    } finally {
      setSubmitting(false);
    }
  };

  const redFocusRing = "focus:border-accent-red/50 focus:outline-none focus:ring-1 focus:ring-accent-red/25";

  return (
    <div
      ref={cardRef}
      className={cn(
        "rounded-2xl border border-border-subtle p-6",
        "bg-bg-widget backdrop-blur-2xl",
      )}
    >
      {/* Header */}
      <div className="mb-6 text-center">
        <div className="mb-4 flex justify-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-accent-red-muted text-accent-red">
            <svg width="22" height="22" viewBox="0 0 16 16" fill="currentColor">
              <path d="M8 0L16 8L8 16L0 8L8 0Z" />
            </svg>
          </div>
        </div>
        <h1 className="text-headline font-semibold text-text-primary">Welcome back</h1>
        <p className="mt-1.5 text-sm text-text-secondary">Sign in to CORTEX</p>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-xs font-medium text-text-secondary mb-1.5">Username</label>
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            autoComplete="username"
            placeholder="your-name"
            className={cn(
              "w-full rounded-lg border border-border-default bg-bg-surface px-3 py-2 text-sm text-text-primary",
              "placeholder:text-text-muted",
              "motion-safe:transition-colors motion-safe:duration-200",
              redFocusRing,
              error && "border-accent-red/50",
            )}
          />
        </div>

        <div>
          <label className="block text-xs font-medium text-text-secondary mb-1.5">Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            autoComplete="current-password"
            placeholder="Enter your password"
            className={cn(
              "w-full rounded-lg border border-border-default bg-bg-surface px-3 py-2 text-sm text-text-primary",
              "placeholder:text-text-muted",
              "motion-safe:transition-colors motion-safe:duration-200",
              redFocusRing,
              error && "border-accent-red/50",
            )}
          />
        </div>

        {/* Error */}
        {error && (
          <div className="rounded-lg border border-accent-red/20 bg-accent-red/5 px-3 py-2">
            <p className="text-xs text-accent-red">{error}</p>
          </div>
        )}

        {/* Submit — silk red with pulse */}
        <button
          type="submit"
          disabled={submitting}
          className={cn(
            "w-full rounded-lg py-2 px-4 text-sm font-semibold text-white",
            "bg-accent-red shadow-red",
            "hover:bg-accent-red/90 motion-safe:transition-colors motion-safe:duration-200",
            "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-red",
            "disabled:opacity-50 disabled:cursor-not-allowed",
            "motion-safe:animate-glow-pulse-red",
          )}
        >
          {submitting ? (
            <span className="flex items-center justify-center gap-2">
              <span className="inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-white/30 border-t-white" />
              Signing in…
            </span>
          ) : (
            "Sign in"
          )}
        </button>
      </form>

      {/* Register link */}
      <div className="mt-5 pt-4 border-t border-border-subtle">
        <p className="text-center text-sm text-text-muted">
          No account?{" "}
          <Link
            href="/auth/register"
            className="text-accent-red hover:text-accent-red/80 font-medium motion-safe:transition-colors motion-safe:duration-150"
          >
            Create one
          </Link>
        </p>
      </div>
    </div>
  );
}
