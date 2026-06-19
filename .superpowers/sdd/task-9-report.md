# Task 9: Redesign Landing Page

**Status:** DONE

## Changes

- Replaced `frontend/app/page.tsx` with immersive landing page
- Added CSS particle dots with animated cyan glow (40 particles with randomized positions, sizes, drift, and opacity)
- Added Cortex logo with breathing glow animation (framer-motion animated box-shadow)
- Added typewriter tagline effect ("Your AI workspace, locally run." with cursor blink)
- Two CTAs: "Enter Cortex" (accent button with glow) + "GitHub" (ghost button with inline SVG icon)
- Added GlowOrb ambient effects in hero background
- Added scroll-triggered feature cards with 3D hover tilt (CSS perspective transform + framer-motion)
- Staggered card entrance animation using `useInView` + delay
- Added scroll indicator mouse wheel at bottom of hero
- Minimal footer preserved
- Uses design tokens: bg, bg-elevated, bg-surface, accent, text, text-secondary, text-muted
- Uses: framer-motion, lucide-react (ArrowRight, Shield, Brain, Cpu, Lock), GlowOrb, AuthRedirect

## Notes

- `Github` icon is not exported from lucide-react — used inline SVG instead (same as original)
- Pre-existing lint warnings in auth/page.tsx, memory/page.tsx, profile/page.tsx (setState in effects) are unrelated to this task
- Clean `.next` cache was needed to resolve stale build artifacts
