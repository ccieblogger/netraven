/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Map Tailwind colors to our CSS variables
        'primary': 'var(--nr-primary)',
        'primary-light': 'var(--nr-primary-light)', 
        'primary-dark': 'var(--nr-primary-dark)',
        
        // Background colors
        'sidebar': 'var(--nr-bg-sidebar)',
        'content': 'var(--nr-bg-content)',
        'card': 'var(--nr-bg-card)',
        
        // Text colors
        'text-primary': 'var(--nr-text-primary)',
        'text-secondary': 'var(--nr-text-secondary)',
        
        // Keep original color palette for compatibility
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
        blue: {
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
        },
        green: {
          300: '#86efac',
          400: '#4ade80',
          500: '#22c55e',
          600: '#16a34a',
          700: '#15803d',
          800: '#166534',
        },
        purple: {
          300: '#d8b4fe',
          400: '#c084fc',
          500: '#a855f7',
          600: '#9333ea',
          700: '#7e22ce',
          800: '#6b21a8',
          900: '#581c87',
        },
      },
      borderColor: {
        'divider': 'var(--nr-border)',
      },
      borderRadius: {
        'card': 'var(--nr-card-radius)',
      },
      width: {
        'sidebar': 'var(--nr-sidebar-width)',
      },
    },
  },
  plugins: [
    // eslint-disable-next-line no-undef
    function({ addBase, addComponents, addUtilities, theme }) {
      // Add your custom styles here if needed
    },
  ],
}
