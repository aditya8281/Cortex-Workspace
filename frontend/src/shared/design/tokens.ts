/**
 * Cortex Design Tokens — Neural Dark
 * Monochrome dark canvas with electric cyan pulse.
 */

const tokens = {
  colors: {
    // Backgrounds
    void: "#000000",
    bg: "#000000",
    "bg-elevated": "#040406",
    "bg-surface": "#0a0a0f",
    "bg-hover": "#111118",

    // Borders
    "border-subtle": "rgba(255,255,255,0.06)",
    border: "rgba(255,255,255,0.10)",
    "border-accent": "rgba(6,182,212,0.3)",

    // Text
    text: "#f0f0f5",
    "text-secondary": "#8a8a9a",
    "text-muted": "#555566",

    // Accent — the pulse
    accent: "#06b6d4",
    "accent-hover": "#22d3ee",
    "accent-muted": "rgba(6,182,212,0.12)",
    "accent-faint": "rgba(6,182,212,0.06)",
    "accent-glow": "rgba(6,182,212,0.15)",

    // Semantic
    error: "#ef4444",
    "error-muted": "rgba(239,68,68,0.12)",
    success: "#22c55e",
    "success-muted": "rgba(34,197,94,0.12)",
    warning: "#f59e0b",
    "warning-muted": "rgba(245,158,11,0.12)",
  } as Record<string, string>,

  fontFamily: {
    sans: ["var(--font-inter)", "system-ui", "sans-serif"],
    mono: ["var(--font-jetbrains-mono)", "monospace"],
    display: ["var(--font-geist)", "var(--font-inter)", "system-ui", "sans-serif"],
  } as Record<string, string[]>,

  borderRadius: {
    sm: "6px",
    md: "8px",
    lg: "12px",
    xl: "16px",
    "2xl": "20px",
    full: "9999px",
  } as Record<string, string>,

  boxShadow: {
    subtle: "0 1px 2px rgba(0,0,0,0.4)",
    card: "0 2px 8px rgba(0,0,0,0.4), 0 0 0 1px rgba(255,255,255,0.04)",
    elevated: "0 4px 16px rgba(0,0,0,0.5), 0 0 0 1px rgba(255,255,255,0.05)",
    glow: "0 0 20px rgba(6,182,212,0.12)",
    "glow-strong": "0 0 40px rgba(6,182,212,0.2)",
    modal: "0 8px 32px rgba(0,0,0,0.6), 0 0 0 1px rgba(255,255,255,0.05)",
  } as Record<string, string>,

  maxWidth: {
    content: "1200px",
    narrow: "640px",
  } as Record<string, string>,
};

export default tokens;
