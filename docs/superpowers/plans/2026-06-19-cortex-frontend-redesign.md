# Cortex Frontend Redesign — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the entire Cortex frontend with a cinematic, AI-native "Neural Dark" interface featuring spring-physics animations, 3D effects, command palette, and a responsive adaptive layout.

**Architecture:** Next.js 15 App Router with framer-motion for animations, react-three-fiber for 3D landing hero, Radix UI primitives for accessible components, cmdk for command palette, and sonner for toasts. All built on a monochrome dark canvas with electric cyan accent.

**Tech Stack:** Next.js 15, React 19, TypeScript, Tailwind CSS 3.4, framer-motion, lucide-react, @radix-ui/react-dialog, @radix-ui/react-dropdown-menu, @radix-ui/react-tooltip, cmdk, sonner, three, @react-three/fiber, @react-three/drei, clsx, tailwind-merge

## Global Constraints

- Next.js 15.3+ with App Router (file-system routing)
- React 19.1+
- TypeScript 5.8+ strict mode
- Tailwind CSS 3.4 with custom design tokens
- Dark mode only (hardcoded `className="dark"`)
- All API contracts unchanged (cortexApi.ts preserved)
- Auth flow unchanged (httpOnly cookies, JWT)
- Must pass `npm run build`, `npm run lint`, `npm run test`
- Responsive: 375px / 768px / 1024px / 1440px
- `prefers-reduced-motion` support required

---

## Phase 1: Foundation

### Task 1: Install Dependencies & Configure Utilities

**Files:**
- Modify: `frontend/package.json`
- Create: `frontend/src/lib/utils.ts`
- Create: `frontend/src/lib/motion.ts`

**Interfaces:**
- Produces: `cn()` utility function, `motionVariants` constants

- [ ] **Step 1: Install all new dependencies**

Run from `frontend/`:
```bash
cd /home/adi/Desktop/Cortex-Workspace/frontend
npm install framer-motion lucide-react clsx tailwind-merge @radix-ui/react-dialog @radix-ui/react-dropdown-menu @radix-ui/react-tooltip cmdk sonner three @react-three/fiber @react-three/drei
npm install -D @types/three
```

- [ ] **Step 2: Create cn() utility**

Create `frontend/src/lib/utils.ts`:
```typescript
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

- [ ] **Step 3: Create motion variants**

Create `frontend/src/lib/motion.ts`:
```typescript
export const pageTransition = {
  initial: { opacity: 0, x: 20 },
  animate: { opacity: 1, x: 0 },
  exit: { opacity: 0, x: -20 },
  transition: { type: "spring", damping: 25, stiffness: 200 },
};

export const fadeUp = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  transition: { type: "spring", damping: 25, stiffness: 200 },
};

export const fadeIn = {
  initial: { opacity: 0 },
  animate: { opacity: 1 },
  transition: { duration: 0.3 },
};

export const scaleIn = {
  initial: { opacity: 0, scale: 0.95 },
  animate: { opacity: 1, scale: 1 },
  transition: { type: "spring", damping: 25, stiffness: 300 },
};

export const staggerContainer = {
  animate: {
    transition: {
      staggerChildren: 0.08,
    },
  },
};

export const staggerItem = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  transition: { type: "spring", damping: 25, stiffness: 200 },
};
```

- [ ] **Step 4: Verify build**

Run: `cd /home/adi/Desktop/Cortex-Workspace/frontend && npm run build`
Expected: Build succeeds

- [ ] **Step 5: Commit**

```bash
cd /home/adi/Desktop/Cortex-Workspace/frontend
git add package.json package-lock.json src/lib/
git commit -m "chore: install redesign dependencies and create utilities"
```

---

### Task 2: Update Design Tokens & Global Styles

**Files:**
- Modify: `frontend/src/shared/design/tokens.ts`
- Modify: `frontend/app/globals.css`
- Modify: `frontend/tailwind.config.ts`

**Interfaces:**
- Consumes: Nothing
- Produces: Updated token system, new CSS utility classes

- [ ] **Step 1: Update design tokens**

Replace `frontend/src/shared/design/tokens.ts` with:
```typescript
/**
 * Cortex Design Tokens — Neural Dark
 * Monochrome dark canvas with electric cyan pulse.
 */

const tokens = {
  colors: {
    // Backgrounds
    void: "#000000",
    bg: "#050508",
    "bg-elevated": "#0a0a0f",
    "bg-surface": "#111118",
    "bg-hover": "#1a1a24",

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
```

- [ ] **Step 2: Update Tailwind config**

Replace `frontend/tailwind.config.ts` with:
```typescript
import type { Config } from "tailwindcss";
import tokens from "./src/shared/design/tokens";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./app/**/*.{ts,tsx}",
    "./src/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: tokens.colors,
      fontFamily: tokens.fontFamily,
      borderRadius: tokens.borderRadius,
      boxShadow: tokens.boxShadow,
      maxWidth: tokens.maxWidth,
      keyframes: {
        "fade-in": {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "fade-in-up": {
          "0%": { opacity: "0", transform: "translateY(16px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "fade-in-scale": {
          "0%": { opacity: "0", transform: "scale(0.95)" },
          "100%": { opacity: "1", transform: "scale(1)" },
        },
        "slide-in-right": {
          "0%": { opacity: "0", transform: "translateX(12px)" },
          "100%": { opacity: "1", transform: "translateX(0)" },
        },
        "glow-pulse": {
          "0%, 100%": { boxShadow: "0 0 20px rgba(6,182,212,0.1)" },
          "50%": { boxShadow: "0 0 40px rgba(6,182,212,0.25)" },
        },
        "shimmer": {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        "float": {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-10px)" },
        },
      },
      animation: {
        "fade-in": "fade-in 300ms ease-out both",
        "fade-in-up": "fade-in-up 400ms ease-out both",
        "fade-in-scale": "fade-in-scale 300ms ease-out both",
        "slide-in-right": "slide-in-right 300ms ease-out both",
        "glow-pulse": "glow-pulse 3s ease-in-out infinite",
        "shimmer": "shimmer 2s linear infinite",
        "float": "float 6s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};

export default config;
```

- [ ] **Step 3: Update global CSS**

Replace `frontend/app/globals.css` with:
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  html {
    @apply bg-bg text-text scroll-smooth;
    color-scheme: dark;
  }

  body {
    @apply min-h-screen font-sans antialiased;
    background: linear-gradient(180deg, #050508 0%, #030306 100%);
  }

  code, pre, kbd {
    @apply font-mono;
  }

  ::selection {
    background: rgba(6, 182, 212, 0.3);
    color: #f0f0f5;
  }

  ::-webkit-scrollbar {
    width: 5px;
    height: 5px;
  }
  ::-webkit-scrollbar-track {
    background: transparent;
  }
  ::-webkit-scrollbar-thumb {
    background: rgba(138, 138, 154, 0.2);
    border-radius: 3px;
  }
  ::-webkit-scrollbar-thumb:hover {
    background: rgba(138, 138, 154, 0.4);
  }
}

@layer components {
  .glass-panel {
    background: rgba(10, 10, 15, 0.8);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(255, 255, 255, 0.06);
  }

  .glass-panel-strong {
    background: rgba(10, 10, 15, 0.92);
    backdrop-filter: blur(24px);
    -webkit-backdrop-filter: blur(24px);
    border: 1px solid rgba(255, 255, 255, 0.08);
  }

  .shimmer-bg {
    background: linear-gradient(
      90deg,
      rgba(17, 17, 24, 0.3) 25%,
      rgba(17, 17, 24, 0.6) 50%,
      rgba(17, 17, 24, 0.3) 75%
    );
    background-size: 200% 100%;
    animation: shimmer 2s linear infinite;
  }

  .text-gradient {
    background: linear-gradient(135deg, #f0f0f5 0%, #8a8a9a 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  .text-gradient-accent {
    background: linear-gradient(135deg, #06b6d4 0%, #22d3ee 50%, #06b6d4 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  .focus-ring {
    @apply outline-none ring-2 ring-accent/40 ring-offset-2 ring-offset-bg transition-all duration-200;
  }

  .interactive-card {
    @apply rounded-xl bg-bg-elevated border border-border-subtle shadow-card
           transition-all duration-300 ease-out;
  }
  .interactive-card:hover {
    @apply border-border-accent shadow-glow;
    transform: translateY(-2px);
  }
  .interactive-card:active {
    transform: translateY(0) scale(0.99);
  }

  .nav-item {
    @apply flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm
           text-text-secondary hover:bg-bg-hover hover:text-text
           transition-all duration-200 cursor-pointer;
  }
  .nav-item.active {
    @apply bg-accent-faint text-accent font-medium;
    box-shadow: inset 0 0 0 1px rgba(6,182,212,0.15);
  }

  .stat-card {
    @apply rounded-xl bg-bg-elevated border border-border-subtle p-5 shadow-card
           transition-all duration-300;
  }
  .stat-card:hover {
    @apply border-border-accent shadow-glow;
    transform: translateY(-1px);
  }

  .modal-overlay {
    @apply fixed inset-0 z-50 flex items-center justify-center
           bg-void/80 backdrop-blur-sm p-4;
  }

  .modal-content {
    @apply w-full rounded-2xl border border-border bg-bg-elevated p-6
           shadow-modal;
  }

  .page-header {
    @apply mb-8;
  }
  .page-header h1 {
    @apply text-2xl font-semibold text-text font-display tracking-tight;
  }
  .page-header p {
    @apply text-sm text-text-muted mt-1.5;
  }

  .btn-glow {
    position: relative;
    overflow: hidden;
  }
  .btn-glow::before {
    content: '';
    position: absolute;
    inset: -2px;
    background: linear-gradient(135deg, rgba(6,182,212,0.3), rgba(34,211,238,0.1));
    border-radius: inherit;
    opacity: 0;
    transition: opacity 0.3s;
    z-index: -1;
  }
  .btn-glow:hover::before {
    opacity: 1;
  }

  .micro-label {
    @apply font-mono text-[10px] tracking-[0.2em] uppercase text-text-muted;
  }
}

@layer utilities {
  .border-glow {
    box-shadow: 0 0 0 1px rgba(6,182,212,0.2), 0 0 20px rgba(6,182,212,0.08);
  }

  .perspective-1000 {
    perspective: 1000px;
  }
}
```

- [ ] **Step 4: Verify build**

Run: `cd /home/adi/Desktop/Cortex-Workspace/frontend && npm run build`
Expected: Build succeeds

- [ ] **Step 5: Commit**

```bash
cd /home/adi/Desktop/Cortex-Workspace/frontend
git add src/shared/design/tokens.ts tailwind.config.ts app/globals.css
git commit -m "feat: update design tokens and global styles for Neural Dark theme"
```

---

### Task 3: Update Root Layout with Geist Font

**Files:**
- Modify: `frontend/app/layout.tsx`

**Interfaces:**
- Consumes: tokens from Task 2
- Produces: Updated root layout with Geist font

- [ ] **Step 1: Update root layout**

Replace `frontend/app/layout.tsx` with:
```tsx
import { Inter, JetBrains_Mono } from "next/font/google";
import localFont from "next/font/local";
import "./globals.css";
import { AuthProvider } from "../src/shared/auth/AuthProvider";
import ErrorBoundary from "../src/shared/ui/ErrorBoundary";
import type { Metadata } from "next";
import type { ReactNode } from "react";

const geist = localFont({
  src: "./fonts/GeistVF.woff",
  variable: "--font-geist",
  display: "swap",
  fallback: ["system-ui", "sans-serif"],
});

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

const jetBrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains-mono",
});

export const metadata: Metadata = {
  title: "Cortex",
  description: "Your machine's intelligence layer",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body
        className={`${geist.variable} ${inter.variable} ${jetBrainsMono.variable} min-h-screen bg-bg text-text font-sans antialiased`}
      >
        <AuthProvider>
          <ErrorBoundary>{children}</ErrorBoundary>
        </AuthProvider>
      </body>
    </html>
  );
}
```

- [ ] **Step 2: Download Geist font**

Since Geist VF may not be available via next/font/local easily, use a simpler approach — use Geist from a CDN or fall back to Inter. Update the layout to handle missing Geist gracefully:

Replace the geist font config with:
```typescript
// Geist font — use Inter as fallback if Geist unavailable
const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

const jetBrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains-mono",
});
```

And update the body class to not reference `geist.variable` if Geist is not available. The key change is the metadata update and the `className="dark"` being properly set.

- [ ] **Step 3: Verify build**

Run: `cd /home/adi/Desktop/Cortex-Workspace/frontend && npm run build`
Expected: Build succeeds

- [ ] **Step 4: Commit**

```bash
cd /home/adi/Desktop/Cortex-Workspace/frontend
git add app/layout.tsx
git commit -m "feat: update root layout for Neural Dark theme"
```

---

## Phase 2: Core UI Components

### Task 4: Build New Button Component

**Files:**
- Modify: `frontend/src/shared/ui/Button.tsx`

**Interfaces:**
- Consumes: `cn()` from `src/lib/utils`
- Produces: `<Button>` component with primary/secondary/ghost/danger variants, sizes, loading state, glow effect

- [ ] **Step 1: Replace Button component**

Replace `frontend/src/shared/ui/Button.tsx` with:
```tsx
"use client";

import { forwardRef, type ButtonHTMLAttributes, type ReactNode } from "react";
import { cn } from "../../lib/utils";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost" | "danger";
  size?: "sm" | "md" | "lg";
  loading?: boolean;
  children: ReactNode;
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = "primary", size = "md", loading = false, className, children, disabled, ...props }, ref) => {
    const base =
      "inline-flex items-center justify-center gap-2 font-medium rounded-xl transition-all duration-200 cursor-pointer disabled:cursor-not-allowed disabled:opacity-40";

    const variants = {
      primary:
        "bg-accent text-void hover:bg-accent-hover active:scale-[0.97] shadow-glow hover:shadow-glow-strong",
      secondary:
        "bg-bg-surface text-text border border-border-subtle hover:border-border-accent hover:bg-bg-hover active:scale-[0.97]",
      ghost:
        "text-text-secondary hover:text-text hover:bg-bg-hover active:scale-[0.97]",
      danger:
        "bg-error/10 text-error border border-error/20 hover:bg-error/20 active:scale-[0.97]",
    };

    const sizes = {
      sm: "h-8 px-3 text-xs",
      md: "h-10 px-4 text-sm",
      lg: "h-12 px-6 text-sm",
    };

    return (
      <button
        ref={ref}
        className={cn(base, variants[variant], sizes[size], className)}
        disabled={disabled || loading}
        {...props}
      >
        {loading && (
          <svg
            className="h-4 w-4 animate-spin"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        )}
        {children}
      </button>
    );
  }
);

Button.displayName = "Button";
export default Button;
```

- [ ] **Step 2: Run Button test**

Run: `cd /home/adi/Desktop/Cortex-Workspace/frontend && npm run test -- --run src/shared/ui/Button.test.tsx`
Expected: Tests pass (update if needed for new variants)

- [ ] **Step 3: Verify build**

Run: `cd /home/adi/Desktop/Cortex-Workspace/frontend && npm run build`
Expected: Build succeeds

- [ ] **Step 4: Commit**

```bash
cd /home/adi/Desktop/Cortex-Workspace/frontend
git add src/shared/ui/Button.tsx
git commit -m "feat: redesign Button component for Neural Dark theme"
```

---

### Task 5: Build New Input Component

**Files:**
- Modify: `frontend/src/shared/ui/Input.tsx`

**Interfaces:**
- Consumes: `cn()` from `src/lib/utils`
- Produces: `<Input>` component with floating label, focus glow, error state, password toggle

- [ ] **Step 1: Replace Input component**

Replace `frontend/src/shared/ui/Input.tsx` with:
```tsx
"use client";

import { forwardRef, useState, type InputHTMLAttributes } from "react";
import { cn } from "../../lib/utils";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, className, type, ...props }, ref) => {
    const [showPassword, setShowPassword] = useState(false);
    const isPassword = type === "password";

    return (
      <div className="grid gap-1.5">
        {label && (
          <label className="text-xs font-medium text-text-secondary">
            {label}
          </label>
        )}
        <div className="relative">
          <input
            ref={ref}
            type={isPassword && showPassword ? "text" : type}
            className={cn(
              "w-full rounded-xl bg-bg-surface border border-border-subtle px-3.5 py-2.5 text-sm text-text",
              "placeholder:text-text-muted outline-none transition-all duration-200",
              "focus:border-accent/40 focus:ring-2 focus:ring-accent/10 focus:shadow-glow",
              error && "border-error/50 focus:border-error/50 focus:ring-error/10",
              isPassword && "pr-10",
              className
            )}
            {...props}
          />
          {isPassword && (
            <button
              type="button"
              onClick={() => setShowPassword((v) => !v)}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-secondary transition-colors p-1"
              tabIndex={-1}
            >
              {showPassword ? (
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88" />
                </svg>
              ) : (
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              )}
            </button>
          )}
        </div>
        {error && (
          <p className="text-xs text-error">{error}</p>
        )}
      </div>
    );
  }
);

Input.displayName = "Input";
export default Input;
```

- [ ] **Step 2: Verify build**

Run: `cd /home/adi/Desktop/Cortex-Workspace/frontend && npm run build`
Expected: Build succeeds

- [ ] **Step 3: Commit**

```bash
cd /home/adi/Desktop/Cortex-Workspace/frontend
git add src/shared/ui/Input.tsx
git commit -m "feat: redesign Input component for Neural Dark theme"
```

---

### Task 6: Build New Card, Badge, Skeleton, Tooltip, Modal, Dropdown, Toast Components

**Files:**
- Modify: `frontend/src/shared/ui/Card.tsx`
- Create: `frontend/src/shared/ui/Badge.tsx`
- Create: `frontend/src/shared/ui/Skeleton.tsx`
- Create: `frontend/src/shared/ui/Tooltip.tsx`
- Create: `frontend/src/shared/ui/Modal.tsx`
- Create: `frontend/src/shared/ui/Dropdown.tsx`
- Create: `frontend/src/shared/ui/Toast.tsx`
- Create: `frontend/src/lib/utils.ts` (already created in Task 1)

**Interfaces:**
- Consumes: `cn()` from `src/lib/utils`
- Produces: All reusable UI components

- [ ] **Step 1: Update Card component**

Replace `frontend/src/shared/ui/Card.tsx` with:
```tsx
"use client";

import { type HTMLAttributes, type ReactNode } from "react";
import { cn } from "../../lib/utils";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  hover?: boolean;
  glass?: boolean;
  children: ReactNode;
}

export default function Card({ hover, glass, className, children, ...props }: CardProps) {
  return (
    <div
      className={cn(
        "rounded-xl border border-border-subtle bg-bg-elevated shadow-card transition-all duration-300",
        glass && "glass-panel",
        hover && "hover:border-border-accent hover:shadow-glow hover:-translate-y-0.5 cursor-pointer active:translate-y-0 active:scale-[0.995]",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}
```

- [ ] **Step 2: Create Badge component**

Create `frontend/src/shared/ui/Badge.tsx`:
```tsx
import { type ReactNode } from "react";
import { cn } from "../../lib/utils";

interface BadgeProps {
  variant?: "default" | "accent" | "success" | "warning" | "danger";
  children: ReactNode;
  className?: string;
}

export default function Badge({ variant = "default", className, children }: BadgeProps) {
  const variants = {
    default: "bg-bg-surface text-text-secondary border-border-subtle",
    accent: "bg-accent-faint text-accent border-accent/20",
    success: "bg-success-muted text-success border-success/20",
    warning: "bg-warning-muted text-warning border-warning/20",
    danger: "bg-error-muted text-error border-error/20",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-[10px] font-mono font-medium uppercase tracking-wider border",
        variants[variant],
        className
      )}
    >
      {children}
    </span>
  );
}
```

- [ ] **Step 3: Create Skeleton component**

Create `frontend/src/shared/ui/Skeleton.tsx`:
```tsx
import { cn } from "../../lib/utils";

interface SkeletonProps {
  className?: string;
}

export default function Skeleton({ className }: SkeletonProps) {
  return (
    <div
      className={cn(
        "rounded-xl bg-bg-surface shimmer-bg",
        className
      )}
    />
  );
}
```

- [ ] **Step 4: Create Tooltip component**

Create `frontend/src/shared/ui/Tooltip.tsx`:
```tsx
"use client";

import * as TooltipPrimitive from "@radix-ui/react-tooltip";
import { type ReactNode } from "react";
import { cn } from "../../lib/utils";

interface TooltipProps {
  content: string;
  children: ReactNode;
  side?: "top" | "right" | "bottom" | "left";
}

export default function Tooltip({ content, children, side = "top" }: TooltipProps) {
  return (
    <TooltipPrimitive.Provider delayDuration={300}>
      <TooltipPrimitive.Root>
        <TooltipPrimitive.Trigger asChild>
          {children}
        </TooltipPrimitive.Trigger>
        <TooltipPrimitive.Portal>
          <TooltipPrimitive.Content
            side={side}
            sideOffset={6}
            className={cn(
              "z-50 rounded-lg bg-bg-elevated border border-border-subtle px-3 py-1.5",
              "text-xs text-text-secondary shadow-elevated",
              "animate-fade-in"
            )}
          >
            {content}
            <TooltipPrimitive.Arrow className="fill-bg-elevated" />
          </TooltipPrimitive.Content>
        </TooltipPrimitive.Portal>
      </TooltipPrimitive.Root>
    </TooltipPrimitive.Provider>
  );
}
```

- [ ] **Step 5: Create Modal component**

Create `frontend/src/shared/ui/Modal.tsx`:
```tsx
"use client";

import * as DialogPrimitive from "@radix-ui/react-dialog";
import { type ReactNode } from "react";
import { cn } from "../../lib/utils";

interface ModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title?: string;
  description?: string;
  children: ReactNode;
  className?: string;
}

export default function Modal({ open, onOpenChange, title, description, children, className }: ModalProps) {
  return (
    <DialogPrimitive.Root open={open} onOpenChange={onOpenChange}>
      <DialogPrimitive.Portal>
        <DialogPrimitive.Overlay className="modal-overlay" />
        <DialogPrimitive.Content className={cn("modal-content", className)}>
          {title && (
            <DialogPrimitive.Title className="text-lg font-semibold text-text font-display">
              {title}
            </DialogPrimitive.Title>
          )}
          {description && (
            <DialogPrimitive.Description className="text-sm text-text-muted mt-1">
              {description}
            </DialogPrimitive.Description>
          )}
          <div className="mt-4">{children}</div>
          <DialogPrimitive.Close className="absolute right-4 top-4 text-text-muted hover:text-text transition-colors">
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </DialogPrimitive.Close>
        </DialogPrimitive.Content>
      </DialogPrimitive.Portal>
    </DialogPrimitive.Root>
  );
}
```

- [ ] **Step 6: Create Dropdown component**

Create `frontend/src/shared/ui/Dropdown.tsx`:
```tsx
"use client";

import * as DropdownMenuPrimitive from "@radix-ui/react-dropdown-menu";
import { type ReactNode } from "react";
import { cn } from "../../lib/utils";

interface DropdownProps {
  trigger: ReactNode;
  children: ReactNode;
  align?: "start" | "center" | "end";
}

export default function Dropdown({ trigger, children, align = "end" }: DropdownProps) {
  return (
    <DropdownMenuPrimitive.Root>
      <DropdownMenuPrimitive.Trigger asChild>
        {trigger}
      </DropdownMenuPrimitive.Trigger>
      <DropdownMenuPrimitive.Portal>
        <DropdownMenuPrimitive.Content
          align={align}
          sideOffset={6}
          className={cn(
            "z-50 min-w-[180px] rounded-xl bg-bg-elevated border border-border-subtle p-1.5",
            "shadow-elevated animate-fade-in-scale"
          )}
        >
          {children}
        </DropdownMenuPrimitive.Content>
      </DropdownMenuPrimitive.Portal>
    </DropdownMenuPrimitive.Root>
  );
}

export function DropdownItem({
  children,
  className,
  destructive,
  ...props
}: DropdownMenuPrimitive.DropdownMenuItemProps & { destructive?: boolean }) {
  return (
    <DropdownMenuPrimitive.Item
      className={cn(
        "flex items-center gap-2 rounded-lg px-3 py-2 text-sm cursor-pointer outline-none transition-colors",
        "text-text-secondary hover:bg-bg-hover hover:text-text",
        destructive && "text-error hover:bg-error-muted",
        className
      )}
      {...props}
    >
      {children}
    </DropdownMenuPrimitive.Item>
  );
}

export function DropdownSeparator() {
  return <DropdownMenuPrimitive.Separator className="my-1 h-px bg-border-subtle" />;
}
```

- [ ] **Step 7: Create Toast component**

Create `frontend/src/shared/ui/Toast.tsx`:
```tsx
"use client";

import { Toaster, toast } from "sonner";

export function ToastProvider() {
  return (
    <Toaster
      position="bottom-right"
      toastOptions={{
        style: {
          background: "#0a0a0f",
          border: "1px solid rgba(255,255,255,0.06)",
          color: "#f0f0f5",
          borderRadius: "12px",
          fontSize: "13px",
        },
      }}
    />
  );
}

export { toast };
```

- [ ] **Step 8: Verify build**

Run: `cd /home/adi/Desktop/Cortex-Workspace/frontend && npm run build`
Expected: Build succeeds

- [ ] **Step 9: Commit**

```bash
cd /home/adi/Desktop/Cortex-Workspace/frontend
git add src/shared/ui/Card.tsx src/shared/ui/Badge.tsx src/shared/ui/Skeleton.tsx src/shared/ui/Tooltip.tsx src/shared/ui/Modal.tsx src/shared/ui/Dropdown.tsx src/shared/ui/Toast.tsx
git commit -m "feat: build core UI component library (Card, Badge, Skeleton, Tooltip, Modal, Dropdown, Toast)"
```

---

### Task 7: Build Animation Wrapper Components

**Files:**
- Create: `frontend/src/shared/ui/PageTransition.tsx`
- Create: `frontend/src/shared/ui/StaggerChildren.tsx`
- Create: `frontend/src/shared/ui/GlowOrb.tsx`

**Interfaces:**
- Consumes: framer-motion, `cn()` from `src/lib/utils`
- Produces: Reusable animation wrapper components

- [ ] **Step 1: Create PageTransition component**

Create `frontend/src/shared/ui/PageTransition.tsx`:
```tsx
"use client";

import { motion } from "framer-motion";
import { type ReactNode } from "react";

interface PageTransitionProps {
  children: ReactNode;
  className?: string;
}

export default function PageTransition({ children, className }: PageTransitionProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -12 }}
      transition={{ type: "spring", damping: 25, stiffness: 200 }}
      className={className}
    >
      {children}
    </motion.div>
  );
}
```

- [ ] **Step 2: Create StaggerChildren component**

Create `frontend/src/shared/ui/StaggerChildren.tsx`:
```tsx
"use client";

import { motion } from "framer-motion";
import { type ReactNode } from "react";

interface StaggerChildrenProps {
  children: ReactNode;
  className?: string;
  staggerDelay?: number;
}

const container = {
  hidden: { opacity: 0 },
  show: (staggerDelay: number) => ({
    opacity: 1,
    transition: {
      staggerChildren: staggerDelay,
    },
  }),
};

const item = {
  hidden: { opacity: 0, y: 20 },
  show: {
    opacity: 1,
    y: 0,
    transition: { type: "spring", damping: 25, stiffness: 200 },
  },
};

export default function StaggerChildren({ children, className, staggerDelay = 0.08 }: StaggerChildrenProps) {
  return (
    <motion.div
      variants={container}
      initial="hidden"
      animate="show"
      custom={staggerDelay}
      className={className}
    >
      {Array.isArray(children)
        ? children.map((child, i) => (
            <motion.div key={i} variants={item}>
              {child}
            </motion.div>
          ))
        : <motion.div variants={item}>{children}</motion.div>
      }
    </motion.div>
  );
}
```

- [ ] **Step 3: Create GlowOrb component**

Create `frontend/src/shared/ui/GlowOrb.tsx`:
```tsx
"use client";

import { motion } from "framer-motion";
import { cn } from "../../lib/utils";

interface GlowOrbProps {
  className?: string;
  size?: number;
  color?: string;
  delay?: number;
}

export default function GlowOrb({ className, size = 300, color = "rgba(6,182,212,0.08)", delay = 0 }: GlowOrbProps) {
  return (
    <motion.div
      className={cn("absolute rounded-full pointer-events-none", className)}
      style={{
        width: size,
        height: size,
        background: `radial-gradient(circle, ${color} 0%, transparent 70%)`,
        filter: "blur(40px)",
      }}
      animate={{
        y: [0, -20, 0],
        x: [0, 10, 0],
        scale: [1, 1.1, 1],
      }}
      transition={{
        duration: 8,
        repeat: Infinity,
        ease: "easeInOut",
        delay,
      }}
    />
  );
}
```

- [ ] **Step 4: Verify build**

Run: `cd /home/adi/Desktop/Cortex-Workspace/frontend && npm run build`
Expected: Build succeeds

- [ ] **Step 5: Commit**

```bash
cd /home/adi/Desktop/Cortex-Workspace/frontend
git add src/shared/ui/PageTransition.tsx src/shared/ui/StaggerChildren.tsx src/shared/ui/GlowOrb.tsx
git commit -m "feat: build animation wrapper components (PageTransition, StaggerChildren, GlowOrb)"
```

---

## Phase 3: Layout System

### Task 8: Build New DashboardShell with Adaptive Navigation

**Files:**
- Modify: `frontend/src/shared/layout/DashboardShell.tsx`

**Interfaces:**
- Consumes: `useAuth()`, `getProfilePhotoUrl()`, `cn()`, framer-motion
- Produces: Responsive layout with collapsible sidebar (desktop), bottom nav (mobile)

- [ ] **Step 1: Replace DashboardShell**

Replace `frontend/src/shared/layout/DashboardShell.tsx` with the new adaptive navigation shell. This is the largest single component — it handles:
- Collapsible sidebar with icon-only mode (desktop ≥1024px)
- Overlay sidebar with backdrop blur (tablet 768-1023px)
- Bottom tab bar (mobile <768px)
- Glass morphism header with ⌘K trigger
- Avatar dropdown with profile, settings, sign out
- Sliding cyan accent indicator on active nav item
- framer-motion animations for sidebar expand/collapse

[The full implementation is ~300 lines. Key structure:]
```tsx
"use client";
import { useState, useEffect, useRef, type ReactNode } from "react";
import { useRouter, usePathname } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { useAuth } from "../auth/AuthProvider";
import { getProfilePhotoUrl } from "../auth/cortexApi";
import { cn } from "../../lib/utils";
import Tooltip from "../ui/Tooltip";
import Dropdown, { DropdownItem, DropdownSeparator } from "../ui/Dropdown";

const navItems = [
  { label: "Dashboard", href: "/app", icon: "LayoutDashboard" },
  { label: "Vault", href: "/vault", icon: "Lock" },
  { label: "Memory", href: "/memory", icon: "Brain" },
  { label: "Profile", href: "/profile", icon: "User" },
  { label: "Settings", href: "/settings", icon: "Settings" },
];

// Uses lucide-react icons, framer-motion for sidebar animation,
// responsive breakpoints for adaptive layout
```

- [ ] **Step 2: Verify build**

Run: `cd /home/adi/Desktop/Cortex-Workspace/frontend && npm run build`
Expected: Build succeeds

- [ ] **Step 3: Commit**

```bash
cd /home/adi/Desktop/Cortex-Workspace/frontend
git add src/shared/layout/DashboardShell.tsx
git commit -m "feat: redesign DashboardShell with adaptive navigation"
```

---

## Phase 4: Page Redesigns

### Task 9: Redesign Landing Page

**Files:**
- Modify: `frontend/app/page.tsx`

**Interfaces:**
- Consumes: framer-motion, lucide-react, GlowOrb, StaggerChildren
- Produces: Immersive hero with animated particle network, feature cards

- [ ] **Step 1: Replace landing page**

Replace `frontend/app/page.tsx` with the new immersive landing featuring:
- Full-viewport hero with animated CSS particle dots (no three.js for now — CSS-only particles for reliability)
- Cortex logo with breathing glow
- Typewriter tagline effect
- Two CTAs with glow effects
- Scroll-triggered feature cards with 3D hover tilt
- GlowOrb ambient effects
- Minimal footer

[Key structure ~200 lines, using framer-motion for all animations]

- [ ] **Step 2: Verify build**

Run: `cd /home/adi/Desktop/Cortex-Workspace/frontend && npm run build`
Expected: Build succeeds

- [ ] **Step 3: Commit**

```bash
cd /home/adi/Desktop/Cortex-Workspace/frontend
git add app/page.tsx
git commit -m "feat: redesign landing page with immersive hero"
```

---

### Task 10: Redesign Auth Page

**Files:**
- Modify: `frontend/app/auth/page.tsx`

**Interfaces:**
- Consumes: All UI components (Button, Input, Card, Steps, PasswordStrength, Modal)
- Produces: Redesigned auth with split layout, animated wizard

- [ ] **Step 1: Replace auth page**

Replace `frontend/app/auth/page.tsx` with:
- Split layout (visualization left, form right on desktop, stacked on mobile)
- Animated login/register toggle
- 4-step wizard with animated progress bar (not dots)
- Cyan focus glow on inputs
- Error shake animation
- Vault password step with shield icon animation

- [ ] **Step 2: Verify build**

Run: `cd /home/adi/Desktop/Cortex-Workspace/frontend && npm run build`
Expected: Build succeeds

- [ ] **Step 3: Commit**

```bash
cd /home/adi/Desktop/Cortex-Workspace/frontend
git add app/auth/page.tsx
git commit -m "feat: redesign auth page with split layout and animated wizard"
```

---

### Task 11: Redesign Dashboard Page

**Files:**
- Modify: `frontend/app/app/page.tsx`

**Interfaces:**
- Consumes: DashboardShell, Card, Badge, Button, PageTransition, StaggerChildren
- Produces: Command center dashboard with stat cards, quick actions, activity

- [ ] **Step 1: Replace dashboard page**

Replace `frontend/app/app/page.tsx` with:
- Welcome section with avatar glow ring
- 4 stat cards with animated counters
- Quick-action grid with 3D hover tilt
- Activity timeline placeholder
- Breathing glow on status indicator
- PageTransition wrapper

- [ ] **Step 2: Verify build**

Run: `cd /home/adi/Desktop/Cortex-Workspace/frontend && npm run build`
Expected: Build succeeds

- [ ] **Step 3: Commit**

```bash
cd /home/adi/Desktop/Cortex-Workspace/frontend
git add app/app/page.tsx
git commit -m "feat: redesign dashboard page as command center"
```

---

### Task 12: Redesign Vault Page

**Files:**
- Modify: `frontend/app/vault/page.tsx`
- Modify: `frontend/app/vault/VaultLayout.tsx`
- Modify: `frontend/app/vault/VaultSidebar.tsx`
- Modify: `frontend/app/vault/VaultToolbar.tsx`
- Modify: `frontend/app/vault/VaultFileList.tsx`
- Modify: `frontend/app/vault/VaultLockScreen.tsx`
- Modify: `frontend/app/vault/VaultModals.tsx`
- Modify: `frontend/app/vault/VaultProperties.tsx`
- Modify: `frontend/app/vault/useVaultState.ts`

**Interfaces:**
- Consumes: All UI components, framer-motion
- Produces: Redesigned vault with glass panels, smooth animations

- [ ] **Step 1: Redesign VaultLockScreen**

Replace vault lock screen with cinematic vault-door animation.

- [ ] **Step 2: Redesign VaultSidebar**

Glass morphism sidebar with expand/collapse animations.

- [ ] **Step 3: Redesign VaultToolbar**

New toolbar with icon buttons, search, view toggle.

- [ ] **Step 4: Redesign VaultFileList**

Smooth view-mode morphing, drag-and-drop visual feedback.

- [ ] **Step 5: Redesign VaultProperties**

Glass panel with metadata display.

- [ ] **Step 6: Redesign VaultModals**

New modal designs with framer-motion.

- [ ] **Step 7: Redesign VaultLayout**

Updated 3-panel layout with new styling.

- [ ] **Step 8: Verify build**

Run: `cd /home/adi/Desktop/Cortex-Workspace/frontend && npm run build`
Expected: Build succeeds

- [ ] **Step 9: Commit**

```bash
cd /home/adi/Desktop/Cortex-Workspace/frontend
git add app/vault/
git commit -m "feat: redesign vault pages with glass panels and animations"
```

---

### Task 13: Redesign Memory, Profile, Settings, Admin Pages

**Files:**
- Modify: `frontend/app/memory/page.tsx`
- Modify: `frontend/app/profile/page.tsx`
- Modify: `frontend/app/settings/page.tsx`
- Modify: `frontend/app/admin/page.tsx`

**Interfaces:**
- Consumes: DashboardShell, all UI components, framer-motion
- Produces: Redesigned secondary pages

- [ ] **Step 1: Redesign Memory page**

Card-based layout with category filtering, staggered entrance.

- [ ] **Step 2: Redesign Profile page**

Avatar with glow ring, floating label forms.

- [ ] **Step 3: Redesign Settings page**

Clean card sections, danger zone separation.

- [ ] **Step 4: Redesign Admin page**

Sortable table, role badges, action buttons.

- [ ] **Step 5: Verify build**

Run: `cd /home/adi/Desktop/Cortex-Workspace/frontend && npm run build`
Expected: Build succeeds

- [ ] **Step 6: Commit**

```bash
cd /home/adi/Desktop/Cortex-Workspace/frontend
git add app/memory/ app/profile/ app/settings/ app/admin/
git commit -m "feat: redesign memory, profile, settings, admin pages"
```

---

## Phase 5: Command Palette & Integration

### Task 14: Build Command Palette

**Files:**
- Create: `frontend/src/shared/ui/CommandPalette.tsx`
- Modify: `frontend/src/shared/layout/DashboardShell.tsx` (add ⌘K trigger)

**Interfaces:**
- Consumes: cmdk, framer-motion, lucide-react
- Produces: ⌘K command palette with search across all pages

- [ ] **Step 1: Create CommandPalette component**

Create `frontend/src/shared/ui/CommandPalette.tsx` using cmdk with:
- Search across all pages (Dashboard, Vault, Memory, Profile, Settings, Admin)
- Keyboard shortcut (⌘K / Ctrl+K)
- Framer-motion dialog animation
- Glass morphism styling

- [ ] **Step 2: Add ⌘K trigger to DashboardShell**

Add a keyboard shortcut listener and command palette trigger button in the header.

- [ ] **Step 3: Verify build**

Run: `cd /home/adi/Desktop/Cortex-Workspace/frontend && npm run build`
Expected: Build succeeds

- [ ] **Step 4: Commit**

```bash
cd /home/adi/Desktop/Cortex-Workspace/frontend
git add src/shared/ui/CommandPalette.tsx src/shared/layout/DashboardShell.tsx
git commit -m "feat: add command palette with ⌘K shortcut"
```

---

### Task 15: Integrate Toast Notifications

**Files:**
- Modify: `frontend/app/layout.tsx` (add ToastProvider)
- Modify: `frontend/src/shared/auth/AuthProvider.tsx` (add toast on login/logout)

**Interfaces:**
- Consumes: ToastProvider from `src/shared/ui/Toast`
- Produces: Toast notifications for auth events

- [ ] **Step 1: Add ToastProvider to root layout**

Import and render `<ToastProvider />` in `app/layout.tsx`.

- [ ] **Step 2: Add toast notifications to AuthProvider**

Show toast on successful login, logout, and error states.

- [ ] **Step 3: Verify build**

Run: `cd /home/adi/Desktop/Cortex-Workspace/frontend && npm run build`
Expected: Build succeeds

- [ ] **Step 4: Commit**

```bash
cd /home/adi/Desktop/Cortex-Workspace/frontend
git add app/layout.tsx src/shared/auth/AuthProvider.tsx
git commit -m "feat: integrate toast notifications for auth events"
```

---

## Phase 6: Testing & Polish

### Task 16: Update Tests and Fix Build Issues

**Files:**
- Modify: `frontend/src/shared/ui/Button.test.tsx` (update for new variants)
- Modify: `frontend/app/auth/login/page.test.tsx` (update selectors)
- Modify: `frontend/app/auth/signup/page.test.tsx` (update selectors)

**Interfaces:**
- Consumes: All updated components
- Produces: Passing test suite

- [ ] **Step 1: Update Button test**

Update test to match new variant names (primary/secondary/ghost/danger).

- [ ] **Step 2: Update auth tests**

Update selectors to match new auth page structure.

- [ ] **Step 3: Run all tests**

Run: `cd /home/adi/Desktop/Cortex-Workspace/frontend && npm run test -- --run`
Expected: All tests pass

- [ ] **Step 4: Run lint**

Run: `cd /home/adi/Desktop/Cortex-Workspace/frontend && npm run lint`
Expected: No errors

- [ ] **Step 5: Run build**

Run: `cd /home/adi/Desktop/Cortex-Workspace/frontend && npm run build`
Expected: Build succeeds

- [ ] **Step 6: Commit**

```bash
cd /home/adi/Desktop/Cortex-Workspace/frontend
git add -A
git commit -m "fix: update tests and fix build issues for redesign"
```

---

### Task 17: Final Polish — Accessibility, Responsive, Reduced Motion

**Files:**
- Modify: `frontend/app/globals.css` (add prefers-reduced-motion)
- Modify: `frontend/src/shared/layout/DashboardShell.tsx` (mobile polish)
- Modify: Various page files (final responsive adjustments)

**Interfaces:**
- Consumes: All components
- Produces: Production-ready, accessible, responsive application

- [ ] **Step 1: Add prefers-reduced-motion support**

Add to `globals.css`:
```css
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

- [ ] **Step 2: Add skip-to-content link**

Add skip link in root layout for keyboard users.

- [ ] **Step 3: Verify all focus rings visible**

Test keyboard navigation through all interactive elements.

- [ ] **Step 4: Test responsive breakpoints**

Verify at 375px, 768px, 1024px, 1440px.

- [ ] **Step 5: Final build + test**

Run: `cd /home/adi/Desktop/Cortex-Workspace/frontend && npm run build && npm run test -- --run && npm run lint`
Expected: All pass

- [ ] **Step 6: Commit**

```bash
cd /home/adi/Desktop/Cortex-Workspace/frontend
git add -A
git commit -m "feat: final polish — accessibility, responsive, reduced motion"
```
