"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "../auth/AuthProvider";
import { apiGetProfilePhotoUrl } from "../auth/cortexApi";

const adminRoutes = ["/models", "/vitals"];

function HeaderAvatarMenu({ sessionUser }) {
  const router = useRouter();

  function handleOpenProfile(e) {
    try {
      const btn = e.currentTarget.querySelector(".cortex-header-avatar");
      if (btn) {
        import("../ui/avatarTransition").then(({ getElementRect, saveAvatarRect }) => {
          try {
            saveAvatarRect(getElementRect(btn));
          } catch (error) {}
          router.push("/profile");
        });
        return;
      }
    } catch (error) {}

    router.push("/profile");
  }

  const name = sessionUser?.full_name || sessionUser?.username || "?";
  const initial = (name || "").toString().trim().split(" ")[0].charAt(0).toUpperCase() || "?";

  return (
    <button
      type="button"
      aria-label="Open profile"
      onClick={handleOpenProfile}
      className="flex items-center gap-2 rounded-full p-1 hover:bg-cortex-bg focus:outline-none"
    >
      <div className="cortex-header-avatar flex h-9 w-9 items-center justify-center overflow-hidden rounded-full border border-cortex-border bg-cortex-bg-secondary text-cortex-text">
        {sessionUser?.profile_photo ? (
          <img
            src={apiGetProfilePhotoUrl()}
            alt={`${name}'s avatar`}
            className="h-full w-full rounded-full object-cover"
          />
        ) : (
          <span className="font-medium">{initial}</span>
        )}
      </div>
    </button>
  );
}

export function AppShell({ children }) {
  const pathname = usePathname();
  const router = useRouter();
  const [ready, setReady] = useState(false);
  const { user: sessionUser, loading } = useAuth();
  const authRoute = pathname === "/auth";
  const bootRoute = pathname === "/boot";
  const admin = sessionUser?.role === "admin";

  useEffect(() => {
    if (authRoute || bootRoute) {
      setReady(true);
      return;
    }

    if (loading) {
      setReady(false);
      return;
    }

    if (!sessionUser && pathname === "/") {
      router.replace("/boot");
      return;
    }

    if (!sessionUser) {
      router.replace("/auth");
      return;
    }

    if (!admin && adminRoutes.some((route) => pathname === route || pathname.startsWith(`${route}/`))) {
      router.replace("/");
      return;
    }

    setReady(true);
  }, [admin, authRoute, bootRoute, loading, pathname, router, sessionUser]);

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
          <div className="flex h-full items-center justify-end gap-cortex-16 px-cortex-16 lg:px-cortex-24">
            <HeaderAvatarMenu sessionUser={sessionUser} />
          </div>
        </header>

        <main className="px-cortex-16 py-cortex-16 lg:px-cortex-24 lg:py-cortex-24">
          <div className="mx-auto w-full max-w-cortex">{children}</div>
        </main>
      </div>
    </div>
  );
}

export default AppShell;
