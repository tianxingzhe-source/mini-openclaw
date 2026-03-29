import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        klein: {
          50: "#e8ecf7",
          100: "#c5ceed",
          200: "#9eafe2",
          300: "#778fd6",
          400: "#5977ce",
          500: "#3b5fc5",
          600: "#3457bf",
          700: "#2b4db8",
          800: "#2243b0",
          900: "#002FA7",
        },
        surface: {
          DEFAULT: "#fafafa",
          secondary: "#f5f5f5",
          tertiary: "#ebebeb",
        },
      },
      backdropBlur: {
        xs: "2px",
      },
      animation: {
        "pulse-dot": "pulse-dot 1.4s ease-in-out infinite",
      },
      keyframes: {
        "pulse-dot": {
          "0%, 80%, 100%": { opacity: "0.3" },
          "40%": { opacity: "1" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
