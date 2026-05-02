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
        gold: {
          DEFAULT: '#C9A227',
          light: '#E8C547',
          dark: '#A07B0A',
        },
        buy: '#0E7A2C',
        sell: '#B0140C',
        dark: {
          900: '#0A0A0A',
          800: '#111111',
          700: '#1A1A1A',
          600: '#222222',
          500: '#2A2A2A',
        },
      },
      fontFamily: {
        cairo: ['Cairo', 'sans-serif'],
        inter: ['Inter', 'sans-serif'],
        sans: ['Cairo', 'Inter', 'sans-serif'],
      },
      backgroundImage: {
        'gold-gradient': 'linear-gradient(135deg, #C9A227, #E8C547, #A07B0A)',
        'dark-gradient': 'linear-gradient(180deg, #111111 0%, #0A0A0A 100%)',
        'card-gradient': 'linear-gradient(135deg, #1A1A1A 0%, #111111 100%)',
      },
      boxShadow: {
        'gold': '0 0 20px rgba(201, 162, 39, 0.3)',
        'gold-lg': '0 0 40px rgba(201, 162, 39, 0.4)',
        'card': '0 4px 24px rgba(0, 0, 0, 0.4)',
      },
      animation: {
        'pulse-gold': 'pulse-gold 2s infinite',
        'ticker': 'ticker 30s linear infinite',
        'float': 'float 3s ease-in-out infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        'pulse-gold': {
          '0%, 100%': { boxShadow: '0 0 10px rgba(201, 162, 39, 0.3)' },
          '50%': { boxShadow: '0 0 30px rgba(201, 162, 39, 0.6)' },
        },
        'ticker': {
          '0%': { transform: 'translateX(0)' },
          '100%': { transform: 'translateX(-50%)' },
        },
        'float': {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        'glow': {
          'from': { textShadow: '0 0 10px #C9A227, 0 0 20px #C9A227' },
          'to': { textShadow: '0 0 20px #E8C547, 0 0 40px #C9A227, 0 0 60px #A07B0A' },
        },
      },
    },
  },
  plugins: [],
}
export default config
