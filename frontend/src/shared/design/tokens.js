/**
 * Cortex Design Tokens
 * 
 * Minimal dark theme with cyan accent.
 * All colors, spacing, typography, and motion in one place.
 */

const tokens = {
  colors: {
    // Backgrounds
    bg: '#09090b',
    'bg-surface': '#131316',
    'bg-card': '#18181b',
    'bg-elevated': '#1f1f23',
    'bg-hover': '#27272a',

    // Borders
    border: '#27272a',
    'border-subtle': '#1f1f23',

    // Text
    text: '#fafafa',
    'text-secondary': '#a1a1aa',
    'text-muted': '#71717a',

    // Accent — cyan
    accent: '#06b6d4',
    'accent-hover': '#22d3ee',
    'accent-muted': 'rgba(6, 182, 212, 0.12)',
    'accent-faint': 'rgba(6, 182, 212, 0.06)',

    // Semantic
    error: '#ef4444',
    'error-muted': 'rgba(239, 68, 68, 0.12)',
    success: '#22c55e',
    'success-muted': 'rgba(34, 197, 94, 0.12)',
  },

  fontFamily: {
    sans: ['var(--font-inter)', 'system-ui', 'sans-serif'],
    mono: ['var(--font-jetbrains-mono)', 'monospace'],
  },

  borderRadius: {
    sm: '6px',
    md: '8px',
    lg: '12px',
    full: '9999px',
  },

  boxShadow: {
    subtle: '0 1px 2px rgba(0,0,0,0.3)',
    card: '0 2px 8px rgba(0,0,0,0.3), 0 0 0 1px rgba(255,255,255,0.03)',
    glow: '0 0 20px rgba(6,182,212,0.1)',
  },

  maxWidth: {
    content: '1120px',
    narrow: '640px',
  },
};

export default tokens;
