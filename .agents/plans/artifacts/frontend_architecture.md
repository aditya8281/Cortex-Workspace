# Frontend Architecture — CORTEX

**Document:** Frontend Application Architecture
**Authority:** Stage 5 — Repository & Architecture Restructure
**Date:** 2026-06-27

---

## Purpose

This document defines the frontend architecture for Cortex. It specifies the application structure, navigation, feature organization, component hierarchy, and state management. The design communicates trust, intelligence, calmness, and professionalism.

---

## Design Direction

Cortex's interface should feel like interacting with an intelligent operating layer — not a chatbot, not a dashboard, not a code editor.

**Primary color:** Warm Black (#0A0A0B)
**Secondary color:** Electric Cyan (#00F0FF)

The interface should feel:
- **Trustworthy** — clear, honest, predictable
- **Intelligent** — deep, capable, understanding
- **Calm** — not noisy, not demanding, not overwhelming
- **Professional** — technical depth without complexity
- **Warm** — approachable despite its power

---

## Application Structure

```
frontend/src/
├── app/                        # Next.js App Router
│   ├── layout.tsx              # Root layout
│   ├── page.tsx                # Landing/redirect
│   ├── (auth)/                 # Auth pages
│   │   ├── login/page.tsx
│   │   └── register/page.tsx
│   ├── (dashboard)/            # Main application
│   │   ├── layout.tsx          # Dashboard layout
│   │   ├── page.tsx            # Dashboard home
│   │   ├── memory/             # Memory pages
│   │   ├── conversations/      # Conversation pages
│   │   ├── repositories/       # Repository pages
│   │   ├── documents/          # Document pages
│   │   ├── search/             # Search pages
│   │   ├── agents/             # Agent pages
│   │   ├── notifications/      # Notification pages
│   │   ├── settings/           # Settings pages
│   │   └── system/             # System pages
│   └── api/                    # API proxy routes
│
├── features/                   # Feature modules
│   ├── memory/                 # Memory feature
│   ├── conversations/          # Conversation feature
│   ├── repositories/           # Repository feature
│   ├── documents/              # Document feature
│   ├── search/                 # Search feature
│   ├── agents/                 # Agent feature
│   ├── notifications/          # Notification feature
│   ├── settings/               # Settings feature
│   └── system/                 # System feature
│
├── shared/                     # Shared components
│   ├── components/             # Shared UI components
│   ├── hooks/                  # Shared hooks
│   ├── services/               # Shared services
│   ├── design/                 # Design system
│   └── ui/                     # UI primitives
│
├── lib/                        # Utilities
│   ├── types/
│   ├── utils/
│   └── constants/
│
└── design/                     # Design system
    ├── tokens.ts
    ├── colors.ts
    ├── typography.ts
    ├── spacing.ts
    └── animations.ts
```

---

## Navigation Architecture

### Sidebar Navigation

```
┌──────────────────────────────┐
│  CORTEX                     │  Logo
│  ─────────────────────────  │
│  🏠 Dashboard               │  /dashboard
│  🧠 Memory                  │  /memory
│  💬 Conversations           │  /conversations
│  📁 Repositories            │  /repositories
│  📄 Documents               │  /documents
│  🔍 Search                  │  /search
│  🤖 Agents                  │  /agents
│  🔔 Notifications           │  /notifications
│  ─────────────────────────  │
│  ⚙️ Settings                │  /settings
│  📊 System                  │  /system
│  ─────────────────────────  │
│  ● Online                   │  Status indicator
│  v1.0.0                     │  Version
└──────────────────────────────┘
```

### Navigation Behaviors

| Screen | Sidebar | Behavior |
|--------|---------|----------|
| Desktop (≥1200px) | 240px fixed | Always visible |
| Tablet (768-1199px) | 240px overlay | Toggle with hamburger |
| Mobile (<768px) | Bottom tabs | Replaces sidebar |

---

## Page Architecture

### Dashboard Home

```
┌─────────────────────────────────────────────────────────────┐
│  Dashboard                                      🔔  👤     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Memory       │  │ Active       │  │ Recent       │     │
│  │ Status       │  │ Projects     │  │ Activity     │     │
│  │              │  │              │  │              │     │
│  │ 1,247 items  │  │ 3 projects   │  │ 12 events    │     │
│  │ 89% quality  │  │ 2 active     │  │ today        │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Recent Conversations                                  │  │
│  │ ...                                                  │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ System Health                                         │  │
│  │ CPU: 12%  Memory: 45%  Disk: 67%  Uptime: 3d 2h    │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Memory Page

```
┌─────────────────────────────────────────────────────────────┐
│  Memory                                          🔍 Search │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────────────────────────────┐  │
│  │ Filters     │  │ Memory List                          │  │
│  │             │  │                                      │  │
│  │ □ Episodic  │  │  📅 Meeting with Alex - discussed   │  │
│  │ □ Semantic  │  │     Q3 roadmap (2 hours ago)         │  │
│  │ □ Working   │  │                                      │  │
│  │             │  │  📚 Learned that Cortex uses ONNX   │  │
│  │ Timeframe   │  │     for embeddings (1 day ago)       │  │
│  │ ○ Last hour │  │                                      │  │
│  │ ○ Last day  │  │  🔧 Fixed auth middleware bug        │  │
│  │ ○ Last week │  │     (3 days ago)                     │  │
│  │ ○ Custom    │  │                                      │  │
│  │             │  │  ...                                 │  │
│  │ Confidence  │  │                                      │  │
│  │ ████░░ 65%  │  │                                      │  │
│  └─────────────┘  └─────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Knowledge Graph                                       │  │
│  │ [Interactive graph visualization]                     │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Conversation Page

```
┌─────────────────────────────────────────────────────────────┐
│  Conversation                                    ⚙️ Options│
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                                                      │  │
│  │  You: What's the status of the memory system?        │  │
│  │                                                      │  │
│  │  Cortex: The memory system currently has 1,247       │  │
│  │  items stored. Episodic memory has 89% quality       │  │
│  │  score. Semantic memory has 342 knowledge items.     │  │
│  │  Memory consolidation ran 2 hours ago and            │  │
│  │  strengthened 23 memories.                           │  │
│  │                                                      │  │
│  │  You: Show me the knowledge graph                    │  │
│  │                                                      │  │
│  │  Cortex: [Knowledge graph visualization]             │  │
│  │                                                      │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Type a message...                              Send → │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Hierarchy

```
App
├── AuthProvider
├── RootLayout
├── (auth)
│   ├── LoginPage
│   └── RegisterPage
└── (dashboard)
    ├── DashboardLayout
    │   ├── Sidebar
    │   │   ├── Logo
    │   │   ├── NavigationLinks
    │   │   ├── DomainStatus
    │   │   └── SystemStatus
    │   ├── Header
    │   │   ├── SearchBar
    │   │   ├── NotificationCenter
    │   │   └── UserMenu
    │   └── ContentArea
    │       ├── DashboardPage
    │       ├── MemoryPage
    │       │   ├── MemoryFilters
    │       │   ├── MemoryList
    │       │   ├── MemoryDetail
    │       │   └── KnowledgeGraph
    │       ├── ConversationsPage
    │       │   ├── ConversationList
    │       │   ├── ConversationView
    │       │   └── MessageInput
    │       ├── RepositoriesPage
    │       ├── DocumentsPage
    │       ├── SearchPage
    │       ├── AgentsPage
    │       ├── NotificationsPage
    │       ├── SettingsPage
    │       └── SystemPage
    └── BackgroundLayer
        └── VisualIdentity (canvas animation)
```

---

## Feature Module Structure

Each feature follows this structure:

```
features/{domain}/
├── components/         # Domain-specific components
│   ├── {Domain}Page.tsx
│   ├── {Domain}List.tsx
│   ├── {Domain}Detail.tsx
│   └── {Domain}Filters.tsx
├── hooks/              # Domain-specific hooks
│   ├── use{Domain}.ts
│   └── use{Domain}Api.ts
├── services/           # Domain API calls
│   └── {domain}Api.ts
└── types/              # Domain types
    └── {domain}.ts
```

---

## State Management

### Authentication State
- **Provider:** React Context (`AuthProvider`)
- **Persistence:** httpOnly cookies (JWT)
- **Refresh:** Auto-refresh on 401

### Component State
- **Pattern:** useState/useReducer per component
- **No global state library.** Component-local keeps things simple.

### Server State
- **Pattern:** Direct API calls with React Suspense
- **Caching:** React Query (optional, for complex data)
- **Streaming:** ReadableStream for SSE

### Design System State
- **Tokens:** Static TypeScript constants
- **Theme:** Dark-only (no theme switching)
- **Responsive:** CSS media queries + React hooks

---

## API Communication

```
Client → Next.js API Route → FastAPI Backend
```

All API calls go through Next.js API routes (same-origin proxy). This avoids CORS issues and keeps the backend internal.

### API Client

```typescript
// shared/services/api.ts
const API_BASE = '/api/v1';

async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`);
  if (response.status === 401) {
    // Auto-refresh token
    await refreshToken();
    return apiGet(path);
  }
  return response.json();
}
```

### SSE Streaming

```typescript
// shared/hooks/useSSE.ts
function useSSE(url: string, onMessage: (data: any) => void) {
  useEffect(() => {
    const eventSource = new EventSource(url);
    eventSource.onmessage = (event) => {
      onMessage(JSON.parse(event.data));
    };
    return () => eventSource.close();
  }, [url]);
}
```

---

## Responsive Breakpoints

| Breakpoint | Width | Sidebar | Layout |
|------------|-------|---------|--------|
| Desktop | ≥1200px | 240px fixed | Side-by-side |
| Tablet | 768-1199px | 240px overlay | Overlay |
| Mobile | <768px | Bottom tabs | Stacked |

---

## Accessibility

- All components follow WCAG 2.1 AA
- Keyboard navigation for all interactive elements
- Screen reader labels for all icons
- Color contrast ratios meet AA standards
- Focus indicators visible on all interactive elements

---

## Performance Targets

| Metric | Target |
|--------|--------|
| First Contentful Paint | <1.5s |
| Largest Contentful Paint | <2.5s |
| Time to Interactive | <3.0s |
| Cumulative Layout Shift | <0.1 |
| Bundle Size | <200KB gzipped |

---

## Design System

### Design Philosophy

Cortex's interface should feel like interacting with an intelligent operating layer. Not a chatbot. Not a dashboard. Not a code editor. An intelligent companion's visual presence.

**Key qualities:**
- **Trustworthy** — clear, honest, predictable
- **Intelligent** — deep, capable, understanding
- **Calm** — not noisy, not demanding, not overwhelming
- **Professional** — technical depth without complexity
- **Warm** — approachable despite its power

### Color System

#### Primary Colors

| Name | Hex | Usage |
|------|-----|-------|
| Warm Black | #0A0A0B | Background, primary surface |
| Deep Charcoal | #141416 | Elevated surfaces, cards |
| Soft Gray | #1E1E22 | Borders, dividers |
| Muted Gray | #2A2A30 | Secondary text |
| Light Gray | #8A8A95 | Tertiary text, icons |
| Off White | #E8E8ED | Primary text |
| Pure White | #F5F5F7 | Headings, emphasis |

#### Accent Colors

| Name | Hex | Usage |
|------|-----|-------|
| Electric Cyan | #00F0FF | Primary accent, links, active states |
| Cyan Glow | #00F0FF33 | Hover states, subtle highlights |
| Cyan Deep | #0080AA | Pressed states |
| Warm Amber | #FFB347 | Warnings, attention |
| Success Green | #34D399 | Success states |
| Error Red | #EF4444 | Error states |

#### Gradient System

| Name | Usage |
|------|-------|
| Surface Gradient | Linear from #0A0A0B to #141416 |
| Card Gradient | Linear from #141416 to #1E1E22 |
| Accent Gradient | Linear from #00F0FF to #0080AA |
| Glow Gradient | Radial from #00F0FF33 to transparent |

### Typography

#### Font Stack

```css
--font-primary: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
--font-mono: 'JetBrains Mono', 'Fira Code', monospace;
```

#### Type Scale

| Name | Size | Weight | Usage |
|------|------|--------|-------|
| Display | 32px | 700 | Page titles |
| Heading 1 | 24px | 600 | Section headings |
| Heading 2 | 20px | 600 | Subsection headings |
| Heading 3 | 16px | 600 | Card titles |
| Body Large | 16px | 400 | Primary content |
| Body | 14px | 400 | Standard text |
| Body Small | 12px | 400 | Secondary text |
| Caption | 11px | 400 | Labels, timestamps |
| Mono | 14px | 400 | Code, data |

### Spacing Scale

| Token | Value | Usage |
|-------|-------|-------|
| space-0 | 0px | — |
| space-1 | 4px | Tight spacing |
| space-2 | 8px | Compact spacing |
| space-3 | 12px | Default spacing |
| space-4 | 16px | Comfortable spacing |
| space-5 | 20px | Loose spacing |
| space-6 | 24px | Section spacing |
| space-8 | 32px | Large section spacing |
| space-10 | 40px | Page spacing |
| space-12 | 48px | Major section spacing |

### Border Radius

| Token | Value | Usage |
|-------|-------|-------|
| radius-sm | 4px | Buttons, inputs |
| radius-md | 8px | Cards, modals |
| radius-lg | 12px | Large cards, panels |
| radius-xl | 16px | Feature cards |
| radius-full | 9999px | Avatars, badges |

### Shadows

| Name | Usage |
|------|-------|
| shadow-sm | Subtle elevation for cards |
| shadow-md | Medium elevation for modals |
| shadow-lg | High elevation for overlays |
| shadow-glow | Cyan glow effect for active elements |

### Component Library

#### Button

```typescript
interface ButtonProps {
  variant: 'primary' | 'secondary' | 'ghost' | 'danger';
  size: 'sm' | 'md' | 'lg';
  icon?: React.ReactNode;
  loading?: boolean;
  disabled?: boolean;
  children: React.ReactNode;
}
```

**Variants:**
- **Primary:** Electric Cyan background, black text
- **Secondary:** Transparent background, cyan border, cyan text
- **Ghost:** Transparent background, gray text, hover highlights
- **Danger:** Red background, white text

#### Input

```typescript
interface InputProps {
  type: 'text' | 'password' | 'email' | 'search';
  placeholder?: string;
  icon?: React.ReactNode;
  error?: string;
  disabled?: boolean;
}
```

**States:**
- Default: Soft Gray border
- Focus: Electric Cyan border with glow
- Error: Red border
- Disabled: Muted Gray background

#### Card

```typescript
interface CardProps {
  variant: 'default' | 'elevated' | 'interactive';
  padding?: 'sm' | 'md' | 'lg';
  children: React.ReactNode;
}
```

**Variants:**
- **Default:** Deep Charcoal background, Soft Gray border
- **Elevated:** Higher elevation, subtle shadow
- **Interactive:** Hover effect, clickable

#### Modal

```typescript
interface ModalProps {
  open: boolean;
  onClose: () => void;
  title?: string;
  size?: 'sm' | 'md' | 'lg';
  children: React.ReactNode;
}
```

**Behavior:**
- Backdrop: Semi-transparent black
- Animation: Scale from 0.95 to 1.0
- Focus trap: Yes
- Close on escape: Yes

#### Toast

```typescript
interface ToastProps {
  type: 'success' | 'error' | 'warning' | 'info';
  message: string;
  duration?: number;
  action?: { label: string; onClick: () => void };
}
```

**Position:** Bottom-right
**Animation:** Slide in from right

#### Sidebar

```typescript
interface SidebarProps {
  collapsed?: boolean;
  onToggle?: () => void;
}
```

**Design:**
- Width: 240px (expanded), 64px (collapsed)
- Background: Warm Black
- Active item: Electric Cyan highlight
- Hover: Subtle gray highlight

#### SearchBar

```typescript
interface SearchBarProps {
  placeholder?: string;
  onSearch: (query: string) => void;
  loading?: boolean;
}
```

**Design:**
- Full width within header
- Electric Cyan focus ring
- Loading state: subtle pulse animation

### Animation Principles

1. **Purposeful:** Every animation communicates something
2. **Subtle:** Animations should not distract
3. **Consistent:** Same element, same animation, always
4. **Fast:** 150-300ms for most transitions
5. **Smooth:** Ease-out for entrances, ease-in for exits

#### Standard Transitions

| Element | Duration | Easing |
|---------|----------|--------|
| Button hover | 150ms | ease-out |
| Card hover | 200ms | ease-out |
| Modal open | 250ms | ease-out |
| Page transition | 300ms | ease-in-out |
| Toast enter | 250ms | ease-out |
| Toast exit | 200ms | ease-in |

#### Loading States

| State | Animation |
|-------|-----------|
| Skeleton | Shimmer effect (gradient animation) |
| Spinner | Rotating circle with Electric Cyan |
| Pulse | Subtle opacity pulse |
| Progress | Linear bar with gradient |

### Visual Identity

#### Background Animation

The canvas animation should represent **knowledge networks** — nodes and edges forming, strengthening, and evolving.

**Concept:** Dynamic graph visualization where:
- Nodes represent knowledge items
- Edges represent connections
- Active nodes glow Electric Cyan
- Connections form and strengthen over time
- The graph breathes — subtle pulsing of active nodes

**Rules:**
- Always subtle (low opacity, slow movement)
- Never distracting from content
- Responsive to system state (more active = more movement)
- Smooth 60fps animation

#### Status Indicators

| Status | Color | Animation |
|--------|-------|-----------|
| Online | Success Green | Subtle pulse |
| Processing | Electric Cyan | Rotating ring |
| Warning | Warm Amber | Static |
| Error | Error Red | Static |
| Offline | Muted Gray | Static |

### Dark Theme Only

Cortex uses dark theme exclusively. Rationale:
1. Dark theme reduces eye strain for long sessions
2. Dark theme communicates technical depth
3. Dark theme aligns with "calm technology" philosophy
4. Light theme would require separate design effort with minimal user benefit

**No theme switching.** Dark theme is the only theme.

### Icon System

**Library:** Lucide React (consistent, modern, customizable)
**Size:** 16px (small), 20px (default), 24px (large)
**Color:** Inherit from parent (usually Light Gray, Electric Cyan for active)

### Responsive Design

| Breakpoint | Width | Sidebar | Content | Navigation |
|------------|-------|---------|---------|------------|
| Desktop | ≥1200px | 240px fixed | Full width | Sidebar |
| Tablet | 768-1199px | 240px overlay | Full width | Hamburger |
| Mobile | <768px | Hidden | Full width | Bottom tabs |

#### Mobile Bottom Tabs

```
┌─────────────────────────────────────────┐
│  🏠  🧠  💬  🔍  ⚙️                    │
│  Home Memory Chat Search Settings       │
└─────────────────────────────────────────┘
```
