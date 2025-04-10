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
        // Blue colors updated to match UI screenshot - more subdued navy tones
        blue: {
          500: '#3b82f6', // Medium blue for backgrounds
          600: '#2563eb', // Device card background
          700: '#1d4ed8', // Darker blue elements
          800: '#1e3a8a', // Sidebar background (navy blue)
          900: '#0D1321', // Main content background (Rich Black)
        },
        // Greens for Jobs card and accents
        green: {
          500: '#10b981', // Main green for accents
          600: '#059669',
          700: '#047857',
          800: '#065f46',
        },
        // Purples for Credentials card
        purple: {
          600: '#9333ea', // Main purple for credentials card
          700: '#7e22ce',
          800: '#6b21a8',
          900: '#581c87',
        },
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
  ],
}
