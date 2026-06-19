/**
 * Session — Low-level sessionStorage helpers for auth state.
 * AuthProvider is the single source of truth; don't use these directly from components.
 * Tokens are now stored in httpOnly cookies, not sessionStorage.
 */

import type { User } from "../types";

const USER_KEY = "cortex_user";

export function getSessionToken(): string | null {
  return null;
}

export function getSessionUser(): User | null {
  if (typeof window === "undefined") return null;
  try {
    return JSON.parse(sessionStorage.getItem(USER_KEY) ?? "null") as User | null;
  } catch {
    return null;
  }
}

export function setSession(user?: User | null): void {
  if (typeof window === "undefined") return;
  if (user !== undefined) {
    sessionStorage.setItem(USER_KEY, JSON.stringify(user ?? null));
  }
}

export function getSessionRefresh(): string | null {
  return null;
}

export function setSessionRefresh(_refreshToken: string | null): void {
  // No-op: refresh tokens are in httpOnly cookies
}

export function clearSession(): void {
  if (typeof window === "undefined") return;
  sessionStorage.removeItem(USER_KEY);
}
