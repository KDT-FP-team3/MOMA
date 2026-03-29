/**
 * Layout — Samsung Health 스타일 레이아웃
 * light-mode: 밝은 배경 + 블루 액센트
 * dark-mode: 어두운 배경 (기존)
 */
import Sidebar from "./Sidebar";

export default function Layout({ children }) {
  return (
    <div className="flex h-screen bg-gray-900 text-white overflow-hidden">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Premium gradient accent bar */}
        <div className="h-[2px] flex-shrink-0 accent-bar" />
        <main className="flex-1 overflow-y-auto pb-16 lg:pb-0 bg-gray-900">
          {children}
        </main>
      </div>
    </div>
  );
}
