"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Card, Loader, Badge } from "../../src/shared/ui";
import { getSessionToken } from "../../src/shared/auth/session";

const subtitles = [
  "I am the mind of the machine.",
  "Bootstrapping secure systems.",
  "Loading developer-grade intelligence.",
];

export default function BootPage() {
  const router = useRouter();
  const [index, setIndex] = useState(0);
  const subtitle = useMemo(() => subtitles[index % subtitles.length], [index]);

  useEffect(() => {
    if (getSessionToken()) {
      router.replace("/");
      return;
    }

    const subtitleTimer = window.setInterval(() => {
      setIndex((current) => current + 1);
    }, 900);

    const redirectTimer = window.setTimeout(() => {
      router.replace("/auth");
    }, 3200);

    return () => {
      window.clearInterval(subtitleTimer);
      window.clearTimeout(redirectTimer);
    };
  }, [router]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-cortex-bg px-cortex-16">
      <Card className="relative w-full max-w-[720px] overflow-hidden border-cortex-border bg-cortex-surface backdrop-blur-xl">
        <div className="absolute inset-0 opacity-60">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(0,245,255,0.08),transparent_45%)]" />
        </div>

        <div className="relative grid gap-cortex-16 p-cortex-32 text-center">
          <div className="flex justify-center">
            <div className="flex h-16 w-16 items-center justify-center rounded-full border border-cortex-cyan/30 bg-cortex-bg-secondary shadow-cortex-cyan">
              <div className="h-8 w-8 rounded-full border-2 border-cortex-cyan border-t-transparent animate-spin" />
            </div>
          </div>

          <div className="grid gap-cortex-8">
            <p className="font-mono text-xs uppercase tracking-[0.24em] text-cortex-cyan">CORTEX WORKSPACE</p>
            <h1 className="text-3xl font-medium text-cortex-text">System Initialising</h1>
            <p className="font-mono text-sm text-cortex-text-muted">{subtitle}</p>
          </div>

          <div className="grid gap-cortex-8">
            <div className="flex items-center justify-center gap-cortex-8">
              <Loader className="h-4 w-4" />
              <span className="font-mono text-xs uppercase tracking-[0.18em] text-cortex-text-muted">
                secure boot sequence active
              </span>
              <Badge variant="cyan">live</Badge>
            </div>
            <div className="h-1 overflow-hidden rounded-cortex bg-cortex-bg">
              <div
                className="h-full rounded-cortex bg-cortex-cyan transition-all duration-cortex"
                style={{ width: `${Math.min(100, (index + 1) * 35)}%` }}
              />
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}
