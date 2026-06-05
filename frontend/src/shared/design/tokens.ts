export const cortexTokens = {
  colors: {
    cortex: {
      bg: "#070B14",
      "bg-secondary": "#0B1220",
      surface: "rgba(255,255,255,0.04)",
      border: "rgba(255,255,255,0.08)",
      cyan: "#00F5FF",
      green: "#39FF88",
      warning: "#FBBF24",
      error: "#FF4D4D",
      text: "#E6EDF3",
      "text-muted": "#8B9BB3",
    },
  },
  spacing: {
    "cortex-4": "4px",
    "cortex-8": "8px",
    "cortex-12": "12px",
    "cortex-16": "16px",
    "cortex-24": "24px",
    "cortex-32": "32px",
    "cortex-48": "48px",
    "cortex-64": "64px",
    "cortex-sidebar": "260px",
    "cortex-topbar": "56px",
  },
  fontFamily: {
    sans: ["var(--font-inter)", "Inter", "sans-serif"],
    mono: ["var(--font-jetbrains-mono)", "JetBrains Mono", "monospace"],
  },
  fontSize: {
    xs: ["12px", { lineHeight: "16px" }],
    sm: ["14px", { lineHeight: "20px" }],
    base: ["16px", { lineHeight: "24px" }],
    lg: ["18px", { lineHeight: "28px" }],
    xl: ["20px", { lineHeight: "28px" }],
    "2xl": ["24px", { lineHeight: "32px" }],
    "3xl": ["30px", { lineHeight: "36px" }],
  },
  borderRadius: {
    cortex: "10px",
    "cortex-sm": "8px",
    "cortex-lg": "12px",
    "cortex-pill": "9999px",
  },
  boxShadow: {
    cortex: "0 0 0 1px rgba(255,255,255,0.08)",
    "cortex-cyan": "0 0 0 1px rgba(0,245,255,0.08), 0 0 18px rgba(0,245,255,0.12)",
    "cortex-green": "0 0 0 1px rgba(57,255,136,0.08), 0 0 18px rgba(57,255,136,0.1)",
  },
  maxWidth: {
    cortex: "1400px",
  },
  transitionDuration: {
    cortex: "180ms",
    "cortex-fast": "120ms",
    "cortex-slow": "300ms",
  },
  transitionTimingFunction: {
    cortex: "cubic-bezier(0.4, 0, 0.2, 1)",
  },
  screens: {
    cortex: "0px",
    sm: "640px",
    md: "768px",
    lg: "1024px",
    xl: "1280px",
    "2xl": "1536px",
  },
} as const;

export type CortexTokens = typeof cortexTokens;
