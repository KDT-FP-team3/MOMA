/**
 * App — React Router 설정 (lazy loading + Error Boundary)
 */
import React, { Suspense, useEffect } from "react";
import { HashRouter, Routes, Route, useNavigate } from "react-router-dom";
import { App as CapApp } from "@capacitor/app";
import ErrorBoundary from "./components/ErrorBoundary";

// Lazy-loaded 페이지 (코드 스플리팅으로 초기 로딩 최적화)
const LandingPage = React.lazy(() => import("./pages/LandingPage"));
const LoginPage = React.lazy(() => import("./pages/LoginPage"));
const DashboardPage = React.lazy(() => import("./pages/DashboardPage"));
const AnalysisPage = React.lazy(() => import("./pages/AnalysisPage"));
// RoadmapPage는 SimulatorPage 내 탭으로 통합됨
const SimulatorPage = React.lazy(() => import("./pages/SimulatorPage"));
const SchedulePage = React.lazy(() => import("./pages/SchedulePage"));
const ArchitecturePage = React.lazy(() => import("./pages/ArchitecturePage"));
const AvatarSimPage = React.lazy(() => import("./pages/AvatarSimPage"));
const ReportPage = React.lazy(() => import("./pages/ReportPage"));
const OnboardingPage = React.lazy(() => import("./pages/OnboardingPage"));
const AdminPage = React.lazy(() => import("./pages/AdminPage"));
const TeamLeaderPage = React.lazy(() => import("./pages/TeamLeaderPage"));

function PageLoader() {
  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-900">
      <div className="text-center">
        <div className="w-8 h-8 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
        <p className="text-white text-sm">로딩 중...</p>
      </div>
    </div>
  );
}

/** Android 뒤로가기 버튼 처리 (HashRouter 내부에서 사용)
 *
 * window.history.length는 세션 전체 히스토리이므로 부정확.
 * 대신 앱 내 네비게이션 횟수를 직접 추적합니다.
 */
const navCountRef = { current: 0 };

function BackButtonHandler() {
  const navigate = useNavigate();

  // 페이지 이동 시마다 카운트 증가
  useEffect(() => {
    const onHash = () => { navCountRef.current++; };
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  // 뒤로가기 버튼 리스너
  useEffect(() => {
    let listenerHandle = null;

    CapApp.addListener("backButton", () => {
      if (navCountRef.current > 0) {
        navCountRef.current--;
        window.history.back();
      } else {
        // 홈 화면(첫 페이지)에서 뒤로가기 → 앱을 백그라운드로
        CapApp.minimizeApp();
      }
    }).then(handle => { listenerHandle = handle; });

    return () => {
      if (listenerHandle) listenerHandle.remove();
    };
  }, [navigate]);

  return null;
}

export default function App() {
  // 앱 시작 시 모델 자동 동기화 (백그라운드, 5초 지연)
  useEffect(() => {
    const timer = setTimeout(() => {
      import("./services/offlineEngine").then(({ syncAllModels }) => {
        syncAllModels().then((results) => {
          console.info("[ModelSync]", results);
        });
      }).catch(() => {});
    }, 5000);
    return () => clearTimeout(timer);
  }, []);

  return (
    <ErrorBoundary>
      <HashRouter>
        <BackButtonHandler />
        <Suspense fallback={<PageLoader />}>
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/auth/kakao/callback" element={<LoginPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/analysis" element={<AnalysisPage />} />
            {/* /roadmap → SimulatorPage 내 "12주 로드맵" 탭으로 통합 */}
            <Route path="/simulator" element={<SimulatorPage />} />
            <Route path="/schedule" element={<SchedulePage />} />
            <Route path="/architecture" element={<ArchitecturePage />} />
            <Route path="/avatar" element={<AvatarSimPage />} />
            <Route path="/report" element={<ReportPage />} />
            <Route path="/onboarding" element={<OnboardingPage />} />
            <Route path="/admin" element={<AdminPage />} />
            <Route path="/team-leader" element={<TeamLeaderPage />} />
          </Routes>
        </Suspense>
      </HashRouter>
    </ErrorBoundary>
  );
}
