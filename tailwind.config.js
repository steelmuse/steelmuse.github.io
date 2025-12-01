/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/**/*.{astro,html,js,jsx,ts,tsx,md,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: '#1B4332',
        secondary: '#4682B4',
        accent: '#FF6F00',
      },
      maxWidth: {
        content: '1280px',
        container: '1440px',
      },
      fontFamily: {
        sans: ['Inter', 'Satoshi', 'IBM Plex Sans', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
