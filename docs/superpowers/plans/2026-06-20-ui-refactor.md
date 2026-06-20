# UI Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor the entire Cortex frontend UI — update theme to warmer dark, wrap all pages in DashboardShell, redesign dashboard as command center with premium metrics and tabbed content, make search conversational, agents hybrid, memory graph-first, and apply subtle organic animations throughout.

**Architecture:** Token-driven design system (tokens.ts → tailwind.config.ts → components). All pages use DashboardShell for consistent navigation. New components: MetricRing (premium), ProcessTable, ActivityFeed, TabGroup, ConversationalSearch, GraphView (memory), CollapsiblePanel.

**Tech Stack:** Next.js 15, React 19, TypeScript, Tailwind CSS 3.4, framer-motion, Radix UI, Lucide icons, Recharts (for sparklines), d3-force (for memory graph)

## Global Constraints

- Python 3.12+, Node.js 20+
- TypeScript strict mode, ESLint zero warnings
- Tailwind CSS with semantic tokens from `tokens.ts`
- All animations respect `prefers-reduced-motion`
- No new external dependencies without approval (Recharts and d3-force need approval)
- Each task must pass `npx next build` before committing
- Follow existing code patterns: `cn()` utility, `motion` from framer-motion, Radix primitives

---

## Task 1: Update Design Tokens

**Files:**
- Modify: `frontend/src/shared/design/tokens.ts`

**Interfaces:**
- Consumes: None (foundation task)
- Produces: Updated token colors used by all subsequent tasks

- [ ] **Step 1: Update color tokens in tokens.ts**

Replace the colors object in `frontend/src/shared/design/tokens.ts`:

```typescript
export const tokens = {
  colors: {
    void: "#0a0a0f",
    bg: "#0a0a0f",
    "bg-elevated": "#111118",
    "bg-surface": "#16161f",
    "bg-hover": "#1c1c28",
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
    accent: {
      DEFAULT: "#0ea5c9",
      hover: "#38bdf8",
      muted: "rgba(14,165,201,0.25)",
      faint: "rgba(14,165,201,0.08)",
      glow: "rgba(14,165,201,0.12)",
    },
    error: "#ef4444",
    success: "#22c55e",
    warning: "#f59e0b",
  },
  // ... keep fonts, shadows, borderRadius, maxWidth as-is
} as const;
```

- [ ] **Step 2: Verify Tailwind picks up new tokens**

Run: `cd frontend && npx tailwindcss --content 'src/**/*.tsx' --output /dev/null 2>&1 | head -5`
Expected: No errors

- [ ] **Step 3: Commit**

```bash
git add frontend/src/shared/design/tokens.ts
git commit -m "refactor: update design tokens to warmer dark palette"
```

---

## Task 2: Update Global CSS

**Files:**
- Modify: `frontend/app/globals.css`

**Interfaces:**
- Consumes: New token colors from Task 1
- Produces: Updated CSS variables and component classes used by all pages

- [ ] **Step 1: Update globals.css base layer**

Replace the `@layer base` section in `frontend/app/globals.css`:

```css
@layer base {
  :root {
    color-scheme: dark;
  }

  html {
    background: var(--bg);
  }

  ::selection {
    background-color: rgba(14, 165, 201, 0.3);
  }

  * {
    scrollbar-width: thin;
    scrollbar-color: rgba(255, 255, 255, 0.1) transparent;
  }

  *::-webkit-scrollbar {
    width: 6px;
  }

  *::-webkit-scrollbar-track {
    background: transparent;
  }

  *::-webkit-scrollbar-thumb {
    background-color: rgba(255, 255, 255, 0.1);
    border-radius: 3px;
  }

  *::-webkit-scrollbar-thumb:hover {
    background-color: rgba(255, 255, 255, 0.2);
  }
}
```

- [ ] **Step 2: Update component classes**

Replace the `@layer components` section:

```css
@layer components {
  .glass-panel {
    background: rgba(10, 10, 15, 0.7);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.08);
  }

  .glass-panel-strong {
    background: rgba(10, 10, 15, 0.85);
    backdrop-filter: blur(30px);
    -webkit-backdrop-filter: blur(30px);
    border: 1px solid rgba(255, 255, 255, 0.1);
  }

  .shimmer-bg {
    background: linear-gradient(
      90deg,
      rgba(255, 255, 255, 0) 0%,
      rgba(255, 255, 255, 0.03) 50%,
      rgba(255, 255, 255, 0) 100%
    );
    background-size: 200% 100%;
    animation: shimmer 2s linear infinite;
  }

  .text-gradient {
    background: linear-gradient(135deg, #e8e8ed 0%, #7a7a8a 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  .text-gradient-accent {
    background: linear-gradient(135deg, #0ea5c9 0%, #38bdf8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  .focus-ring {
    outline: none;
    box-shadow: 0 0 0 2px rgba(14, 165, 201, 0.3);
  }

  .interactive-card {
    transition: all 0.2s ease;
  }

  .interactive-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.3), 0 0 20px rgba(14, 165, 201, 0.06);
    border-color: rgba(14, 165, 201, 0.2);
  }

  .nav-item {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.5rem 0.75rem;
    border-radius: 0.5rem;
    color: var(--text-secondary);
    transition: all 0.15s ease;
    font-size: 0.875rem;
    font-weight: 500;
  }

  .nav-item:hover {
    color: var(--text);
    background: var(--bg-hover);
  }

  .stat-card {
    padding: 1rem;
    border-radius: 0.75rem;
    border: 1px solid rgba(255, 255, 255, 0.08);
    background: var(--bg-elevated);
  }

  .modal-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.6);
    backdrop-filter: blur(4px);
    z-index: 50;
  }

  .modal-content {
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    z-index: 51;
    width: 100%;
    max-width: 32rem;
    padding: 1.5rem;
    border-radius: 1rem;
    border: 1px solid rgba(255, 255, 255, 0.08);
    background: var(--bg-elevated);
    box-shadow: 0 25px 60px rgba(0, 0, 0, 0.5);
  }

  .page-header {
    padding: 1.5rem 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    margin-bottom: 1.5rem;
  }

  .btn-glow {
    position: relative;
    overflow: hidden;
  }

  .btn-glow::before {
    content: '';
    position: absolute;
    inset: -2px;
    border-radius: inherit;
    background: linear-gradient(135deg, rgba(14, 165, 201, 0.15), rgba(14, 165, 201, 0));
    opacity: 0;
    transition: opacity 0.3s ease;
    z-index: -1;
  }

  .btn-glow:hover::before {
    opacity: 1;
  }

  .micro-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.625rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--text-muted);
  }
}
```

- [ ] **Step 3: Update keyframes and reduced motion**

Replace the keyframes and reduced motion section at the bottom of `globals.css`:

```css
@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

@keyframes pulse-dot {
  0%, 100% { opacity: 0.6; }
  50% { opacity: 1; }
}

@keyframes fade-in {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes count-up {
  from { opacity: 0; transform: translateY(4px); }
  to { opacity: 1; transform: translateY(0); }
}

@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

- [ ] **Step 4: Verify build**

Run: `cd frontend && npx next build 2>&1 | tail -5`
Expected: Build succeeds

- [ ] **Step 5: Commit**

```bash
git add frontend/app/globals.css
git commit -m "refactor: update global CSS for warmer dark theme"
```

---

## Task 3: Upgrade Card Component

**Files:**
- Modify: `frontend/src/shared/ui/Card.tsx`

**Interfaces:**
- Consumes: New token colors from Task 1
- Produces: Enhanced Card component used by Dashboard and all pages

- [ ] **Step 1: Rewrite Card.tsx with gradient and depth**

Replace `frontend/src/shared/ui/Card.tsx`:

```tsx
import { type ReactNode, forwardRef } from "react";
import { cn } from "@/lib/utils";

interface CardProps {
  children: ReactNode;
  className?: string;
  hover?: boolean;
  glass?: boolean;
  gradient?: boolean;
  glow?: boolean;
}

const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ children, className, hover, glass, gradient, glow }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          "rounded-xl border border-border-subtle bg-bg-elevated",
          "shadow-card transition-all duration-200 ease-out",
          hover && [
            "cursor-pointer",
            "hover:border-accent/20 hover:shadow-glow",
            "hover:-translate-y-0.5",
            "active:scale-[0.98]",
          ],
          glass && "glass-panel",
          gradient && [
            "bg-gradient-to-br from-bg-elevated via-bg-surface to-bg-elevated",
            "before:absolute before:inset-0 before:rounded-xl before:opacity-0",
            "before:bg-gradient-to-br before:from-accent/5 before:to-transparent",
            "before:transition-opacity before:duration-300",
            "hover:before:opacity-100",
          ],
          glow && "shadow-glow hover:shadow-glow-strong",
          "relative overflow-hidden",
          className
        )}
      >
        {children}
      </div>
    );
  }
);

Card.displayName = "Card";

export { Card };
```

- [ ] **Step 2: Verify build**

Run: `cd frontend && npx next build 2>&1 | tail -5`
Expected: Build succeeds

- [ ] **Step 3: Commit**

```bash
git add frontend/src/shared/ui/Card.tsx
git commit -m "refactor: upgrade Card with gradient fills, depth, and micro-interactions"
```

---

## Task 4: Create MetricRing Component

**Files:**
- Create: `frontend/src/shared/ui/MetricRing.tsx`

**Interfaces:**
- Consumes: New accent color from tokens
- Produces: `MetricRing` component used by Dashboard

- [ ] **Step 1: Create MetricRing.tsx**

Create `frontend/src/shared/ui/MetricRing.tsx`:

```tsx
"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface MetricRingProps {
  label: string;
  value: number;
  max?: number;
  unit?: string;
  color?: string;
  size?: number;
  strokeWidth?: number;
  className?: string;
}

export function MetricRing({
  label,
  value,
  max = 100,
  unit = "%",
  color = "#0ea5c9",
  size = 120,
  strokeWidth = 8,
  className,
}: MetricRingProps) {
  const [displayValue, setDisplayValue] = useState(0);
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const progress = Math.min(value / max, 1);
  const strokeDashoffset = circumference * (1 - progress);

  useEffect(() => {
    const duration = 1500;
    const start = performance.now();
    const animate = (now: number) => {
      const elapsed = now - start;
      const t = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - t, 3);
      setDisplayValue(Math.round(eased * value));
      if (t < 1) requestAnimationFrame(animate);
    };
    requestAnimationFrame(animate);
  }, [value]);

  return (
    <div className={cn("flex flex-col items-center gap-2", className)}>
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="-rotate-90">
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="rgba(255,255,255,0.06)"
            strokeWidth={strokeWidth}
          />
          <motion.circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={circumference}
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset }}
            transition={{ duration: 1.5, ease: "easeOut" }}
            style={{
              filter: `drop-shadow(0 0 6px ${color}40)`,
            }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-2xl font-semibold text-text tabular-nums">
            {displayValue}
          </span>
          <span className="text-xs text-text-muted">{unit}</span>
        </div>
      </div>
      <span className="micro-label">{label}</span>
    </div>
  );
}
```

- [ ] **Step 2: Verify build**

Run: `cd frontend && npx next build 2>&1 | tail -5`
Expected: Build succeeds

- [ ] **Step 3: Commit**

```bash
git add frontend/src/shared/ui/MetricRing.tsx
git commit -m "feat: add MetricRing component with animated gradient fills"
```

---

## Task 5: Create TabGroup Component

**Files:**
- Create: `frontend/src/shared/ui/TabGroup.tsx`

**Interfaces:**
- Consumes: Token colors
- Produces: `TabGroup` + `TabPanel` components used by Dashboard, Search

- [ ] **Step 1: Create TabGroup.tsx**

Create `frontend/src/shared/ui/TabGroup.tsx`:

```tsx
"use client";

import { useState, type ReactNode } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface Tab {
  id: string;
  label: string;
  icon?: ReactNode;
  count?: number;
}

interface TabGroupProps {
  tabs: Tab[];
  defaultTab?: string;
  onChange?: (tabId: string) => void;
  className?: string;
  children: ReactNode;
}

export function TabGroup({
  tabs,
  defaultTab,
  onChange,
  className,
  children,
}: TabGroupProps) {
  const [activeTab, setActiveTab] = useState(defaultTab || tabs[0]?.id);

  const handleChange = (tabId: string) => {
    setActiveTab(tabId);
    onChange?.(tabId);
  };

  return (
    <div className={className}>
      <div className="flex gap-1 border-b border-border-subtle mb-4">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => handleChange(tab.id)}
            className={cn(
              "relative flex items-center gap-2 px-4 py-2.5 text-sm font-medium",
              "transition-colors duration-150",
              activeTab === tab.id
                ? "text-text"
                : "text-text-secondary hover:text-text"
            )}
          >
            {tab.icon}
            {tab.label}
            {tab.count !== undefined && (
              <span className="text-xs text-text-muted bg-bg-surface px-1.5 py-0.5 rounded-full">
                {tab.count}
              </span>
            )}
            {activeTab === tab.id && (
              <motion.div
                layoutId="tab-indicator"
                className="absolute bottom-0 left-0 right-0 h-0.5 bg-accent"
                transition={{ type: "spring", damping: 30, stiffness: 300 }}
              />
            )}
          </button>
        ))}
      </div>
      <TabContext.Provider value={activeTab}>{children}</TabContext.Provider>
    </div>
  );
}

import { createContext, useContext } from "react";

const TabContext = createContext<string>("");

export function TabPanel({
  tabId,
  children,
  className,
}: {
  tabId: string;
  children: ReactNode;
  className?: string;
}) {
  const activeTab = useContext(TabContext);
  if (activeTab !== tabId) return null;
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.2 }}
      className={className}
    >
      {children}
    </motion.div>
  );
}
```

- [ ] **Step 2: Verify build**

Run: `cd frontend && npx next build 2>&1 | tail -5`
Expected: Build succeeds

- [ ] **Step 3: Commit**

```bash
git add frontend/src/shared/ui/TabGroup.tsx
git commit -m "feat: add TabGroup component with animated indicator"
```

---

## Task 6: Create CollapsiblePanel Component

**Files:**
- Create: `frontend/src/shared/ui/CollapsiblePanel.tsx`

**Interfaces:**
- Consumes: Token colors
- Produces: `CollapsiblePanel` used by Agents, Memory

- [ ] **Step 1: Create CollapsiblePanel.tsx**

Create `frontend/src/shared/ui/CollapsiblePanel.tsx`:

```tsx
"use client";

import { useState, type ReactNode } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { PanelLeftClose, PanelLeftOpen } from "lucide-react";
import { cn } from "@/lib/utils";

interface CollapsiblePanelProps {
  defaultOpen?: boolean;
  minWidth?: number;
  collapsedWidth?: number;
  className?: string;
  header: ReactNode;
  children: ReactNode;
}

export function CollapsiblePanel({
  defaultOpen = true,
  minWidth = 240,
  collapsedWidth = 48,
  className,
  header,
  children,
}: CollapsiblePanelProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div className={cn("flex h-full", className)}>
      <AnimatePresence mode="wait">
        {isOpen && (
          <motion.div
            initial={{ width: collapsedWidth, opacity: 0.5 }}
            animate={{ width: minWidth, opacity: 1 }}
            exit={{ width: collapsedWidth, opacity: 0 }}
            transition={{ type: "spring", damping: 25, stiffness: 200 }}
            className="flex flex-col border-r border-border-subtle bg-bg-surface/50 overflow-hidden"
          >
            <div className="flex items-center justify-between p-3 border-b border-border-subtle">
              {header}
              <button
                onClick={() => setIsOpen(false)}
                className="p-1 rounded-md hover:bg-bg-hover text-text-secondary hover:text-text transition-colors"
              >
                <PanelLeftClose size={16} />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-3">{children}</div>
          </motion.div>
        )}
      </AnimatePresence>
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="flex items-center justify-center w-12 h-full border-r border-border-subtle hover:bg-bg-hover text-text-secondary hover:text-text transition-colors"
        >
          <PanelLeftOpen size={16} />
        </button>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Verify build**

Run: `cd frontend && npx next build 2>&1 | tail -5`
Expected: Build succeeds

- [ ] **Step 3: Commit**

```bash
git add frontend/src/shared/ui/CollapsiblePanel.tsx
git commit -m "feat: add CollapsiblePanel component for page sidebars"
```

---

## Task 7: Update DashboardShell — Navigation Groups

**Files:**
- Modify: `frontend/src/shared/layout/DashboardShell.tsx`

**Interfaces:**
- Consumes: New tokens, Card, CollapsiblePanel
- Produces: Updated DashboardShell with Work/You nav groups, glass sidebar, minimal header

- [ ] **Step 1: Update nav items with group labels**

In `DashboardShell.tsx`, update the `navItems` array and add group labels. Find the navItems definition and replace:

```typescript
const workNavItems = [
  { label: "Dashboard", href: "/app", icon: LayoutDashboard },
  { label: "Search", href: "/search", icon: Search },
  { label: "Agents", href: "/agents", icon: Bot },
];

const accountNavItems = [
  { label: "Vault", href: "/vault", icon: Lock },
  { label: "Memory", href: "/memory", icon: Brain },
  { label: "Profile", href: "/profile", icon: User },
  { label: "Settings", href: "/settings", icon: Settings },
];
```

- [ ] **Step 2: Update sidebar rendering to use groups**

Find the sidebar nav rendering section and replace with grouped rendering. The sidebar should show "WORK" label above the first group and "YOU" label above the second group:

```tsx
{/* Work Group */}
<div className="px-3 mb-1">
  <span className="micro-label">Work</span>
</div>
{workNavItems.map((item) => {
  const isActive = pathname === item.href;
  return (
    <Link
      key={item.href}
      href={item.href}
      className={cn("nav-item relative", isActive && "text-text bg-bg-hover")}
    >
      {isActive && (
        <motion.div
          layoutId="sidebar-active"
          className="absolute inset-0 rounded-lg bg-bg-hover"
          transition={{ type: "spring", damping: 25, stiffness: 200 }}
        />
      )}
      <item.icon size={18} className="relative z-10" />
      <span className="relative z-10">{item.label}</span>
      {isActive && (
        <div className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-4 bg-accent rounded-full" />
      )}
    </Link>
  );
})}

{/* Divider */}
<div className="mx-3 my-2 h-px bg-gradient-to-r from-transparent via-border-subtle to-transparent" />

{/* You Group */}
<div className="px-3 mb-1">
  <span className="micro-label">You</span>
</div>
{accountNavItems.map((item) => {
  const isActive = pathname === item.href;
  return (
    <Link
      key={item.href}
      href={item.href}
      className={cn("nav-item relative", isActive && "text-text bg-bg-hover")}
    >
      {isActive && (
        <motion.div
          layoutId="sidebar-active"
          className="absolute inset-0 rounded-lg bg-bg-hover"
          transition={{ type: "spring", damping: 25, stiffness: 200 }}
        />
      )}
      <item.icon size={18} className="relative z-10" />
      <span className="relative z-10">{item.label}</span>
      {isActive && (
        <div className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-4 bg-accent rounded-full" />
      )}
    </Link>
  );
})}
```

- [ ] **Step 3: Update sidebar class for glass effect**

Find the sidebar container div and update its classes to use the glass effect:

```tsx
<aside className="hidden lg:flex flex-col w-60 h-screen fixed left-0 top-0 z-40 glass-panel-strong border-r border-border-subtle">
```

- [ ] **Step 4: Update header to be minimal**

Simplify the header — remove page-specific elements, keep only logo, search trigger, notifications, avatar:

```tsx
<header className="sticky top-0 z-30 h-14 flex items-center justify-between px-4 glass-panel border-b border-border-subtle">
  {/* Left: Logo (tablet/mobile only, desktop has sidebar) */}
  <div className="flex items-center gap-3">
    <button
      onClick={() => setSidebarOpen(!sidebarOpen)}
      className="lg:hidden p-2 rounded-lg hover:bg-bg-hover text-text-secondary"
    >
      {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
    </button>
    <Link href="/app" className="flex items-center gap-2">
      <CortexLogo className="w-6 h-6 text-accent" />
      <span className="font-semibold text-text hidden sm:inline">Cortex</span>
    </Link>
  </div>

  {/* Right: Actions */}
  <div className="flex items-center gap-2">
    <button
      onClick={() => document.dispatchEvent(new KeyboardEvent("keydown", { key: "k", metaKey: true }))}
      className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-border-subtle bg-bg-surface text-text-secondary text-sm hover:border-accent/20 hover:text-text transition-colors"
    >
      <Search size={14} />
      <span className="hidden sm:inline">Search</span>
      <kbd className="text-[10px] font-mono bg-bg-hover px-1.5 py-0.5 rounded">⌘K</kbd>
    </button>
    <NotificationBell />
    <AvatarDropdown />
  </div>
</header>
```

- [ ] **Step 5: Verify build**

Run: `cd frontend && npx next build 2>&1 | tail -5`
Expected: Build succeeds

- [ ] **Step 6: Commit**

```bash
git add frontend/src/shared/layout/DashboardShell.tsx
git commit -m "refactor: update DashboardShell with Work/You nav groups, glass sidebar, minimal header"
```

---

## Task 8: Redesign Dashboard

**Files:**
- Modify: `frontend/app/app/page.tsx`

**Interfaces:**
- Consumes: DashboardShell, MetricRing, Card, TabGroup, TabPanel
- Produces: Redesigned dashboard with hero, premium metrics, tabbed content

- [ ] **Step 1: Rewrite dashboard page.tsx**

Replace `frontend/app/app/page.tsx` with:

```tsx
"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  Activity,
  Brain,
  Bot,
  Clock,
  Cpu,
  HardDrive,
  MemoryStick,
  Server,
  Shield,
  User,
} from "lucide-react";
import DashboardShell from "@/shared/layout/DashboardShell";
import { Card } from "@/shared/ui/Card";
import { MetricRing } from "@/shared/ui/MetricRing";
import { TabGroup, TabPanel } from "@/shared/ui/TabGroup";
import { NeuralNetwork } from "@/shared/ui/NeuralNetwork";
import { useAuth } from "@/shared/auth/AuthProvider";
import { systemApi } from "@/shared/api";
import Link from "next/link";

export default function DashboardPage() {
  const { user } = useAuth();
  const [metrics, setMetrics] = useState({
    cpu: 0,
    ram: 0,
    disk: 0,
    gpu: "N/A",
  });
  const [processes, setProcesses] = useState([]);
  const [recentActivity, setRecentActivity] = useState([]);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const data = await systemApi.metrics();
        setMetrics({
          cpu: data.cpu_percent || 0,
          ram: data.memory_percent || 0,
          disk: data.disk_percent || 0,
          gpu: data.gpu_name || "N/A",
        });
        setProcesses(data.processes || []);
      } catch {}
    };
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <DashboardShell>
      <NeuralNetwork intensity="medium" />
      <div className="relative z-10 max-w-6xl mx-auto px-4 sm:px-6 py-8">
        {/* Hero Welcome */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: "easeOut" }}
          className="mb-8"
        >
          <div className="flex items-center gap-4 mb-6">
            <div className="relative">
              <div className="w-16 h-16 rounded-full bg-bg-surface border border-border-subtle flex items-center justify-center">
                <User size={28} className="text-accent" />
              </div>
              <div className="absolute -bottom-0.5 -right-0.5 w-4 h-4 bg-success rounded-full border-2 border-bg" />
            </div>
            <div>
              <h1 className="text-2xl font-semibold text-text">
                Welcome back, {user?.name || "there"}
              </h1>
              <div className="flex items-center gap-2 mt-1">
                <span className="micro-label">
                  {user?.role === "admin" ? "Admin" : "Member"}
                </span>
                <span className="text-text-muted text-sm">@{user?.username}</span>
              </div>
            </div>
          </div>

          {/* Premium Metric Rings */}
          <div className="flex flex-wrap items-center justify-center gap-8 sm:gap-12">
            <MetricRing label="CPU" value={metrics.cpu} color="#0ea5c9" />
            <MetricRing label="RAM" value={metrics.ram} color="#8b5cf6" />
            <MetricRing label="Disk" value={metrics.disk} color="#22c55e" />
            <Card className="flex flex-col items-center justify-center gap-2 px-6 py-4" gradient>
              <Cpu size={20} className="text-accent" />
              <span className="micro-label">GPU</span>
              <span className="text-sm text-text text-center">{metrics.gpu}</span>
            </Card>
          </div>
        </motion.div>

        {/* Tabbed Content */}
        <TabGroup
          tabs={[
            { id: "activity", label: "Activity", icon: <Activity size={16} /> },
            { id: "processes", label: "Processes", icon: <Server size={16} />, count: processes.length },
            { id: "insights", label: "Insights", icon: <Brain size={16} /> },
          ]}
        >
          <TabPanel tabId="activity">
            <Card className="p-6" gradient>
              <h3 className="text-lg font-semibold text-text mb-4 flex items-center gap-2">
                <Activity size={18} className="text-accent" />
                Recent Activity
              </h3>
              <div className="space-y-3">
                {recentActivity.length === 0 ? (
                  <p className="text-text-secondary text-sm">
                    No recent activity. Start by searching, creating agents, or adding memories.
                  </p>
                ) : (
                  recentActivity.map((item: any, i: number) => (
                    <div key={i} className="flex items-center gap-3 p-3 rounded-lg bg-bg-surface/50">
                      <div className="w-8 h-8 rounded-full bg-accent/10 flex items-center justify-center">
                        <Bot size={14} className="text-accent" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-text truncate">{item.title}</p>
                        <p className="text-xs text-text-muted">{item.time}</p>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </Card>
          </TabPanel>

          <TabPanel tabId="processes">
            <Card className="p-6" gradient>
              <h3 className="text-lg font-semibold text-text mb-4 flex items-center gap-2">
                <Server size={18} className="text-accent" />
                System Processes
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border-subtle">
                      <th className="text-left py-2 text-text-muted font-medium">Name</th>
                      <th className="text-right py-2 text-text-muted font-medium">PID</th>
                      <th className="text-right py-2 text-text-muted font-medium">CPU%</th>
                      <th className="text-right py-2 text-text-muted font-medium">Memory%</th>
                      <th className="text-right py-2 text-text-muted font-medium">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {processes.slice(0, 20).map((p: any, i: number) => (
                      <tr
                        key={i}
                        className="border-b border-border-subtle/50 hover:bg-bg-hover/50 transition-colors"
                      >
                        <td className="py-2 text-text font-mono text-xs">{p.name}</td>
                        <td className="py-2 text-text-secondary text-right font-mono text-xs">{p.pid}</td>
                        <td className="py-2 text-right font-mono text-xs">
                          <span className={p.cpu > 50 ? "text-warning" : "text-text-secondary"}>
                            {p.cpu?.toFixed(1)}
                          </span>
                        </td>
                        <td className="py-2 text-right font-mono text-xs text-text-secondary">
                          {p.memory?.toFixed(1)}
                        </td>
                        <td className="py-2 text-right">
                          <span
                            className={`inline-block px-2 py-0.5 rounded-full text-xs ${
                              p.status === "running"
                                ? "bg-success/10 text-success"
                                : "bg-bg-hover text-text-muted"
                            }`}
                          >
                            {p.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          </TabPanel>

          <TabPanel tabId="insights">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <Link href="/vault">
                <Card hover gradient className="p-5">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="w-10 h-10 rounded-lg bg-accent/10 flex items-center justify-center">
                      <HardDrive size={18} className="text-accent" />
                    </div>
                    <span className="micro-label">Vault</span>
                  </div>
                  <p className="text-2xl font-semibold text-text">Active</p>
                </Card>
              </Link>
              <Link href="/memory">
                <Card hover gradient className="p-5">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="w-10 h-10 rounded-lg bg-accent/10 flex items-center justify-center">
                      <Brain size={18} className="text-accent" />
                    </div>
                    <span className="micro-label">Memories</span>
                  </div>
                  <p className="text-2xl font-semibold text-text">—</p>
                </Card>
              </Link>
              <Card gradient className="p-5">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-10 rounded-lg bg-accent/10 flex items-center justify-center">
                    <Bot size={18} className="text-accent" />
                  </div>
                  <span className="micro-label">Agents</span>
                </div>
                <p className="text-2xl font-semibold text-text">—</p>
              </Card>
              <Card gradient className="p-5">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-10 rounded-lg bg-accent/10 flex items-center justify-center">
                    <Clock size={18} className="text-accent" />
                  </div>
                  <span className="micro-label">Member Since</span>
                </div>
                <p className="text-sm font-semibold text-text">
                  {user?.created_at
                    ? new Date(user.created_at).toLocaleDateString()
                    : "—"}
                </p>
              </Card>
            </div>
          </TabPanel>
        </TabGroup>
      </div>
    </DashboardShell>
  );
}
```

- [ ] **Step 2: Verify build**

Run: `cd frontend && npx next build 2>&1 | tail -5`
Expected: Build succeeds

- [ ] **Step 3: Commit**

```bash
git add frontend/app/app/page.tsx
git commit -m "refactor: redesign dashboard with hero, premium metrics, tabbed content"
```

---

## Task 9: Wrap Search in DashboardShell + Conversational UI

**Files:**
- Modify: `frontend/app/search/page.tsx`

**Interfaces:**
- Consumes: DashboardShell, Card, CollapsiblePanel
- Produces: Search page with conversational input, AI answer panel, sources list

- [ ] **Step 1: Rewrite search page.tsx**

Replace `frontend/app/search/page.tsx`:

```tsx
"use client";

import { useState, useCallback } from "react";
import { motion } from "framer-motion";
import { Search, Sparkles, ExternalLink, Code, Brain, FileText, ToggleLeft, ToggleRight } from "lucide-react";
import DashboardShell from "@/shared/layout/DashboardShell";
import { Card } from "@/shared/ui/Card";
import { NeuralNetwork } from "@/shared/ui/NeuralNetwork";
import { searchApi } from "@/shared/api";
import { cn } from "@/lib/utils";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<any[]>([]);
  const [aiAnswer, setAiAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  const handleSearch = useCallback(
    async (q: string) => {
      if (!q.trim()) return;
      setLoading(true);
      setHasSearched(true);
      try {
        const data = await searchApi.unified({ query: q, max_results: 20 });
        setResults(data.results || []);
        // Synthesize AI answer from results
        if (data.results?.length > 0) {
          const sources = data.results
            .slice(0, 5)
            .map((r: any, i: number) => `[${i + 1}] ${r.title || r.file_path || "Result"}`)
            .join("\n");
          setAiAnswer(`Found ${data.results.length} relevant results across your codebase and memories.\n\nTop sources:\n${sources}`);
        } else {
          setAiAnswer("No results found for this query. Try rephrasing or checking your indexed repositories.");
        }
      } catch {
        setAiAnswer("Search failed. Please try again.");
      } finally {
        setLoading(false);
      }
    },
    []
  );

  return (
    <DashboardShell>
      <NeuralNetwork intensity="low" />
      <div className="relative z-10 max-w-4xl mx-auto px-4 sm:px-6 py-8">
        {/* Hero Header */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-8"
        >
          <h1 className="text-3xl font-semibold text-text mb-2">Search your workspace</h1>
          <p className="text-text-secondary">
            Ask anything about your code, memories, or files
          </p>
        </motion.div>

        {/* Conversational Search Input */}
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="mb-8"
        >
          <div className="relative">
            <Search size={20} className="absolute left-4 top-1/2 -translate-y-1/2 text-text-muted" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch(query)}
              placeholder="Ask anything about your code, memories, or files..."
              className="w-full h-14 pl-12 pr-24 rounded-2xl border border-border-subtle bg-bg-elevated text-text placeholder:text-text-muted text-lg focus:outline-none focus:border-accent/30 focus:shadow-glow transition-all"
            />
            <button
              onClick={() => handleSearch(query)}
              disabled={loading || !query.trim()}
              className={cn(
                "absolute right-2 top-1/2 -translate-y-1/2",
                "px-4 py-2 rounded-xl font-medium text-sm",
                "bg-accent text-void hover:bg-accent-hover",
                "disabled:opacity-50 disabled:cursor-not-allowed",
                "transition-colors"
              )}
            >
              {loading ? "Searching..." : "Search"}
            </button>
          </div>
        </motion.div>

        {/* AI Answer Panel */}
        {hasSearched && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-6"
          >
            <Card className="p-6" gradient>
              <div className="flex items-center gap-2 mb-3">
                <Sparkles size={18} className="text-accent" />
                <span className="text-sm font-semibold text-text">AI Answer</span>
              </div>
              <div className="text-text-secondary whitespace-pre-wrap leading-relaxed">
                {aiAnswer}
              </div>
            </Card>
          </motion.div>
        )}

        {/* Sources */}
        {hasSearched && results.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <h3 className="text-sm font-semibold text-text mb-3 flex items-center gap-2">
              <span>Sources</span>
              <span className="text-xs text-text-muted bg-bg-surface px-2 py-0.5 rounded-full">
                {results.length}
              </span>
            </h3>
            <div className="space-y-2">
              {results.map((result: any, i: number) => (
                <Card key={i} hover className="p-4" gradient>
                  <div className="flex items-start gap-3">
                    <div className="w-8 h-8 rounded-lg bg-accent/10 flex items-center justify-center shrink-0">
                      {result.type === "code" ? (
                        <Code size={14} className="text-accent" />
                      ) : result.type === "memory" ? (
                        <Brain size={14} className="text-accent" />
                      ) : (
                        <FileText size={14} className="text-accent" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-sm font-medium text-text truncate">
                          {result.title || result.file_path || "Result"}
                        </span>
                        <span className="text-xs text-text-muted shrink-0">
                          [{i + 1}]
                        </span>
                      </div>
                      {result.preview && (
                        <p className="text-xs text-text-secondary line-clamp-2">
                          {result.preview}
                        </p>
                      )}
                      <div className="flex items-center gap-2 mt-2">
                        <span className="text-xs text-text-muted">
                          {result.type}
                        </span>
                        {result.score && (
                          <span className="text-xs text-accent">
                            {(result.score * 100).toFixed(0)}% match
                          </span>
                        )}
                      </div>
                    </div>
                    <ExternalLink size={14} className="text-text-muted shrink-0 mt-1" />
                  </div>
                </Card>
              ))}
            </div>
          </motion.div>
        )}

        {/* Empty State */}
        {!hasSearched && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="text-center py-16"
          >
            <Search size={48} className="mx-auto text-text-muted mb-4" />
            <p className="text-text-secondary">
              Type a question above to search across your codebase and memories
            </p>
          </motion.div>
        )}
      </div>
    </DashboardShell>
  );
}
```

- [ ] **Step 2: Verify build**

Run: `cd frontend && npx next build 2>&1 | tail -5`
Expected: Build succeeds

- [ ] **Step 3: Commit**

```bash
git add frontend/app/search/page.tsx
git commit -m "refactor: wrap search in DashboardShell with conversational AI-first UI"
```

---

## Task 10: Wrap Agents in DashboardShell + Hybrid Chat

**Files:**
- Modify: `frontend/app/agents/page.tsx`
- Modify: `frontend/app/agents/AgentChat.tsx`

**Interfaces:**
- Consumes: DashboardShell, CollapsiblePanel, Card
- Produces: Agents page with collapsible agent list, hybrid chat interface

- [ ] **Step 1: Rewrite agents/page.tsx**

Replace `frontend/app/agents/page.tsx` with a version that uses DashboardShell and CollapsiblePanel for the agent list sidebar.

- [ ] **Step 2: Update AgentChat.tsx for structured step output**

Update the AgentChat component to show structured step output when an agent executes — numbered steps with status icons, collapsible details.

- [ ] **Step 3: Verify build**

Run: `cd frontend && npx next build 2>&1 | tail -5`
Expected: Build succeeds

- [ ] **Step 4: Commit**

```bash
git add frontend/app/agents/page.tsx frontend/app/agents/AgentChat.tsx
git commit -m "refactor: wrap agents in DashboardShell with hybrid chat and structured steps"
```

---

## Task 11: Wrap Memory in DashboardShell + Graph View

**Files:**
- Modify: `frontend/app/memory/page.tsx`

**Interfaces:**
- Consumes: DashboardShell, Card, CollapsiblePanel
- Produces: Memory page with graph-first view, category nodes, filter chips

- [ ] **Step 1: Rewrite memory/page.tsx**

Replace `frontend/app/memory/page.tsx` with a version that:
- Uses DashboardShell
- Default view is a graph visualization (using SVG/canvas for category nodes)
- Toggle to list view with filter chips instead of sidebar
- Categories shown as visual nodes in graph, filter chips in list
- Detail panel on right side (collapsible)

- [ ] **Step 2: Verify build**

Run: `cd frontend && npx next build 2>&1 | tail -5`
Expected: Build succeeds

- [ ] **Step 3: Commit**

```bash
git add frontend/app/memory/page.tsx
git commit -m "refactor: wrap memory in DashboardShell with knowledge graph view"
```

---

## Task 12: Update Remaining Pages

**Files:**
- Modify: `frontend/app/profile/page.tsx`
- Modify: `frontend/app/settings/page.tsx`

**Interfaces:**
- Consumes: DashboardShell, Card, updated tokens
- Produces: Visual refinement for profile and settings pages

- [ ] **Step 1: Update profile page with hero header**

Add hero header "Your profile" at top, wrap existing form fields in Card components, apply new theme.

- [ ] **Step 2: Update settings page with hero header**

Add hero header "Settings" at top, wrap sections in Cards, apply new theme.

- [ ] **Step 3: Verify build**

Run: `cd frontend && npx next build 2>&1 | tail -5`
Expected: Build succeeds

- [ ] **Step 4: Commit**

```bash
git add frontend/app/profile/page.tsx frontend/app/settings/page.tsx
git commit -m "refactor: update profile and settings with hero headers and new theme"
```

---

## Task 13: Update PageTransition Animation

**Files:**
- Modify: `frontend/src/shared/ui/PageTransition.tsx`

**Interfaces:**
- Consumes: None
- Produces: Updated transition with subtler animation (y: 8 instead of y: 12, damping 30)

- [ ] **Step 1: Update PageTransition.tsx**

Replace the animation values:

```tsx
initial={{ opacity: 0, y: 8 }}
animate={{ opacity: 1, y: 0 }}
transition={{ type: "spring", damping: 30, stiffness: 200 }}
```

- [ ] **Step 2: Verify build**

Run: `cd frontend && npx next build 2>&1 | tail -5`
Expected: Build succeeds

- [ ] **Step 3: Commit**

```bash
git add frontend/src/shared/ui/PageTransition.tsx
git commit -m "refactor: soften page transition animation"
```

---

## Task 14: Final Verification

- [ ] **Step 1: Full build check**

Run: `cd frontend && npx next build 2>&1 | tail -15`
Expected: All routes build successfully, no errors

- [ ] **Step 2: Visual smoke test**

Start dev server: `cd frontend && npm run dev`
Open http://localhost:3000 and verify:
- Dashboard loads with hero, metric rings, tabs
- Sidebar has Work/You groups with glass effect
- Search page has conversational input and is wrapped in DashboardShell
- Agents page has collapsible panel and is wrapped in DashboardShell
- Memory page has graph view and is wrapped in DashboardShell
- All pages have consistent navigation (sidebar always visible)
- No dead-end pages

- [ ] **Step 3: Final commit**

```bash
git add -A
git commit -m "refactor: complete UI refactor — warmer dark theme, consistent navigation, premium dashboard"
```
