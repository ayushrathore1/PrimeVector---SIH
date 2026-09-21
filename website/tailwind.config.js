/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        forest: '#18280E',
        'forest-dark': '#0F1A09',
        'forest-light': '#253C18',
        'forest-hover': '#1F3413',
        lemongrass: '#C5FF34',
        'lemongrass-hover': '#B5F024',
        'lemongrass-muted': 'rgba(197, 255, 52, 0.2)',
        sage: '#F4F6F0',
        'sage-1': '#F4F6F0',
        'sage-2': '#E9EDE3',
        'sage-3': '#D8DFC9',
        'sage-4': '#C2CBB2',
        'pv-black': '#18280E',
        'pv-gray': '#4B5563',
        'pv-darkgray': '#1F2937',
        'pv-lightgray': '#6B7280',
        'pv-border': 'rgba(24, 40, 14, 0.15)',
        'pv-bg': '#FAFBF8',
        'pv-card': '#FFFFFF',
        verdict: {
          real: '#059669',
          realBg: '#ECFDF5',
          realBorder: '#A7F3D0',
          fake: '#E11D48',
          fakeBg: '#FFF1F2',
          fakeBorder: '#FECDD3',
        }
      },
      borderRadius: {
        'xs': '4px',
        'sm': '6px',
        'md': '8px',
        'lg': '12px',
        'xl': '16px',
        '2xl': '20px',
        '3xl': '24px',
      },
      fontFamily: {
        sans: ['Inter', 'SF Pro Display', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'Consolas', 'monospace'],
        display: ['Outfit', 'Inter', 'sans-serif'],
      },
      boxShadow: {
        'spade': '0 4px 20px -2px rgba(24, 40, 14, 0.08), 0 2px 6px -2px rgba(24, 40, 14, 0.04)',
        'spade-lg': '0 12px 32px -4px rgba(24, 40, 14, 0.12), 0 4px 12px -2px rgba(24, 40, 14, 0.06)',
        'glow-lime': '0 0 15px rgba(197, 255, 52, 0.4)',
        'glow-lime-lg': '0 0 25px rgba(197, 255, 52, 0.55)',
      },
    },
  },
  plugins: [],
}
