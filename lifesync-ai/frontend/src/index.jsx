/**
 * React 애플리케이션 엔트리포인트
 */
import React from "react";
import ReactDOM from "react-dom/client";
import axios from "axios";
import App from "./App";
import { ThemeProvider } from "./context/ThemeContext";
import { AppStateProvider } from "./context/AppStateContext";
import "./index.css";

// 프로덕션 빌드에서 API 호출이 백엔드로 향하도록 baseURL 설정
const API_BASE = import.meta.env.VITE_API_BASE || "";
if (API_BASE) {
  axios.defaults.baseURL = API_BASE;
}

// API 타임아웃 설정 (30초)
axios.defaults.timeout = 30000;

// 요청 인터셉터 — 모든 API 요청에 Authorization 헤더 자동 추가
axios.interceptors.request.use((config) => {
  try {
    const saved = localStorage.getItem("lifesync-app-state");
    if (saved) {
      // authToken은 localStorage에 저장하지 않으므로 sessionStorage에서 가져옴
      const token = sessionStorage.getItem("lifesync-auth-token");
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
  } catch { /* ignore */ }
  return config;
});

// 응답 인터셉터 — 401 시 로그인 리다이렉트, 서버 에러 콘솔 로깅
axios.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      window.location.hash = "#/login";
    } else if (err.response?.status >= 500) {
      console.error("[API 서버 에러]", err.response?.data || err.message);
    }
    return Promise.reject(err);
  }
);

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <ThemeProvider>
      <AppStateProvider>
        <App />
      </AppStateProvider>
    </ThemeProvider>
  </React.StrictMode>
);
