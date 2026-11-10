/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        canvas: "#090A0D",
        surface: {
          DEFAULT: "#111318",
          elevated: "#171A21",
        },
        border: {
          subtle: "#1E222B",
          focus: "#58FF9C",
        },
        accent: {
          DEFAULT: "#58FF9C",
          hover: "#42E686",
          subtle: "rgba(88, 255, 156, 0.12)",
          glow: "rgba(88, 255, 156, 0.25)",
        },
        citi: {
          text: {
            primary: "#F8FAFC",
            secondary: "#94A3B8",
            muted: "#64748B",
          }
        }
      },
      fontFamily: {
        sans: ["'Plus Jakarta Sans'", "'Inter'", "system-ui", "sans-serif"],
        mono: ["'JetBrains Mono'", "monospace"],
      },
      boxShadow: {
        'technical': '0 0 0 1px #1E222B',
        'accent-glow': '0 0 16px -2px rgba(88, 255, 156, 0.25)',
      }
    },
  },
  plugins: [],
}
