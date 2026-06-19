# Cortex Frontend Redesign — Design Spec

## Overview

Complete redesign of the Cortex frontend from a basic dark theme to a cinematic, AI-native operating system interface. The design follows a "Neural Dark" identity: monochrome dark canvas with a single electric cyan pulse as the living accent. The UI should feel like a living intelligence — responsive, fluid, and alive.

## Design Principles

1. **Neural Dark**: Deep black canvas (#000000 → #050508) with electric cyan (#06b6d4) as the single accent color
2. **Hybrid Density**: Clean minimal default view with expandable detail panels (progressive disclosure)
3. **Living Motion**: Every animation has meaning — spring physics, shared element transitions, ambient glow
4. **AI-Native**: The interface should feel like interacting with an intelligence, not a dashboard

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | Next.js 15 (App Router) + React 19 + TypeScript |
| Styling | Tailwind CSS 3.4 with custom design tokens |
| Animations | framer-motion (page transitions, layout animations, gestures, 3D) |
| Icons | lucide-react |
| 3D | three.js + @react-three/fiber + @react-three/drei (landing hero only) |
| UI Primitives | @radix-ui (dialog, dropdown-menu, tooltip) |
| Command Palette | cmdk |
| Toasts | sonner |
| Utilities | clsx + tailwind-merge |
| Fonts | Geist (display), Inter (body), Geist Mono/JetBrains Mono (mono) |

## Color System

| Token | Value | Usage |
|-------|-------|-------|
| `--bg-void` | `#000000` | Deep canvas |
| `--bg-base` | `#050508` | Page surface |
| `--bg-elevated` | `#0a0a0f` | Cards, panels |
| `--bg-surface` | `#111118` | Interactive surfaces |
| `--bg-hover` | `#1a1a24` | Hover states |
| `--border-subtle` | `rgba(255,255,255,0.06)` | Hairline borders |
| `--border-default` | `rgba(255,255,255,0.10)` | Standard borders |
| `--border-accent` | `rgba(6,182,212,0.3)` | Accent borders |
| `--text-primary` | `#f0f0f5` | Primary text |
| `--text-secondary` | `#8a8a9a` | Supporting text |
| `--text-muted` | `#555566` | Hints, labels |
| `--accent` | `#06b6d4` | Primary accent |
| `--accent-glow` | `rgba(6,182,212,0.15)` | Glow effects |
| `--accent-bright` | `#22d3ee` | Hover accent |
| `--danger` | `#ef4444` | Destructive |
| `--success` | `#22c55e` | Positive |

## Typography

| Role | Font | Weights | Usage |
|------|------|---------|-------|
| Display | Geist | 500, 600, 700 | Hero headings, page titles |
| Body | Inter | 400, 500, 600 | Body text, forms, controls |
| Mono | Geist Mono / JetBrains Mono | 400, 500 | Code, labels, metadata |

## Page Designs

### 1. Landing Page (`/`) — "Neural Gateway"

- Full-viewport hero with animated 3D particle network (react-three-fiber)
- Cortex logo pulses with cyan glow at network center
- Tagline with typewriter entrance effect
- Two CTAs: "Enter Cortex" (glowing accent) + "GitHub" (ghost)
- Scroll-triggered feature cards with 3D hover tilt
- Minimal footer

### 2. Auth Page (`/auth`) — "Neural Handshake"

- Split layout: left = animated visualization, right = form
- Login/Register toggle with smooth slide transition
- 4-step wizard with animated progress bar
- Form inputs with cyan focus glow, error shake
- Vault step with shield animation

### 3. Dashboard (`/app`) — "Command Center"

- Welcome section with avatar (glow ring)
- 4 stat cards with animated counters
- Quick-action grid with 3D hover tilt
- Activity timeline placeholder
- Breathing glow on status indicator

### 4. Vault (`/vault`) — "Encrypted Nexus"

- 3-panel resizable layout
- Folder tree with expand/collapse animations
- File views with smooth morphing transitions
- Drag-and-drop with visual feedback
- Lock screen with cinematic animation

### 5. Memory (`/memory`) — "Knowledge Web"

- Card-based layout with category filtering
- Staggered card entrance
- Create/edit modal
- Category tabs with sliding indicator

### 6. Profile (`/profile`) — "Identity Matrix"

- Avatar with glow ring and upload overlay
- Floating label form fields
- GitHub connection with animated status

### 7. Settings (`/settings`) — "System Config"

- Clean card sections
- Danger zone with red border separation
- Confirmation modals

### 8. Admin (`/admin`) — "Control Panel"

- Sortable/filterable user table
- Action buttons with confirmation
- Role badges

## Layout & Navigation

- **Desktop (≥1024px)**: Collapsible sidebar (icon-only mode available)
- **Tablet (768-1023px)**: Overlay sidebar with backdrop blur
- **Mobile (<768px)**: Bottom tab bar + hamburger for secondary
- Glass morphism sidebar with backdrop blur
- Sliding cyan accent indicator for active nav
- Sticky glass morphism header
- ⌘K command palette trigger in header

## Animation System

### Page Transitions
- Directional slides (forward: right→left, back: left→right)
- Crossfade with subtle scale
- Spring physics: damping 25, stiffness 200

### Micro-interactions
- Buttons: scale 0.97 on press, glow pulse on hover
- Cards: 3D tilt on mouse move (perspective)
- Nav: sliding accent indicator
- Inputs: border glow on focus
- Success: spring bounce entrance

### Ambient Effects
- Landing: animated particle network (three.js)
- Dashboard: breathing glow on accent dot
- Backgrounds: subtle floating gradient orbs
- Vault lock: matrix-style falling characters (toggleable)

### Loading States
- Skeleton shimmer for data fetching
- Staggered content reveal
- Spinner → content crossfade

## Responsive Strategy

- Breakpoints: 375 / 768 / 1024 / 1440
- Mobile-first single column
- Touch targets ≥44px on mobile
- Bottom nav on mobile, sidebar on desktop
- Vault: bottom sheet for properties on mobile

## Accessibility

- Visible focus rings on all interactive elements
- Keyboard navigation (Radix primitives)
- `prefers-reduced-motion` support
- Color contrast ≥4.5:1
- ARIA labels for icon-only buttons
- Skip-to-content link
- Proper heading hierarchy

## API Integration

All existing API contracts remain unchanged. The frontend API client (`cortexApi.ts`) is preserved as-is. New features:
- Add automatic token refresh flow (currently unused `apiRefresh`)
- Add WebSocket connection for real-time vault status updates (future)
- Toast notifications for all async operations via sonner

## File Structure (New)

```
frontend/
├── app/
│   ├── layout.tsx              # Root layout (fonts, providers)
│   ├── page.tsx                # Landing page
│   ├── globals.css             # Tailwind + design tokens
│   ├── auth/page.tsx           # Auth page
│   ├── app/page.tsx            # Dashboard
│   ├── vault/page.tsx          # Vault
│   ├── memory/page.tsx         # Memory
│   ├── profile/page.tsx        # Profile
│   ├── settings/page.tsx       # Settings
│   ├── admin/page.tsx          # Admin
│   └── api/[...path]/route.ts  # API proxy
├── src/
│   ├── shared/
│   │   ├── auth/               # AuthProvider, cortexApi, session
│   │   ├── design/             # tokens.ts
│   │   ├── layout/             # DashboardShell, Sidebar, Header
│   │   ├── types.ts
│   │   └── ui/                 # Reusable components
│   │       ├── Button.tsx
│   │       ├── Input.tsx
│   │       ├── Card.tsx
│   │       ├── Modal.tsx
│   │       ├── Dropdown.tsx
│   │       ├── Tooltip.tsx
│   │       ├── Badge.tsx
│   │       ├── Skeleton.tsx
│   │       ├── CommandPalette.tsx
│   │       ├── Toast.tsx
│   │       ├── NeuralBackground.tsx
│   │       ├── GlowOrb.tsx
│   │       ├── PageTransition.tsx
│   │       ├── StaggerChildren.tsx
│   │       ├── PasswordStrength.tsx
│   │       ├── Steps.tsx
│   │       └── ErrorBoundary.tsx
│   └── lib/
│       └── utils.ts            # cn() utility
```
