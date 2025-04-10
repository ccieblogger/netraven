/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Standard gray scale
        gray: {
          100: 'oklch(0.961 0.02 91)',
          200: 'oklch(0.921 0.02 91)',
          300: 'oklch(0.866 0.02 91)',
          400: 'oklch(0.71 0.02 91)',
          500: 'oklch(0.51 0.02 91)',
          600: 'oklch(0.41 0.02 91)',
          700: 'oklch(0.31 0.02 91)',
          800: 'oklch(0.21 0.02 91)',
          900: 'oklch(0.12 0.02 91)',
        },
        // Blue colors updated to match UI screenshot - more subdued navy tones
        blue: {
          300: 'oklch(0.8 0.15 250)',
          400: 'oklch(0.7 0.15 250)',
          500: 'oklch(0.6 0.15 250)', // Medium blue for backgrounds
          600: 'oklch(0.5 0.15 250)', // Device card background
          700: 'oklch(0.4 0.15 250)', // Darker blue elements
          800: 'oklch(0.3 0.15 250)', // Sidebar background (navy blue)
          900: 'oklch(0.15 0.08 265)', // Main content background (Rich Black)
        },
        // Greens for Jobs card and accents
        green: {
          300: 'oklch(0.8 0.15 150)',
          400: 'oklch(0.7 0.15 150)',
          500: 'oklch(0.6 0.15 150)', // Main green for accents
          600: 'oklch(0.5 0.15 150)',
          700: 'oklch(0.4 0.15 150)',
          800: 'oklch(0.3 0.15 150)',
        },
        // Purples for Credentials card
        purple: {
          300: 'oklch(0.8 0.15 310)',
          400: 'oklch(0.7 0.15 310)',
          500: 'oklch(0.6 0.15 310)',
          600: 'oklch(0.5 0.15 310)', // Main purple for credentials card
          700: 'oklch(0.4 0.15 310)',
          800: 'oklch(0.3 0.15 310)',
          900: 'oklch(0.2 0.15 310)',
        },
      },
      backgroundColor: {
        'sidebar': 'oklch(0.16 0.06 265)', // Exact sidebar and header color
      },
      borderColor: {
        'divider': 'oklch(0.23 0.04 265)', // Exact border color
      },
    },
  },
  plugins: [
    // Using modern syntax for Tailwind CSS v4
    ['@tailwindcss/forms', {}],
  ],
}
