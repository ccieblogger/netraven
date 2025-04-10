/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  purge: [
    './src/**/*.html', './src/**/*.vue', './src/**/*.jsx'
  ],
  safelist: [
    'bg-gray-900',
    'text-gray-900'
  ],
  theme: {
    extend: {
      colors: {
        // Standard gray scale that works in v4
        gray: {
          100: '#f3f4f6',
          200: '#e5e7eb',
          300: '#d1d5db',
          400: '#9ca3af',
          500: '#6b7280',
          600: '#4b5563',
          700: '#374151',
          800: '#1f2937',
          900: '#111827',
        },
        // Dark blue backgrounds
        blue: {
          800: '#1a365d',
          900: '#1e3a8a',
        },
        // Greens for buttons and accents
        green: {
          500: '#10b981',
          600: '#059669',
          700: '#047857',
          800: '#065f46',
        },
        // Purples for cards
        purple: {
          800: '#5b21b6',
          900: '#4c1d95',
        },
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
  ],
}
