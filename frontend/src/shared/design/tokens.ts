export const cortexTokens = {
  colors: {
    cortex: {
      bg: "#070B14",
      "bg-secondary": "#0B1220",
      surface: "rgba(0, 10, 44, 0.74)",
      "surface-elevated": "rgba(143, 83, 192, 0.64)",
      "modal-surface": "rgba(143, 83, 192, 0.64)",
      border: "rgba(143, 83, 192, 0.64)",
      cyan: "#26C6D6",
      "cyan-strong": "#13B1C0",
      green: "#2ECC7A",
      warning: "#F6C85F",
      error: "#FF6B6B",
      text: "#E6EDF3",
      // slightly lighter muted text for improved contrast on dark surfaces
      "text-muted": "#97A9BF",
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
    "cortex-cyan": "0 0 0 1px rgba(38,198,214,0.08), 0 0 18px rgba(38,198,214,0.12)",
    "cortex-green": "0 0 0 1px rgba(46,204,122,0.08), 0 0 18px rgba(46,204,122,0.1)",
  },
  zIndex: {
    modal: 900,
    toast: 850,
    dropdown: 800,
    header: 700,
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