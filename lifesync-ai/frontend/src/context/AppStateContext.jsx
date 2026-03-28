/**
 * AppStateContext — 전역 상태 유지 (탭 이동해도 초기화 안 됨)
 * localStorage에 자동 저장하여 브라우저 새로고침 후에도 유지
 */
import { createContext, useContext, useState, useCallback, useEffect } from "react";

const AppStateContext = createContext();

const STORAGE_KEY = "lifesync-app-state";

const DEFAULT_STATE = {
  // SchedulePage
  schedule: [],
  scheduleResults: null,
  simDays: 30,
  // SimulatorPage
  simulatorState: null,
  simulatorStarted: false,
  simulatorActions: [],
  // AvatarSimPage
  avatarProfile: null,
  avatarComparison: null,
  // OnboardingPage
  onboardingData: null,
  onboardingStep: 0,
  // DashboardPage — 6개 게이지 + 4개 도메인 요약
  dashboardData: null,
  gauges: {
    reactive_oxygen: 62,
    blood_purity: 78,
    hair_loss_risk: 23,
    sleep_score: 71,
    stress_level: 45,
    weekly_achievement: 67,
  },
  domainSummary: {
    food: { value: "0 kcal", sub: "오늘 섭취" },
    exercise: { value: "0분", sub: "오늘 활동" },
    health: { value: "-", sub: "종합 상태" },
    hobby: { value: "0분", sub: "오늘 활동" },
  },
  // 최근 연쇄 효과 (채팅/사진 분석 결과)
  lastCascade: null,
  // User
  userProfile: null,
  userId: "default",
  // Auth
  authUser: null,
  authToken: null,
};

function loadState() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return { ...DEFAULT_STATE, ...JSON.parse(raw) };
  } catch {}
  return DEFAULT_STATE;
}

function saveState(state) {
  try {
    // 민감 정보(토큰)는 localStorage에 저장하지 않음 — XSS 방어
    const { authToken, ...safe } = state;
    localStorage.setItem(STORAGE_KEY, JSON.stringify(safe));
  } catch {}
}

export function AppStateProvider({ children }) {
  const [state, setState] = useState(loadState);

  // Auto-save to localStorage on every change
  useEffect(() => { saveState(state); }, [state]);

  const updateState = useCallback((key, value) => {
    setState((prev) => ({ ...prev, [key]: typeof value === "function" ? value(prev[key]) : value }));
  }, []);

  const resetState = useCallback(() => {
    setState(DEFAULT_STATE);
    try { localStorage.removeItem(STORAGE_KEY); } catch {}
  }, []);

  return (
    <AppStateContext.Provider value={{ state, updateState, resetState }}>
      {children}
    </AppStateContext.Provider>
  );
}

export function useAppState() {
  return useContext(AppStateContext);
}
