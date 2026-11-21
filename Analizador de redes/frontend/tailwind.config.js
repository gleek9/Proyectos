/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        canvas: "#0B0C0E",
        surface: {
          DEFAULT: "#121316",
          elevated: "#191B20",
        },
        border: {
          subtle: "#27272A",
          focus: "#A1A1AA",
        },
        ink: {
          primary: "#E4E5E9",
          secondary: "#9499A6",
          muted: "#646975",
        },
      },
      fontFamily: {
        sans: ["'Plus Jakarta Sans'", "'Inter'", "system-ui", "sans-serif"],
        mono: ["'JetBrains Mono'", "monospace"],
      },
    },
  },
  plugins: [],
}
