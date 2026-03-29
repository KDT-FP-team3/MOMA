/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Pretendard"', '"Inter"', '-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', 'sans-serif'],
      },
      colors: {
        // Samsung Health Blue — 프로젝트 전체 기본 액센트
        primary: {
          50: "#e8f0fe", 100: "#d2e3fc", 200: "#aecbfa", 300: "#8ab4f8",
          400: "#669df6", 500: "#4285f4", 600: "#1a73e8", 700: "#1967d2",
          800: "#185abc", 900: "#174ea6", 950: "#0d3276",
        },
        // Samsung Dark Blue — 보조 색상
        secondary: {
          50: "#e8eaf6", 100: "#c5cae9", 200: "#9fa8da", 300: "#7986cb",
          400: "#5c6bc0", 500: "#3f51b5", 600: "#3949ab", 700: "#303f9f",
          800: "#283593", 900: "#1a237e", 950: "#0d1257",
        },
        // 건강 도메인 액센트 (범용 — 변경 없음)
        health: {
          positive: "#10b981", negative: "#ef4444", warning: "#f59e0b",
          info: "#1a73e8", calm: "#5c6bc0",
        },
        // Surface 색상 — Samsung Health 느낌
        surface: {
          dark: "#0f1724", "dark-card": "#1a2332", "dark-elevated": "#243044",
          light: "#f5f7fa", "light-card": "#ffffff", "light-elevated": "#f0f4f8",
        },
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
        glow: { "0%": { boxShadow: "0 0 5px rgba(26,115,232,0.3)" }, "100%": { boxShadow: "0 0 20px rgba(26,115,232,0.6)" } },
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
        "glow-cyan": "0 0 20px rgba(26,115,232,0.25), 0 0 60px rgba(26,115,232,0.1)",
        "glow-violet": "0 0 20px rgba(92,107,192,0.25), 0 0 60px rgba(92,107,192,0.1)",
        "glass": "0 8px 32px rgba(0,0,0,0.12)",
        "inner-glow": "inset 0 1px 0 rgba(255,255,255,0.05)",
      },
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "mesh-dark": "radial-gradient(at 20% 30%, rgba(26,115,232,0.06) 0px, transparent 50%), radial-gradient(at 80% 70%, rgba(92,107,192,0.06) 0px, transparent 50%)",
        "mesh-light": "radial-gradient(at 20% 30%, rgba(26,115,232,0.04) 0px, transparent 50%), radial-gradient(at 80% 70%, rgba(92,107,192,0.04) 0px, transparent 50%)",
      },
      borderRadius: {
        "2xl": "1rem",
        "3xl": "1.5rem",
      },
    },
  },
  plugins: [],
};
