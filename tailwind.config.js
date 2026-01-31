/** @type {import('tailwindcss').Config} */
export default {
    content: [
      "./index.html",
      "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
      extend: {
        colors: {
          midnight: '#0f172a',
          emerald: '#10b981',
        }
      },
    },
    plugins: [],
  }