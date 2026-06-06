"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { getSessionToken, getSessionUser, setSession, clearSession } from "../auth/session";
import { apiLogin } from "../auth/cortexApi";

const userNavItems = [
  { label: "Dashboard", href: "/" },
  { label: "Chat", href: "/chat" },
  { label: "Memory", href: "/memory" },
  { label: "Knowledge Graph", href: "/knowledge-graph" },
  { label: "Profile", href: "/profile" },
  { label: "Vault", href: "/vault" },
];

const adminNavItems = [
  { label: "Models", href: "/models" },
  { label: "Vitals", href: "/vitals" },
];

const adminRoutes = ["/models", "/vitals"];

  import { apiGetProfilePhotoUrl } from "../auth/cortexApi";

  function HeaderAvatarMenu({ sessionUser }) {
    const router = useRouter();

    function handleOpenProfile(e) {
      try {
        const btn = e.currentTarget.querySelector('.cortex-header-avatar');
        if (btn) {
          import('../ui/avatarTransition').then(({ getElementRect, saveAvatarRect }) => {
            try {
              const r = getElementRect(btn);
              saveAvatarRect(r);
            } catch (e) {}
            router.push('/profile');
          });
          return;
        }
      } catch (e) {}
      router.push('/profile');
    }

    // compute visible avatar: image when profile photo exists, otherwise single capital initial
    const AvatarInner = () => {
      const photo = sessionUser?.profile_photo;
      if (photo) {
        const src = apiGetProfilePhotoUrl();
        return (
          // image will be fetched with auth token via same-origin request
          <img src={src} alt={`${sessionUser?.full_name || sessionUser?.username}'s avatar`} className="h-9 w-9 rounded-full object-cover" />
        );
      }
      const name = sessionUser?.full_name || sessionUser?.username || "?";
      const first = (name || "").toString().trim().split(' ')[0].charAt(0).toUpperCase() || '?';
      return <span className="font-medium">{first}</span>;
    };

    return (
      <div className="relative">
        <button
          aria-label="Open profile"
          onClick={handleOpenProfile}
          className="flex items-center gap-2 rounded-full p-1 hover:bg-cortex-bg focus:outline-none"
        >
          <div className="cortex-header-avatar h-9 w-9 flex items-center justify-center rounded-full border border-cortex-border bg-cortex-bg-secondary text-cortex-text">
            <AvatarInner />
          </div>
        </button>
      </div>
    );
  }

function isActiveRoute(pathname, href) {
  if (href === "/") return pathname === "/";
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function AppShell({ children }) {
  const pathname = usePathname();
  const router = useRouter();
  const [ready, setReady] = useState(false);
  const [sessionUser, setSessionUser] = useState(null);
  const authRoute = pathname === "/auth";
  const bootRoute = pathname === "/boot";
  const token = typeof window !== "undefined" ? getSessionToken() : null;
  const isAdmin = sessionUser?.role === "admin";
  const navItems = isAdmin ? [...userNavItems, ...adminNavItems] : userNavItems;

  useEffect(() => {
    if (typeof window === "undefined") return;

    const token = getSessionToken();
    const user = getSessionUser();
    const admin = user?.role === "admin";
    setSessionUser(user);

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

    if (token && !admin && adminRoutes.some((route) => pathname === route || pathname.startsWith(`${route}/`))) {
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
      <div className="min-h-screen">
          <header className="sticky top-0 z-20 h-[56px] border-b border-cortex-border bg-cortex-bg-secondary/80 backdrop-blur-xl">
            <div className="flex h-full items-center justify-between gap-cortex-16 px-cortex-16 lg:px-cortex-24">

              <div className="flex items-center gap-cortex-12">
                {/* Top-right avatar only (header intentionally empty) */}
                <div className="relative">
                  <HeaderAvatarMenu sessionUser={sessionUser} />
                </div>
              </div>
            </div>
          </header>

          <main className="px-cortex-16 py-cortex-16 lg:px-cortex-24 lg:py-cortex-24">
            <div className="mx-auto w-full max-w-cortex">{children}</div>
          </main>
        </div>
      </div>
    // </div>
  );
}
