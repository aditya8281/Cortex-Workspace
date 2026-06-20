/**
 * Shared backend URL resolution.
 * Used by the Next.js API proxy and any other server-side code that needs
 * to know where the FastAPI backend is running.
 *
 * Priority:
 *   1. CORTEX_BACKEND_URL (written by start.sh to frontend/.env.local)
 *   2. NEXT_PUBLIC_API_BASE_URL (manual override)
 *   3. http://localhost:8000 (fallback)
 */

export function getBackendBase(): string {
  const env = process.env.CORTEX_BACKEND_URL || process.env.NEXT_PUBLIC_API_BASE_URL;
  if (env && /^https?:\/\//.test(env)) return env.replace(/\/api\/v1\/?$/, "").replace(/\/$/, "");
  return "http://localhost:8000";
}
