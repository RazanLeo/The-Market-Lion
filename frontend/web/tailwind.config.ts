import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // The Market Lion Brand Colors
        gold: {
          50:  '#fefce8',
          100: '#fef9c3',
          200: '#fef08a',
          300: '#fde047',
          400: '#facc15',
          500: '#C9A227',  // Primary gold
          600: '#b8941f',
          700: '#a07818',
          800: '#856012',
          900: '#6b4c0e',
        },
        dark: {
          50:  '#1a1a1a',
          100: '#141414',
          200: '#0f0f0f',
          300: '#0A0A0A',  // Main background
          400: '#060606',
          500: '#030303',
        },
        bull: {
          DEFAULT: '#0E7A2C',
          light: '#10a33a',
          dark: '#0a5e21',
        },
        bear: {
          DEFAULT: '#B0140C',
          light: '#d01810',
          dark: '#8a0f09',
        },
        neutral: {
          DEFAULT: '#6b7280',
          light: '#9ca3af',
        },
      },
      fontFamily: {
        arabic: ['Cairo', 'Tajawal', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      animation: {
        'pulse-gold': 'pulse-gold 2s ease-in-out infinite',
        'slide-up': 'slide-up 0.3s ease-out',
        'fade-in': 'fade-in 0.2s ease-in',
        'ticker': 'ticker 30s linear infinite',
        'lion-glow': 'lion-glow 3s ease-in-out infinite',
      },
      keyframes: {
        'pulse-gold': {
          '0%, 100%': { opacity: '1', boxShadow: '0 0 0 0 rgba(201, 162, 39, 0.4)' },
          '50%': { opacity: '0.8', boxShadow: '0 0 0 8px rgba(201, 162, 39, 0)' },
        },
        'slide-up': {
          from: { transform: 'translateY(10px)', opacity: '0' },
          to: { transform: 'translateY(0)', opacity: '1' },
        },
        'fade-in': {
          from: { opacity: '0' },
          to: { opacity: '1' },
        },
        'ticker': {
          from: { transform: 'translateX(100%)' },
          to: { transform: 'translateX(-100%)' },
        },
        'lion-glow': {
          '0%, 100%': { filter: 'drop-shadow(0 0 8px rgba(201, 162, 39, 0.6))' },
          '50%': { filter: 'drop-shadow(0 0 20px rgba(201, 162, 39, 1))' },
        },
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gold-shimmer': 'linear-gradient(90deg, #C9A227 0%, #f0c040 50%, #C9A227 100%)',
      },
    },
  },
  plugins: [],
}
export default config
