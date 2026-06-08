/**
 * Session — Low-level sessionStorage helpers for auth state.
 * AuthProvider is the single source of truth; don't use these directly from components.
 */

const TOKEN_KEY = "cortex_token";
const USER_KEY = "cortex_user";

export function getSessionToken() {
  if (typeof window === "undefined") return null;
  return sessionStorage.getItem(TOKEN_KEY);
}

export function getSessionUser() {
  if (typeof window === "undefined") return null;
  try {
    return JSON.parse(sessionStorage.getItem(USER_KEY));
  } catch {
    return null;
  }
}

export function setSession(token, user) {
  if (typeof window === "undefined") return;
  if (token) {
    sessionStorage.setItem(TOKEN_KEY, token);
  } else {
    sessionStorage.removeItem(TOKEN_KEY);
  }
  if (user !== undefined) {
    sessionStorage.setItem(USER_KEY, JSON.stringify(user || null));
  }
}

export function clearSession() {
  if (typeof window === "undefined") return;
  sessionStorage.removeItem(TOKEN_KEY);
  sessionStorage.removeItem(USER_KEY);
}
