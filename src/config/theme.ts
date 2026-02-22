/**
 * Theme configuration — all visual parameters in one place.
 *
 * This file is the single source of truth for:
 *   - Color palettes (per theme)
 *   - Typography scale
 *   - Layout dimensions
 *   - Transition timing
 *
 * Used by: global.css (via CSS custom properties), tailwind.config.mjs,
 * and components that need direct access to values.
 */

// ── Color Palettes ─────────────────────────────────────────

export interface ThemePalette {
  bg: string;
  bgSurface: string;
  text: string;
  textMuted: string;
  border: string;
  accent: string;
  link: string;
  /** Sidenote trigger text underline (default/inactive) */
  sidenoteHint: string;
  /** Sidenote trigger text when active/hovered */
  sidenoteActive: string;
  /** Sidenote content background (inline/accordion mode) */
  sidenoteBg: string;
  /** Sidenote content border-left */
  sidenoteBorder: string;
  /** Selection highlight */
  selection: string;
}

export const palettes: Record<string, ThemePalette> = {
  paper: {
    bg: '#F4F1EA',
    bgSurface: '#EDE9E0',
    text: '#2C2C2C',
    textMuted: '#6B6560',
    border: '#D4CFC6',
    accent: '#8B4513',
    link: '#8B4513',
    sidenoteHint: 'rgba(139, 69, 19, 0.3)',
    sidenoteActive: '#8B4513',
    sidenoteBg: '#EDE9E0',
    sidenoteBorder: '#8B4513',
    selection: 'rgba(139, 69, 19, 0.15)',
  },
  white: {
    bg: '#FAFAFA',
    bgSurface: '#F0F0F0',
    text: '#2C2C2C',
    textMuted: '#666666',
    border: '#E0E0E0',
    accent: '#8B4513',
    link: '#8B4513',
    sidenoteHint: 'rgba(139, 69, 19, 0.3)',
    sidenoteActive: '#8B4513',
    sidenoteBg: '#F0F0F0',
    sidenoteBorder: '#8B4513',
    selection: 'rgba(139, 69, 19, 0.15)',
  },
  dark: {
    bg: '#1A1A1A',
    bgSurface: '#242424',
    text: '#D4CFC6',
    textMuted: '#8A8580',
    border: '#3A3A3A',
    accent: '#C4875B',
    link: '#C4875B',
    sidenoteHint: 'rgba(196, 135, 91, 0.35)',
    sidenoteActive: '#C4875B',
    sidenoteBg: '#242424',
    sidenoteBorder: '#C4875B',
    selection: 'rgba(196, 135, 91, 0.2)',
  },
};

// ── Button Preview Colors (for settings panel) ────────────
// These are the visual appearance of theme selector buttons themselves
export const themeButtonStyles: Record<string, { bg: string; text: string }> = {
  paper: { bg: '#F4F1EA', text: '#2C2C2C' },
  white: { bg: '#FAFAFA', text: '#2C2C2C' },
  dark: { bg: '#1A1A1A', text: '#D4CFC6' },
};

// ── Typography ─────────────────────────────────────────────

export const typography = {
  fontFamilies: {
    serif: "'CJKExtB-Serif', 'CJKRare-Serif', 'Noto Serif SC', 'NushuSerif-Fallback', serif",
    sans: "'Noto Sans SC', sans-serif",
  },
  fontSizes: {
    small: '1rem',
    medium: '1.125rem',
    large: '1.25rem',
  },
  lineHeight: '1.9',
  /** Base font size for prose content */
  proseSize: '1.125rem',
} as const;

// ── Layout ─────────────────────────────────────────────────

export const layout = {
  /** Max width for prose content column */
  contentMaxWidth: '42rem',
  /** Width of the sidenote column on wide screens */
  sidenoteWidth: '14rem',
  /** Gap between content and sidenote columns */
  sidenoteGap: '2rem',
  /** Breakpoint at which sidenotes move to the side */
  sidenoteBreakpoint: '1200px',
  /** Drawer sidebar width */
  drawerWidth: '18rem',
  /** Progress bar height */
  progressBarHeight: '2px',
} as const;

// ── Transitions ────────────────────────────────────────────

export const transitions = {
  colorDuration: '0.3s',
  colorEasing: 'ease',
  viewTransitionDuration: '0.15s',
} as const;
