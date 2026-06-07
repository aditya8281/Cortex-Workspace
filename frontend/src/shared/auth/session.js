// Low-level session utilities. AuthContext is the single source of truth
const TOKEN_KEY = "cortex_session_token";
const USER_KEY = "cortex_session_user";

function safeParse(raw) {
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function getSessionToken() {
  if (typeof window === "undefined") return null;
  return window.sessionStorage.getItem(TOKEN_KEY);
}

export function getSessionUser() {
  if (typeof window === "undefined") return null;
  const raw = window.sessionStorage.getItem(USER_KEY);
  return safeParse(raw);
}

export function setSession(token, user) {
  if (typeof window === "undefined") return;
  try {
    if (token) {
      window.sessionStorage.setItem(TOKEN_KEY, token);
    } else {
      window.sessionStorage.removeItem(TOKEN_KEY);
    }
    if (user !== undefined) {
      window.sessionStorage.setItem(USER_KEY, JSON.stringify(user || null));
    }
  } catch (e) {}
}

export function clearSession() {
  if (typeof window === "undefined") return;
  try {
    window.sessionStorage.removeItem(TOKEN_KEY);
    window.sessionStorage.removeItem(USER_KEY);
  } catch (e) {}
}

export const _getRawToken = getSessionToken;
export const _getRawUser = getSessionUser;
export const _setRawSession = setSession;
export const _clearRawSession = clearSession;

// Note: Do not access these directly from application components — use AuthProvider/useAuth instead.

