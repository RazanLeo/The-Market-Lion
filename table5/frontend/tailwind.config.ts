import type { Config } from 'tailwindcss';

export default {
  content: ['./app/**/*.{ts,tsx}', './components/**/*.{ts,tsx}', './lib/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        gold: '#C9A227',
        ink: '#0A0A0A',
      },
    },
  },
  plugins: [],
} satisfies Config;
