/**
 * DashboardPage — Samsung Health 스타일 대시보드
 *
 * 구조:
 *   1. 모니터링 허브 (종합 링 + 핵심 지표 + AI 진단)
 *   2. 3-탭 액션 패널 (솔루션 / 인사이트 / 코칭)
 *   3. 6개 상세 게이지 (GaugePanel)
 *   4. 주간 요약
 *
 * 데이터 흐름:
 *   마운트 → GET /api/dashboard/default → gauges + domainSummary
 *   솔루션 적용 → POST /api/query → cascade + gauge 업데이트
 *   WebSocket → gauge_update → 실시간 반영
 */
import { useState, useEffect, useMemo, useCallback } from "react";
import Layout from "../components/layout/Layout";
import GaugePanel from "../components/dashboard/GaugePanel";
import QuickChat from "../components/dashboard/QuickChat";
import CascadeAlert from "../components/cascade/CascadeAlert";
import { useAppState } from "../context/AppStateContext";
import {
  Activity, TrendingUp, Utensils, Dumbbell, Heart, Palette,
  Lightbulb, BarChart3, MessageCircle, Sparkles, Moon, Brain,
  Droplets, Target, ChevronRight, Zap, ArrowRight, CheckCircle,
} from "lucide-react";
// Recharts는 GaugePanel에서 사용 (DashboardPage에서는 SVG 직접 사용)
import axios from "axios";

/* ─── 도메인 설정 ─── */
const DOMAINS = {
  food:     { icon: Utensils,  label: "요리", color: "#fb923c", accent: "from-orange-500 to-amber-500",   bg: "bg-orange-500/8",  border: "border-orange-500/20", text: "text-orange-400" },
  exercise: { icon: Dumbbell,  label: "운동", color: "#60a5fa", accent: "from-blue-500 to-cyan-500",      bg: "bg-blue-500/8",    border: "border-blue-500/20",   text: "text-blue-400" },
  health:   { icon: Heart,     label: "건강", color: "#34d399", accent: "from-emerald-500 to-green-500",  bg: "bg-emerald-500/8", border: "border-emerald-500/20", text: "text-emerald-400" },
  hobby:    { icon: Palette,   label: "취미", color: "#a78bfa", accent: "from-violet-500 to-purple-500",  bg: "bg-violet-500/8",  border: "border-violet-500/20", text: "text-violet-400" },
};

/* ─── AI 자동 솔루션 추천 ─── */
const AUTO_SOLUTIONS = [
  { domain: "food",     title: "맞춤 식단 추천",       desc: "현재 건강 상태에 최적화된 식단을 AI가 추천합니다.", query: "오늘 건강 상태에 맞는 식단 추천해줘" },
  { domain: "exercise", title: "운동 플랜 최적화",      desc: "날씨와 컨디션을 고려한 오늘의 운동을 제안합니다.", query: "오늘 컨디션에 맞는 운동 추천해줘" },
  { domain: "health",   title: "건강 위험 분석",        desc: "현재 지표 기반으로 주의할 건강 요소를 분석합니다.", query: "현재 건강 상태 분석해줘" },
  { domain: "hobby",    title: "스트레스 해소 활동",     desc: "스트레스 수치에 맞는 취미 활동을 추천합니다.",     query: "스트레스 해소할 취미 추천해줘" },
];

/* ─── 오늘의 미션 ─── */
const DAILY_MISSIONS = [
  { id: 1, title: "아침 스트레칭 10분",   domain: "exercise", reward: "+3 달성률", done: false },
  { id: 2, title: "물 8잔 마시기",        domain: "health",   reward: "+2 혈액 청정", done: false },
  { id: 3, title: "15분 명상 또는 독서",  domain: "hobby",    reward: "-5 스트레스", done: false },
];

/* ─── AI 진단 생성 ─── */
function generateDiagnosis(gauges) {
  const g = gauges || {};
  const sleep = g.sleep_score || 0;
  const stress = g.stress_level || 0;
  const blood = g.blood_purity || 0;
  const achieve = g.weekly_achievement || 0;

  const issues = [];
  if (sleep < 60) issues.push("수면 질이 낮습니다");
  if (stress > 60) issues.push("스트레스 관리가 필요합니다");
  if (blood < 60) issues.push("혈액 건강에 주의하세요");
  if (achieve < 50) issues.push("주간 목표 달성률을 높여보세요");

  if (issues.length === 0) return "전반적으로 양호한 상태입니다. 현재 루틴을 유지하세요!";
  if (issues.length === 1) return `${issues[0]}. AI가 맞춤 솔루션을 준비했습니다.`;
  return `${issues[0]}, ${issues[1]}. 아래 솔루션을 확인해보세요.`;
}

function getScoreColor(score) {
  if (score >= 80) return "#34d399";
  if (score >= 60) return "#06b6d4";
  if (score >= 40) return "#fbbf24";
  return "#f87171";
}

/* ─── 메인 대시보드 ─── */
export default function DashboardPage() {
  const { state, updateState } = useAppState();
  const [activeTab, setActiveTab] = useState("solution");
  const [solutionLoading, setSolutionLoading] = useState(new Set());
  const [solutionResults, setSolutionResults] = useState({});
  const [missions, setMissions] = useState(DAILY_MISSIONS);
  const [fetchError, setFetchError] = useState(false);

  // 마운트 시 대시보드 데이터 로드
  useEffect(() => {
    axios.get(`/api/dashboard/${state.userId || "default"}`)
      .then((res) => {
        if (res.data.gauges) updateState("gauges", res.data.gauges);
        if (res.data.domain_summary) updateState("domainSummary", res.data.domain_summary);
        setFetchError(false);
      })
      .catch(() => { setFetchError(true); });
  }, []);

  const gauges = state.gauges || {
    reactive_oxygen: 62, blood_purity: 78, hair_loss_risk: 23,
    sleep_score: 71, stress_level: 45, weekly_achievement: 67,
  };

  // 종합 점수 계산 (inverted 지표 보정)
  const overallScore = useMemo(() => {
    const g = gauges;
    const scores = [
      g.blood_purity || 0,
      g.sleep_score || 0,
      100 - (g.stress_level || 0),
      100 - (g.hair_loss_risk || 0),
      100 - (g.reactive_oxygen || 0),
      g.weekly_achievement || 0,
    ];
    return Math.round(scores.reduce((a, b) => a + b, 0) / scores.length);
  }, [gauges]);

  const diagnosis = useMemo(() => generateDiagnosis(gauges), [gauges]);
  const scoreColor = getScoreColor(overallScore);

  // 솔루션 적용 (여러 도메인 동시 로딩 지원)
  const applySolution = useCallback(async (sol) => {
    setSolutionLoading((prev) => new Set([...prev, sol.domain]));
    try {
      const res = await axios.post("/api/query", {
        domain: sol.domain,
        action: { query: sol.query, meal_type: "", preference: sol.query },
        user_id: state.userId || "default",
      });
      setSolutionResults((prev) => ({ ...prev, [sol.domain]: res.data }));
      if (res.data.updated_gauges) {
        updateState("gauges", (prev) => ({ ...prev, ...res.data.updated_gauges }));
      }
      if (res.data.cascade_effects) {
        updateState("lastCascade", res.data.cascade_effects);
      }
    } catch {
      setSolutionResults((prev) => ({ ...prev, [sol.domain]: { error: true } }));
    } finally {
      setSolutionLoading((prev) => { const next = new Set(prev); next.delete(sol.domain); return next; });
    }
  }, [state.userId, updateState]);

  // 미션 완료 토글
  const toggleMission = (id) => {
    setMissions((prev) => prev.map((m) => m.id === id ? { ...m, done: !m.done } : m));
  };

  // 도메인 요약
  const domainSummary = state.domainSummary || {};

  // 오늘 날짜
  const today = new Date();
  const dateStr = `${today.getMonth() + 1}월 ${today.getDate()}일 ${["일","월","화","수","목","금","토"][today.getDay()]}요일`;

  /* ─── 핵심 지표 4개 ─── */
  const keyMetrics = [
    { key: "sleep_score",        label: "수면",     icon: Moon,     value: gauges.sleep_score || 0,     unit: "점",  color: "#748ffc" },
    { key: "stress_level",       label: "스트레스", icon: Brain,    value: gauges.stress_level || 0,    unit: "레벨", color: "#ff922b", invert: true },
    { key: "blood_purity",       label: "혈액",     icon: Droplets, value: gauges.blood_purity || 0,    unit: "점",  color: "#51cf66" },
    { key: "weekly_achievement", label: "달성률",   icon: Target,   value: gauges.weekly_achievement || 0, unit: "%", color: "#20c997" },
  ];

  return (
    <Layout>
      <div className="p-4 md:p-6 space-y-5 max-w-7xl mx-auto">

        {/* ════════════════════════════════════════════════
            헤더 — 인사말 + 날짜 + AI 상태
           ════════════════════════════════════════════════ */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-white">
              안녕하세요 <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-violet-400">LifeSync</span>
            </h1>
            <p className="text-sm text-white mt-0.5">{dateStr} — 오늘의 건강 리포트</p>
          </div>
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20">
            <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-xs text-emerald-400 font-medium">AI 모니터링 활성</span>
          </div>
        </div>

        {/* 데이터 로드 실패 알림 */}
        {fetchError && (
          <div className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-red-500/10 border border-red-500/20 text-sm text-red-400">
            <span>서버 연결에 실패했습니다. 오프라인 데이터를 표시합니다.</span>
            <button onClick={() => window.location.reload()} className="ml-auto text-xs underline hover:text-red-300">재시도</button>
          </div>
        )}

        {/* ════════════════════════════════════════════════
            모니터링 허브 — 중앙 링 + 핵심 지표 + AI 진단
           ════════════════════════════════════════════════ */}
        <div className="bg-gray-800 rounded-2xl border border-gray-700 p-5 md:p-6">
          <div className="flex flex-col lg:flex-row items-center gap-6">

            {/* 중앙 링 차트 */}
            <div className="relative w-44 h-44 md:w-52 md:h-52 flex-shrink-0">
              <svg viewBox="0 0 200 200" className="absolute inset-0 w-full h-full">
                <circle cx="100" cy="100" r="80" fill="none" stroke="#e5e7eb" strokeWidth="14"
                  strokeDasharray={`${Math.PI * 80 * 270 / 360} ${Math.PI * 80 * 90 / 360}`}
                  strokeLinecap="round" transform="rotate(135 100 100)" opacity="0.3" />
                <circle cx="100" cy="100" r="80" fill="none" stroke={scoreColor} strokeWidth="14"
                  strokeDasharray={`${Math.PI * 80 * 270 * overallScore / 36000} ${Math.PI * 80 * 2}`}
                  strokeLinecap="round" transform="rotate(135 100 100)"
                  style={{ transition: "stroke-dasharray 0.5s ease" }} />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-3xl md:text-4xl font-black" style={{ color: scoreColor }}>
                  {overallScore}
                </span>
                <span className="text-[10px] text-white font-medium tracking-wider mt-0.5">종합 건강 점수</span>
              </div>
            </div>

            {/* 핵심 지표 + AI 진단 */}
            <div className="flex-1 w-full">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
                {keyMetrics.map((m) => {
                  const display = m.value;
                  return (
                    <div key={m.key} className="bg-gray-800/60 rounded-xl p-3 border border-gray-700/40 hover:border-gray-600/60 transition-all group">
                      <div className="flex items-center gap-2 mb-2">
                        <m.icon size={14} style={{ color: m.color }} className="group-hover:scale-110 transition-transform" />
                        <span className="text-[11px] text-white">{m.label}</span>
                      </div>
                      <div className="flex items-baseline gap-1">
                        <span className="text-xl font-bold" style={{ color: m.color }}>{display}</span>
                        <span className="text-[10px] text-white">{m.unit}</span>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* AI 한줄 진단 */}
              <div className="flex items-start gap-2.5 bg-gradient-to-r from-cyan-500/5 to-violet-500/5 rounded-xl px-4 py-3 border border-cyan-500/10">
                <Sparkles size={16} className="text-cyan-400 flex-shrink-0 mt-0.5" />
                <div>
                  <span className="text-[10px] text-cyan-500 font-semibold tracking-wide">AI DIAGNOSIS</span>
                  <p className="text-sm text-white mt-0.5 leading-relaxed">{diagnosis}</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* ════════════════════════════════════════════════
            3-탭 액션 패널 — 솔루션 / 인사이트 / 코칭
           ════════════════════════════════════════════════ */}
        <div>
          {/* 탭 헤더 */}
          <div className="flex gap-1 mb-4 bg-gray-800/50 p-1 rounded-xl w-fit">
            {[
              { key: "solution", label: "솔루션", icon: Lightbulb, desc: "AI 맞춤 추천" },
              { key: "insight",  label: "인사이트", icon: BarChart3, desc: "연쇄 분석" },
              { key: "coaching", label: "코칭",    icon: MessageCircle, desc: "AI 코칭" },
            ].map((t) => (
              <button
                key={t.key}
                onClick={() => setActiveTab(t.key)}
                className={`flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-medium transition-all ${
                  activeTab === t.key
                    ? "bg-gradient-to-r from-cyan-500/15 to-violet-500/10 text-cyan-400 shadow-sm shadow-cyan-500/10"
                    : "text-white hover:text-white"
                }`}
              >
                <t.icon size={15} />
                <span>{t.label}</span>
                <span className="text-[9px] text-white hidden md:inline">{t.desc}</span>
              </button>
            ))}
          </div>

          {/* 솔루션 탭 */}
          {activeTab === "solution" && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {AUTO_SOLUTIONS.map((sol) => {
                const d = DOMAINS[sol.domain];
                const Icon = d.icon;
                const result = solutionResults[sol.domain];
                const isLoading = solutionLoading.has(sol.domain);
                const recs = result?.result?.recommendations || [];

                return (
                  <div key={sol.domain} className={`bg-gray-800/60 rounded-2xl border ${d.border} p-5 hover:bg-gray-800/80 transition-all group`}>
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${d.accent} flex items-center justify-center shadow-lg`}>
                          <Icon size={18} className="text-white" />
                        </div>
                        <div>
                          <h3 className="text-sm font-bold text-white">{sol.title}</h3>
                          <p className="text-[11px] text-white">{sol.desc}</p>
                        </div>
                      </div>
                      {!result && (
                        <button
                          onClick={() => applySolution(sol)}
                          disabled={isLoading}
                          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                            isLoading
                              ? "bg-gray-700 text-white"
                              : `bg-gradient-to-r ${d.accent} text-white hover:shadow-lg`
                          }`}
                        >
                          {isLoading ? (
                            <div className="w-3 h-3 border-2 border-gray-400 border-t-transparent rounded-full animate-spin" />
                          ) : (
                            <Zap size={12} />
                          )}
                          {isLoading ? "분석 중..." : "적용하기"}
                        </button>
                      )}
                    </div>

                    {/* 추천 결과 (로딩 중에는 숨김) */}
                    {!isLoading && result && !result.error && recs.length > 0 && (
                      <div className="mt-3 space-y-2">
                        {recs.slice(0, 3).map((r, i) => (
                          <div key={i} className="flex items-center gap-2 bg-gray-900/50 rounded-lg px-3 py-2 text-xs">
                            <span className={`font-bold ${d.text}`}>{i + 1}</span>
                            <span className="text-white font-medium">{r.name}</span>
                            {r.calories && <span className="text-white ml-auto">{r.calories}kcal</span>}
                            {r.duration_min && <span className="text-white ml-auto">{r.duration_min}분</span>}
                          </div>
                        ))}
                        {result.cascade_effects?.effects && Object.keys(result.cascade_effects.effects).length > 0 && (
                          <div className="mt-2 bg-cyan-500/5 rounded-lg px-3 py-2 border border-cyan-500/10">
                            <div className="flex items-center gap-1.5 text-[10px] text-cyan-500 mb-1.5">
                              <ArrowRight size={10} />
                              <span className="font-medium">CASCADE: {Object.keys(result.cascade_effects.effects).length}개 도메인 연쇄 효과</span>
                            </div>
                            {Object.entries(result.cascade_effects.effects).map(([domain, eff]) => (
                              <div key={domain} className="flex items-center gap-2 text-[10px] text-white ml-3">
                                <span className={DOMAINS[domain]?.text || "text-white"}>{DOMAINS[domain]?.label || domain}</span>
                                <span>— {eff.description}</span>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                    {result?.error && (
                      <p className="text-xs text-red-400 mt-3">서버 연결에 실패했습니다.</p>
                    )}

                    {/* 도메인 요약 (API 데이터) */}
                    {!result && domainSummary[sol.domain] && (
                      <div className="mt-3 flex items-center justify-between text-xs">
                        <span className="text-white">현재 상태</span>
                        <span className={`font-medium ${d.text}`}>
                          {domainSummary[sol.domain].value || "-"}
                          <span className="text-white ml-1">{domainSummary[sol.domain].sub || ""}</span>
                        </span>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}

          {/* 인사이트 탭 */}
          {activeTab === "insight" && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
              {/* CASCADE 분석 */}
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <BarChart3 size={15} className="text-cyan-400" />
                  <h3 className="text-sm font-semibold text-white">연쇄 효과 분석</h3>
                </div>
                <CascadeAlert />
              </div>

              {/* 도메인 상관관계 */}
              <div className="space-y-4">
                <div className="flex items-center gap-2 mb-3">
                  <TrendingUp size={15} className="text-violet-400" />
                  <h3 className="text-sm font-semibold text-white">도메인 상관관계</h3>
                </div>

                {/* 크로스 도메인 매트릭스 */}
                <div className="bg-gray-800/60 rounded-2xl border border-gray-700/40 p-4">
                  <p className="text-[10px] text-white mb-3 tracking-wide">CASCADE RULES — 오케스트레이터 연결</p>
                  <div className="space-y-2">
                    {[
                      { from: "food", to: "health", effect: "칼로리/영양 → 건강 영향", strength: 85 },
                      { from: "exercise", to: "health", effect: "운동 → 수면/스트레스 개선", strength: 75 },
                      { from: "hobby", to: "health", effect: "취미 → 스트레스 해소", strength: 65 },
                      { from: "food", to: "exercise", effect: "과식 → 추가 운동 필요", strength: 50 },
                      { from: "hobby", to: "food", effect: "취미 → 폭식 충동 감소", strength: 40 },
                    ].map((rel, i) => (
                      <div key={i} className="flex items-center gap-3 text-xs">
                        <span className={`font-medium w-8 ${DOMAINS[rel.from]?.text}`}>{DOMAINS[rel.from]?.label}</span>
                        <ArrowRight size={10} className="text-white" />
                        <span className={`font-medium w-8 ${DOMAINS[rel.to]?.text}`}>{DOMAINS[rel.to]?.label}</span>
                        <div className="flex-1 bg-gray-700/50 rounded-full h-1.5 overflow-hidden">
                          <div
                            className="h-full rounded-full bg-gradient-to-r from-cyan-500 to-violet-500 transition-all duration-1000"
                            style={{ width: `${rel.strength}%` }}
                          />
                        </div>
                        <span className="text-white w-32 text-[10px] text-right">{rel.effect}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* 주간 하이라이트 */}
                <div className="bg-gray-800/60 rounded-2xl border border-gray-700/40 p-4">
                  <p className="text-[10px] text-white mb-3 tracking-wide">이번 주 핵심 인사이트</p>
                  <div className="space-y-2">
                    <InsightItem icon="+" color="text-emerald-400" text="운동 후 수면 점수가 평균 12% 상승했습니다" />
                    <InsightItem icon="!" color="text-amber-400" text="야식 빈도가 주 2회로 스트레스 상승에 영향" />
                    <InsightItem icon="" color="text-cyan-400" text="기타 연주가 가장 높은 스트레스 감소 효과" />
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* 코칭 탭 */}
          {activeTab === "coaching" && (
            <div className="space-y-4">
              {/* 오늘의 미션 */}
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <Target size={15} className="text-amber-400" />
                  <h3 className="text-sm font-semibold text-white">오늘의 미션</h3>
                  <span className="text-[10px] text-white ml-auto">
                    {missions.filter((m) => m.done).length}/{missions.length} 완료
                  </span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
                  {missions.map((m) => {
                    const d = DOMAINS[m.domain];
                    return (
                      <button
                        key={m.id}
                        onClick={() => toggleMission(m.id)}
                        className={`flex items-center gap-3 rounded-xl p-3 border transition-all text-left ${
                          m.done
                            ? "bg-emerald-500/5 border-emerald-500/30"
                            : `bg-gray-800/60 ${d.border} hover:bg-gray-800/80`
                        }`}
                      >
                        <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center flex-shrink-0 transition-all ${
                          m.done ? "border-emerald-400 bg-emerald-500/20" : "border-gray-600"
                        }`}>
                          {m.done && <CheckCircle size={12} className="text-emerald-400" />}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className={`text-xs font-medium ${m.done ? "text-white line-through" : "text-white"}`}>{m.title}</p>
                          <p className={`text-[10px] mt-0.5 ${m.done ? "text-emerald-500" : d.text}`}>{m.reward}</p>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* AI 채팅 (기존 QuickChat 100% 재사용) */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
                <QuickChat />
                <CascadeAlert />
              </div>
            </div>
          )}
        </div>

        {/* ════════════════════════════════════════════════
            6개 상세 게이지 (기존 GaugePanel 유지)
           ════════════════════════════════════════════════ */}
        <GaugePanel />

        {/* ════════════════════════════════════════════════
            주간 요약 — Samsung Health 스타일 카드
           ════════════════════════════════════════════════ */}
        <div className="bg-gray-800 rounded-2xl border border-gray-700 p-5 md:p-6">
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp size={16} className="text-cyan-400" />
            <h3 className="text-sm font-semibold text-white">이번 주 요약</h3>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { value: "12,950", unit: "kcal",   label: "칼로리 섭취", color: DOMAINS.food.color, icon: Utensils },
              { value: "4.5",    unit: "시간",    label: "운동 시간",   color: DOMAINS.exercise.color, icon: Dumbbell },
              { value: "7.2",    unit: "시간",    label: "평균 수면",   color: DOMAINS.health.color, icon: Moon },
              { value: "2.5",    unit: "시간",    label: "취미 활동",   color: DOMAINS.hobby.color, icon: Palette },
            ].map((item, i) => (
              <div key={i} className="bg-gray-800/40 rounded-xl p-4 border border-gray-700/30 hover:border-gray-600/50 transition-all group text-center">
                <item.icon size={18} style={{ color: item.color }} className="mx-auto mb-2 group-hover:scale-110 transition-transform" />
                <p className="text-2xl font-bold" style={{ color: item.color }}>{item.value}</p>
                <p className="text-[10px] text-white mt-0.5">{item.unit}</p>
                <p className="text-xs text-white mt-1">{item.label}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </Layout>
  );
}

/* ─── 인사이트 아이템 ─── */
function InsightItem({ icon, color, text }) {
  return (
    <div className="flex items-start gap-2 text-xs">
      <span className={`font-bold ${color} flex-shrink-0 w-4 text-center`}>{icon}</span>
      <span className="text-white leading-relaxed">{text}</span>
    </div>
  );
}
