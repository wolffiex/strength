/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./**/templates/**/*.{html,js}"],
  plugins: [
    require('@tailwindcss/forms'),
  ],
}

