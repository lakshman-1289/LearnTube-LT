/** @type {import('tailwindcss').Config} */
  module.exports = {
    content: [
      './src/app/**/*.{js,ts,jsx,tsx}', // App Router files
      './src/components/**/*.{js,ts,jsx,tsx}', // Component files
      './src/app/*/*.{js,ts,jsx,tsx}', // Specific pages like signup and login
    ],
    theme: {
      extend: {},
    },
    plugins: [],
  };