"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { getSessionToken } from "../auth/session";

const navItems = [
  { label: "Dashboard", href: "/" },
  { label: "Chat", href: "/chat" },
  { label: "Memory", href: "/memory" },
  { label: "Knowledge Graph", href: "/knowledge-graph" },
  { label: "Models", href: "/models" },
  { label: "Marketplace", href: "/marketplace" },
  { label: "Vitals", href: "/vitals" },
  { label: "Profile", href: "/profile" },
  { label: "Vault", href: "/vault" },
];

function isActiveRoute(pathname, href) {
  if (href === "/") return pathname === "/";
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function AppShell({ children }) {
  const pathname = usePathname();
  const router = useRouter();
  const [ready, setReady] = useState(false);
  const authRoute = pathname === "/auth";
  const bootRoute = pathname === "/boot";

  useEffect(() => {
    if (typeof window === "undefined") return;

    const token = getSessionToken();
    if (!token && pathname === "/") {
      router.replace("/boot");
      return;
    }

    if (!authRoute && !bootRoute && !token) {
      router.replace("/auth");
      return;
    }

    if ((authRoute || bootRoute) && token) {
      router.replace("/");
      return;
    }

    setReady(true);
  }, [authRoute, bootRoute, pathname, router]);

  if (!ready && !authRoute && !bootRoute) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-cortex-bg text-cortex-text">
        <div className="rounded-cortex-lg border border-cortex-border bg-cortex-surface px-cortex-24 py-cortex-16 font-mono text-sm text-cortex-text-muted backdrop-blur-xl">
          Booting secure shell...
        </div>
      </div>
    );
  }

  if (authRoute || bootRoute) {
    return children;
  }

  return (
    <div className="min-h-screen bg-cortex-bg text-cortex-text">
      <div className="grid min-h-screen grid-cols-1 lg:grid-cols-[260px_minmax(0,1fr)]">
        <aside className="sticky top-0 hidden h-screen border-r border-cortex-border bg-cortex-bg-secondary/90 backdrop-blur-xl lg:flex lg:flex-col">
          <div className="flex h-[56px] items-center border-b border-cortex-border px-cortex-16">
            <div className="flex items-center gap-cortex-12">
              <div className="h-2.5 w-2.5 rounded-full bg-cortex-cyan shadow-cortex-cyan" />
              <div className="flex flex-col">
                <span className="font-mono text-xs tracking-[0.18em] text-cortex-cyan">CORTEX</span>
                <span className="text-xs text-cortex-text-muted">developer shell</span>
              </div>
            </div>
          </div>

          <nav className="flex flex-1 flex-col gap-cortex-8 p-cortex-16" aria-label="Primary">
            {navItems.map((item) => {
              const active = isActiveRoute(pathname, item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  aria-current={active ? "page" : undefined}
                  className={[
                    "cortex-nav-motion group flex h-10 items-center rounded-cortex border px-cortex-12 text-sm transition duration-cortex ease-cortex",
                    active
                      ? "border-cortex-cyan/30 bg-cortex-surface text-cortex-text shadow-cortex-cyan cortex-active-glow"
                      : "border-transparent text-cortex-text-muted hover:border-cortex-border hover:bg-cortex-surface hover:text-cortex-text",
                  ].join(" ")}
                >
                  <span
                    className={[
                      "mr-cortex-12 h-2 w-2 rounded-full transition duration-cortex ease-cortex",
                      active ? "bg-cortex-cyan shadow-cortex-cyan" : "bg-cortex-border group-hover:bg-cortex-cyan/60",
                    ].join(" ")}
                  />
                  <span className="font-medium">{item.label}</span>
                </Link>
              );
            })}
          </nav>

          <div className="border-t border-cortex-border p-cortex-16">
            <div className="rounded-cortex-lg border border-cortex-border bg-cortex-surface p-cortex-12 backdrop-blur-xl">
              <div className="mb-cortex-8 flex items-center justify-between">
                <span className="text-xs uppercase tracking-[0.12em] text-cortex-text-muted">System</span>
                <span className="rounded-cortex-pill border border-cortex-green/30 px-cortex-12 py-1 font-mono text-[11px] uppercase tracking-[0.12em] text-cortex-green shadow-cortex-green">
                  online
                </span>
              </div>
              <p className="text-xs leading-5 text-cortex-text-muted">
                Fixed rail for developer workflows, chat, models, and vault operations.
              </p>
            </div>
          </div>
        </aside>

        <div className="min-w-0">
          <header className="sticky top-0 z-20 h-[56px] border-b border-cortex-border bg-cortex-bg-secondary/80 backdrop-blur-xl">
            <div className="flex h-full items-center justify-between gap-cortex-16 px-cortex-16 lg:px-cortex-24">
              <div className="flex items-center gap-cortex-12">
                <span className="hidden rounded-cortex-pill border border-cortex-border px-cortex-12 py-1 font-mono text-[11px] uppercase tracking-[0.12em] text-cortex-text-muted sm:inline-flex">
                  system header
                </span>
                <span className="text-sm text-cortex-text-muted">VSCode shell with Linear-style density</span>
              </div>

              <div className="flex items-center gap-cortex-12">
                <span className="rounded-cortex-pill border border-cortex-cyan/30 bg-cortex-surface px-cortex-12 py-1 font-mono text-[11px] uppercase tracking-[0.12em] text-cortex-cyan shadow-cortex-cyan">
                  active
                </span>
                <span className="rounded-cortex-pill border border-cortex-border bg-cortex-surface px-cortex-12 py-1 font-mono text-[11px] uppercase tracking-[0.12em] text-cortex-text-muted">
                  {pathname}
                </span>
              </div>
            </div>
          </header>

          <main className="px-cortex-16 py-cortex-16 lg:px-cortex-24 lg:py-cortex-24">
            <div className="cortex-panel-motion mx-auto flex w-full max-w-cortex flex-col gap-cortex-16">{children}</div>
          </main>
        </div>
      </div>
    </div>
  );
}
