/**
 * TopNav — Samsung Health 스타일 상단 네비게이션 바
 *
 * 다크/라이트 모드 자동 전환:
 * - bg-gray-900: 다크에서 어두운 배경, 라이트에서 CSS 오버라이드로 흰색
 * - text-white: 다크에서 밝은 텍스트, 라이트에서 어두운 텍스트
 * - border-gray-700: 다크에서 미세 테두리, 라이트에서 밝은 테두리
 */
import { useState } from "react";
import { useLocation, Link } from "react-router-dom";
import {
  Home, LayoutDashboard, Camera, User, Clock, Network,
  PersonStanding, FileText, Shield, Sun, Moon, Menu, X, LogIn, LogOut, Zap,
} from "lucide-react";
import { useTheme } from "../../context/ThemeContext";
import SyncIndicator from "../SyncIndicator";
import { useAppState } from "../../context/AppStateContext";

const NAV_ITEMS = [
  { path: "/", label: "홈", icon: Home },
  { path: "/dashboard", label: "대시보드", icon: LayoutDashboard },
  { path: "/analysis", label: "사진 분석", icon: Camera },
  { path: "/simulator", label: "시뮬레이터", icon: User },
  { path: "/schedule", label: "생활패턴", icon: Clock },
  { path: "/avatar", label: "가상인물", icon: PersonStanding },
  { path: "/report", label: "리포트", icon: FileText },
  { path: "/team-leader", label: "전체 관리", icon: Shield },
];

export default function TopNav() {
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);
  const { theme, toggle } = useTheme();
  const { state: appState, updateState } = useAppState();
  const isLoggedIn = !!appState.authUser;

  return (
    <>
      <header className="sticky top-0 z-50 bg-gray-900 border-b border-gray-700 backdrop-blur-md pt-safe">
        <div className="max-w-[1440px] mx-auto px-4 md:px-6 flex items-center h-14">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 mr-8 flex-shrink-0">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center"
              style={{ background: "linear-gradient(135deg, #1a73e8, #4285f4)" }}>
              <Zap size={16} color="#fff" />
            </div>
            <span className="font-bold text-base tracking-tight text-cyan-400">LifeSync AI</span>
          </Link>

          {/* Desktop Links */}
          <nav className="hidden lg:flex items-center gap-1 flex-1">
            {NAV_ITEMS.map((item) => {
              const active = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`px-3 py-1.5 rounded-lg text-[13px] font-medium transition-all ${
                    active
                      ? "text-cyan-400 bg-cyan-500/10"
                      : "text-white hover:text-cyan-400 hover:bg-gray-800"
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>

          {/* Right Controls */}
          <div className="hidden lg:flex items-center gap-3 ml-auto">
            <SyncIndicator />
            <button onClick={toggle} className="p-2 rounded-lg text-white hover:bg-gray-800 transition-all">
              {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
            </button>
            {isLoggedIn ? (
              <button
                onClick={() => { updateState("authUser", null); updateState("authToken", null); }}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm text-white hover:text-red-400 hover:bg-red-500/10 transition-all"
              >
                <LogOut size={15} />
                <span>로그아웃</span>
              </button>
            ) : (
              <Link to="/login" className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm text-cyan-400 hover:bg-cyan-500/10 transition-all">
                <LogIn size={15} />
                <span>로그인</span>
              </Link>
            )}
          </div>

          {/* Mobile: Sync + Hamburger */}
          <div className="lg:hidden ml-auto flex items-center gap-2">
            <SyncIndicator />
          </div>
          <button onClick={() => setMobileOpen(!mobileOpen)} className="lg:hidden p-2 rounded-lg text-white hover:bg-gray-800">
            {mobileOpen ? <X size={22} /> : <Menu size={22} />}
          </button>
        </div>

        {/* Mobile Dropdown */}
        {mobileOpen && (
          <div className="lg:hidden border-t border-gray-700 bg-gray-900 px-4 py-3">
            <nav className="grid grid-cols-3 gap-2">
              {NAV_ITEMS.map((item) => {
                const active = location.pathname === item.path;
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    onClick={() => setMobileOpen(false)}
                    className={`flex flex-col items-center gap-1 p-2.5 rounded-lg text-[11px] transition-all ${
                      active ? "text-cyan-400 bg-cyan-500/10" : "text-white hover:bg-gray-800"
                    }`}
                  >
                    <item.icon size={18} />
                    <span>{item.label}</span>
                  </Link>
                );
              })}
            </nav>
            <div className="flex items-center justify-between mt-3 pt-3 border-t border-gray-700">
              <button onClick={toggle} className="text-sm text-white">
                {theme === "dark" ? "라이트 모드" : "다크 모드"}
              </button>
              {isLoggedIn ? (
                <button onClick={() => { updateState("authUser", null); updateState("authToken", null); setMobileOpen(false); }}
                  className="text-sm text-red-400">로그아웃</button>
              ) : (
                <Link to="/login" onClick={() => setMobileOpen(false)} className="text-sm text-cyan-400">로그인</Link>
              )}
            </div>
          </div>
        )}
      </header>
    </>
  );
}
