/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        obsidian: {
          950: '#07090E',
          900: '#0B0F17',
          850: '#0F1523',
          800: '#141C2E',
          700: '#1E293B',
          600: '#334155',
        },
        forensic: {
          amber: '#F59E0B',
          gold: '#D97706',
          light: '#FBBF24',
          glow: 'rgba(245, 158, 11, 0.15)',
        },
        risk: {
          low: '#10B981',      // Emerald green
          medium: '#F59E0B',   // Amber
          high: '#EF4444',     // Crimson red
          critical: '#DC2626', // Deep red
        }
      },
      fontFamily: {
        serif: ['Fraunces', 'Georgia', 'serif'],
        sans: ['Space Grotesk', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      boxShadow: {
        'amber-glow': '0 0 25px -5px rgba(245, 158, 11, 0.25)',
        'cyan-glow': '0 0 25px -5px rgba(6, 182, 212, 0.25)',
        'card-glow': '0 4px 20px -2px rgba(0, 0, 0, 0.5)',
      },
      backgroundImage: {
        'grid-pattern': "radial-gradient(circle at 1px 1px, rgba(255,255,255,0.05) 1px, transparent 0)",
        'amber-gradient': "linear-gradient(135deg, #F59E0B 0%, #D97706 100%)",
      }
    },
  },
  plugins: [],
}
