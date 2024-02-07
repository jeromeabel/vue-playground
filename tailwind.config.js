/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{html,js,ts,vue}'],
  theme: {
    extend: {
      colors: {
        black: '#111118',
        white: '#fdfdfd'
      },
      container: {
        center: true,
        padding: '1rem'
      }
    }
  },
  plugins: []
}
