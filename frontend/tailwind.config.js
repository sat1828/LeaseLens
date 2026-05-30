/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        display: ['"Playfair Display"', 'Georgia', 'serif'],
        body:    ['"DM Sans"', 'system-ui', 'sans-serif'],
        mono:    ['"JetBrains Mono"', 'monospace'],
      },
      colors: {
        navy: {
          50:  '#EEF2FF',
          100: '#E0E7FF',
          500: '#1E3A5F',
          600: '#172C4A',
          700: '#0F1E35',
          900: '#060D18',
        },
      },
      animation: {
        'fade-up':    'fadeUp 0.5s ease-out',
        'scale-in':   'scaleIn 0.3s ease-out',
        'pulse-slow': 'pulse 3s infinite',
      },
      keyframes: {
        fadeUp:  { '0%': { opacity: '0', transform: 'translateY(16px)' }, '100%': { opacity: '1', transform: 'translateY(0)' } },
        scaleIn: { '0%': { opacity: '0', transform: 'scale(0.95)' },     '100%': { opacity: '1', transform: 'scale(1)' } },
      },
    },
  },
  // BUG-23 FIX: typography plugin for react-markdown rendering
  plugins: [require('@tailwindcss/typography')],
}
