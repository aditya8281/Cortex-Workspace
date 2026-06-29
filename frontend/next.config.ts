import type { NextConfig } from "next";

const DEFAULT_BACKEND_URL = "http://localhost:8000";
const userUrl = process.env.CORTEX_BACKEND_URL || DEFAULT_BACKEND_URL;

const nextConfig: NextConfig = {
  // Expose CORTEX_BACKEND_URL to browser code via NEXT_PUBLIC_ prefix.
  // User sets CORTEX_BACKEND_URL in .env.local; Next.js inlines
  // NEXT_PUBLIC_CORTEX_BACKEND_URL into the browser bundle at compile time.
  env: {
    NEXT_PUBLIC_CORTEX_BACKEND_URL: userUrl,
  },

  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${userUrl}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
