"use client";

/**
 * AuthProvider — React context for authentication state.
 * Wraps the app and provides user, login, logout to all children.
 * Auth tokens are stored in httpOnly cookies, not client-side.
 */

import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import { apiGetMe, apiLogout, apiVaultLock } from "./cortexApi";
import { getSessionUser, setSession, clearSession } from "./session";
import { toast } from "../ui/Toast";
import type { User } from "../types";

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  login: (userVal: User) => void;
  logout: () => void;
  updateUser: (userVal: User) => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  // Bootstrap: check auth with backend (cookies are sent automatically)
  useEffect(() => {
    let cancelled = false;
    async function bootstrap() {
      setLoading(true);
      const cached = getSessionUser();
      if (cached) setUser(cached);
      try {
        const me = await apiGetMe();
        if (!cancelled) {
          setUser(me);
          setSession(me);
        }
      } catch {
        if (!cancelled) {
          clearSession();
          setUser(null);
          const PROTECTED = ["/app", "/vault", "/settings", "/admin", "/memory", "/profile"];
          if (typeof window !== "undefined" && PROTECTED.some((p) => window.location.pathname.startsWith(p))) {
            window.location.replace("/auth");
          }
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    bootstrap();
    return () => { cancelled = true; };
  }, []);

  /** Login: set user in state and cache. Token is in httpOnly cookie. */
  const login = useCallback((userVal: User) => {
    setUser(userVal);
    setSession(userVal);
    toast.success("Signed in successfully");
  }, []);

  /** Update user data. */
  const updateUser = useCallback((userVal: User) => {
    setUser(userVal);
    setSession(userVal);
  }, []);

  /** Logout: call backend to revoke tokens and lock vault, then clear session. */
  const logout = useCallback(async () => {
    try {
      await apiVaultLock();
    } catch {
      // ignore
    }
    try {
      await apiLogout();
    } catch {
      // ignore — cookie may already be cleared
    }
    setUser(null);
    clearSession();
    toast.success("Signed out");
    router.replace("/auth");
  }, [router]);

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, updateUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
