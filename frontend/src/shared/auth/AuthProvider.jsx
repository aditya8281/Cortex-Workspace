"use client";

import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import * as cortexApi from "./cortexApi";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const router = useRouter();
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);

  // token provider for API modules
  const getToken = useCallback(() => token, [token]);

  const onAuthError = useCallback(() => {
    // clear locally and across tabs
    setUser(null);
    setToken(null);
    try { window.sessionStorage.removeItem("cortex_session_token"); window.sessionStorage.removeItem("cortex_session_user"); } catch (e) {}
    // navigate to auth
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
      const storedToken = typeof window !== "undefined" ? window.sessionStorage.getItem("cortex_session_token") : null;
      const storedUser = typeof window !== "undefined" ? JSON.parse(window.sessionStorage.getItem("cortex_session_user") || "null") : null;
      if (storedToken && storedUser) {
        setToken(storedToken);
        setUser(storedUser);
        // verify token with backend
        try {
          const me = await cortexApi.apiGetMe();
          setUser(me);
          window.sessionStorage.setItem("cortex_session_user", JSON.stringify(me));
        } catch (e) {
          // invalid token
          setToken(null);
          setUser(null);
          window.sessionStorage.removeItem("cortex_session_token");
          window.sessionStorage.removeItem("cortex_session_user");
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
    // cross-tab sync
    function onStorage(e) {
      if (e.key === "cortex_session_token") {
        if (!e.newValue) {
          // logged out elsewhere
          setUser(null); setToken(null);
          router.replace("/auth");
        } else {
          // token changed elsewhere, bootstrap
          bootstrapAuth();
        }
      }
    }
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, [bootstrapAuth, router]);

  const login = useCallback(async (tokenValue, userValue) => {
    // tokenValue and userValue can be obtained from server response
    setToken(tokenValue);
    setUser(userValue);
    try { window.sessionStorage.setItem("cortex_session_token", tokenValue); window.sessionStorage.setItem("cortex_session_user", JSON.stringify(userValue)); } catch (e) {}
    return true;
  }, []);

  const logout = useCallback(() => {
    setUser(null); setToken(null);
    try { window.sessionStorage.removeItem("cortex_session_token"); window.sessionStorage.removeItem("cortex_session_user"); } catch (e) {}
    router.replace("/auth");
  }, [router]);

  return (
    <AuthContext.Provider value={{ user, token, loading, login, logout, bootstrapAuth }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

export default AuthProvider;
