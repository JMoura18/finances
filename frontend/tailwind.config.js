/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
      },
      colors: {
        ink: {
          950: '#08090c',
          900: '#0c0d12',
          800: '#13141b',
          700: '#1a1c25',
          600: '#252834',
          500: '#3a3d4d',
        },
        gold: {
          400: '#d4b577',
          500: '#c89a52',
          600: '#9c7637',
        },
        accent: {
          green: '#5fd09b',
          red: '#ef6b73',
          amber: '#f1c062',
          blue: '#7aa3ff',
        },
      },
      boxShadow: {
        glow: '0 0 0 1px rgba(212,181,119,0.10), 0 12px 30px -10px rgba(0,0,0,0.6)',
      },
      backgroundImage: {
        'glass': 'linear-gradient(180deg, rgba(255,255,255,0.04) 0%, rgba(255,255,255,0.01) 100%)',
        'aurora': 'radial-gradient(1200px 600px at 0% -10%, rgba(122,163,255,0.10), transparent 60%), radial-gradient(900px 500px at 100% 0%, rgba(212,181,119,0.08), transparent 55%)',
      },
    },
  },
  plugins: [],
}
