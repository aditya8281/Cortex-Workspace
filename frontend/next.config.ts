import type { NextConfig } from "next";

/** Backend port. Read from NEXT_PUBLIC_BACKEND_PORT, then CORTEX_BACKEND_URL, otherwise 8000. */
const _getBackendPort = (): string => {
  if (process.env.NEXT_PUBLIC_BACKEND_PORT) return process.env.NEXT_PUBLIC_BACKEND_PORT;
  const url = process.env.CORTEX_BACKEND_URL;
  if (url) {
    try { const p = new URL(url); if (p.port) return p.port; } catch { /* ignore */ }
  }
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
