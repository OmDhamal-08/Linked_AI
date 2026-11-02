import type { Config } from "tailwindcss";

/**
 * Design tokens. Brand colours live here so the look can be re-skinned in one place.
 */
const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./hooks/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#ecfdfb",
          100: "#d2f7f1",
          200: "#a6ede2",
          300: "#6fdccb",
          400: "#33c4ae",
          500: "#14a390",
          600: "#0e8475",
          700: "#0d6960",
          800: "#0f544e",
          900: "#0e4642",
        },
        ink: {
          50: "#f6f8f9",
          100: "#eceff1",
          200: "#d6dde1",
          300: "#b3bfc6",
          400: "#8294a0",
          500: "#5f7480",
          600: "#4a5c66",
          700: "#374650",
          800: "#22303a",
          900: "#131d24",
        },
        amberish: {
          100: "#fdf1d6",
          500: "#c98a0b",
        },
      },
      boxShadow: {
        card: "0 1px 2px rgba(19, 29, 36, 0.05), 0 4px 16px rgba(19, 29, 36, 0.04)",
      },
      fontFamily: {
        sans: ["ui-sans-serif", "system-ui", "-apple-system", "Segoe UI", "Roboto", "Helvetica Neue", "Arial", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
