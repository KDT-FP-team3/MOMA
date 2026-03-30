/**
 * SimulatorPage — 가상 인물 건강 시뮬레이터
 *
 * 긍정/부정 선택에 따라 가상 인물의 건강 상태가 실시간 변화하는 것을 시각화.
 * PPO 강화학습 환경(LifeEnv)을 API로 호출하여 시뮬레이션.
 */
import { useState, useEffect, useCallback } from "react";
import { RadialBarChart, RadialBar, ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, BarChart, Bar } from "recharts";
import { Play, RotateCcw, TrendingUp, TrendingDown, Minus, User, Zap, AlertTriangle, Map } from "lucide-react";
import axios from "axios";
import Layout from "../components/layout/Layout";
import CharacterCard from "../components/CharacterCard";
import SimulationAnimation from "../components/SimulationAnimation";
import { useAppState } from "../context/AppStateContext";

// 행동별 이모지 + 색상
const ACTION_STYLES = {
  healthy_meal:      { emoji: "", color: "text-green-400",  bg: "bg-green-500/10", border: "border-green-500/30", label: "건강한 식사" },
  unhealthy_meal:    { emoji: "", color: "text-red-400",    bg: "bg-red-500/10",   border: "border-red-500/30",   label: "불건강한 식사" },
  skip_meal:         { emoji: "", color: "text-white",   bg: "bg-gray-500/10",  border: "border-gray-500/30",  label: "식사 건너뛰기" },
  cardio_exercise:   { emoji: "", color: "text-blue-400",   bg: "bg-blue-500/10",  border: "border-blue-500/30",  label: "유산소 운동" },
  strength_exercise: { emoji: "", color: "text-blue-400",   bg: "bg-blue-500/10",  border: "border-blue-500/30",  label: "근력 운동" },
  skip_exercise:     { emoji: "", color: "text-white",   bg: "bg-gray-500/10",  border: "border-gray-500/30",  label: "운동 건너뛰기" },
  health_check:      { emoji: "", color: "text-green-400",  bg: "bg-green-500/10", border: "border-green-500/30", label: "건강 체크" },
  sleep_optimize:    { emoji: "", color: "text-purple-400", bg: "bg-purple-500/10",border: "border-purple-500/30",label: "수면 최적화" },
  hobby_activity:    { emoji: "", color: "text-purple-400", bg: "bg-purple-500/10",border: "border-purple-500/30",label: "취미 활동" },
  rest:              { emoji: "", color: "text-yellow-400",  bg: "bg-yellow-500/10",border: "border-yellow-500/30",label: "휴식" },
};

const GAUGE_CONFIG = [
  { key: "sleep_score",   label: "수면",     color: "#748ffc" },
  { key: "stress_level",  label: "스트레스",  color: "#ff922b", invert: true },
  { key: "mood_score",    label: "기분",     color: "#20c997" },
];

const STAT_KEYS = [
  { key: "weight_kg",      label: "체중",     unit: "kg",    color: "#ff6b6b" },
  { key: "bmi",            label: "BMI",      unit: "",      color: "#ffd43b" },
  { key: "calorie_intake", label: "칼로리섭취", unit: "kcal",  color: "#ff922b" },
  { key: "calorie_burned", label: "칼로리소모", unit: "kcal",  color: "#51cf66" },
];

export default function SimulatorPage() {
  const { state: appState, updateState: updateAppState } = useAppState();
  const saved = appState.simulatorState || {};

  const [started, setStarted] = useState(() => saved.started || false);
  const [state, setState] = useState(() => saved.healthState || null);
  const [gauges, setGauges] = useState(() => saved.gauges || {});
  const [step, setStep] = useState(() => saved.step || 0);
  const [week, setWeek] = useState(() => saved.week || 1);
  const [day, setDay] = useState(() => saved.day || 1);
  const [history, setHistory] = useState(() => saved.history || []);
  const [lastReward, setLastReward] = useState(null);
  const [lastCascade, setLastCascade] = useState(null);
  const [terminated, setTerminated] = useState(() => saved.terminated || false);
  const [loading, setLoading] = useState(false);
  const [totalReward, setTotalReward] = useState(() => saved.totalReward || 0);
  const [showAnimation, setShowAnimation] = useState(false);
  const [actionLog, setActionLog] = useState(() => saved.actionLog || []);
  const [simTab, setSimTab] = useState("sim");

  // Save simulator state to global context + localStorage whenever it changes
  useEffect(() => {
    updateAppState("simulatorState", {
      started, healthState: state, gauges, step, week, day,
      history, lastReward, lastCascade, terminated, totalReward, actionLog,
    });
  }, [started, state, gauges, step, week, day, history, lastReward, lastCascade, terminated, totalReward, actionLog, updateAppState]);

  // 오프라인 폴백 초기 상태
  const FALLBACK_HEALTH = {
    weight_kg: 70, bmi: 24.2, calorie_intake: 0, calorie_burned: 0,
    sleep_score: 65, stress_level: 45, mood_score: 60,
  };
  const FALLBACK_GAUGES = {
    reactive_oxygen: 55, blood_purity: 72, hair_loss_risk: 30,
    sleep_score: 65, stress_level: 45, weekly_achievement: 50,
  };

  const initSimulation = (healthState, gaugeData) => {
    setState(healthState);
    setGauges(gaugeData);
    setStep(0);
    setWeek(1);
    setDay(1);
    setHistory([{ step: 0, ...healthState }]);
    setLastReward(null);
    setLastCascade(null);
    setTerminated(false);
    setStarted(true);
    setTotalReward(0);
    setActionLog([]);
    setShowAnimation(true);
    setTimeout(() => setShowAnimation(false), 3000);
  };

  const reset = async () => {
    setLoading(true);
    try {
      // AbortController로 확실한 타임아웃 (CapacitorHttp 대응)
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), 8000);
      const res = await axios.post("/api/simulation/reset?session_id=sim1", null, {
        timeout: 8000,
        signal: controller.signal,
      });
      clearTimeout(timer);
      initSimulation(res.data.health_state, res.data.gauges);
    } catch (e) {
      console.error("시뮬레이션 초기화 실패 (오프라인 모드로 시작):", e);
      // 오프라인 폴백: 기본 데이터로 시뮬레이션 시작
      initSimulation(FALLBACK_HEALTH, FALLBACK_GAUGES);
    } finally {
      setLoading(false);
    }
  };

  const takeAction = async (actionId) => {
    if (terminated || loading) return;
    setLoading(true);
    try {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), 8000);
      const res = await axios.post("/api/simulation/step", {
        session_id: "sim1",
        action_id: actionId,
      }, { timeout: 8000, signal: controller.signal });
      clearTimeout(timer);
      setState(res.data.health_state);
      setGauges(res.data.gauges);
      setStep(res.data.step);
      setWeek(res.data.week);
      setDay(res.data.day);
      setLastReward(res.data.reward);
      setLastCascade(res.data.cascade_message);
      setTerminated(res.data.terminated);
      setTotalReward((prev) => prev + res.data.reward);
      setHistory((prev) => [
        ...prev,
        { step: res.data.step, action: res.data.action.description, ...res.data.health_state },
      ].slice(-30));

      // 행동 로그 누적
      const actionKeys = Object.keys(ACTION_STYLES);
      const actionName = actionId < actionKeys.length ? actionKeys[actionId] : `action_${actionId}`;
      setActionLog((prev) => [
        ...prev,
        { name: actionName, step: res.data.step, reward: res.data.reward },
      ]);
    } catch (e) {
      console.error("시뮬레이션 스텝 실패 (오프라인 폴백):", e);
      // 오프라인 폴백: 로컬에서 간단한 상태 변화 시뮬레이션
      const actionKeys = Object.keys(ACTION_STYLES);
      const actionName = actionId < actionKeys.length ? actionKeys[actionId] : `action_${actionId}`;
      const positive = ["healthy_meal", "cardio_exercise", "strength_exercise", "health_check", "sleep_optimize", "hobby_activity"].includes(actionName);
      const delta = positive ? 1 : -1;
      const reward = positive ? +(Math.random() * 3 + 1).toFixed(1) : -(Math.random() * 2 + 0.5).toFixed(1);
      const newStep = step + 1;
      const newWeek = Math.floor((newStep - 1) / 7) + 1;
      const newDay = ((newStep - 1) % 7) + 1;

      setState((prev) => ({
        ...prev,
        sleep_score: Math.min(100, Math.max(0, (prev?.sleep_score || 65) + delta * 2)),
        stress_level: Math.min(100, Math.max(0, (prev?.stress_level || 45) - delta * 2)),
        mood_score: Math.min(100, Math.max(0, (prev?.mood_score || 60) + delta * 3)),
        weight_kg: +((prev?.weight_kg || 70) - delta * 0.05).toFixed(1),
        bmi: +((prev?.bmi || 24.2) - delta * 0.02).toFixed(1),
      }));
      setStep(newStep);
      setWeek(newWeek);
      setDay(newDay);
      setLastReward(+reward);
      setTotalReward((prev) => prev + +reward);
      setTerminated(newStep >= 84);
      setHistory((prev) => [...prev, { step: newStep, action: ACTION_STYLES[actionName]?.label || actionName }].slice(-30));
      setActionLog((prev) => [...prev, { name: actionName, step: newStep, reward: +reward }]);
    } finally {
      setLoading(false);
    }
  };

  // 시작 전 화면
  if (!started) {
    return (
      <Layout>
        <div className="flex items-center justify-center min-h-screen p-4 md:p-6">
          <div className="max-w-lg text-center space-y-6">
            <div className="w-16 h-16 md:w-24 md:h-24 mx-auto rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center">
              <User size={36} className="text-white" />
            </div>
            <h1 className="text-xl md:text-3xl font-bold">
              건강 <span className="text-cyan-400">시뮬레이터</span>
            </h1>
            <p className="text-white leading-relaxed">
              가상의 인물을 생성하고, 매일의 선택(식사, 운동, 취미 등)에 따라{" "}
              건강 상태가 어떻게 변화하는지 <strong className="text-white">12주간 시뮬레이션</strong>합니다.{" "}
              <span className="text-cyan-400">PPO 강화학습 환경</span>이 보상과 패널티를 계산합니다.
            </p>
            <button
              onClick={reset}
              disabled={loading}
              className="inline-flex items-center gap-2 bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-400 hover:to-blue-400 text-white font-semibold px-8 py-3.5 rounded-xl transition-all shadow-lg shadow-cyan-500/25"
            >
              <Play size={20} />
              시뮬레이션 시작
            </button>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="p-4 md:p-6 space-y-5 max-w-7xl mx-auto">
        {/* 탭 헤더: 시뮬레이션 / 12주 로드맵 */}
        <div className="flex gap-1 bg-gray-800/50 p-1 rounded-xl w-fit">
          <button onClick={() => setSimTab("sim")}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${simTab === "sim" ? "bg-cyan-500/15 text-cyan-400" : "text-white hover:text-cyan-400"}`}>
            <Zap size={15} /> 시뮬레이션
          </button>
          <button onClick={() => setSimTab("roadmap")}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${simTab === "roadmap" ? "bg-cyan-500/15 text-cyan-400" : "text-white hover:text-cyan-400"}`}>
            <Map size={15} /> 12주 로드맵
          </button>
        </div>

        {simTab === "roadmap" && <RoadmapTab />}
        {simTab === "sim" && <>
        {/* 상단 바 */}
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div>
            <h1 className="text-xl font-bold">
              건강 시뮬레이터
              <span className="text-sm font-normal text-white ml-2">
                {week}주차 {day}일 (Day {step}/84)
              </span>
            </h1>
          </div>
          <div className="flex items-center gap-3">
            <div className={`text-sm font-bold ${totalReward >= 0 ? "text-green-400" : "text-red-400"}`}>
              총 보상: {totalReward >= 0 ? "+" : ""}{totalReward.toFixed(1)}
            </div>
            <button onClick={reset} className="flex items-center gap-1.5 px-3 py-1.5 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm transition-colors">
              <RotateCcw size={14} />
              초기화
            </button>
          </div>
        </div>

        {/* 종료 배너 */}
        {terminated && (
          <div className="bg-gradient-to-r from-cyan-900/40 to-blue-900/40 border border-cyan-700/30 rounded-xl p-5 text-center">
            <h2 className="text-lg font-bold text-cyan-400">12주 시뮬레이션 완료!</h2>
            <p className="text-white mt-1">총 보상: <strong className={totalReward >= 0 ? "text-green-400" : "text-red-400"}>{totalReward.toFixed(1)}</strong></p>
            <p className="text-sm text-white mt-1">
              체중: {state?.weight_kg}kg | BMI: {state?.bmi} | 수면: {state?.sleep_score} | 스트레스: {state?.stress_level}
            </p>
            <button onClick={reset} className="mt-3 px-5 py-2 bg-cyan-600 hover:bg-cyan-500 rounded-lg text-sm font-medium transition-colors">
              다시 시작
            </button>
          </div>
        )}

        {/* 시뮬레이션 시작 애니메이션 (초기화 클릭 시에만 표시) */}
        {showAnimation && (
          <SimulationAnimation active={showAnimation} onComplete={() => setShowAnimation(false)}>
            <div className="text-center text-cyan-400 text-lg font-semibold">시뮬레이션 초기화 중...</div>
          </SimulationAnimation>
        )}

        {/* 가상 인물 + 게이지 */}
        {!showAnimation && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          {/* 가상 인물 카드 (CharacterCard) */}
          <CharacterCard
            profile={{
              level: Math.floor(step / 12) + 1,
              exp: step % 12,
              nextLevelExp: 12,
              title: terminated ? "시뮬레이션 완료" : `${week}주차 ${day}일`,
              badges: totalReward >= 10 ? ["건강 달인"] : [],
              streak: step,
            }}
            stats={{
              bmi: state?.bmi || 0,
              mood: state?.mood_score || 0,
              energy: 100 - (state?.stress_level || 0),
              stress: state?.stress_level || 0,
              sleep: state?.sleep_score || 0,
              health: Math.round(((state?.sleep_score || 0) + (state?.mood_score || 0) + (100 - (state?.stress_level || 0))) / 3),
            }}
          />

          {/* 행동 선택 패널 */}
          <div className="lg:col-span-2 bg-gray-800 border border-gray-700 rounded-xl p-5">
            <h3 className="text-sm font-semibold text-white mb-3">
              오늘의 선택 <span className="text-cyan-400">— 행동을 클릭하세요</span>
            </h3>

            <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
              {Object.entries(ACTION_STYLES).map(([name, style], idx) => (
                <button
                  key={name}
                  onClick={() => takeAction(idx)}
                  disabled={terminated || loading}
                  className={`flex flex-col items-center gap-1.5 p-2 md:p-3 rounded-xl border ${style.border} ${style.bg} hover:brightness-125 disabled:opacity-40 disabled:cursor-not-allowed transition-all`}
                >
                  <span className="text-2xl">{style.emoji}</span>
                  <span className={`text-xs font-medium ${style.color}`}>{style.label}</span>
                </button>
              ))}
            </div>

            {/* 행동 누적 요약 */}
            {actionLog.length > 0 && (() => {
              // 같은 행동끼리 그룹화
              const grouped = {};
              for (const log of actionLog) {
                if (!grouped[log.name]) {
                  grouped[log.name] = { count: 0, totalReward: 0 };
                }
                grouped[log.name].count += 1;
                grouped[log.name].totalReward += log.reward;
              }
              const entries = Object.entries(grouped).sort((a, b) => b[1].count - a[1].count);
              return (
                <div className="mt-4 bg-gray-900/50 border border-gray-700/50 rounded-xl p-3 max-h-64 overflow-y-auto">
                  <div className="flex items-center justify-between mb-2 sticky top-0 bg-gray-900/90 pb-1 z-10">
                    <h4 className="text-xs font-semibold text-white">행동 누적 기록</h4>
                    <span className="text-[10px] text-white">총 {actionLog.length}회</span>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {entries.map(([name, info]) => {
                      const style = ACTION_STYLES[name] || {};
                      return (
                        <div
                          key={name}
                          className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border ${style.border || "border-gray-600"} ${style.bg || "bg-gray-700/30"}`}
                        >
                          <span className="text-sm">{style.emoji}</span>
                          <span className={`text-[11px] font-medium ${style.color || "text-white"}`}>
                            {style.label || name}
                          </span>
                          <span className="text-[11px] font-bold text-white bg-gray-700 rounded-full px-1.5 min-w-[20px] text-center">
                            {info.count}
                          </span>
                          <span className={`text-[10px] ${info.totalReward >= 0 ? "text-green-400" : "text-red-400"}`}>
                            {info.totalReward >= 0 ? "+" : ""}{info.totalReward.toFixed(0)}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                  {/* 전체 시간순 리스트 (스크롤) */}
                  <div className="mt-2 space-y-0.5">
                    {[...actionLog].reverse().map((log, i) => {
                      const style = ACTION_STYLES[log.name] || {};
                      return (
                        <div key={i} className="flex items-center gap-2 text-[10px] text-white">
                          <span className="text-white w-10">Day {log.step}</span>
                          <span>{style.emoji} {style.label}</span>
                          <span className={`ml-auto ${log.reward >= 0 ? "text-green-500" : "text-red-500"}`}>
                            {log.reward >= 0 ? "+" : ""}{log.reward.toFixed(1)}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })()}

            {/* 마지막 행동 결과 (행동을 한 적이 있을 때만 표시) */}
            {lastCascade && step > 0 && actionLog.length > 0 && (
              <div className={`mt-4 border rounded-xl p-4 ${
                lastCascade.severity === "positive" ? "border-green-500/30 bg-green-500/5" :
                lastCascade.severity === "medium" ? "border-yellow-500/30 bg-yellow-500/5" :
                "border-red-500/30 bg-red-500/5"
              }`}>
                <div className="flex items-center gap-2 mb-2">
                  {lastReward >= 0 ? <TrendingUp size={16} className="text-green-400" /> :
                   lastReward > -3 ? <Minus size={16} className="text-yellow-400" /> :
                   <TrendingDown size={16} className="text-red-400" />}
                  <span className="font-medium text-sm">{lastCascade.action_name}</span>
                  <span className={`text-sm font-bold ml-auto ${lastReward >= 0 ? "text-green-400" : "text-red-400"}`}>
                    보상 {lastReward >= 0 ? "+" : ""}{lastReward}
                  </span>
                </div>
                <div className="space-y-1">
                  {lastCascade.effects?.map((eff, i) => (
                    <div key={i} className="flex items-center gap-2 text-xs text-white">
                      <span className="text-white">→</span>
                      <span>{eff.impact}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
        )}

        {/* 건강 변화 그래프 */}
        {history.length > 1 && (
          <div className="bg-gray-800 border border-gray-700 rounded-xl p-5">
            <h3 className="text-sm font-semibold text-white mb-3">건강 상태 변화 추이</h3>
            <div className="h-52">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={history}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="step" tick={{ fill: "#6b7280", fontSize: 10 }} />
                  <YAxis tick={{ fill: "#6b7280", fontSize: 10 }} />
                  <Tooltip
                    contentStyle={{ backgroundColor: "#1f2937", border: "1px solid #374151", borderRadius: 8, fontSize: 12 }}
                    labelFormatter={(v) => `Day ${v}`}
                  />
                  <Line type="monotone" dataKey="weight_kg" stroke="#ff6b6b" strokeWidth={2} dot={false} name="체중(kg)" />
                  <Line type="monotone" dataKey="sleep_score" stroke="#748ffc" strokeWidth={2} dot={false} name="수면" />
                  <Line type="monotone" dataKey="stress_level" stroke="#ff922b" strokeWidth={2} dot={false} name="스트레스" />
                  <Line type="monotone" dataKey="mood_score" stroke="#20c997" strokeWidth={2} dot={false} name="기분" />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <div className="flex gap-4 mt-2 justify-center">
              {[["체중", "#ff6b6b"], ["수면", "#748ffc"], ["스트레스", "#ff922b"], ["기분", "#20c997"]].map(([l, c]) => (
                <div key={l} className="flex items-center gap-1.5 text-[10px] text-white">
                  <span className="w-2.5 h-2.5 rounded-sm" style={{ backgroundColor: c }} />
                  {l}
                </div>
              ))}
            </div>
          </div>
        )}
        </>}
      </div>
    </Layout>
  );
}

/* ============================================================
   RoadmapTab — 12주 로드맵 (시뮬레이터 탭으로 통합)
   ============================================================ */
const roadmapPhaseStyles = {
  "적응기": { color: "bg-blue-500", text: "text-blue-400" },
  "발전기": { color: "bg-orange-500", text: "text-orange-400" },
  "강화기": { color: "bg-purple-500", text: "text-purple-400" },
  "완성기": { color: "bg-cyan-500", text: "text-cyan-400" },
};
const roadmapDomainColors = { exercise: "#60a5fa", food: "#fb923c", health: "#4ade80", hobby: "#c084fc" };

function fallbackRoadmap() {
  const phases = ["적응기","적응기","발전기","발전기","강화기","강화기","강화기","강화기","완성기","완성기","완성기","완성기"];
  return phases.map((phase, i) => ({
    week: i + 1, phase,
    goals: [
      { name: "체중 관리", domain: "exercise", intensity: Math.min(1, (i+1)/8.4), description: "목표 체중 달성" },
      { name: "식단 개선", domain: "food", intensity: Math.min(1, (i+1)/8.4), description: "균형 잡힌 식단" },
      { name: "스트레스 관리", domain: "hobby", intensity: Math.min(1, (i+1)/8.4), description: "스트레스 해소" },
    ],
  }));
}

function RoadmapTab() {
  const [roadmap, setRoadmap] = useState([]);
  const [expandedWeek, setExpandedWeek] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const res = await axios.get("/api/roadmap/default");
        setRoadmap(res.data.roadmap || []);
      } catch { setRoadmap(fallbackRoadmap()); }
      finally { setLoading(false); }
    })();
  }, []);

  const chartData = roadmap.map((w) => ({
    week: `${w.week}주`,
    exercise: Math.round((w.goals?.find((g) => g.domain === "exercise")?.intensity || 0) * 100),
    food: Math.round((w.goals?.find((g) => g.domain === "food")?.intensity || 0) * 100),
    health: Math.round((w.goals?.find((g) => g.domain === "health")?.intensity || 0) * 100),
    hobby: Math.round((w.goals?.find((g) => g.domain === "hobby")?.intensity || 0) * 100),
  }));

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-bold text-white">12주 로드맵</h2>
        <p className="text-sm text-white mt-0.5">Top-5 조언 기반 자동 생성된 결과 로드맵</p>
      </div>

      <div className="bg-gray-800 border border-gray-700 rounded-xl p-5">
        <h3 className="text-sm font-semibold text-white mb-4">주간 도메인별 강도</h3>
        <div className="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData}>
              <XAxis dataKey="week" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} domain={[0, 100]} />
              <Tooltip />
              <Bar dataKey="exercise" fill={roadmapDomainColors.exercise} radius={[2,2,0,0]} name="운동" />
              <Bar dataKey="food" fill={roadmapDomainColors.food} radius={[2,2,0,0]} name="식단" />
              <Bar dataKey="health" fill={roadmapDomainColors.health} radius={[2,2,0,0]} name="건강" />
              <Bar dataKey="hobby" fill={roadmapDomainColors.hobby} radius={[2,2,0,0]} name="취미" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-10">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-400" />
        </div>
      ) : (
        <div className="relative">
          <div className="absolute left-5 top-0 bottom-0 w-0.5 bg-gray-700" />
          <div className="space-y-3">
            {roadmap.map((week) => {
              const ps = roadmapPhaseStyles[week.phase] || roadmapPhaseStyles["적응기"];
              const isOpen = expandedWeek === week.week;
              const progress = Math.min(100, Math.round((week.week / 12) * 100));
              return (
                <div key={week.week} className="relative pl-12">
                  <div className={`absolute left-3.5 w-3 h-3 rounded-full ${ps.color} border-2 border-gray-900`} style={{ top: 8 }} />
                  <div className="bg-gray-800 border border-gray-700 rounded-xl p-4 hover:border-gray-600 cursor-pointer transition-all"
                    onClick={() => setExpandedWeek(isOpen ? null : week.week)}>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-white">{week.week}주차</span>
                        <span className={`text-[10px] px-2 py-0.5 rounded-full text-white ${ps.color}`}>{week.phase}</span>
                      </div>
                      <span className="text-xs text-white">{progress}%</span>
                    </div>
                    <div className="mt-2 w-full bg-gray-700 rounded-full h-1">
                      <div className={`${ps.color} h-1 rounded-full`} style={{ width: `${progress}%` }} />
                    </div>
                    {isOpen && week.goals && (
                      <div className="mt-3 space-y-2">
                        {week.goals.map((goal, i) => (
                          <div key={i} className="flex items-center gap-3 text-sm bg-gray-700/40 rounded-lg p-2.5">
                            <span className="w-2 h-2 rounded-full" style={{ backgroundColor: roadmapDomainColors[goal.domain] || "#6b7280" }} />
                            <span style={{ color: roadmapDomainColors[goal.domain] }}>{goal.name}</span>
                            <span className="text-white text-xs">강도 {Math.round(goal.intensity * 100)}%</span>
                            <span className="text-white text-xs ml-auto">{goal.description}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
