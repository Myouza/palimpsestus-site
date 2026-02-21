/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        paper: {
          DEFAULT: '#F4F1EA',
          white: '#FAFAFA',
          dark: '#1A1A1A',
          'dark-surface': '#242424',
        },
        ink: {
          DEFAULT: '#2C2C2C',
          light: '#E8E4DC',
          muted: '#6B6560',
          'dark-muted': '#8A8580',
        },
        accent: {
          DEFAULT: '#8B4513',
          light: '#A0522D',
        },
      },
      fontFamily: {
        serif: ['"Noto Serif SC"', '"Nushu"', 'serif'],
        kai: ['"LXGW WenKai"', 'serif'],
      },
      typography: ({ theme }) => ({
        paper: {
          css: {
            '--tw-prose-body': theme('colors.ink.DEFAULT'),
            '--tw-prose-headings': theme('colors.ink.DEFAULT'),
            '--tw-prose-links': theme('colors.accent.DEFAULT'),
            '--tw-prose-bold': theme('colors.ink.DEFAULT'),
            '--tw-prose-quotes': theme('colors.ink.muted'),
            '--tw-prose-quote-borders': theme('colors.accent.DEFAULT'),
            '--tw-prose-hr': theme('colors.ink.light'),
            maxWidth: '100%',
            lineHeight: '1.9',
            fontSize: 'var(--font-size, 1.125rem)',
            fontFamily: 'var(--font-family)',
            p: {
              textIndent: '2em',
              marginTop: '0.8em',
              marginBottom: '0.8em',
            },
            'h1, h2, h3': {
              textIndent: '0',
              fontWeight: '600',
            },
            blockquote: {
              borderLeftWidth: '2px',
              fontStyle: 'normal',
            },
          },
        },
      }),
    },
  },
  plugins: [require('@tailwindcss/typography')],
};
