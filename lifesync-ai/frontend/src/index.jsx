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

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <ThemeProvider>
      <AppStateProvider>
        <App />
      </AppStateProvider>
    </ThemeProvider>
  </React.StrictMode>
);
