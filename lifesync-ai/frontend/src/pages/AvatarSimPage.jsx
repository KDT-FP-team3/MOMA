/**
 * AvatarSimPage — 가상 인물 건강 시뮬레이터
 * 긍정적/부정적 선택에 따른 캐릭터 변화를 시각화
 */
import { useState, useCallback, useRef, useEffect } from "react";
import Layout from "../components/layout/Layout";
import AvatarBody from "../components/AvatarBody";
import QuickInput from "../components/QuickInput";
import { useAppState } from "../context/AppStateContext";

/* ------------------------------------------------------------------ */
/*  선택지 데이터                                                      */
/* ------------------------------------------------------------------ */

const CHOICES = [
  {
    category: "식사",
    items: [
      { label: "균형 잡힌 한식", icon: "", effect: { bmi: -0.1, mood: +5, energy: +8, stress: -3, sleep: +2, health: +5 }, type: "positive" },
      { label: "에어프라이어 요리", icon: "", effect: { bmi: -0.05, mood: +3, energy: +5, stress: -2, sleep: 0, health: +3 }, type: "positive" },
      { label: "야식 라면 (23시)", icon: "", effect: { bmi: +0.3, mood: +2, energy: -5, stress: +5, sleep: -15, health: -8 }, type: "negative" },
      { label: "튀김 치킨", icon: "", effect: { bmi: +0.2, mood: +4, energy: -3, stress: +2, sleep: -5, health: -6 }, type: "negative" },
      { label: "과일 간식", icon: "", effect: { bmi: -0.05, mood: +3, energy: +5, stress: -2, sleep: +1, health: +4 }, type: "positive" },
      { label: "폭식 (스트레스)", icon: "", effect: { bmi: +0.5, mood: -5, energy: -10, stress: +8, sleep: -8, health: -10 }, type: "negative" },
    ],
  },
  {
    category: "운동",
    items: [
      { label: "30분 조깅", icon: "", effect: { bmi: -0.15, mood: +8, energy: +10, stress: -10, sleep: +8, health: +8 }, type: "positive" },
      { label: "헬스장 근력운동", icon: "", effect: { bmi: -0.1, mood: +6, energy: +5, stress: -8, sleep: +5, health: +7 }, type: "positive" },
      { label: "요가 / 스트레칭", icon: "", effect: { bmi: -0.02, mood: +5, energy: +6, stress: -12, sleep: +6, health: +5 }, type: "positive" },
      { label: "운동 안 함 (하루)", icon: "", effect: { bmi: +0.05, mood: -3, energy: -5, stress: +3, sleep: -2, health: -3 }, type: "negative" },
      { label: "미세먼지 속 러닝", icon: "", effect: { bmi: -0.1, mood: -2, energy: -3, stress: +5, sleep: -1, health: -6 }, type: "negative" },
    ],
  },
  {
    category: "수면",
    items: [
      { label: "7~8시간 숙면", icon: "", effect: { bmi: 0, mood: +8, energy: +15, stress: -10, sleep: +20, health: +6 }, type: "positive" },
      { label: "규칙적 기상", icon: "", effect: { bmi: 0, mood: +5, energy: +8, stress: -5, sleep: +10, health: +4 }, type: "positive" },
      { label: "4시간 수면", icon: "", effect: { bmi: +0.1, mood: -10, energy: -20, stress: +15, sleep: -25, health: -10 }, type: "negative" },
      { label: "새벽 3시 취침", icon: "", effect: { bmi: +0.05, mood: -5, energy: -12, stress: +8, sleep: -15, health: -6 }, type: "negative" },
    ],
  },
  {
    category: "취미/휴식",
    items: [
      { label: "기타 연주 30분", icon: "", effect: { bmi: 0, mood: +10, energy: +3, stress: -15, sleep: +3, health: +3 }, type: "positive" },
      { label: "독서 1시간", icon: "", effect: { bmi: 0, mood: +6, energy: +2, stress: -8, sleep: +4, health: +2 }, type: "positive" },
      { label: "자연 산책", icon: "", effect: { bmi: -0.03, mood: +8, energy: +8, stress: -12, sleep: +5, health: +5 }, type: "positive" },
      { label: "SNS 3시간+", icon: "", effect: { bmi: 0, mood: -6, energy: -8, stress: +10, sleep: -8, health: -4 }, type: "negative" },
      { label: "음주 (소주 1병)", icon: "", effect: { bmi: +0.15, mood: +3, energy: -10, stress: +5, sleep: -10, health: -8 }, type: "negative" },
    ],
  },
  {
    category: "건강관리",
    items: [
      { label: "건강검진 이행", icon: "", effect: { bmi: 0, mood: +5, energy: +2, stress: -8, sleep: +2, health: +10 }, type: "positive" },
      { label: "충분한 수분 섭취", icon: "", effect: { bmi: -0.02, mood: +2, energy: +5, stress: -3, sleep: +2, health: +4 }, type: "positive" },
      { label: "약 복용 거부", icon: "", effect: { bmi: 0, mood: -3, energy: -5, stress: +5, sleep: -3, health: -8 }, type: "negative" },
      { label: "검진 결과 무시", icon: "", effect: { bmi: 0, mood: -5, energy: -2, stress: +10, sleep: -2, health: -12 }, type: "negative" },
    ],
  },
];

/* ------------------------------------------------------------------ */
/*  HistoryEntry                                                       */
/* ------------------------------------------------------------------ */

function HistoryEntry({ entry, index, onDelete }) {
  const isPos = entry.type === "positive";
  // Show key effect values
  const effects = Object.entries(entry.effect || {})
    .filter(([, v]) => v !== 0)
    .map(([k, v]) => `${k} ${v > 0 ? "+" : ""}${v}`)
    .join(", ");
  return (
    <div className={`flex items-center gap-2 px-2 py-1.5 rounded-lg text-xs group ${isPos ? "bg-emerald-900/20" : "bg-red-900/20"}`}>
      <span className="text-white font-mono w-5 text-center">{index + 1}</span>
      <span className="text-sm">{entry.icon}</span>
      <div className="flex-1 min-w-0">
        <span className="text-white truncate block">{entry.label}</span>
        <span className="text-white text-[10px] truncate block">{effects}</span>
      </div>
      <span className={`font-mono text-xs ${isPos ? "text-emerald-400" : "text-red-400"}`}>
        {isPos ? "+" : "-"}
      </span>
      <button
        onClick={() => onDelete(index)}
        className="opacity-0 group-hover:opacity-100 text-white hover:text-red-400 transition-opacity text-xs px-1"
        title="삭제"
      >
        X
      </button>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  StatBar                                                            */
/* ------------------------------------------------------------------ */

function StatBar({ label, value, icon, color }) {
  const pct = Math.max(0, Math.min(100, value));
  const textColor = pct >= 60 ? "text-emerald-400" : pct >= 35 ? "text-amber-400" : "text-red-400";
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-xs">
        <span className="text-white">{icon} {label}</span>
        <span className={`font-semibold ${textColor}`}>{pct.toFixed(0)}</span>
      </div>
      <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  PAGE                                                               */
/* ------------------------------------------------------------------ */

const INITIAL_STATE = { bmi: 23.0, mood: 60, energy: 60, stress: 40, sleep: 70, health: 70 };

export default function AvatarSimPage() {
  const { state: appState, updateState: updateAppState } = useAppState();

  // Load from global state or default
  const [state, setState] = useState(() => appState.avatarState || { ...INITIAL_STATE });
  const [history, setHistory] = useState(() => appState.avatarHistory || []);
  const [openCat, setOpenCat] = useState(null);
  const [showCompare, setShowCompare] = useState(false);
  const [showCustomize, setShowCustomize] = useState(false);
  const [avatarCustom, setAvatarCustom] = useState(() => appState.avatarCustom || { skinTone: "default", hairStyle: 0, hairColor: null });
  const initialStateRef = useRef({ ...INITIAL_STATE });

  // Persist to global state on change
  useEffect(() => { updateAppState("avatarState", state); }, [state, updateAppState]);
  useEffect(() => { updateAppState("avatarHistory", history); }, [history, updateAppState]);
  useEffect(() => { updateAppState("avatarCustom", avatarCustom); }, [avatarCustom, updateAppState]);

  const SKIN_OPTIONS = [
    { key: "default", label: "자동", color: "#f0c8a0" },
    { key: "light", label: "밝은", color: "#ffe0c8" },
    { key: "medium", label: "중간", color: "#f0c8aa" },
    { key: "tan", label: "황갈", color: "#d2aa82" },
    { key: "dark", label: "어두운", color: "#a07855" },
  ];
  const HAIR_OPTIONS = [
    { key: 0, label: "기본 숏컷" },
    { key: 1, label: "웨이브" },
    { key: 2, label: "사이드 파트" },
    { key: 3, label: "뒤로 넘김" },
    { key: 4, label: "짧은 머리" },
  ];
  const HAIR_COLORS = [
    { label: "검정", color: "#1e293b" },
    { label: "갈색", color: "#78350f" },
    { label: "밤색", color: "#92400e" },
    { label: "금발", color: "#ca8a04" },
    { label: "회색", color: "#6b7280" },
    { label: "파랑", color: "#2563eb" },
  ];

  const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));

  const applyChoice = useCallback((item) => {
    setState((prev) => ({
      bmi:    clamp(prev.bmi    + item.effect.bmi,    15, 40),
      mood:   clamp(prev.mood   + item.effect.mood,   0, 100),
      energy: clamp(prev.energy + item.effect.energy, 0, 100),
      stress: clamp(prev.stress + item.effect.stress, 0, 100),
      sleep:  clamp(prev.sleep  + item.effect.sleep,  0, 100),
      health: clamp(prev.health + item.effect.health, 0, 100),
    }));
    setHistory((prev) => [...prev, { label: item.label, icon: item.icon, type: item.type, effect: item.effect }]);
  }, []);

  const deleteHistoryItem = useCallback((idx) => {
    setHistory((prev) => {
      const next = prev.filter((_, i) => i !== idx);
      // Recalculate state from scratch
      const newState = { ...INITIAL_STATE };
      next.forEach((item) => {
        newState.bmi    = clamp(newState.bmi    + item.effect.bmi,    15, 40);
        newState.mood   = clamp(newState.mood   + item.effect.mood,   0, 100);
        newState.energy = clamp(newState.energy + item.effect.energy, 0, 100);
        newState.stress = clamp(newState.stress + item.effect.stress, 0, 100);
        newState.sleep  = clamp(newState.sleep  + item.effect.sleep,  0, 100);
        newState.health = clamp(newState.health + item.effect.health, 0, 100);
      });
      setState(newState);
      return next;
    });
  }, []);

  const reset = useCallback(() => {
    setState({ ...INITIAL_STATE });
    setHistory([]);
  }, []);

  // 종합 점수
  const overallScore = Math.round(
    state.mood * 0.2 + state.energy * 0.2 + (100 - state.stress) * 0.15 +
    state.sleep * 0.2 + state.health * 0.25
  );
  const overallColor = overallScore >= 70 ? "#10b981" : overallScore >= 45 ? "#f59e0b" : "#ef4444";
  const overallLabel = overallScore >= 70 ? "양호" : overallScore >= 45 ? "주의" : "위험";

  return (
    <Layout>
      <div className="p-4 lg:p-6 space-y-6">
        {/* 헤더 */}
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-white">가상 인물 건강 시뮬레이터</h1>
          <div className="flex items-center gap-2 flex-wrap">
            <button
              onClick={() => setShowCustomize((prev) => !prev)}
              className={`px-3 py-2 rounded-lg text-sm transition-colors ${
                showCustomize ? "bg-purple-700 hover:bg-purple-600 text-white" : "bg-gray-700 hover:bg-gray-600 text-white"
              }`}
            >
              {showCustomize ? "완료" : "꾸미기"}
            </button>
            <button
              onClick={() => setShowCompare((prev) => !prev)}
              className={`px-3 py-2 rounded-lg text-sm transition-colors ${
                showCompare ? "bg-cyan-700 hover:bg-cyan-600 text-white" : "bg-gray-700 hover:bg-gray-600 text-white"
              }`}
            >
              {showCompare ? "돌아가기" : "비교"}
            </button>
            <button onClick={reset} className="px-3 py-2 rounded-lg bg-gray-700 hover:bg-gray-600 text-sm text-white">
              초기화
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* 왼쪽: 선택지 */}
          <div className="lg:col-span-4 space-y-2">
            <h2 className="text-sm font-semibold text-white mb-2">생활 선택하기</h2>
            {CHOICES.map((cat) => (
              <div key={cat.category} className="bg-gray-800/50 rounded-xl border border-gray-700 overflow-hidden">
                <button
                  onClick={() => setOpenCat(openCat === cat.category ? null : cat.category)}
                  className="w-full flex items-center justify-between px-4 py-3 text-sm font-medium text-white hover:bg-gray-700/30 transition-colors"
                >
                  <span>{cat.category}</span>
                  <span className="text-white text-xs">{openCat === cat.category ? "▲" : "▼"}</span>
                </button>
                {openCat === cat.category && (
                  <div className="px-3 pb-3 grid grid-cols-1 gap-1.5">
                    {cat.items.map((item) => (
                      <button
                        key={item.label}
                        onClick={() => applyChoice(item)}
                        className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs text-left transition-all ${
                          item.type === "positive"
                            ? "bg-emerald-900/20 hover:bg-emerald-900/40 border border-emerald-800/30"
                            : "bg-red-900/20 hover:bg-red-900/40 border border-red-800/30"
                        }`}
                      >
                        <span className="text-base">{item.icon}</span>
                        <div className="flex-1 min-w-0">
                          <p className="text-gray-200 font-medium">{item.label}</p>
                          <p className="text-white text-[10px] mt-0.5">
                            {Object.entries(item.effect)
                              .filter(([, v]) => v !== 0)
                              .map(([k, v]) => `${k} ${v > 0 ? "+" : ""}${v}`)
                              .join(" · ")}
                          </p>
                        </div>
                        <span className={`text-lg ${item.type === "positive" ? "text-emerald-500" : "text-red-500"}`}>
                          {item.type === "positive" ? "+" : "−"}
                        </span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* 중앙: 캐릭터 */}
          <div className="lg:col-span-4 flex flex-col items-center gap-4">
            {showCompare ? (
              /* Before / After 비교 모드 */
              <>
                <h2 className="text-sm font-semibold text-white">Before / After 비교</h2>
                <div className="flex items-end gap-6">
                  {/* Before (시작) */}
                  <div className="flex flex-col items-center gap-2">
                    <span className="text-xs font-semibold text-white bg-gray-800 px-3 py-1 rounded-full">시작</span>
                    <AvatarBody
                      bmi={initialStateRef.current.bmi}
                      mood={initialStateRef.current.mood}
                      energy={initialStateRef.current.energy}
                      stress={initialStateRef.current.stress}
                      sleep={initialStateRef.current.sleep}
                      health={initialStateRef.current.health}
                      size={160}
                      skinTone={avatarCustom.skinTone}
                      hairStyle={avatarCustom.hairStyle}
                      hairColorOverride={avatarCustom.hairColor}
                    />
                  </div>
                  {/* Arrow */}
                  <div className="text-2xl text-white mb-16">→</div>
                  {/* After (현재) */}
                  <div className="flex flex-col items-center gap-2">
                    <span className="text-xs font-semibold text-cyan-400 bg-cyan-900/30 px-3 py-1 rounded-full">현재</span>
                    <AvatarBody
                      bmi={state.bmi}
                      mood={state.mood}
                      energy={state.energy}
                      stress={state.stress}
                      sleep={state.sleep}
                      health={state.health}
                      size={160}
                      skinTone={avatarCustom.skinTone}
                      hairStyle={avatarCustom.hairStyle}
                      hairColorOverride={avatarCustom.hairColor}
                    />
                  </div>
                </div>
                {/* 종합 점수 (비교 모드) */}
                <div className="text-center">
                  <div className="text-4xl font-bold" style={{ color: overallColor }}>
                    {overallScore}
                  </div>
                  <div className="text-sm text-white mt-1">
                    종합 건강 점수 · <span style={{ color: overallColor }}>{overallLabel}</span>
                  </div>
                </div>
              </>
            ) : (
              /* 일반 모드 */
              <>
                {/* 종합 점수 */}
                <div className="text-center">
                  <div className="text-5xl font-bold" style={{ color: overallColor }}>
                    {overallScore}
                  </div>
                  <div className="text-sm text-white mt-1">
                    종합 건강 점수 · <span style={{ color: overallColor }}>{overallLabel}</span>
                  </div>
                </div>

                {/* 캐릭터 */}
                <div className="relative">
                  <AvatarBody
                    bmi={state.bmi}
                    mood={state.mood}
                    energy={state.energy}
                    stress={state.stress}
                    sleep={state.sleep}
                    health={state.health}
                    size={240}
                    skinTone={avatarCustom.skinTone}
                    hairStyle={avatarCustom.hairStyle}
                    hairColorOverride={avatarCustom.hairColor}
                  />
                </div>

                {/* 꾸미기 패널 */}
                {showCustomize && (
                  <div className="w-full max-w-xs bg-gray-800/50 rounded-xl border border-gray-700 p-3 space-y-3">
                    <p className="text-xs font-semibold text-white">캐릭터 꾸미기</p>
                    {/* 피부색 */}
                    <div>
                      <p className="text-[10px] text-white mb-1.5">피부색</p>
                      <div className="flex gap-2">
                        {SKIN_OPTIONS.map((s) => (
                          <button
                            key={s.key}
                            onClick={() => setAvatarCustom((p) => ({ ...p, skinTone: s.key }))}
                            className={`w-8 h-8 rounded-full border-2 transition-all ${avatarCustom.skinTone === s.key ? "border-cyan-400 scale-110" : "border-gray-600"}`}
                            style={{ backgroundColor: s.color }}
                            title={s.label}
                          />
                        ))}
                      </div>
                    </div>
                    {/* 헤어스타일 */}
                    <div>
                      <p className="text-[10px] text-white mb-1.5">헤어스타일</p>
                      <div className="flex gap-1.5 flex-wrap">
                        {HAIR_OPTIONS.map((h) => (
                          <button
                            key={h.key}
                            onClick={() => setAvatarCustom((p) => ({ ...p, hairStyle: h.key }))}
                            className={`px-2.5 py-1 rounded-lg text-[10px] transition-all ${avatarCustom.hairStyle === h.key ? "bg-cyan-600 text-white" : "bg-gray-700 text-white"}`}
                          >
                            {h.label}
                          </button>
                        ))}
                      </div>
                    </div>
                    {/* 머리색 */}
                    <div>
                      <p className="text-[10px] text-white mb-1.5">머리색</p>
                      <div className="flex gap-2">
                        {HAIR_COLORS.map((hc) => (
                          <button
                            key={hc.color}
                            onClick={() => setAvatarCustom((p) => ({ ...p, hairColor: hc.color }))}
                            className={`w-7 h-7 rounded-full border-2 transition-all ${avatarCustom.hairColor === hc.color ? "border-cyan-400 scale-110" : "border-gray-600"}`}
                            style={{ backgroundColor: hc.color }}
                            title={hc.label}
                          />
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {/* 상태 바 */}
                <div className="w-full max-w-xs space-y-2">
                  <StatBar label="BMI" value={((state.bmi - 15) / 25) * 100} icon="" color="#60a5fa" />
                  <StatBar label="기분" value={state.mood} icon="" color="#10b981" />
                  <StatBar label="에너지" value={state.energy} icon="" color="#f59e0b" />
                  <StatBar label="스트레스" value={100 - state.stress} icon="" color="#8b5cf6" />
                  <StatBar label="수면" value={state.sleep} icon="" color="#6366f1" />
                  <StatBar label="건강" value={state.health} icon="" color="#ef4444" />
                </div>
              </>
            )}
          </div>

          {/* 오른쪽: 히스토리 */}
          <div className="lg:col-span-4 space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold text-white">선택 히스토리 ({history.length})</h2>
              {history.length > 0 && (
                <span className="text-xs text-white">
                  +{history.filter((h) => h.type === "positive").length} / -{history.filter((h) => h.type === "negative").length}
                </span>
              )}
            </div>

            <div className="bg-gray-800/50 rounded-xl border border-gray-700 p-3 max-h-[600px] overflow-y-auto space-y-1.5">
              {history.length === 0 ? (
                <p className="text-xs text-white text-center py-8">
                  왼쪽에서 생활 선택을 하면<br />캐릭터가 변화합니다
                </p>
              ) : (
                history.map((entry, i) => (
                  <HistoryEntry key={i} entry={entry} index={i} onDelete={deleteHistoryItem} />
                ))
              )}
            </div>

            {/* 현재 상태 경고 */}
            {state.health < 40 && (
              <div className="bg-red-900/20 border border-red-800/30 rounded-xl p-3 text-xs text-red-300">
                [경고] 건강 수치가 위험 수준입니다. 긍정적 선택이 필요합니다!
              </div>
            )}
            {state.stress > 70 && (
              <div className="bg-amber-900/20 border border-amber-800/30 rounded-xl p-3 text-xs text-amber-300">
                [주의] 스트레스가 매우 높습니다. 휴식이나 취미 활동을 추천합니다.
              </div>
            )}
            {state.sleep < 30 && (
              <div className="bg-purple-900/20 border border-purple-800/30 rounded-xl p-3 text-xs text-purple-300">
                [주의] 수면 부족 심각! 충분한 수면이 시급합니다.
              </div>
            )}
            {overallScore >= 80 && (
              <div className="bg-emerald-900/20 border border-emerald-800/30 rounded-xl p-3 text-xs text-emerald-300">
                훌륭합니다! 건강한 생활을 유지하고 있습니다.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* QuickInput floating bar */}
      <QuickInput allChoices={CHOICES} onMatch={applyChoice} />
    </Layout>
  );
}
