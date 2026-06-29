/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        premium: {
          bg: '#050505',
          surface: '#0A0A0A',
          card: '#111111',
          border: 'rgba(255, 255, 255, 0.08)',
          text: '#FAFAFA',
          subtext: '#A1A1AA',
          accent: '#3B82F6', // Electric Blue
        },
      },
      boxShadow: {
        'inner-premium': 'inset 0 1px 0 0 rgba(255, 255, 255, 0.05)',
      },
      fontFamily: {
        sans: ['Outfit', 'sans-serif'],
      }
    },
  },
  plugins: [],
};
