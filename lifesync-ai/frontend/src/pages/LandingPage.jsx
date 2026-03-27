/**
 * LandingPage — SCL-inspired clean healthcare design + gamification CTA
 */
import { useNavigate } from "react-router-dom";
import {
  Camera, Zap, Gauge, Brain, ArrowRight, Utensils, Dumbbell,
  Heart, Palette, Shield, TrendingUp, Trophy, Star, Clock, Activity
} from "lucide-react";

const TECH_TAGS = [
  "LangGraph", "LangChain", "PPO RL", "OpenCLIP", "YOLO",
  "MediaPipe", "RAG", "ChromaDB", "Supabase", "GPT-4o",
];

const DOMAINS = [
  { icon: Utensils, label: "요리", color: "#f97316", desc: "레시피 추천 · 영양 분석 · 위험도 평가", stat: "10만+ 레시피" },
  { icon: Dumbbell, label: "운동", color: "#3b82f6", desc: "맞춤 운동 · 날씨 연동 · 부상 예방", stat: "30+ 운동종목" },
  { icon: Heart, label: "건강", color: "#10b981", desc: "검진 분석 · 수면 관리 · 혈액 모니터링", stat: "6개 건강모델" },
  { icon: Palette, label: "취미", color: "#8b5cf6", desc: "스트레스 해소 · 시너지 계산 · 선순환", stat: "크로스도메인" },
];

const FEATURES = [
  { icon: Camera, title: "멀티모달 AI 분석", desc: "사진 한 장으로 BMI 추정, 피부 상태, 자세 분석 후 맞춤 조언을 제공합니다.", badge: "CLIP + MediaPipe" },
  { icon: Zap, title: "크로스 도메인 연쇄", desc: "하나의 선택이 4개 도메인으로 전파됩니다. 야식 → 수면 -35% → 운동 -20%.", badge: "LangGraph" },
  { icon: Gauge, title: "실시간 건강 대시보드", desc: "활성산소, 혈액 청정도, 탈모 위험도 등 6개 지표를 실시간 모니터링합니다.", badge: "WebSocket" },
  { icon: Brain, title: "강화학습 예측 엔진", desc: "PPO 강화학습이 당신의 선택 패턴을 학습하고 최적 전략을 자동 진화시킵니다.", badge: "PPO + Optuna" },
  { icon: Shield, title: "검증된 건강 모델", desc: "Harris-Benedict, Framingham, PSQI 등 논문 기반 6개 모델로 과학적 분석.", badge: "DOI 검증" },
  { icon: TrendingUp, title: "불확실성 시각화", desc: "미래 예측에 에러바와 95% 신뢰구간을 적용하여 정확한 범위를 제시합니다.", badge: "Monte Carlo" },
];

const GAME_FEATURES = [
  { icon: Trophy, label: "레벨 시스템", desc: "건강한 선택으로 EXP를 쌓고 레벨 50까지 성장" },
  { icon: Star, label: "일일 퀘스트", desc: "매일 3개의 건강 퀘스트를 완료하면 보너스 EXP" },
  { icon: Clock, label: "24시간 시뮬레이션", desc: "원형 시계에 일정을 배치하고 미래 건강을 예측" },
  { icon: Activity, label: "캐릭터 성장", desc: "내 선택이 캐릭터에 그대로 반영되는 디지털 트윈" },
];

export default function LandingPage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#050a18] via-[#0c1222] to-[#050a18] text-white overflow-hidden">

      {/* ──── Hero Section (SCL-inspired: clean, spacious, confident) ──── */}
      <section className="relative">
        {/* Ambient glow */}
        <div className="absolute top-[-200px] left-1/2 -translate-x-1/2 w-[800px] h-[800px] bg-cyan-500/[0.04] rounded-full blur-[120px]" />
        <div className="absolute top-[100px] right-[10%] w-[300px] h-[300px] bg-blue-500/[0.03] rounded-full blur-[80px]" />

        <nav className="relative max-w-6xl mx-auto px-6 pt-8 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-9 h-9 rounded-xl flex items-center justify-center text-white shadow-glow-cyan" style={{ background: "linear-gradient(135deg, #06b6d4, #8b5cf6)" }}>
              <Zap size={18} />
            </div>
            <span className="text-lg font-bold tracking-tight text-gradient">LifeSync AI</span>
          </div>
          <div className="hidden md:flex items-center gap-6 text-sm text-gray-400">
            <button onClick={() => navigate("/dashboard")} className="hover:text-white transition">대시보드</button>
            <button onClick={() => navigate("/schedule")} className="hover:text-white transition">스케줄러</button>
            <button onClick={() => navigate("/architecture")} className="hover:text-white transition">아키텍처</button>
            <button onClick={() => navigate("/onboarding")} className="px-5 py-2 rounded-xl font-medium text-white transition-all shadow-lg shadow-cyan-500/20 hover:shadow-cyan-500/30" style={{ background: "linear-gradient(135deg, #06b6d4, #8b5cf6)" }}>시작하기</button>
          </div>
        </nav>

        <div className="relative max-w-6xl mx-auto px-6 pt-24 pb-20 text-center">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-cyan-500/30 bg-cyan-500/5 text-cyan-400 text-xs font-medium mb-8">
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
            AI 기반 크로스 도메인 건강 관리 플랫폼
          </div>

          <h1 className="text-5xl md:text-7xl font-black tracking-tight leading-[1.1]">
            당신의 건강을{" "}
            <span className="bg-gradient-to-r from-cyan-400 via-blue-400 to-purple-400 bg-clip-text text-transparent">
              과학적으로
            </span>
            <br />관리하는 AI
          </h1>

          <p className="mt-6 text-lg md:text-xl text-gray-400 max-w-2xl mx-auto leading-relaxed">
            요리 · 운동 · 건강 · 취미를 하나의 유기체로 통합 관리합니다.
            <br className="hidden md:block" />
            한 가지 선택이 모든 영역에 연쇄 효과를 만듭니다.
          </p>

          {/* Tech tags - subtle, SCL-style */}
          <div className="flex flex-wrap justify-center gap-2 mt-8">
            {TECH_TAGS.map((tag) => (
              <span key={tag} className="px-3 py-1 rounded-md bg-white/[0.04] border border-white/[0.08] text-gray-500 text-xs">
                {tag}
              </span>
            ))}
          </div>

          {/* Dual CTA */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mt-12">
            <button
              onClick={() => navigate("/onboarding")}
              className="group inline-flex items-center gap-2 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-semibold px-8 py-4 rounded-xl transition-all shadow-lg shadow-cyan-500/20 hover:shadow-cyan-500/30 text-lg"
            >
              무료로 시작하기
              <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
            </button>
            <button
              onClick={() => navigate("/simulator")}
              className="inline-flex items-center gap-2 border border-gray-600 hover:border-gray-400 text-gray-300 hover:text-white font-medium px-8 py-4 rounded-xl transition-all"
            >
              시뮬레이터 체험
            </button>
          </div>
        </div>
      </section>

      {/* ──── 4 Domain Cards (SCL-style: card grid, icon + stat) ──── */}
      <section className="max-w-6xl mx-auto px-6 py-16">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold">4개 도메인 통합 관리</h2>
          <p className="mt-3 text-gray-500">각 도메인의 AI 에이전트가 유기적으로 연결됩니다</p>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-5">
          {DOMAINS.map(({ icon: Icon, label, color, desc, stat }) => (
            <div key={label} className="group bg-gray-800/40 backdrop-blur border border-gray-700/50 rounded-2xl p-6 hover:border-gray-500/50 hover:bg-gray-800/60 transition-all duration-300">
              <div className="w-14 h-14 rounded-2xl flex items-center justify-center mb-4" style={{ backgroundColor: color + "18" }}>
                <Icon size={28} style={{ color }} />
              </div>
              <h3 className="text-xl font-bold mb-2">{label}</h3>
              <p className="text-sm text-gray-500 leading-relaxed mb-3">{desc}</p>
              <span className="text-xs font-medium px-2.5 py-1 rounded-md" style={{ backgroundColor: color + "15", color }}>{stat}</span>
            </div>
          ))}
        </div>
      </section>

      {/* ──── Cascade Visual (SCL-inspired: clean process flow) ──── */}
      <section className="max-w-6xl mx-auto px-6 py-16">
        <div className="bg-gradient-to-r from-red-500/5 via-amber-500/5 to-cyan-500/5 border border-gray-700/30 rounded-3xl p-8 md:p-12">
          <h2 className="text-2xl font-bold text-center mb-2">크로스 도메인 연쇄 효과</h2>
          <p className="text-center text-gray-500 mb-8">하나의 선택이 만드는 나비효과를 실시간 추적합니다</p>
          <div className="flex flex-col md:flex-row items-center justify-center gap-3 text-sm">
            {[
              { text: "야식 라면 (23시)", color: "bg-red-500/10 text-red-400 border-red-500/30" },
              { text: "수면 품질 -35%", color: "bg-amber-500/10 text-amber-400 border-amber-500/30" },
              { text: "운동 능력 -20%", color: "bg-orange-500/10 text-orange-400 border-orange-500/30" },
              { text: "체중 목표 +2일 지연", color: "bg-yellow-500/10 text-yellow-400 border-yellow-500/30" },
              { text: "전체 점수 -12", color: "bg-cyan-500/10 text-cyan-400 border-cyan-500/30" },
            ].map((step, i) => (
              <div key={i} className="flex items-center gap-3">
                <span className={`px-4 py-2.5 rounded-xl border font-medium whitespace-nowrap ${step.color}`}>
                  {step.text}
                </span>
                {i < 4 && <span className="text-gray-600 hidden md:block">→</span>}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ──── Features Grid (SCL-style: 2x3 card grid) ──── */}
      <section className="max-w-6xl mx-auto px-6 py-16">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold">핵심 기술</h2>
          <p className="mt-3 text-gray-500">기존 헬스케어 앱에서 불가능했던 기능을 제공합니다</p>
        </div>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
          {FEATURES.map(({ icon: Icon, title, desc, badge }) => (
            <div key={title} className="bg-gray-800/30 border border-gray-700/40 rounded-2xl p-6 hover:border-gray-600/50 transition-all group">
              <div className="flex items-center justify-between mb-4">
                <div className="w-11 h-11 rounded-xl bg-cyan-500/10 flex items-center justify-center">
                  <Icon size={22} className="text-cyan-400" />
                </div>
                <span className="text-[10px] px-2 py-0.5 rounded bg-gray-700/60 text-gray-500 font-mono">{badge}</span>
              </div>
              <h3 className="font-bold text-lg mb-2">{title}</h3>
              <p className="text-sm text-gray-500 leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ──── Gamification Section ──── */}
      <section className="max-w-6xl mx-auto px-6 py-16">
        <div className="bg-gradient-to-br from-purple-500/5 via-gray-900 to-cyan-500/5 border border-gray-700/30 rounded-3xl p-8 md:p-12">
          <div className="text-center mb-10">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-purple-500/10 border border-purple-500/30 text-purple-400 text-xs font-medium mb-4">
              <Trophy size={14} /> NEW
            </span>
            <h2 className="text-3xl font-bold">건강을 게임처럼</h2>
            <p className="mt-3 text-gray-500">캐릭터를 키우면서 자연스럽게 건강해집니다</p>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {GAME_FEATURES.map(({ icon: Icon, label, desc }) => (
              <div key={label} className="text-center p-5">
                <div className="w-14 h-14 rounded-2xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center mx-auto mb-4">
                  <Icon size={24} className="text-purple-400" />
                </div>
                <h3 className="font-bold mb-1.5">{label}</h3>
                <p className="text-xs text-gray-500 leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>
          <div className="text-center mt-8">
            <button
              onClick={() => navigate("/avatar")}
              className="inline-flex items-center gap-2 px-6 py-3 bg-purple-600 hover:bg-purple-500 rounded-xl text-white font-medium transition-all"
            >
              캐릭터 만들기
              <ArrowRight size={18} />
            </button>
          </div>
        </div>
      </section>

      {/* ──── Differentiators (What others can't do) ──── */}
      <section className="max-w-6xl mx-auto px-6 py-16">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold">기존 서비스와의 차별점</h2>
        </div>
        <div className="grid md:grid-cols-3 gap-6">
          {[
            { title: "크로스 도메인 연쇄", existing: "각 영역 독립 관리", ours: "음식→운동→건강→취미 자동 연쇄", color: "cyan" },
            { title: "강화학습 적응", existing: "고정 알고리즘 추천", ours: "사용자 패턴 학습 + 자동 진화", color: "purple" },
            { title: "불확실성 시각화", existing: "단일 예측값만 제시", ours: "95% 신뢰구간 + 에러바 확장", color: "emerald" },
          ].map(({ title, existing, ours, color }) => (
            <div key={title} className="bg-gray-800/30 border border-gray-700/40 rounded-2xl p-6">
              <h3 className={`font-bold text-${color}-400 mb-4`}>{title}</h3>
              <div className="space-y-3">
                <div className="flex items-start gap-2">
                  <span className="text-red-500 text-xs mt-0.5">✕</span>
                  <p className="text-sm text-gray-500">{existing}</p>
                </div>
                <div className="flex items-start gap-2">
                  <span className="text-emerald-500 text-xs mt-0.5">✓</span>
                  <p className="text-sm text-gray-300">{ours}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ──── Final CTA ──── */}
      <section className="max-w-6xl mx-auto px-6 py-20 text-center">
        <h2 className="text-3xl md:text-4xl font-bold mb-4">
          지금 바로 <span className="bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent">시작하세요</span>
        </h2>
        <p className="text-gray-500 mb-8 max-w-lg mx-auto">
          3단계 온보딩으로 1분 만에 당신만의 AI 건강 관리 캐릭터가 생성됩니다.
        </p>
        <button
          onClick={() => navigate("/onboarding")}
          className="group inline-flex items-center gap-2 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-bold px-10 py-4 rounded-xl text-lg transition-all shadow-xl shadow-cyan-500/20"
        >
          무료 체험 시작
          <ArrowRight size={22} className="group-hover:translate-x-1 transition-transform" />
        </button>
      </section>

      {/* ──── Footer (SCL-style: minimal, institutional) ──── */}
      <footer className="border-t border-gray-800/50 py-10">
        <div className="max-w-6xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-md bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center text-white font-black text-[10px]">LS</div>
            <span className="text-sm font-semibold text-gray-400">LifeSync AI</span>
          </div>
          <p className="text-xs text-gray-600">
            KDT Team Chainers · 6명 · Python + FastAPI + LangGraph + PPO + React
          </p>
          <div className="flex items-center gap-4 text-xs text-gray-600">
            <button onClick={() => navigate("/architecture")} className="hover:text-gray-400 transition">아키텍처</button>
            <span>·</span>
            <button onClick={() => navigate("/report")} className="hover:text-gray-400 transition">리포트</button>
          </div>
        </div>
      </footer>
    </div>
  );
}
