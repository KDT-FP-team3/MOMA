/**
 * Sidebar — Samsung Health 스타일 네비게이션
 * light-mode: 흰 배경 + 블루 액센트
 * dark-mode: 다크 배경
 */
import { useLocation, Link } from "react-router-dom";
import { Home, LayoutDashboard, Camera, Map, ChevronLeft, ChevronRight, Zap, User, Clock, Network, PersonStanding, FileText, Sun, Moon, LogIn, LogOut, Shield } from "lucide-react";
import { useState } from "react";
import { useTheme } from "../../context/ThemeContext";
import { useAppState } from "../../context/AppStateContext";

const NAV_ITEMS = [
  { path: "/", label: "홈", icon: Home },
  { path: "/dashboard", label: "대시보드", icon: LayoutDashboard },
  { path: "/analysis", label: "사진 분석", icon: Camera },
  { path: "/simulator", label: "시뮬레이터", icon: User },
  { path: "/schedule", label: "생활패턴", icon: Clock },
  { path: "/avatar", label: "가상인물", icon: PersonStanding },
  { path: "/report", label: "주간리포트", icon: FileText },
  { path: "/team-leader", label: "전체 관리", icon: Shield },
];

export default function Sidebar() {
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(false);
  const { theme, toggle } = useTheme();
  const { state: appState, updateState } = useAppState();
  const isLoggedIn = !!appState.authUser;

  return (
    <>
      {/* Desktop Sidebar */}
      <aside
        className={`hidden lg:flex flex-col transition-all duration-300 border-r border-gray-700 bg-gray-900 ${
          collapsed ? "w-[68px]" : "w-56"
        }`}
      >
        {/* Logo */}
        <div className={`flex items-center gap-2.5 py-5 border-b border-gray-700/50 ${collapsed ? "px-3 justify-center" : "px-4"}`}>
          <div className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0"
            style={{ background: "linear-gradient(135deg, #1a73e8, #4285f4)" }}
          >
            <Zap size={18} className="text-white" style={{ color: "#fff" }} />
          </div>
          {!collapsed && (
            <div className="flex flex-col">
              <span className="font-bold text-sm tracking-wide" style={{ color: "#1a73e8" }}>LifeSync AI</span>
              <span className="text-[9px] text-white tracking-widest uppercase">Healthcare Intelligence</span>
            </div>
          )}
        </div>

        {/* Navigation */}
        <nav className="flex-1 py-3 px-2 space-y-0.5 overflow-y-auto">
          {NAV_ITEMS.map((item) => {
            const active = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 group ${
                  active
                    ? "bg-blue-500/10 text-blue-600 font-semibold"
                    : "text-white hover:bg-gray-700/30"
                }`}
                title={collapsed ? item.label : undefined}
              >
                <item.icon
                  size={19}
                  className={`flex-shrink-0 transition-all duration-200 ${
                    active ? "text-blue-600" : "text-white group-hover:text-blue-500"
                  }`}
                />
                {!collapsed && <span className="truncate">{item.label}</span>}
                {active && !collapsed && (
                  <div className="ml-auto w-1.5 h-1.5 rounded-full bg-blue-500" />
                )}
              </Link>
            );
          })}
        </nav>

        {/* Bottom controls */}
        <div className="px-2 py-3 space-y-1 border-t border-gray-700/50">
          {isLoggedIn ? (
            <div className="px-3 py-2">
              {!collapsed && (
                <div className="flex items-center gap-2 mb-1">
                  {appState.authUser.profile_image ? (
                    <img src={appState.authUser.profile_image} alt="" className="w-7 h-7 rounded-full" />
                  ) : (
                    <div className="w-7 h-7 rounded-full bg-blue-500/15 flex items-center justify-center">
                      <User size={14} className="text-blue-600" />
                    </div>
                  )}
                  <span className="text-sm text-white truncate">{appState.authUser.nickname}</span>
                </div>
              )}
              <button
                onClick={() => { updateState("authUser", null); updateState("authToken", null); }}
                className="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-sm text-white hover:text-red-500 hover:bg-red-500/10 transition-all"
              >
                <LogOut size={17} className="flex-shrink-0" />
                {!collapsed && <span>로그아웃</span>}
              </button>
            </div>
          ) : (
            <Link
              to="/login"
              className="flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-sm text-white hover:text-blue-600 hover:bg-blue-500/10 transition-all"
            >
              <LogIn size={19} className="flex-shrink-0" />
              {!collapsed && <span>로그인</span>}
            </Link>
          )}

          {/* Theme toggle */}
          <button
            onClick={toggle}
            className="w-full flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-sm text-white hover:bg-gray-700/30 transition-all group"
          >
            {theme === "dark" ? (
              <Sun size={19} className="flex-shrink-0 text-amber-500 transition-all" />
            ) : (
              <Moon size={19} className="flex-shrink-0 text-violet-500 transition-all" />
            )}
            {!collapsed && <span>{theme === "dark" ? "라이트 모드" : "다크 모드"}</span>}
          </button>

          {/* Collapse toggle */}
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="w-full flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-sm text-white hover:bg-gray-700/30 transition-all"
          >
            {collapsed ? <ChevronRight size={19} className="flex-shrink-0" /> : <ChevronLeft size={19} className="flex-shrink-0" />}
            {!collapsed && <span>접기</span>}
          </button>
        </div>
      </aside>

      {/* Mobile bottom tab bar */}
      <nav className="lg:hidden fixed bottom-0 left-0 right-0 z-50 flex border-t bg-gray-900 safe-area-bottom"
        style={{ backdropFilter: "blur(20px) saturate(180%)" }}
      >
        {NAV_ITEMS.slice(0, 5).map((item) => {
          const active = location.pathname === item.path;
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`flex-1 flex flex-col items-center gap-0.5 py-2.5 transition-all ${
                active ? "text-blue-600" : "text-white"
              }`}
            >
              <item.icon size={20} />
              <span className="text-[10px] font-medium">{item.label}</span>
              {active && (
                <div className="absolute top-0 w-8 h-0.5 rounded-full bg-blue-500" />
              )}
            </Link>
          );
        })}
        <button onClick={toggle} className="flex-1 flex flex-col items-center gap-0.5 py-2.5 text-white">
          {theme === "dark" ? <Sun size={20} /> : <Moon size={20} />}
          <span className="text-[10px] font-medium">테마</span>
        </button>
      </nav>
    </>
  );
}
