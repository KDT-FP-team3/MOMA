/**
 * ErrorBoundary — React 에러 경계 컴포넌트
 * 하위 컴포넌트에서 발생한 렌더링 에러를 잡아 fallback UI 표시.
 */
import React from "react";

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("ErrorBoundary caught:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex items-center justify-center min-h-screen bg-gray-900 p-6">
          <div className="bg-gray-800 rounded-2xl p-8 max-w-md w-full text-center border border-red-500/30">
            <div className="text-4xl mb-4">⚠️</div>
            <h2 className="text-xl font-bold text-white mb-2">
              오류가 발생했습니다
            </h2>
            <p className="text-white text-sm mb-6">
              {this.state.error?.message || "알 수 없는 오류"}
            </p>
            <button
              onClick={() => {
                this.setState({ hasError: false, error: null });
                window.location.hash = "#/dashboard";
                window.location.reload();
              }}
              className="px-6 py-2.5 bg-cyan-500 hover:bg-cyan-600 text-white rounded-lg transition-colors text-sm font-medium"
            >
              대시보드로 돌아가기
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
