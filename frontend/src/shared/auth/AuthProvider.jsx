"use client";

/**
 * AuthProvider — React context for authentication state.
 * Wraps the app and provides user, token, login, logout to all children.
 */

import { createContext, useContext, useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { setTokenProvider, apiGetMe } from "./cortexApi";
import {
  getSessionToken,
  getSessionUser,
  setSession,
  clearSession,
} from "./session";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const router = useRouter();
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);

  // Wire token provider so API calls include auth header
  const getToken = useCallback(() => token, [token]);
  useEffect(() => {
    setTokenProvider(getToken);
  }, [getToken]);

  // Bootstrap: read session, validate with backend
  useEffect(() => {
    let cancelled = false;
    async function bootstrap() {
      setLoading(true);
      const stored = getSessionToken();
      if (!stored) {
        setLoading(false);
        return;
      }
      setToken(stored);
      const cached = getSessionUser();
      if (cached) setUser(cached);
      try {
        const me = await apiGetMe();
        if (!cancelled) {
          setUser(me);
          setSession(stored, me);
        }
      } catch {
        if (!cancelled) {
          clearSession();
          setToken(null);
          setUser(null);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    bootstrap();
    return () => { cancelled = true; };
  }, []);

  /** Login: store token + user in state and sessionStorage. */
  const login = useCallback((tokenVal, userVal) => {
    setToken(tokenVal);
    setUser(userVal);
    setSession(tokenVal, userVal);
  }, []);

  /** Update user data without changing the token. */
  const updateUser = useCallback((userVal) => {
    setUser(userVal);
    setSession(token, userVal);
  }, [token]);

  /** Logout: clear everything and redirect to /auth. */
  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
    clearSession();
    router.replace("/auth");
  }, [router]);

  return (
    <AuthContext.Provider value={{ user, token, loading, login, logout, updateUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
