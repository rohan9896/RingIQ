/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        display: ['Outfit', 'sans-serif'],
        body: ['Work Sans', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      colors: {
        // Primary colors - will be replaced during generation
        'primary': {
          50: '#eef6ff',
          100: '#d9ebff',
          200: '#bcdcff',
          300: '#8fc6ff',
          400: '#5aa7f5',
          500: '#3d7fbe',
          600: '#315f91',
          700: '#284c74',
          800: '#1f3a5f',
          900: '#172b46',
          950: '#0f1c2e',
        },
        // Accent colors
        'accent': {
          50: '#f3f9ff',
          100: '#e3f2ff',
          200: '#cee8ff',
          300: '#a9d5fb',
          400: '#7fb8e7',
          500: '#5f95c4',
          600: '#4d648d',
          700: '#3d5a80',
          800: '#304767',
          900: '#25384f',
          950: '#182536',
        },
        // Background colors
        'bg': {
          'base': '#0f1c2e',
          'card': '#172b46',
          'elevated': '#1f3a5f',
        },
        // Text colors
        'text': {
          'primary': '#f3f9ff',
          'secondary': '#bcdcff',
          'muted': '#7f9fbe',
        },
        // Border colors
        'border': {
          'default': '#315f91',
          'subtle': '#1f3a5f',
        },
      },
    },
  },
  plugins: [],
}
