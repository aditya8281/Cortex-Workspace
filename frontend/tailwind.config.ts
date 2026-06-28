import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontSize: {
        headline: ["1.25rem", { lineHeight: "1.75rem", fontWeight: "600" }],
        title: ["0.9375rem", { lineHeight: "1.25rem", fontWeight: "600" }],
        body: ["0.875rem", { lineHeight: "1.25rem" }],
        label: ["0.75rem", { lineHeight: "1rem" }],
      },
      colors: {
        // Primary accent
        accent: {
          DEFAULT: "#0ea5c9",
          hover: "#38bdf8",
          muted: "rgba(14,165,201,0.25)",
          faint: "rgba(14,165,201,0.08)",
          glow: "rgba(14,165,201,0.12)",
        },
        // Neutral scale (tonal layering)
        void: "#0a0a0f",
        "bg-elevated": "#111118",
        "bg-surface": "#16161f",
        "bg-hover": "#1c1c28",
        // Borders
        "border-subtle": "rgba(255,255,255,0.08)",
        "border-default": "rgba(255,255,255,0.12)",
        "border-accent": "rgba(14,165,201,0.3)",
        // Text
        "text-primary": "#e8e8ed",
        "text-secondary": "#9a9aaa",
        "text-muted": "#7a7a8a",
        // Semantic
        danger: "#ef4444",
        success: "#22c55e",
        warning: "#f59e0b",
      },
      fontFamily: {
        sans: ["var(--font-geist)", "system-ui", "sans-serif"],
        mono: ["var(--font-jetbrains-mono)", "monospace"],
      },
      borderRadius: {
        sm: "6px",
        md: "8px",
        lg: "12px",
        xl: "16px",
      },
      boxShadow: {
        subtle: "0 1px 2px rgba(0,0,0,0.4)",
        card: "0 2px 8px rgba(0,0,0,0.4), 0 0 0 1px rgba(255,255,255,0.04)",
        elevated:
          "0 4px 16px rgba(0,0,0,0.5), 0 0 0 1px rgba(255,255,255,0.05)",
        modal:
          "0 8px 32px rgba(0,0,0,0.6), 0 0 0 1px rgba(255,255,255,0.05)",
        glow: "0 0 20px rgba(14,165,201,0.12)",
        "glow-strong": "0 0 40px rgba(14,165,201,0.2)",
      },
      keyframes: {
        "fade-in": {
          from: { opacity: "0", transform: "translateY(8px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        "fade-in-scale": {
          from: { opacity: "0", transform: "scale(0.95)" },
          to: { opacity: "1", transform: "scale(1)" },
        },
        shimmer: {
          from: { backgroundPosition: "-200% 0" },
          to: { backgroundPosition: "200% 0" },
        },
        "pulse-dot": {
          "0%, 100%": { opacity: "0.4" },
          "50%": { opacity: "1" },
        },
      },
      animation: {
        "fade-in": "fade-in 0.25s ease-out",
        "fade-in-scale": "fade-in-scale 0.25s ease-out",
        shimmer: "shimmer 2s linear infinite",
        "pulse-dot": "pulse-dot 1.5s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};

export default config;
