// Design tokens reference — kept in sync with tailwind.config.ts and DESIGN.md
// Not directly imported at runtime; values come via Tailwind utility classes

export const tokens = {
  colors: {
    void: "#0d0d0d",
    "bg-base": "#0d0d0d",
    elevated: "#1c1c1c",
    surface: "#2a2a2a",
    hover: "#363636",
    "bg-glass": "rgba(26,26,26,0.85)",
    "bg-widget": "rgba(26,26,26,0.75)",
    "accent-red": {
      DEFAULT: "#d32f2f",
      bright: "#e53935",
      muted: "rgba(211,47,47,0.20)",
    },
    "accent-cyan": {
      DEFAULT: "#00acc1",
      bright: "#26c6da",
      muted: "rgba(0,172,193,0.18)",
    },
    border: {
      subtle: "rgba(255,255,255,0.06)",
      DEFAULT: "rgba(255,255,255,0.12)",
      red: "rgba(211,47,47,0.35)",
      cyan: "rgba(0,172,193,0.35)",
      "input-focus": "rgba(211,47,47,0.40)",
    },
    text: {
      DEFAULT: "#f0f0f0",
      secondary: "#a0a0a0",
      muted: "#7a7a7a",
      inverse: "#0d0d0d",
    },
    danger: "#e74c3c",
    success: "#2ecc71",
    warning: "#f39c12",
  },
  shadows: {
    subtle: "0 1px 2px rgba(0,0,0,0.4)",
    card: "0 2px 8px rgba(0,0,0,0.4), 0 0 0 1px rgba(255,255,255,0.04)",
    elevated: "0 4px 16px rgba(0,0,0,0.5), 0 0 0 1px rgba(255,255,255,0.05)",
    modal: "0 8px 32px rgba(0,0,0,0.6), 0 0 0 1px rgba(255,255,255,0.05)",
    "shadow-red": "0 0 24px rgba(211,47,47,0.18)",
    "shadow-cyan": "0 0 24px rgba(0,172,193,0.14)",
    "shadow-red-strong": "0 0 40px rgba(211,47,47,0.25)",
    "shadow-cyan-strong": "0 0 40px rgba(0,172,193,0.20)",
  },
} as const;
