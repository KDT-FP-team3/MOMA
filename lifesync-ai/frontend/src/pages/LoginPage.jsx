/**
 * LoginPage — 카카오 로그인 (REST API 리다이렉트) + 게스트 모드
 */
import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { useAppState } from "../context/AppStateContext";

const API_BASE = import.meta.env.VITE_API_BASE || "";

export default function LoginPage() {
  const navigate = useNavigate();
  const { state, updateState } = useAppState();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // 이미 로그인 상태면 대시보드로
  useEffect(() => {
    if (state.authUser) navigate("/dashboard");
  }, [state.authUser, navigate]);

  // 콜백 처리: 카카오 리다이렉트 후 code 파라미터로 돌아왔을 때
  // HashRouter 사용 시: /auth/kakao/callback?code=xxx → /#/login?code=xxx (307 리다이렉트)
  // 또는 직접 접근 시: /#/login?code=xxx 또는 ?code=xxx#/login
  useEffect(() => {
    // 1. window.location.search에서 확인 (일반 경우)
    let params = new URLSearchParams(window.location.search);
    let code = params.get("code");
    // 2. hash 내부 쿼리에서 확인 (HashRouter 리다이렉트 경우)
    if (!code && window.location.hash.includes("?")) {
      const hashQuery = window.location.hash.split("?")[1];
      if (hashQuery) {
        params = new URLSearchParams(hashQuery);
        code = params.get("code");
      }
    }
    if (!code) return;

    setLoading(true);
    setError("");
    axios
      .post(`${API_BASE}/api/auth/kakao/callback`, { code })
      .then((res) => {
        updateState("authUser", res.data.user);
        updateState("authToken", res.data.token);
        updateState("userId", res.data.user.id);
        // 토큰을 sessionStorage에 저장 (브라우저 탭 종료 시 자동 삭제)
        try { sessionStorage.setItem("lifesync-auth-token", res.data.token); } catch {}
        navigate("/dashboard");
      })
      .catch((err) => {
        const msg =
          err.response?.data?.detail || "카카오 로그인 처리 실패";
        setError(msg);
        setLoading(false);
        // URL에서 code 파라미터 제거
        window.history.replaceState({}, "", "/login");
      });
  }, [navigate, updateState]);

  const handleKakaoLogin = useCallback(() => {
    setLoading(true);
    setError("");
    // 백엔드에서 REST API 키로 생성한 로그인 URL로 리다이렉트
    axios
      .get(`${API_BASE}/api/auth/kakao/login-url`)
      .then((res) => {
        window.location.href = res.data.url;
      })
      .catch((err) => {
        console.error("카카오 로그인 URL 요청 실패:", err);
        setError("로그인 URL 생성 실패. 서버 연결을 확인해주세요.");
        setLoading(false);
      });
  }, []);

  const handleGuestLogin = () => {
    updateState("authUser", {
      id: "guest",
      nickname: "게스트 (읽기 전용)",
      profile_image: "",
      provider: "guest",
      isGuest: true,
    });
    updateState("userId", "guest");
    // 게스트는 토큰 없이 접근 — 백엔드에서 읽기만 허용
    try { sessionStorage.removeItem("lifesync-auth-token"); } catch {}
    navigate("/dashboard");
  };

  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center p-4">
      <div className="w-full max-w-sm space-y-6">
        {/* 로고 */}
        <div className="text-center space-y-2">
          <div className="w-20 h-20 mx-auto rounded-2xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
            <span className="text-3xl"></span>
          </div>
          <h1 className="text-2xl font-bold text-white">LifeSync AI</h1>
          <p className="text-sm text-white">일상 생활 통합 건강 관리</p>
        </div>

        {/* 에러 메시지 */}
        {error && (
          <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-3 text-sm text-red-400 text-center">
            {error}
          </div>
        )}

        {/* 카카오 로그인 버튼 */}
        <button
          onClick={handleKakaoLogin}
          disabled={loading}
          className="w-full flex items-center justify-center gap-3 py-3.5 rounded-xl font-semibold text-sm transition-all disabled:opacity-50"
          style={{ backgroundColor: "#FEE500", color: "#191919" }}
        >
          {loading ? (
            <span className="animate-spin rounded-full h-5 w-5 border-b-2 border-gray-800" />
          ) : (
            <>
              <svg width="20" height="20" viewBox="0 0 20 20">
                <path
                  d="M10 2C5.03 2 1 5.13 1 8.97c0 2.48 1.65 4.66 4.13 5.88-.18.66-.65 2.4-.74 2.77-.12.46.17.45.35.33.15-.1 2.33-1.58 3.27-2.22.32.04.65.07.99.07 4.97 0 9-3.13 9-6.97C19 5.13 14.97 2 10 2z"
                  fill="#191919"
                />
              </svg>
              카카오 계정으로 시작하기
            </>
          )}
        </button>

        {/* 구분선 */}
        <div className="flex items-center gap-3">
          <div className="flex-1 h-px bg-gray-700" />
          <span className="text-xs text-white">또는</span>
          <div className="flex-1 h-px bg-gray-700" />
        </div>

        {/* 게스트 로그인 */}
        <button
          onClick={handleGuestLogin}
          className="w-full py-3 rounded-xl border border-gray-700 text-white text-sm font-medium hover:bg-gray-800 transition-all"
        >
          게스트로 둘러보기
        </button>

        <p className="text-center text-[11px] text-white leading-relaxed">
          로그인 시 데이터가 저장되어<br />맞춤형 건강 관리를 받을 수 있습니다.
        </p>
      </div>
    </div>
  );
}
