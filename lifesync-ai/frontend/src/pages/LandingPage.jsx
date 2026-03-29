/**
 * LandingPage — Samsung Health 스타일 풀스크린 섹션
 *
 * Unsplash 공용 이미지 사용 (무료 상업적 라이선스)
 */
import { useNavigate } from "react-router-dom";
import TopNav from "../components/layout/TopNav";
import {
  Utensils, Dumbbell, Heart, Palette, ArrowRight, Zap,
  BarChart3, Brain, Camera, Shield, ChevronDown,
} from "lucide-react";

const HERO_IMG = "https://images.unsplash.com/photo-1571019614242-c5c5dee9f50b?w=1600&q=80";
const FOOD_IMG = "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=800&q=80";
const EXERCISE_IMG = "https://images.unsplash.com/photo-1517836357463-d25dfeac3438?w=800&q=80";
const HEALTH_IMG = "https://images.unsplash.com/photo-1505751172876-fa1923c5c528?w=800&q=80";
const HOBBY_IMG = "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=800&q=80";

const DOMAINS = [
  { key: "food", label: "요리", desc: "AI가 건강 상태에 맞는 맞춤 식단을 추천합니다.", icon: Utensils, img: FOOD_IMG, color: "#ea580c" },
  { key: "exercise", label: "운동", desc: "날씨와 컨디션을 고려한 안전한 운동을 제안합니다.", icon: Dumbbell, img: EXERCISE_IMG, color: "#2563eb" },
  { key: "health", label: "건강", desc: "건강검진 결과를 분석하고 맞춤 관리 플랜을 제공합니다.", icon: Heart, img: HEALTH_IMG, color: "#059669" },
  { key: "hobby", label: "취미", desc: "스트레스 수준에 맞는 취미 활동을 추천합니다.", icon: Palette, img: HOBBY_IMG, color: "#7c3aed" },
];

const FEATURES = [
  { icon: Zap, title: "크로스 도메인 CASCADE", desc: "한 가지 선택이 4개 도메인에 연쇄 효과를 만듭니다." },
  { icon: BarChart3, title: "실시간 모니터링", desc: "6개 건강 게이지가 WebSocket으로 즉시 업데이트됩니다." },
  { icon: Brain, title: "PPO 강화학습", desc: "사용자의 패턴을 학습하여 최적의 행동을 추천합니다." },
  { icon: Camera, title: "사진 AI 분석", desc: "음식 사진으로 자동 칼로리/영양소를 추정합니다." },
  { icon: Shield, title: "6명 독립 개발", desc: "플러그인 아키텍처로 팀원별 독립 개발이 가능합니다." },
  { icon: ArrowRight, title: "오프라인 지원", desc: "네트워크 없이도 핵심 기능이 동작합니다." },
];

export default function LandingPage() {
  const navigate = useNavigate();

  return (
    <div className="bg-gray-900 text-white">
      <TopNav />
      {/* ===== HERO SECTION ===== */}
      <section className="relative h-[85vh] min-h-[600px] flex items-center justify-center overflow-hidden">
        <img src={HERO_IMG} alt="" className="absolute inset-0 w-full h-full object-cover" />
        <div className="absolute inset-0 bg-gradient-to-b from-black/50 via-black/30 to-black/70" />
        <div className="relative z-10 text-center px-6 max-w-3xl">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gray-800/90 shadow-lg mb-8">
            <div className="w-7 h-7 rounded-lg flex items-center justify-center" style={{ background: "linear-gradient(135deg, #1a73e8, #4285f4)" }}>
              <Zap size={14} color="#fff" />
            </div>
            <span className="font-bold text-sm" style={{ color: "#1a73e8" }}>LifeSync AI</span>
          </div>
          <h1 className="text-4xl md:text-6xl font-black text-white leading-tight mb-6" style={{ textShadow: "0 2px 20px rgba(0,0,0,0.3)" }}>
            더 건강한 삶을 위한<br />AI 헬스케어 파트너
          </h1>
          <p className="text-lg md:text-xl text-white/90 mb-10" style={{ textShadow: "0 1px 10px rgba(0,0,0,0.2)" }}>
            건강 데이터를 추적하고 AI 기반 인사이트와 맞춤형 코칭을 받아<br className="hidden md:block" />
            더 건강한 삶을 위한 좋은 습관을 만들어 보세요.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <button
              onClick={() => navigate("/onboarding")}
              className="px-8 py-3.5 rounded-full text-white font-semibold text-base shadow-xl hover:shadow-2xl transition-all"
              style={{ background: "linear-gradient(135deg, #1a73e8, #4285f4)" }}
            >
              무료로 시작하기
            </button>
            <button
              onClick={() => navigate("/dashboard")}
              className="px-8 py-3.5 rounded-full bg-gray-800/90 text-white font-semibold text-base shadow-lg hover:bg-gray-700 transition-all"
            >
              대시보드 체험
            </button>
          </div>
        </div>
        {/* Scroll indicator */}
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 animate-bounce">
          <ChevronDown size={28} className="text-white/60" />
        </div>
      </section>

      {/* ===== AI INTRO SECTION ===== */}
      <section className="py-24 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <p className="text-sm font-semibold tracking-widest text-cyan-400 uppercase mb-4">LifeSync AI</p>
          <h2 className="text-3xl md:text-5xl font-black text-white mb-6">
            한 가지 선택이<br />모든 영역에 연쇄 효과를 만듭니다
          </h2>
          <p className="text-lg text-gray-400 max-w-2xl mx-auto">
            야식 라면 한 그릇이 수면 품질, 다음 날 운동 성과, 체중 목표에 동시에 영향을 미칩니다.
            LifeSync AI가 이 연쇄 효과를 추적하고 최적의 균형을 찾아드립니다.
          </p>
        </div>
      </section>

      {/* ===== 4 DOMAINS SECTION ===== */}
      <section className="py-16 px-6 bg-gray-800">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <p className="text-sm font-semibold tracking-widest text-cyan-400 uppercase mb-3">4 DOMAINS</p>
            <h2 className="text-3xl md:text-4xl font-black text-white">하이라이트</h2>
          </div>
          <div className="grid md:grid-cols-2 gap-8">
            {DOMAINS.map((d) => (
              <div key={d.key} className="group relative rounded-3xl overflow-hidden bg-gray-800 shadow-sm hover:shadow-xl transition-all duration-500">
                <div className="h-56 overflow-hidden">
                  <img src={d.img} alt={d.label} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700" />
                </div>
                <div className="p-6">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ backgroundColor: d.color + "15" }}>
                      <d.icon size={20} style={{ color: d.color }} />
                    </div>
                    <h3 className="text-xl font-bold text-white">{d.label}</h3>
                  </div>
                  <p className="text-gray-400 text-sm leading-relaxed">{d.desc}</p>
                  <button
                    onClick={() => navigate("/dashboard")}
                    className="mt-4 text-sm font-semibold flex items-center gap-1 transition-all hover:gap-2"
                    style={{ color: d.color }}
                  >
                    자세히 알아보기 <ArrowRight size={14} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ===== FEATURES SECTION ===== */}
      <section className="py-24 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <p className="text-sm font-semibold tracking-widest text-cyan-400 uppercase mb-3">FEATURES</p>
            <h2 className="text-3xl md:text-4xl font-black text-white">핵심 기술</h2>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {FEATURES.map((f, i) => (
              <div key={i} className="p-6 rounded-2xl bg-gray-800/50 hover:bg-gray-700 hover:shadow-lg transition-all duration-300">
                <div className="w-12 h-12 rounded-xl bg-cyan-500/10 flex items-center justify-center mb-4">
                  <f.icon size={22} className="text-cyan-400" />
                </div>
                <h3 className="text-base font-bold text-white mb-2">{f.title}</h3>
                <p className="text-sm text-gray-500 leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ===== CTA SECTION ===== */}
      <section className="py-24 px-6" style={{ background: "linear-gradient(135deg, #1a73e8, #4285f4)" }}>
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-3xl md:text-4xl font-black text-white mb-6">
            지금 바로 시작하세요
          </h2>
          <p className="text-lg text-white/80 mb-10">
            4개 도메인의 AI 추천을 무료로 체험해 보세요.
          </p>
          <button
            onClick={() => navigate("/onboarding")}
            className="px-10 py-4 rounded-full bg-gray-800 text-cyan-400 font-bold text-lg shadow-xl hover:shadow-2xl hover:scale-105 transition-all"
          >
            무료로 시작하기
          </button>
        </div>
      </section>

      {/* ===== FOOTER ===== */}
      <footer className="py-12 px-6 bg-gray-800 border-t border-gray-700">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded flex items-center justify-center" style={{ background: "#1a73e8" }}>
              <Zap size={12} color="#fff" />
            </div>
            <span className="text-sm font-bold" style={{ color: "#1a73e8" }}>LifeSync AI</span>
            <span className="text-xs text-gray-500 ml-2">v0.4.0</span>
          </div>
          <p className="text-xs text-gray-400">KDT-FT-team3-Chainers | 2026</p>
        </div>
      </footer>
    </div>
  );
}
