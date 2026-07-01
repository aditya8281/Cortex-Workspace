"use client";

import { useAuth } from "@/shared/auth/AuthProvider";

// ── Component ─────────────────────────────────────────────────────────
export function HubGreeting() {
  const { user } = useAuth();
  const hour = new Date().getHours();
  const greeting =
    hour < 5 ? "Late night"
    : hour < 12 ? "Good morning"
    : hour < 17 ? "Good afternoon"
    : hour < 22 ? "Good evening"
    : "Late night";

  const tagline = hour < 6 || hour >= 22
    ? "Your cortex never sleeps — neither do your agents."
    : "Your machine intelligence layer — always aware, always ready.";

  return (
    <div className="mb-8 text-center">
      <h1 className="text-display font-semibold text-text-primary text-balance">
        {greeting}, {user?.username ?? "Cortex"}.
      </h1>
      <p className="mt-2 text-sm text-text-secondary text-balance max-w-md mx-auto">
        {tagline}
      </p>
    </div>
  );
}
