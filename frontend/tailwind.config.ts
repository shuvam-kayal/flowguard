import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
      },
      colors: {
        brand: {
          DEFAULT: "#087344",
          dark:    "#065e36",
          mid:     "#23aa6b",
          light:   "#dff1e8",
          faint:   "#f1faf4",
        },
        danger: {
          DEFAULT: "#b93a3a",
          light:   "#fff6f6",
        },
        warning: {
          DEFAULT: "#b66b0b",
          light:   "#fff8ed",
        },
        surface: "#f6f8f5",
        border:  "#e4ebe5",
        muted:   "#718078",
      },
      keyframes: {
        fadeIn: {
          from: { opacity: "0" },
          to:   { opacity: "1" },
        },
        slideUp: {
          from: { opacity: "0", transform: "translateY(14px)" },
          to:   { opacity: "1", transform: "translateY(0)" },
        },
        slideInRight: {
          from: { opacity: "0", transform: "translateX(20px)" },
          to:   { opacity: "1", transform: "translateX(0)" },
        },
      },
      animation: {
        "fade-in":       "fadeIn 0.35s ease both",
        "slide-up":      "slideUp 0.4s cubic-bezier(.22,1,.36,1) both",
        "slide-in-right":"slideInRight 0.35s cubic-bezier(.22,1,.36,1) both",
      },
    },
  },
  plugins: [],
};

export default config;
