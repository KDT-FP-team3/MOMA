/**
 * App — React Router 설정 (lazy loading + Error Boundary)
 */
import React, { Suspense, useEffect } from "react";
import { HashRouter, Routes, Route } from "react-router-dom";
import ErrorBoundary from "./components/ErrorBoundary";

// Lazy-loaded 페이지 (코드 스플리팅으로 초기 로딩 최적화)
const LandingPage = React.lazy(() => import("./pages/LandingPage"));
const LoginPage = React.lazy(() => import("./pages/LoginPage"));
const DashboardPage = React.lazy(() => import("./pages/DashboardPage"));
const AnalysisPage = React.lazy(() => import("./pages/AnalysisPage"));
const RoadmapPage = React.lazy(() => import("./pages/RoadmapPage"));
const SimulatorPage = React.lazy(() => import("./pages/SimulatorPage"));
const SchedulePage = React.lazy(() => import("./pages/SchedulePage"));
const ArchitecturePage = React.lazy(() => import("./pages/ArchitecturePage"));
const AvatarSimPage = React.lazy(() => import("./pages/AvatarSimPage"));
const ReportPage = React.lazy(() => import("./pages/ReportPage"));
const OnboardingPage = React.lazy(() => import("./pages/OnboardingPage"));
const AdminPage = React.lazy(() => import("./pages/AdminPage"));

function PageLoader() {
  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-900">
      <div className="text-center">
        <div className="w-8 h-8 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
        <p className="text-gray-400 text-sm">로딩 중...</p>
      </div>
    </div>
  );
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
        <Suspense fallback={<PageLoader />}>
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/auth/kakao/callback" element={<LoginPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/analysis" element={<AnalysisPage />} />
            <Route path="/roadmap" element={<RoadmapPage />} />
            <Route path="/simulator" element={<SimulatorPage />} />
            <Route path="/schedule" element={<SchedulePage />} />
            <Route path="/architecture" element={<ArchitecturePage />} />
            <Route path="/avatar" element={<AvatarSimPage />} />
            <Route path="/report" element={<ReportPage />} />
            <Route path="/onboarding" element={<OnboardingPage />} />
            <Route path="/admin" element={<AdminPage />} />
          </Routes>
        </Suspense>
      </HashRouter>
    </ErrorBoundary>
  );
}
