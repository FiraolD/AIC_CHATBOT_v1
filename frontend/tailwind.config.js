/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        awash: {
          50: '#eef5fc',
          100: '#d9e8f8',
          200: '#b0d0f0',
          300: '#7fb1e4',
          400: '#4a8ed4',
          500: '#1f6cb8',
          600: '#0056a8',
          700: '#004d99',
          800: '#003d7a',
          900: '#003366',
          950: '#00203f',
        },
        accent: {
          DEFAULT: '#c8102e',
          dark: '#990000',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
      boxShadow: {
        soft: '0 1px 3px rgba(16, 24, 40, 0.06), 0 1px 2px rgba(16, 24, 40, 0.04)',
        card: '0 4px 16px rgba(16, 24, 40, 0.08)',
      },
      keyframes: {
        'caret-blink': {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0' },
        },
        'dot-bounce': {
          '0%, 80%, 100%': { transform: 'translateY(0)', opacity: '0.4' },
          '40%': { transform: 'translateY(-4px)', opacity: '1' },
        },
        'message-in': {
          from: { opacity: '0', transform: 'translateY(8px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        'chip-in': {
          from: { opacity: '0', transform: 'translateY(6px) scale(0.97)' },
          to: { opacity: '1', transform: 'translateY(0) scale(1)' },
        },
        'fade-in': {
          from: { opacity: '0' },
          to: { opacity: '1' },
        },
        'pop-in': {
          from: { opacity: '0', transform: 'translate(-50%, 6px) scale(0.9)' },
          to: { opacity: '1', transform: 'translate(-50%, 0) scale(1)' },
        },
      },
      animation: {
        'caret-blink': 'caret-blink 1s steps(2, start) infinite',
        'dot-bounce': 'dot-bounce 1.2s ease-in-out infinite',
        'message-in': 'message-in 0.25s ease-out both',
        'chip-in': 'chip-in 0.35s ease-out forwards',
        'fade-in': 'fade-in 0.4s ease-out both',
        'pop-in': 'pop-in 0.2s ease-out both',
      },
    },
  },
  plugins: [],
};
