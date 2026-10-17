/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        // Backgrounds / surfaces
        ink: "rgb(var(--color-ink) / <alpha-value>)",
        parchment: "rgb(var(--color-parchment) / <alpha-value>)",
        surface: "rgb(var(--color-surface) / <alpha-value>)",
        // Fixed light color for text/borders on permanently-dark bands
        // (Hero, Security, Footer) — does NOT change with dark mode,
        // unlike `parchment` which doubles as the toggled page background.
        cream: "rgb(var(--color-cream) / <alpha-value>)",
        // Text
        ink_text: "rgb(var(--color-text) / <alpha-value>)",
        muted: "rgb(var(--color-muted) / <alpha-value>)",
        // Brand / accents — named after their civic role, not generic "primary/secondary"
        seal: "rgb(var(--color-seal) / <alpha-value>)",       // brand blue — "official seal ink"
        brass: "rgb(var(--color-brass) / <alpha-value>)",     // accent — "civic stamp"
        verified: "rgb(var(--color-verified) / <alpha-value>)", // success — "block verified"
        alert: "rgb(var(--color-alert) / <alpha-value>)",     // danger — "fraud flag"
        line: "rgb(var(--color-line) / <alpha-value>)",       // hairlines / dividers
      },
      fontFamily: {
        display: ["'Libre Caslon Display'", "serif"],
        serif: ["'Libre Caslon Text'", "serif"],
        sans: ["'IBM Plex Sans'", "system-ui", "sans-serif"],
        mono: ["'IBM Plex Mono'", "monospace"],
      },
      maxWidth: {
        prose: "68ch",
      },
      keyframes: {
        "link-in": {
          "0%": { opacity: "0", transform: "translateY(12px) scale(0.96)" },
          "100%": { opacity: "1", transform: "translateY(0) scale(1)" },
        },
        "pulse-verify": {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.55" },
        },
        "draw-line": {
          "0%": { strokeDashoffset: "1" },
          "100%": { strokeDashoffset: "0" },
        },
      },
      animation: {
        "link-in": "link-in 0.5s cubic-bezier(0.16, 1, 0.3, 1) both",
        "pulse-verify": "pulse-verify 2s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
