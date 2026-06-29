/** Backend WebSocket base URL. WS connects directly to FastAPI because Next.js
 *  rewrites don't proxy WebSocket upgrades. Port resolved from:
 *  1. NEXT_PUBLIC_CORTEX_BACKEND_URL (preferred — full URL, works in browser)
 *  2. NEXT_PUBLIC_BACKEND_PORT (just the port)
 *  3. Fallback to 8000
 */
export function getWsBaseUrl(): string {
  const getPort = (): string => {
    // Full backend URL — works in browser because NEXT_PUBLIC_ prefix
    const fullUrl = process.env.NEXT_PUBLIC_CORTEX_BACKEND_URL;
    if (fullUrl) {
      try {
        const parsed = new URL(fullUrl);
        if (parsed.port) return parsed.port;
      } catch { /* ignore */ }
    }
    // Explicit port override
    const port = process.env.NEXT_PUBLIC_BACKEND_PORT;
    if (port) return port;
    return "8000";
  };

  if (typeof window === "undefined") return `ws://localhost:${getPort()}`;
  return `ws://${window.location.hostname}:${getPort()}`;
}