import type { Config } from "tailwindcss";
import { cortexTokens } from "./src/shared/design/tokens";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./app/**/*.{js,jsx,ts,tsx}",
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: cortexTokens.colors,
      spacing: cortexTokens.spacing,
      fontFamily: cortexTokens.fontFamily,
      fontSize: cortexTokens.fontSize,
      borderRadius: cortexTokens.borderRadius,
      boxShadow: cortexTokens.boxShadow,
      maxWidth: cortexTokens.maxWidth,
      transitionDuration: cortexTokens.transitionDuration,
      transitionTimingFunction: cortexTokens.transitionTimingFunction,
      screens: cortexTokens.screens,
      keyframes: {
        "cortex-fade-in": {
          "0%": { opacity: "0", transform: "translateY(4px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "cortex-slide-in": {
          "0%": { opacity: "0", transform: "translateX(-6px)" },
          "100%": { opacity: "1", transform: "translateX(0)" },
        },
        "cortex-glow-pulse": {
          "0%, 100%": { boxShadow: "0 0 0 0 rgba(0, 245, 255, 0)" },
          "50%": { boxShadow: "0 0 0 1px rgba(0, 245, 255, 0.16), 0 0 18px rgba(0, 245, 255, 0.12)" },
        },
        "cortex-processing": {
          "0%, 100%": { opacity: "0.72" },
          "50%": { opacity: "1" },
        },
      },
      animation: {
        "cortex-fade-in": "cortex-fade-in 180ms cubic-bezier(0.4, 0, 0.2, 1) both",
        "cortex-slide-in": "cortex-slide-in 180ms cubic-bezier(0.4, 0, 0.2, 1) both",
        "cortex-glow-pulse": "cortex-glow-pulse 2.4s cubic-bezier(0.4, 0, 0.2, 1) infinite",
        "cortex-processing": "cortex-processing 1.2s cubic-bezier(0.4, 0, 0.2, 1) infinite",
      },
    },
  },
  plugins: [],
};

export default config;
