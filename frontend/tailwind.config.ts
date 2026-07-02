import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontSize: {
        display: ["clamp(1.75rem, 3vw, 2.25rem)", { lineHeight: "1.2", fontWeight: "600" }],
        headline: ["1.25rem", { lineHeight: "1.75rem", fontWeight: "600" }],
        title: ["0.9375rem", { lineHeight: "1.25rem", fontWeight: "500" }],
        body: ["0.875rem", { lineHeight: "1.6" }],
        caption: ["0.75rem", { lineHeight: "1.4" }],
        mono: ["0.8125rem", { lineHeight: "1.5" }],
        xs: ["0.625rem", { lineHeight: "0.875rem", fontWeight: "600" }],
      },
      colors: {
        // Silk Red Accent
        "accent-red": {
          DEFAULT: "#d32f2f",
          bright: "#e53935",
          muted: "rgba(211, 47, 47, 0.20)",
          faint: "rgba(211, 47, 47, 0.08)",
          glow: "rgba(211, 47, 47, 0.18)",
        },
        // Cyan Neural Accent (backward compat: `accent` aliases)
        "accent-cyan": {
          DEFAULT: "#00acc1",
          bright: "#26c6da",
          muted: "rgba(0, 172, 193, 0.18)",
          faint: "rgba(0, 172, 193, 0.08)",
          glow: "rgba(0, 172, 193, 0.14)",
        },
        accent: {
          DEFAULT: "#00acc1",
          hover: "#26c6da",
          muted: "rgba(0, 172, 193, 0.18)",
          faint: "rgba(0, 172, 193, 0.08)",
          glow: "rgba(0, 172, 193, 0.14)",
        },
        // Neutral scale (warm-dark tonal layering)
        void: "#0d0d0d",
        "bg-base": "#0d0d0d",
        "bg-elevated": "#1c1c1c",
        "bg-surface": "#2a2a2a",
        "bg-hover": "#363636",
        "bg-glass": "rgba(26, 26, 26, 0.85)",
        "bg-widget": "rgba(26, 26, 26, 0.75)",
        // Text
        "text-primary": "#f0f0f0",
        "text-secondary": "#a0a0a0",
        "text-muted": "#7a7a7a",
        "text-inverse": "#0d0d0d",
        // Borders
        "border-subtle": "rgba(255, 255, 255, 0.06)",
        "border-default": "rgba(255, 255, 255, 0.12)",
        "border-accent": "rgba(0, 172, 193, 0.3)",
        "border-red": "rgba(211, 47, 47, 0.35)",
        "border-cyan": "rgba(0, 172, 193, 0.35)",
        "border-input-focus": "rgba(211, 47, 47, 0.40)",
        // Semantic
        danger: "#e74c3c",
        success: "#2ecc71",
        warning: "#f39c12",
      },
      fontFamily: {
        sans: ["var(--font-geist)", "system-ui", "sans-serif"],
        mono: ["var(--font-jetbrains-mono)", "JetBrains Mono", "monospace"],
      },
      borderRadius: {
        sm: "6px",
        md: "10px",
        lg: "16px",
        xl: "24px",
        full: "9999px",
      },
      zIndex: {
        base: "0",
        sidebar: "60",
        dock: "50",
        commandbar: "80",
        dropdown: "100",
        sticky: "200",
        "modal-backdrop": "300",
        modal: "400",
        toast: "500",
        tooltip: "600",
      },
      boxShadow: {
        subtle: "0 1px 2px rgba(0,0,0,0.4)",
        card: "0 2px 8px rgba(0,0,0,0.4), 0 0 0 1px rgba(255,255,255,0.04)",
        elevated: "0 4px 16px rgba(0,0,0,0.5), 0 0 0 1px rgba(255,255,255,0.05)",
        modal: "0 8px 32px rgba(0,0,0,0.6), 0 0 0 1px rgba(255,255,255,0.05)",
        "shadow-red": "0 0 24px rgba(211, 47, 47, 0.18)",
        "shadow-cyan": "0 0 24px rgba(0, 172, 193, 0.14)",
        "shadow-red-strong": "0 0 40px rgba(211, 47, 47, 0.25)",
        "shadow-cyan-strong": "0 0 40px rgba(0, 172, 193, 0.20)",
      },
      keyframes: {
        "progress-shimmer": {
          from: { backgroundPosition: "-200% 0" },
          to: { backgroundPosition: "200% 0" },
        },
        "fade-in": {
          from: { opacity: "0", transform: "translateY(6px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        "fade-in-scale": {
          from: { opacity: "0", transform: "scale(0.96)" },
          to: { opacity: "1", transform: "scale(1)" },
        },
        "slide-in-right": {
          from: { opacity: "0", transform: "translateX(12px)" },
          to: { opacity: "1", transform: "translateX(0)" },
        },
        "slide-in-up": {
          from: { opacity: "0", transform: "translateY(16px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        "slide-out-down": {
          from: { opacity: "1", transform: "translateY(0)" },
          to: { opacity: "0", transform: "translateY(8px)" },
        },
        "scale-in": {
          from: { opacity: "0", transform: "scale(0.92)" },
          to: { opacity: "1", transform: "scale(1)" },
        },
        "scale-out": {
          from: { opacity: "1", transform: "scale(1)" },
          to: { opacity: "0", transform: "scale(0.95)" },
        },
        "fade-out": {
          from: { opacity: "1" },
          to: { opacity: "0" },
        },
        "slide-in-from-right": {
          from: { opacity: "0", transform: "translateX(100%)" },
          to: { opacity: "1", transform: "translateX(0)" },
        },
        "slide-out-to-right": {
          from: { opacity: "1", transform: "translateX(0)" },
          to: { opacity: "0", transform: "translateX(100%)" },
        },
        shimmer: {
          from: { backgroundPosition: "-200% 0" },
          to: { backgroundPosition: "200% 0" },
        },
        "glow-pulse-red": {
          "0%, 100%": { boxShadow: "0 0 24px rgba(211, 47, 47, 0.18)" },
          "50%": { boxShadow: "0 0 40px rgba(211, 47, 47, 0.30)" },
        },
        "glow-pulse-cyan": {
          "0%, 100%": { boxShadow: "0 0 24px rgba(0, 172, 193, 0.14)" },
          "50%": { boxShadow: "0 0 40px rgba(0, 172, 193, 0.25)" },
        },
        "neural-drift": {
          "0%": { transform: "translate(0, 0)" },
          "25%": { transform: "translate(10px, -8px)" },
          "50%": { transform: "translate(-5px, 6px)" },
          "75%": { transform: "translate(8px, -4px)" },
          "100%": { transform: "translate(0, 0)" },
        },
        "data-flow": {
          from: { backgroundPosition: "-100% 0" },
          to: { backgroundPosition: "200% 0" },
        },
        shake: {
          "0%, 100%": { transform: "translateX(0)" },
          "10%": { transform: "translateX(-4px)" },
          "20%": { transform: "translateX(4px)" },
          "30%": { transform: "translateX(-4px)" },
          "40%": { transform: "translateX(4px)" },
          "50%": { transform: "translateX(-2px)" },
          "60%": { transform: "translateX(2px)" },
          "70%": { transform: "translateX(-2px)" },
          "80%": { transform: "translateX(2px)" },
        },
        "pulse-dot": {
          "0%, 100%": { opacity: "0.4" },
          "50%": { opacity: "1" },
        },
        "spin-slow": {
          from: { transform: "rotate(0deg)" },
          to: { transform: "rotate(360deg)" },
        },
      },
      animation: {
        "fade-in": "fade-in 0.2s cubic-bezier(0.16, 1, 0.3, 1)",
        "fade-in-slow": "fade-in 0.35s cubic-bezier(0.16, 1, 0.3, 1)",
        "fade-in-scale": "fade-in-scale 0.2s cubic-bezier(0.16, 1, 0.3, 1)",
        "slide-in-right": "slide-in-right 0.25s cubic-bezier(0.16, 1, 0.3, 1)",
        "slide-in-up": "slide-in-up 0.3s cubic-bezier(0.16, 1, 0.3, 1)",
        "slide-out-down": "slide-out-down 0.15s cubic-bezier(0.4, 0, 1, 1)",
        "scale-in": "scale-in 0.2s cubic-bezier(0.16, 1, 0.3, 1)",
        "scale-out": "scale-out 0.12s cubic-bezier(0.4, 0, 1, 1)",
        "fade-out": "fade-out 0.15s cubic-bezier(0.4, 0, 1, 1)",
        "slide-in-from-right": "slide-in-from-right 0.25s cubic-bezier(0.16, 1, 0.3, 1)",
        "slide-out-to-right": "slide-out-to-right 0.2s cubic-bezier(0.4, 0, 1, 1)",
        shimmer: "shimmer 2s linear infinite",
        "progress-shimmer": "progress-shimmer 2s linear infinite",
        "glow-pulse-red": "glow-pulse-red 2s ease-in-out infinite",
        "glow-pulse-cyan": "glow-pulse-cyan 2s ease-in-out infinite",
        "neural-drift": "neural-drift 8s ease-in-out infinite",
        "data-flow": "data-flow 3s linear infinite",
        shake: "shake 0.4s ease-in-out",
        "pulse-dot": "pulse-dot 1.5s ease-in-out infinite",
        "spin-slow": "spin-slow 3s linear infinite",
      },
    },
  },
  plugins: [],
};

export default config;
