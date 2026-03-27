/**
 * App — React Router 설정
 */
import { HashRouter, Routes, Route } from "react-router-dom";
import LandingPage from "./pages/LandingPage";
import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";
import AnalysisPage from "./pages/AnalysisPage";
import RoadmapPage from "./pages/RoadmapPage";
import SimulatorPage from "./pages/SimulatorPage";
import SchedulePage from "./pages/SchedulePage";
import ArchitecturePage from "./pages/ArchitecturePage";
import AvatarSimPage from "./pages/AvatarSimPage";
import ReportPage from "./pages/ReportPage";
import OnboardingPage from "./pages/OnboardingPage";

export default function App() {
  return (
    <HashRouter>
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
      </Routes>
    </HashRouter>
  );
}
