/**
 * Layout — Premium healthcare AI layout
 */
import Sidebar from "./Sidebar";

export default function Layout({ children }) {
  return (
    <div className="flex h-screen bg-gray-900 text-white overflow-hidden">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Premium gradient accent bar */}
        <div className="h-[3px] flex-shrink-0 accent-bar" />
        <main className="flex-1 overflow-y-auto pb-16 lg:pb-0 bg-mesh-dark">
          {children}
        </main>
      </div>
    </div>
  );
}
