import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./app/**/*.{ts,tsx}', './components/**/*.{ts,tsx}', './lib/**/*.{ts,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        gold: {
          DEFAULT: 'var(--gold-primary)',
          light: 'var(--gold-light)',
          dark: 'var(--gold-dark)',
        },
        bg: {
          primary: 'var(--bg-primary)',
          secondary: 'var(--bg-secondary)',
        },
        bull: { DEFAULT: 'var(--bull-green)' },
        bear: { DEFAULT: 'var(--bear-red)' },
        muted: 'var(--text-muted)',
        nav: 'var(--nav-blue)',
        warn: 'var(--warn-yellow)',
        alert: 'var(--alert-orange)',
      },
      fontFamily: {
        sans: ['var(--font-tajawal)', 'var(--font-inter)', 'system-ui', 'sans-serif'],
        display: ['var(--font-playfair)', 'serif'],
        mono: ['var(--font-jb)', 'monospace'],
      },
      boxShadow: {
        glow: '0 0 12px rgba(201,162,39,0.45)',
        'glow-soft': '0 0 6px rgba(201,162,39,0.20)',
      },
      animation: {
        'pulse-soft': 'pulse 2.5s ease-in-out infinite',
        flash: 'flash 0.6s ease-out',
        marquee: 'marquee 40s linear infinite',
      },
      keyframes: {
        flash: {
          '0%': { backgroundColor: 'rgba(201,162,39,0.20)' },
          '100%': { backgroundColor: 'transparent' },
        },
        marquee: {
          '0%': { transform: 'translateX(0)' },
          '100%': { transform: 'translateX(-50%)' },
        },
      },
    },
  },
  plugins: [],
};
export default config;
