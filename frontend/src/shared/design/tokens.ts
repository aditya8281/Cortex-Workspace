export const tokens = {
  colors: {
    void: "#0a0a0f",
    elevated: "#111118",
    surface: "#16161f",
    hover: "#1c1c28",
    accent: {
      DEFAULT: "#0ea5c9",
      hover: "#38bdf8",
      muted: "rgba(14,165,201,0.25)",
      faint: "rgba(14,165,201,0.08)",
      glow: "rgba(14,165,201,0.12)",
    },
    border: {
      subtle: "rgba(255,255,255,0.08)",
      DEFAULT: "rgba(255,255,255,0.12)",
      accent: "rgba(14,165,201,0.3)",
    },
    text: {
      DEFAULT: "#e8e8ed",
      secondary: "#7a7a8a",
      muted: "#555566",
    },
    danger: "#ef4444",
    success: "#22c55e",
    warning: "#f59e0b",
  },
  shadows: {
    subtle: "0 1px 2px rgba(0,0,0,0.4)",
    card: "0 2px 8px rgba(0,0,0,0.4), 0 0 0 1px rgba(255,255,255,0.04)",
    elevated:
      "0 4px 16px rgba(0,0,0,0.5), 0 0 0 1px rgba(255,255,255,0.05)",
    modal:
      "0 8px 32px rgba(0,0,0,0.6), 0 0 0 1px rgba(255,255,255,0.05)",
    glow: "0 0 20px rgba(6,182,212,0.12)",
    "glow-strong": "0 0 40px rgba(6,182,212,0.2)",
  },
} as const;
