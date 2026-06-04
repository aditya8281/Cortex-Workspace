/**
 * Cortex Design System
 * Global design tokens, colors, spacing, and utility classes
 */

export const designSystem = {
  colors: {
    // Base palette
    background: '#0f0f0f',
    surface: '#1a1a1a',
    surfaceHover: '#252525',
    border: '#2d2d2d',
    borderLight: '#3a3a3a',

    // Text
    text: {
      primary: '#ffffff',
      secondary: '#b0b0b0',
      tertiary: '#808080',
      muted: '#606060',
    },

    // Accent (primary action)
    accent: '#3b82f6', // Blue
    accentHover: '#2563eb',
    accentActive: '#1d4ed8',
    accentLight: '#eff6ff',
    accentDark: '#172554',

    // Semantic
    success: '#10b981',
    warning: '#f59e0b',
    error: '#ef4444',
    info: '#06b6d4',

    // States
    disabled: '#4a4a4a',
    disabledText: '#6b6b6b',
  },

  spacing: {
    xs: '4px',
    sm: '8px',
    md: '12px',
    lg: '16px',
    xl: '24px',
    xxl: '32px',
    xxxl: '48px',
  },

  radius: {
    sm: '4px',
    md: '8px',
    lg: '12px',
    xl: '16px',
  },

  typography: {
    fontFamily: {
      base: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
      mono: "'Fira Code', 'Courier New', monospace",
    },
    fontSize: {
      xs: '12px',
      sm: '13px',
      base: '14px',
      lg: '16px',
      xl: '18px',
      xxl: '20px',
      xxxl: '24px',
      huge: '32px',
    },
    fontWeight: {
      light: 300,
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
    },
    lineHeight: {
      tight: 1.2,
      normal: 1.5,
      relaxed: 1.7,
    },
  },

  transitions: {
    fast: '150ms cubic-bezier(0.4, 0, 0.2, 1)',
    base: '200ms cubic-bezier(0.4, 0, 0.2, 1)',
    slow: '300ms cubic-bezier(0.4, 0, 0.2, 1)',
  },

  shadows: {
    sm: '0 1px 2px 0 rgba(0, 0, 0, 0.3)',
    md: '0 4px 6px 0 rgba(0, 0, 0, 0.4)',
    lg: '0 10px 15px 0 rgba(0, 0, 0, 0.5)',
    xl: '0 20px 25px 0 rgba(0, 0, 0, 0.6)',
  },

  zIndex: {
    base: 1,
    dropdown: 100,
    sticky: 200,
    fixed: 300,
    modal: 400,
    tooltip: 500,
  },
};

export type DesignSystem = typeof designSystem;
