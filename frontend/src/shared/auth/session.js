// Low-level session utilities. AuthContext is the single source of truth
const TOKEN_KEY = "cortex_session_token";
const USER_KEY = "cortex_session_user";

export function _getRawToken() {
  if (typeof window === "undefined") return null;
  return window.sessionStorage.getItem(TOKEN_KEY);
}

export function _getRawUser() {
  if (typeof window === "undefined") return null;
  const raw = window.sessionStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function _setRawSession(token, user) {
  if (typeof window === "undefined") return;
  try { window.sessionStorage.setItem(TOKEN_KEY, token); window.sessionStorage.setItem(USER_KEY, JSON.stringify(user || null)); } catch (e) {}
}

export function _clearRawSession() {
  if (typeof window === "undefined") return;
  try { window.sessionStorage.removeItem(TOKEN_KEY); window.sessionStorage.removeItem(USER_KEY); } catch (e) {}
}

// Note: Do not access these directly from application components — use AuthProvider/useAuth instead.


