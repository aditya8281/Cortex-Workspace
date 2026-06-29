import type { NextConfig } from "next";

/** Backend port. Resolved from NEXT_PUBLIC_CORTEX_BACKEND_URL,
 *  then CORTEX_BACKEND_URL (legacy), then NEXT_PUBLIC_BACKEND_PORT,
 *  otherwise 8000. */
const _getBackendPort = (): string => {
  // Full backend URL — primary
  const full = process.env.NEXT_PUBLIC_CORTEX_BACKEND_URL || process.env.CORTEX_BACKEND_URL;
  if (full) {
    try { const p = new URL(full); if (p.port) return p.port; } catch { /* ignore */ }
  }
  // Explicit port override
  if (process.env.NEXT_PUBLIC_BACKEND_PORT) return process.env.NEXT_PUBLIC_BACKEND_PORT;
  return "8000";
};

const BACKEND_PORT = _getBackendPort();

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `http://localhost:${BACKEND_PORT}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;