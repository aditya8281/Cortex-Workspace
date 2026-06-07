"use client";

import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import * as cortexApi from "./cortexApi";
import { clearSession, getSessionToken, getSessionUser, setSession } from "./session";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const router = useRouter();
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);

  // token provider for API modules
  const getToken = useCallback(() => token, [token]);

  const onAuthError = useCallback(() => {
    setUser(null);
    setToken(null);
    clearSession();
    router.replace("/auth");
  }, [router]);

  useEffect(() => {
    // wire token provider
    cortexApi.setTokenProvider(getToken);
    cortexApi.setAuthErrorHandler(onAuthError);
  }, [getToken, onAuthError]);

  // bootstrap auth from sessionStorage or backend
  const bootstrapAuth = useCallback(async () => {
    setLoading(true);
    try {
      const storedToken = getSessionToken();
      const storedUser = getSessionUser();
      if (storedToken) {
        setToken(storedToken);
        if (storedUser) setUser(storedUser);
        try {
          const me = await cortexApi.apiGetMe();
          setUser(me);
          setSession(storedToken, me);
        } catch (e) {
          setToken(null);
          setUser(null);
          clearSession();
        }
      }
    } catch (e) {
      setUser(null);
      setToken(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    bootstrapAuth();

    function onStorage(e) {
      if (e.key !== "cortex_session_token" && e.key !== "cortex_session_user") {
        return;
      }

      if (!e.newValue && e.key === "cortex_session_token") {
        setUser(null);
        setToken(null);
        router.replace("/auth");
        return;
      }

      bootstrapAuth();
    }

    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, [bootstrapAuth, router]);

  const login = useCallback(async (tokenValue, userValue) => {
    setToken(tokenValue);
    setUser(userValue);
    setSession(tokenValue, userValue);
    return true;
  }, []);

  const updateUser = useCallback((nextUser) => {
    setUser((current) => {
      const resolved = typeof nextUser === "function" ? nextUser(current) : { ...(current || {}), ...(nextUser || {}) };
      setSession(token, resolved);
      return resolved;
    });
  }, [token]);

  const logout = useCallback(() => {
    setUser(null);
    setToken(null);
    clearSession();
    router.replace("/auth");
  }, [router]);

  return <AuthContext.Provider value={{ user, token, loading, login, logout, bootstrapAuth, updateUser }}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

export default AuthProvider;
