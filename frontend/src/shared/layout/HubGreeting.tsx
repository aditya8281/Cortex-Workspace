"use client";

import { useRef } from "react";
import { useAuth } from "@/shared/auth/AuthProvider";
import { useGSAP } from "@gsap/react";
import gsap from "gsap";
import { SplitText } from "gsap/SplitText";

gsap.registerPlugin(SplitText);

// ── Component ─────────────────────────────────────────────────────────
export function HubGreeting() {
  const { user } = useAuth();
  const containerRef = useRef<HTMLDivElement>(null);
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

  // SplitText character reveal on mount (and when greeting/username changes)
  useGSAP(() => {
    if (!containerRef.current) return;
    const mm = gsap.matchMedia();
    mm.add("(prefers-reduced-motion: no-preference)", () => {
      const h1 = containerRef.current!.querySelector("h1");
      if (!h1) return;

      const split = new SplitText(h1, { type: "chars" });

      gsap.fromTo(
        split.chars,
        { y: 20, opacity: 0 },
        {
          y: 0,
          opacity: 1,
          duration: 0.5,
          stagger: { each: 0.035, from: "start" },
          ease: "power3.out",
          onComplete: () => split.revert(),
        },
      );
    });
    return () => mm.revert();
  }, { scope: containerRef, dependencies: [greeting, user?.username] });

  return (
    <div ref={containerRef} className="mb-8 text-center">
      <h1 className="text-display font-semibold text-text-primary text-balance">
        {greeting}, {user?.username ?? "Cortex"}.
      </h1>
      <p className="mt-2 text-sm text-text-secondary text-balance max-w-md mx-auto">
        {tagline}
      </p>
    </div>
  );
}
