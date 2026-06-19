/**
 * Cortex Design Tokens
 *
 * Dark cybernetic theme with cyan pulse accent.
 * All visual primitives in one place.
 */

const tokens = {
  colors: {
    bg: "#09090b",
    "bg-surface": "#131316",
    "bg-card": "#18181b",
    "bg-elevated": "#1f1f23",
    "bg-hover": "#27272a",
    "bg-glass": "rgba(24, 24, 27, 0.6)",

    border: "#27272a",
    "border-subtle": "#1f1f23",
    "border-accent": "rgba(6, 182, 212, 0.3)",

    text: "#fafafa",
    "text-secondary": "#a1a1aa",
    "text-muted": "#71717a",

    accent: "#06b6d4",
    "accent-hover": "#22d3ee",
    "accent-muted": "rgba(6, 182, 212, 0.12)",
    "accent-faint": "rgba(6, 182, 212, 0.06)",
    "accent-glow": "rgba(6, 182, 212, 0.15)",

    error: "#ef4444",
    "error-muted": "rgba(239, 68, 68, 0.12)",
    success: "#22c55e",
    "success-muted": "rgba(34, 197, 94, 0.12)",
    warning: "#f59e0b",
    "warning-muted": "rgba(245, 158, 11, 0.12)",
  } as Record<string, string>,

  fontFamily: {
    sans: ["var(--font-inter)", "system-ui", "sans-serif"],
    mono: ["var(--font-jetbrains-mono)", "monospace"],
  } as Record<string, string[]>,

  borderRadius: {
    sm: "6px",
    md: "8px",
    lg: "12px",
    xl: "16px",
    full: "9999px",
  } as Record<string, string>,

  boxShadow: {
    subtle: "0 1px 2px rgba(0,0,0,0.3)",
    card: "0 2px 8px rgba(0,0,0,0.3), 0 0 0 1px rgba(255,255,255,0.03)",
    elevated: "0 4px 16px rgba(0,0,0,0.4), 0 0 0 1px rgba(255,255,255,0.04)",
    glow: "0 0 20px rgba(6,182,212,0.1)",
    "glow-strong": "0 0 30px rgba(6,182,212,0.2)",
    modal: "0 8px 32px rgba(0,0,0,0.5), 0 0 0 1px rgba(255,255,255,0.04)",
  } as Record<string, string>,

  maxWidth: {
    content: "1120px",
    narrow: "640px",
  } as Record<string, string>,
};

export default tokens;
