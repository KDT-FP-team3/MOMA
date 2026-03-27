/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Pretendard"', '"Inter"', '-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', 'sans-serif'],
      },
      colors: {
        // Primary: Teal-Cyan medical feel
        primary: { 50: "#effcfc", 100: "#d5f5f6", 200: "#afe9ed", 300: "#78d6df", 400: "#3abac9", 500: "#1e9eae", 600: "#1b8093", 700: "#1c6778", 800: "#1e5463", 900: "#1e4655", 950: "#0d2c39" },
        // Secondary: Violet-Indigo AI feel
        secondary: { 50: "#f0f0ff", 100: "#e4e1ff", 200: "#cdc6ff", 300: "#a999ff", 400: "#8162ff", 500: "#5b35f5", 600: "#4c15eb", 700: "#400fc7", 800: "#350ea3", 900: "#2c1086", 950: "#19065c" },
        // Healthcare accent colors
        health: { positive: "#10b981", negative: "#ef4444", warning: "#f59e0b", info: "#06b6d4", calm: "#818cf8" },
        // Surface colors
        surface: { dark: "#0c1222", "dark-card": "#111827", "dark-elevated": "#1a2332", light: "#f0f5fa", "light-card": "#ffffff", "light-elevated": "#f8fbff" },
      },
      animation: {
        "bounce": "bounce 1s infinite",
        "levelup": "levelup 0.6s ease-out",
        "glow": "glow 2s ease-in-out infinite alternate",
        "sparkle": "sparkle 0.8s ease-out forwards",
        "float": "float 3s ease-in-out infinite",
        "magic-spin": "magic-spin 1.5s ease-in-out",
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "gradient-x": "gradient-x 6s ease infinite",
        "fade-up": "fade-up 0.5s ease-out forwards",
        "slide-in": "slide-in 0.3s ease-out",
        "shimmer": "shimmer 2s linear infinite",
      },
      keyframes: {
        levelup: { "0%": { transform: "scale(1)" }, "50%": { transform: "scale(1.2)" }, "100%": { transform: "scale(1)" } },
        glow: { "0%": { boxShadow: "0 0 5px rgba(6,182,212,0.3)" }, "100%": { boxShadow: "0 0 20px rgba(6,182,212,0.6)" } },
        sparkle: { "0%": { opacity: 1, transform: "scale(0) rotate(0deg)" }, "100%": { opacity: 0, transform: "scale(1.5) rotate(180deg)" } },
        float: { "0%,100%": { transform: "translateY(0px)" }, "50%": { transform: "translateY(-8px)" } },
        "magic-spin": { "0%": { transform: "perspective(600px) rotateY(0deg)" }, "50%": { transform: "perspective(600px) rotateY(180deg)" }, "100%": { transform: "perspective(600px) rotateY(360deg)" } },
        "gradient-x": { "0%,100%": { "background-position": "0% 50%" }, "50%": { "background-position": "100% 50%" } },
        "fade-up": { "0%": { opacity: 0, transform: "translateY(16px)" }, "100%": { opacity: 1, transform: "translateY(0)" } },
        "slide-in": { "0%": { opacity: 0, transform: "translateX(-8px)" }, "100%": { opacity: 1, transform: "translateX(0)" } },
        "shimmer": { "0%": { "background-position": "-200% 0" }, "100%": { "background-position": "200% 0" } },
      },
      boxShadow: {
        "card": "0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.06)",
        "card-hover": "0 10px 25px rgba(0,0,0,0.12), 0 4px 10px rgba(0,0,0,0.08)",
        "glow-cyan": "0 0 20px rgba(6,182,212,0.25), 0 0 60px rgba(6,182,212,0.1)",
        "glow-violet": "0 0 20px rgba(139,92,246,0.25), 0 0 60px rgba(139,92,246,0.1)",
        "glass": "0 8px 32px rgba(0,0,0,0.12)",
        "inner-glow": "inset 0 1px 0 rgba(255,255,255,0.05)",
      },
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "mesh-dark": "radial-gradient(at 20% 30%, rgba(6,182,212,0.06) 0px, transparent 50%), radial-gradient(at 80% 70%, rgba(139,92,246,0.06) 0px, transparent 50%)",
        "mesh-light": "radial-gradient(at 20% 30%, rgba(6,182,212,0.04) 0px, transparent 50%), radial-gradient(at 80% 70%, rgba(139,92,246,0.04) 0px, transparent 50%)",
      },
      borderRadius: {
        "2xl": "1rem",
        "3xl": "1.5rem",
      },
    },
  },
  plugins: [],
};
