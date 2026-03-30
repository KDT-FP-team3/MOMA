/**
 * Layout — Samsung Health 스타일 (상단 네비게이션)
 * bg-gray-900: 다크에서 어두운 배경, 라이트에서 CSS 오버라이드로 흰색
 */
import TopNav from "./TopNav";

export default function Layout({ children }) {
  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <TopNav />
      <main className="pb-16 lg:pb-0">{children}</main>
    </div>
  );
}
