import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        display: ["Fraunces", "Times New Roman", "serif"],
        body: ["Sora", "Segoe UI", "sans-serif"],
      },
      boxShadow: {
        soft: "0 18px 50px rgba(28, 26, 23, 0.14)",
      },
    },
  },
  plugins: [],
} satisfies Config;
