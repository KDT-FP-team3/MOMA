/**
 * ThemeContext — 다크/라이트 모드 전환 (깜빡임 방지)
 */
import { createContext, useContext, useState, useEffect } from "react";

const ThemeContext = createContext();

// 초기 테마를 동기적으로 결정 + DOM에 즉시 적용 (깜빡임 방지)
function getInitialTheme() {
  try {
    const saved = localStorage.getItem("lifesync-theme");
    return saved === "dark" ? "dark" : "light";
  } catch {
    return "light";
  }
}

// 모듈 로드 시 즉시 DOM 클래스 적용 (React 렌더 전)
const _initialTheme = getInitialTheme();
document.documentElement.classList.add(_initialTheme === "light" ? "light-mode" : "dark-mode");
document.documentElement.classList.remove(_initialTheme === "light" ? "dark-mode" : "light-mode");

export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState(_initialTheme);

  useEffect(() => {
    const root = document.documentElement;
    if (theme === "light") {
      root.classList.add("light-mode");
      root.classList.remove("dark-mode");
    } else {
      root.classList.add("dark-mode");
      root.classList.remove("light-mode");
    }
    try { localStorage.setItem("lifesync-theme", theme); } catch {}
  }, [theme]);

  const toggle = () => setTheme((t) => (t === "dark" ? "light" : "dark"));

  return (
    <ThemeContext.Provider value={{ theme, toggle }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  return useContext(ThemeContext);
}
