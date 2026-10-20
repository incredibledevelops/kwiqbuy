/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./src/app/**/*.{js,jsx,ts,tsx}",
    "./src/components/**/*.{js,jsx,ts,tsx}",
    "./src/lib/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          primary: "#2563EB",
          primaryDark: "#1D4ED8",
          accent: "#7C3AED",
          accentDark: "#6D28D9",
          gold: "#F59E0B",
          success: "#059669",
          danger: "#DC2626",
          warning: "#D97706",
        },
        surface: {
          dark: "#0B1220",
          DEFAULT: "#111827",
          card: "#1F2937",
          cardAlt: "#1A2332",
          border: "#374151",
        },
      },
      fontFamily: {
        heading: ["var(--font-outfit)", "system-ui", "sans-serif"],
        body: ["var(--font-jakarta)", "system-ui", "sans-serif"],
      },
      animation: {
        "slide-in": "slideIn 250ms cubic-bezier(0.16, 1, 0.3, 1)",
        "fade-in": "fadeIn 200ms ease-out",
        "slide-down": "slideDown 200ms ease-out",
      },
      keyframes: {
        slideIn: {
          from: { transform: "translateX(100%)" },
          to: { transform: "translateX(0)" },
        },
        fadeIn: {
          from: { opacity: 0 },
          to: { opacity: 1 },
        },
        slideDown: {
          from: { opacity: 0, transform: "translateY(-8px)" },
          to: { opacity: 1, transform: "translateY(0)" },
        },
      },
    },
  },
  plugins: [],
};