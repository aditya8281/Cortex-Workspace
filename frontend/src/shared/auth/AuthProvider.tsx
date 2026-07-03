"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import type { User } from "@/shared/types";
import { getCsrfToken } from "@/shared/api/client";

interface AuthContextType {
  user: User | null;
  loading: boolean;
  logout: () => Promise<void>;
  setUser: (user: User | null) => void;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  loading: true,
  logout: async () => {},
  setUser: () => {},
});

export function useAuth() {
  return useContext(AuthContext);
}

/**
 * Bootstrap auth on mount using raw fetch (NOT apiFetch).
 * apiFetch redirects to /auth on 401, which creates an infinite loop
 * when the auth page itself calls this provider. Raw fetch lets us
 * distinguish "not logged in" from "error" without side effects.
 */
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function bootstrap() {
      try {
        let res = await fetch("/api/v1/auth/me", { credentials: "include" });

        // Access token expired — try refresh once, then retry /me
        if (res.status === 401) {
          const refreshRes = await fetch("/api/v1/auth/refresh", {
            method: "POST",
            credentials: "include",
          });
          if (refreshRes.ok) {
            res = await fetch("/api/v1/auth/me", { credentials: "include" });
          }
        }

        if (cancelled) return;

        if (res.ok) {
          const data = await res.json();
          setUser(data);
          // Fire background catalog refresh on login (fire-and-forget)
          fetch("/api/v1/models/refresh", {
            method: "POST",
            headers: { "X-CSRF-Token": getCsrfToken() },
            credentials: "include",
          }).catch(() => {});
        } else {
          setUser(null);
        }
      } catch {
        if (!cancelled) setUser(null);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    bootstrap();
    return () => { cancelled = true; };
  }, []);

  const logout = useCallback(async () => {
    try {
      await fetch("/api/v1/auth/logout", {
        method: "POST",
        credentials: "include",
      });
    } catch {
      // ignore
    }
    setUser(null);
    window.location.href = "/auth";
  }, []);

  const value = useMemo(
    () => ({ user, loading, logout, setUser }),
    [user, loading, logout],
  );

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}
