/**
 * SchedulePage — 24시간 원형 시계 스케줄러 + 장기 시뮬레이션
 */
import { useState, useEffect, useCallback, useRef } from "react";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import { Play, Plus, Trash2, AlertTriangle, CheckCircle, Clock, TrendingUp, TrendingDown, ChevronUp, ChevronDown, GripVertical, Edit3, Check, X } from "lucide-react";
import axios from "axios";
import Layout from "../components/layout/Layout";
import ErrorBarChart from "../components/ErrorBarChart";
import { useAppState } from "../context/AppStateContext";

// 활동별 스타일
const ACTIVITY_STYLES = {
  sleep:             { emoji: "😴", color: "#748ffc", label: "수면" },
  meal_healthy:      { emoji: "🥗", color: "#51cf66", label: "건강한 식사" },
  meal_normal:       { emoji: "🍚", color: "#ff922b", label: "일반 식사" },
  meal_unhealthy:    { emoji: "🍔", color: "#ff6b6b", label: "불건강한 식사" },
  night_snack:       { emoji: "🍜", color: "#e64980", label: "야식" },
  exercise_cardio:   { emoji: "🏃", color: "#339af0", label: "유산소 운동" },
  exercise_strength: { emoji: "🏋️", color: "#5c7cfa", label: "근력 운동" },
  work:              { emoji: "💼", color: "#868e96", label: "업무/공부" },
  hobby:             { emoji: "🎸", color: "#cc5de8", label: "취미" },
  rest:              { emoji: "☕", color: "#20c997", label: "휴식" },
  commute:           { emoji: "🚌", color: "#adb5bd", label: "통근" },
  other:             { emoji: "📌", color: "#ced4da", label: "기타" },
};

const DEFAULT_SCHEDULE = [
  { start_hour: 23, end_hour: 7,  activity: "sleep",           label: "수면",     repeat_cycle: 1 },
  { start_hour: 7,  end_hour: 8,  activity: "meal_healthy",    label: "아침",     repeat_cycle: 1 },
  { start_hour: 8,  end_hour: 9,  activity: "commute",         label: "출근",     repeat_cycle: 1 },
  { start_hour: 9,  end_hour: 12, activity: "work",            label: "오전 업무", repeat_cycle: 1 },
  { start_hour: 12, end_hour: 13, activity: "meal_normal",     label: "점심",     repeat_cycle: 1 },
  { start_hour: 13, end_hour: 18, activity: "work",            label: "오후 업무", repeat_cycle: 1 },
  { start_hour: 18, end_hour: 19, activity: "commute",         label: "퇴근",     repeat_cycle: 1 },
  { start_hour: 19, end_hour: 20, activity: "meal_normal",     label: "저녁",     repeat_cycle: 1 },
  { start_hour: 20, end_hour: 21, activity: "rest",            label: "휴식",     repeat_cycle: 1 },
  { start_hour: 21, end_hour: 23, activity: "hobby",           label: "취미",     repeat_cycle: 1 },
];

export default function SchedulePage() {
  const { state, updateState } = useAppState();
  const [schedule, _setSchedule] = useState(() => state.schedule?.length > 0 ? state.schedule : DEFAULT_SCHEDULE);
  const [simDays, setSimDays] = useState(30);
  const [results, setResults] = useState(() => state.scheduleResults || null);
  const [loading, setLoading] = useState(false);
  const [showAddForm, setShowAddForm] = useState(false);
  const [newEntry, setNewEntry] = useState({ start_hour: 6, end_hour: 7, activity: "exercise_cardio", label: "", repeat_cycle: 1 });
  const [dragOverSchedule, setDragOverSchedule] = useState(false);
  const [editingIdx, setEditingIdx] = useState(null);
  const [editData, setEditData] = useState(null);
  const [dragIdx, setDragIdx] = useState(null);
  const [dragOverIdx, setDragOverIdx] = useState(null);

  // Sync schedule to global state
  const setSchedule = useCallback((val) => {
    _setSchedule((prev) => {
      const next = typeof val === "function" ? val(prev) : val;
      updateState("schedule", next);
      return next;
    });
  }, [updateState]);

  // Sync results to global state
  useEffect(() => { updateState("scheduleResults", results); }, [results, updateState]);

  const addEntry = () => {
    const label = newEntry.label || ACTIVITY_STYLES[newEntry.activity]?.label || "";
    setSchedule(prev => [...prev, { ...newEntry, label }]);
    setShowAddForm(false);
    setNewEntry({ start_hour: 6, end_hour: 7, activity: "exercise_cardio", label: "", repeat_cycle: 1 });
  };

  const removeEntry = (idx) => {
    setSchedule(prev => prev.filter((_, i) => i !== idx));
    if (editingIdx === idx) { setEditingIdx(null); setEditData(null); }
  };

  // Inline editing
  const startEdit = (idx) => {
    setEditingIdx(idx);
    setEditData({ ...schedule[idx] });
  };
  const cancelEdit = () => { setEditingIdx(null); setEditData(null); };
  const saveEdit = () => {
    if (editData) {
      setSchedule(prev => prev.map((e, i) => i === editingIdx ? { ...editData } : e));
    }
    setEditingIdx(null);
    setEditData(null);
  };

  // List drag-to-reorder
  const handleListDragStart = (idx) => { setDragIdx(idx); };
  const handleListDragOver = (e, idx) => { e.preventDefault(); setDragOverIdx(idx); };
  const handleListDrop = (idx) => {
    if (dragIdx !== null && dragIdx !== idx) {
      setSchedule(prev => {
        const next = [...prev];
        const [moved] = next.splice(dragIdx, 1);
        next.splice(idx, 0, moved);
        return next;
      });
    }
    setDragIdx(null);
    setDragOverIdx(null);
  };
  const handleListDragEnd = () => { setDragIdx(null); setDragOverIdx(null); };

  const moveEntry = (idx, direction) => {
    setSchedule(prev => {
      const next = [...prev];
      const targetIdx = idx + direction;
      if (targetIdx < 0 || targetIdx >= next.length) return prev;
      [next[idx], next[targetIdx]] = [next[targetIdx], next[idx]];
      return next;
    });
  };

  /* ---- Drag & Drop handlers for activity palette ---- */
  const handlePaletteDragStart = useCallback((e, activityKey) => {
    e.dataTransfer.setData("application/lifesync-activity", activityKey);
    e.dataTransfer.effectAllowed = "copy";
    e.currentTarget.style.opacity = "0.5";
  }, []);

  const handlePaletteDragEnd = useCallback((e) => {
    e.currentTarget.style.opacity = "1";
  }, []);

  const handleScheduleDragOver = useCallback((e) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = "copy";
    setDragOverSchedule(true);
  }, []);

  const handleScheduleDragLeave = useCallback((e) => {
    if (e.currentTarget === e.target || !e.currentTarget.contains(e.relatedTarget)) {
      setDragOverSchedule(false);
    }
  }, []);

  const handleScheduleDrop = useCallback((e) => {
    e.preventDefault();
    setDragOverSchedule(false);
    const activityKey = e.dataTransfer.getData("application/lifesync-activity");
    if (!activityKey || !ACTIVITY_STYLES[activityKey]) return;

    const style = ACTIVITY_STYLES[activityKey];
    let start_hour = 9;
    let end_hour = 10;
    if (activityKey === "sleep") { start_hour = 23; end_hour = 7; }
    else if (activityKey.startsWith("meal")) { start_hour = 12; end_hour = 13; }
    else if (activityKey === "night_snack") { start_hour = 22; end_hour = 23; }
    else if (activityKey.startsWith("exercise")) { start_hour = 7; end_hour = 8; }
    else if (activityKey === "work") { start_hour = 9; end_hour = 18; }
    else if (activityKey === "hobby") { start_hour = 20; end_hour = 22; }
    else if (activityKey === "rest") { start_hour = 15; end_hour = 16; }
    else if (activityKey === "commute") { start_hour = 8; end_hour = 9; }

    setSchedule(prev => [...prev, {
      start_hour,
      end_hour,
      activity: activityKey,
      label: style.label,
      repeat_cycle: 1,
    }]);
  }, []);

  const runSimulation = async () => {
    setLoading(true);
    setResults(null);
    try {
      const res = await axios.post("/api/schedule/simulate", { schedule, days: simDays });
      setResults(res.data);
    } catch (e) {
      console.error("시뮬레이션 실패:", e);
      alert("백엔드 서버 연결 실패! 서버가 실행 중인지 확인하세요.\n\n오류: " + (e.message || e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout>
      <div className="p-4 md:p-6 space-y-6 max-w-7xl mx-auto">
        <div>
          <h1 className="text-xl font-bold">생활 패턴 <span className="text-cyan-400">시뮬레이터</span></h1>
          <p className="text-sm text-gray-500 mt-0.5">24시간 시계에 일과를 배치하고, 장기 건강 변화를 예측합니다</p>
        </div>

        {/* Activity palette — grouped by category */}
        <div className="bg-gray-800 border border-gray-700 rounded-xl p-4">
          <h3 className="text-sm font-semibold text-gray-400 mb-3 flex items-center gap-2">
            <GripVertical size={16} className="text-cyan-400" />
            활동 팔레트 <span className="text-[10px] text-gray-500 font-normal ml-1">— 아래 스케줄 목록으로 드래그하여 추가</span>
          </h3>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            {[
              { group: "식사", keys: ["meal_healthy", "meal_normal", "meal_unhealthy", "night_snack"], color: "#ff922b" },
              { group: "운동", keys: ["exercise_cardio", "exercise_strength"], color: "#339af0" },
              { group: "생활", keys: ["sleep", "work", "commute", "rest"], color: "#748ffc" },
              { group: "여가", keys: ["hobby", "other"], color: "#cc5de8" },
            ].map(({ group, keys, color }) => (
              <div key={group}>
                <div className="text-[10px] font-semibold mb-1.5 px-1" style={{ color }}>{group}</div>
                <div className="flex flex-wrap gap-1.5">
                  {keys.map((key) => {
                    const style = ACTIVITY_STYLES[key];
                    if (!style) return null;
                    return (
                      <div
                        key={key}
                        draggable
                        onDragStart={(e) => handlePaletteDragStart(e, key)}
                        onDragEnd={handlePaletteDragEnd}
                        className="flex items-center gap-1 px-2 py-1 rounded-lg bg-gray-700/50 border border-gray-600/50 cursor-grab active:cursor-grabbing select-none transition-all duration-150 hover:bg-gray-700 hover:border-gray-500 hover:scale-105"
                        style={{ borderLeftColor: style.color, borderLeftWidth: 3 }}
                      >
                        <span className="text-sm">{style.emoji}</span>
                        <span className="text-[11px] text-gray-300">{style.label}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* 원형 시계 */}
          <div className="bg-gray-800 border border-gray-700 rounded-xl p-5">
            <h3 className="text-sm font-semibold text-gray-400 mb-4 flex items-center gap-2">
              <Clock size={16} className="text-cyan-400" />
              24시간 일과표
            </h3>
            <ClockDial schedule={schedule} />
          </div>

          {/* 스케줄 리스트 (drop zone) */}
          <div
            className={`bg-gray-800 border rounded-xl p-5 flex flex-col transition-all duration-200 ${
              dragOverSchedule
                ? "border-cyan-400 bg-cyan-500/5 shadow-[inset_0_0_20px_rgba(6,182,212,0.08)]"
                : "border-gray-700"
            }`}
            onDragOver={handleScheduleDragOver}
            onDragLeave={handleScheduleDragLeave}
            onDrop={handleScheduleDrop}
          >
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-gray-400">
                스케줄 항목
                {dragOverSchedule && (
                  <span className="ml-2 text-cyan-400 text-xs font-normal animate-pulse">여기에 놓으세요!</span>
                )}
              </h3>
              <button onClick={() => setShowAddForm(!showAddForm)} className="flex items-center gap-1 text-xs bg-cyan-600 hover:bg-cyan-500 px-2.5 py-1.5 rounded-lg transition-colors">
                <Plus size={14} /> 추가
              </button>
            </div>

            {/* 추가 폼 */}
            {showAddForm && (
              <div className="bg-gray-700/50 rounded-lg p-3 mb-3 space-y-2">
                <div className="grid grid-cols-3 gap-2">
                  <div>
                    <label className="text-[10px] text-gray-500">시작</label>
                    <select value={newEntry.start_hour} onChange={e => setNewEntry(p => ({...p, start_hour: +e.target.value}))} className="w-full bg-gray-700 border border-gray-600 rounded px-2 py-1 text-sm">
                      {Array.from({length: 24}, (_, i) => <option key={i} value={i}>{i}시</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="text-[10px] text-gray-500">종료</label>
                    <select value={newEntry.end_hour} onChange={e => setNewEntry(p => ({...p, end_hour: +e.target.value}))} className="w-full bg-gray-700 border border-gray-600 rounded px-2 py-1 text-sm">
                      {Array.from({length: 25}, (_, i) => <option key={i} value={i}>{i === 24 ? "24(익일)" : `${i}시`}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="text-[10px] text-gray-500">반복주기</label>
                    <select value={newEntry.repeat_cycle} onChange={e => setNewEntry(p => ({...p, repeat_cycle: +e.target.value}))} className="w-full bg-gray-700 border border-gray-600 rounded px-2 py-1 text-sm">
                      <option value={1}>매일</option>
                      <option value={2}>격일</option>
                      <option value={3}>3일마다</option>
                      <option value={7}>주 1회</option>
                    </select>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="text-[10px] text-gray-500">활동</label>
                    <select value={newEntry.activity} onChange={e => setNewEntry(p => ({...p, activity: e.target.value}))} className="w-full bg-gray-700 border border-gray-600 rounded px-2 py-1 text-sm">
                      {Object.entries(ACTIVITY_STYLES).map(([key, s]) => <option key={key} value={key}>{s.emoji} {s.label}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="text-[10px] text-gray-500">메모</label>
                    <input value={newEntry.label} onChange={e => setNewEntry(p => ({...p, label: e.target.value}))} placeholder="선택사항" className="w-full bg-gray-700 border border-gray-600 rounded px-2 py-1 text-sm" />
                  </div>
                </div>
                <button onClick={addEntry} className="w-full bg-cyan-600 hover:bg-cyan-500 py-1.5 rounded-lg text-sm transition-colors">추가</button>
              </div>
            )}

            {/* 항목 리스트 */}
            <div className="flex-1 overflow-y-auto space-y-1.5 max-h-80">
              {schedule.length === 0 && (
                <div className="flex flex-col items-center justify-center py-10 text-gray-500">
                  <GripVertical size={24} className="mb-2 opacity-50" />
                  <p className="text-sm">위 팔레트에서 활동을 드래그하여 추가하세요</p>
                </div>
              )}
              {schedule.map((entry, idx) => {
                const style = ACTIVITY_STYLES[entry.activity] || ACTIVITY_STYLES.other;
                const duration = entry.end_hour > entry.start_hour ? entry.end_hour - entry.start_hour : entry.end_hour + 24 - entry.start_hour;
                const isEditing = editingIdx === idx;
                const isDragging = dragIdx === idx;
                const isDragOver = dragOverIdx === idx;
                return (
                  <div
                    key={idx}
                    draggable={!isEditing}
                    onDragStart={() => handleListDragStart(idx)}
                    onDragOver={(e) => handleListDragOver(e, idx)}
                    onDrop={() => handleListDrop(idx)}
                    onDragEnd={handleListDragEnd}
                    className={`flex items-center gap-2 rounded-lg px-3 py-2 group transition-all duration-200 cursor-grab active:cursor-grabbing ${
                      isDragging ? "opacity-30 scale-95" : isDragOver ? "bg-cyan-500/10 border-cyan-500/40 border" : "bg-gray-700/30"
                    } ${isEditing ? "ring-1 ring-cyan-500/50 bg-gray-700/60" : ""}`}
                  >
                    <span className="text-lg flex-shrink-0">{style.emoji}</span>
                    {isEditing && editData ? (
                      /* 인라인 편집 모드 */
                      <div className="flex-1 flex flex-wrap items-center gap-1.5">
                        <select value={editData.activity} onChange={e => setEditData(d => ({...d, activity: e.target.value}))} className="bg-gray-700 border border-gray-600 rounded px-1.5 py-0.5 text-xs w-24">
                          {Object.entries(ACTIVITY_STYLES).map(([k, s]) => <option key={k} value={k}>{s.emoji} {s.label}</option>)}
                        </select>
                        <select value={editData.start_hour} onChange={e => setEditData(d => ({...d, start_hour: +e.target.value}))} className="bg-gray-700 border border-gray-600 rounded px-1 py-0.5 text-xs w-14">
                          {Array.from({length: 24}, (_, i) => <option key={i} value={i}>{i}시</option>)}
                        </select>
                        <span className="text-gray-500 text-xs">~</span>
                        <select value={editData.end_hour} onChange={e => setEditData(d => ({...d, end_hour: +e.target.value}))} className="bg-gray-700 border border-gray-600 rounded px-1 py-0.5 text-xs w-14">
                          {Array.from({length: 25}, (_, i) => <option key={i} value={i}>{i === 24 ? "24" : `${i}시`}</option>)}
                        </select>
                        <select value={editData.repeat_cycle} onChange={e => setEditData(d => ({...d, repeat_cycle: +e.target.value}))} className="bg-gray-700 border border-gray-600 rounded px-1 py-0.5 text-xs w-16">
                          <option value={1}>매일</option><option value={2}>격일</option><option value={3}>3일</option><option value={7}>주1</option>
                        </select>
                        <input value={editData.label} onChange={e => setEditData(d => ({...d, label: e.target.value}))} placeholder="메모" className="bg-gray-700 border border-gray-600 rounded px-1.5 py-0.5 text-xs w-16" />
                        <button onClick={saveEdit} className="text-emerald-400 hover:text-emerald-300"><Check size={14} /></button>
                        <button onClick={cancelEdit} className="text-gray-500 hover:text-red-400"><X size={14} /></button>
                      </div>
                    ) : (
                      /* 보기 모드 */
                      <>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium truncate">{entry.label || style.label}</p>
                          <p className="text-[10px] text-gray-500">{entry.start_hour}:00~{entry.end_hour === 24 ? "0" : entry.end_hour}:00 ({duration}h) · {entry.repeat_cycle === 1 ? "매일" : `${entry.repeat_cycle}일 주기`}</p>
                        </div>
                        <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: style.color }} />
                        <button onClick={() => startEdit(idx)} className="opacity-0 group-hover:opacity-100 px-2 py-1 rounded-lg bg-cyan-500/10 text-cyan-400 hover:bg-cyan-500/20 transition-all text-[11px] font-medium flex items-center gap-1">
                          <Edit3 size={12} /> 수정
                        </button>
                        <button onClick={() => removeEntry(idx)} className="opacity-0 group-hover:opacity-100 px-2 py-1 rounded-lg bg-red-500/10 text-red-400 hover:bg-red-500/20 transition-all text-[11px] font-medium flex items-center gap-1">
                          <Trash2 size={12} /> 삭제
                        </button>
                      </>
                    )}
                  </div>
                );
              })}
            </div>

            {/* 시뮬레이션 실행 */}
            <div className="mt-4 flex items-center gap-3">
              <select value={simDays} onChange={e => setSimDays(+e.target.value)} className="bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-sm">
                <option value={7}>1주 (7일)</option>
                <option value={14}>2주 (14일)</option>
                <option value={30}>1개월 (30일)</option>
                <option value={60}>2개월 (60일)</option>
                <option value={90}>3개월 (90일)</option>
              </select>
              <button onClick={runSimulation} disabled={loading || schedule.length === 0} className="flex-1 flex items-center justify-center gap-2 bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-400 hover:to-blue-400 disabled:opacity-40 py-2.5 rounded-xl text-sm font-semibold transition-all">
                {loading ? <span className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" /> : <Play size={16} />}
                시뮬레이션 실행
              </button>
            </div>
          </div>
        </div>

        {/* 결과 */}
        {results && <SimulationResults results={results} />}
      </div>
    </Layout>
  );
}


/* ============ 원형 시계 컴포넌트 ============ */
function ClockDial({ schedule }) {
  const size = 320;
  const cx = size / 2;
  const cy = size / 2;
  const outerR = 140;
  const innerR = 80;

  const hourToAngle = (h) => ((h % 24) / 24) * 360 - 90;
  const toRad = (deg) => (deg * Math.PI) / 180;

  const arcPath = (startH, endH, rOuter, rInner) => {
    let s = startH % 24;
    let e = endH % 24;
    if (e <= s) e += 24;
    const startAngle = toRad(hourToAngle(s));
    const endAngle = toRad(hourToAngle(e));
    const largeArc = (e - s) > 12 ? 1 : 0;

    const x1 = cx + rOuter * Math.cos(startAngle);
    const y1 = cy + rOuter * Math.sin(startAngle);
    const x2 = cx + rOuter * Math.cos(endAngle);
    const y2 = cy + rOuter * Math.sin(endAngle);
    const x3 = cx + rInner * Math.cos(endAngle);
    const y3 = cy + rInner * Math.sin(endAngle);
    const x4 = cx + rInner * Math.cos(startAngle);
    const y4 = cy + rInner * Math.sin(startAngle);

    return `M ${x1} ${y1} A ${rOuter} ${rOuter} 0 ${largeArc} 1 ${x2} ${y2} L ${x3} ${y3} A ${rInner} ${rInner} 0 ${largeArc} 0 ${x4} ${y4} Z`;
  };

  const labelPos = (startH, endH, r) => {
    let s = startH % 24;
    let e = endH % 24;
    if (e <= s) e += 24;
    const mid = (s + e) / 2;
    const angle = toRad(hourToAngle(mid));
    return { x: cx + r * Math.cos(angle), y: cy + r * Math.sin(angle) };
  };

  return (
    <div className="flex justify-center">
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        {/* 배경 원 */}
        <circle cx={cx} cy={cy} r={outerR} fill="none" stroke="#374151" strokeWidth={1} />
        <circle cx={cx} cy={cy} r={innerR} fill="none" stroke="#374151" strokeWidth={1} />
        <circle cx={cx} cy={cy} r={innerR - 1} fill="#1f2937" />

        {/* 시간 눈금 + 숫자 */}
        {Array.from({ length: 24 }, (_, i) => {
          const angle = toRad(hourToAngle(i));
          const x1 = cx + (outerR + 2) * Math.cos(angle);
          const y1 = cy + (outerR + 2) * Math.sin(angle);
          const x2 = cx + (outerR + 10) * Math.cos(angle);
          const y2 = cy + (outerR + 10) * Math.sin(angle);
          const tx = cx + (outerR + 20) * Math.cos(angle);
          const ty = cy + (outerR + 20) * Math.sin(angle);
          return (
            <g key={i}>
              <line x1={x1} y1={y1} x2={x2} y2={y2} stroke="#4b5563" strokeWidth={i % 6 === 0 ? 2 : 1} />
              {i % 3 === 0 && (
                <text x={tx} y={ty} textAnchor="middle" dominantBaseline="central" fill="#9ca3af" fontSize={10}>
                  {i}
                </text>
              )}
            </g>
          );
        })}

        {/* 스케줄 호 */}
        {schedule.map((entry, idx) => {
          const style = ACTIVITY_STYLES[entry.activity] || ACTIVITY_STYLES.other;
          const pos = labelPos(entry.start_hour, entry.end_hour, (outerR + innerR) / 2);
          return (
            <g key={idx}>
              <path d={arcPath(entry.start_hour, entry.end_hour, outerR - 2, innerR + 2)} fill={style.color} opacity={0.7} stroke="#1f2937" strokeWidth={1} />
              <text x={pos.x} y={pos.y} textAnchor="middle" dominantBaseline="central" fontSize={14}>
                {style.emoji}
              </text>
            </g>
          );
        })}

        {/* 중앙 */}
        <text x={cx} y={cy - 6} textAnchor="middle" fill="#e5e7eb" fontSize={12} fontWeight="bold">24H</text>
        <text x={cx} y={cy + 10} textAnchor="middle" fill="#6b7280" fontSize={9}>일과표</text>
      </svg>
    </div>
  );
}


/* ============ 시뮬레이션 결과 컴포넌트 ============ */
function SimulationResults({ results }) {
  const { initial_state, final_state, daily_history, analysis, days } = results;

  const severityColors = { high: "text-red-400", medium: "text-yellow-400", low: "text-gray-400" };
  const rhythmColors = { "우수": "text-green-400", "양호": "text-cyan-400", "주의": "text-yellow-400", "위험": "text-red-400" };

  return (
    <div className="space-y-5">
      {/* 종합 결과 카드 */}
      <div className="bg-gradient-to-r from-gray-800 to-gray-800/50 border border-gray-700 rounded-xl p-6">
        <h2 className="text-lg font-bold mb-4">{days}일 시뮬레이션 <span className="text-cyan-400">결과</span></h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <ResultCard label="체중 변화" value={`${analysis.weight_change > 0 ? "+" : ""}${analysis.weight_change}kg`} color={Math.abs(analysis.weight_change) < 1 ? "#51cf66" : "#ff6b6b"} sub={`${initial_state.weight_kg} → ${final_state.weight_kg}kg`} />
          <ResultCard label="생활리듬 점수" value={`${analysis.rhythm_score}/100`} color={analysis.rhythm_score >= 60 ? "#51cf66" : "#ff6b6b"} sub={analysis.rhythm_grade} />
          <ResultCard label="평균 수면" value={`${analysis.avg_sleep_hours}h`} color={analysis.avg_sleep_hours >= 7 ? "#51cf66" : "#ff6b6b"} sub={analysis.avg_sleep_hours >= 7 ? "적정" : "부족"} />
          <ResultCard label="주간 운동" value={`${analysis.avg_exercise_hours_week}h`} color={analysis.avg_exercise_hours_week >= 2.5 ? "#51cf66" : "#ff6b6b"} sub={analysis.avg_exercise_hours_week >= 2.5 ? "WHO 충족" : "WHO 미달"} />
        </div>
      </div>

      {/* 상태 변화 비교 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* Before/After */}
        <div className="bg-gray-800 border border-gray-700 rounded-xl p-5">
          <h3 className="text-sm font-semibold text-gray-400 mb-3">상태 변화 (Before → After)</h3>
          <div className="space-y-2">
            {analysis.changes.map((ch, i) => {
              const label = { weight_kg: "체중", sleep_score: "수면점수", stress_level: "스트레스", mood_score: "기분", hair_loss_risk: "탈모위험", blood_purity: "혈액청정도" }[ch.metric] || ch.metric;
              const good = (ch.metric === "stress_level" || ch.metric === "hair_loss_risk") ? ch.delta < 0 : ch.delta > 0;
              return (
                <div key={i} className="flex items-center gap-3 text-sm">
                  {good ? <TrendingUp size={14} className="text-green-400" /> : <TrendingDown size={14} className="text-red-400" />}
                  <span className="text-gray-400 w-20">{label}</span>
                  <span className="text-gray-500">{ch.initial}</span>
                  <span className="text-gray-600">→</span>
                  <span className="font-medium">{ch.final}</span>
                  <span className={`text-xs ml-auto ${good ? "text-green-400" : "text-red-400"}`}>
                    {ch.delta > 0 ? "+" : ""}{ch.delta}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* 문제점 & 조언 */}
        <div className="bg-gray-800 border border-gray-700 rounded-xl p-5 space-y-4">
          {analysis.problems.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold text-red-400 mb-2 flex items-center gap-1.5"><AlertTriangle size={14} /> 문제점</h3>
              <div className="space-y-2">
                {analysis.problems.map((p, i) => (
                  <div key={i} className="text-sm bg-red-500/5 border border-red-500/20 rounded-lg p-2.5">
                    <span className={`text-[10px] font-medium ${severityColors[p.severity]}`}>[{p.category}]</span>
                    <p className="text-gray-300 mt-0.5">{p.message}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
          <div>
            <h3 className="text-sm font-semibold text-green-400 mb-2 flex items-center gap-1.5"><CheckCircle size={14} /> 조언 & 해결방안</h3>
            <div className="space-y-2">
              {analysis.advice.map((a, i) => (
                <div key={i} className="text-sm bg-green-500/5 border border-green-500/20 rounded-lg p-2.5">
                  <span className="text-[10px] font-medium text-green-400">[{a.category}]</span>
                  <p className="text-gray-300 mt-0.5">{a.message}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* 건강 변화 그래프 */}
      <div className="bg-gray-800 border border-gray-700 rounded-xl p-5">
        <h3 className="text-sm font-semibold text-gray-400 mb-3">일별 건강 변화 추이</h3>
        <div className="h-56">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={daily_history}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="day" tick={{ fill: "#6b7280", fontSize: 10 }} label={{ value: "일", position: "insideBottom", fill: "#6b7280", fontSize: 10, offset: -5 }} />
              <YAxis tick={{ fill: "#6b7280", fontSize: 10 }} />
              <Tooltip contentStyle={{ backgroundColor: "#1f2937", border: "1px solid #374151", borderRadius: 8, fontSize: 11 }} labelFormatter={v => `Day ${v}`} />
              <Line type="monotone" dataKey="weight_kg" stroke="#ff6b6b" strokeWidth={2} dot={false} name="체중(kg)" />
              <Line type="monotone" dataKey="sleep_score" stroke="#748ffc" strokeWidth={2} dot={false} name="수면" />
              <Line type="monotone" dataKey="stress_level" stroke="#ff922b" strokeWidth={2} dot={false} name="스트레스" />
              <Line type="monotone" dataKey="mood_score" stroke="#20c997" strokeWidth={2} dot={false} name="기분" />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div className="flex gap-4 mt-2 justify-center">
          {[["체중", "#ff6b6b"], ["수면", "#748ffc"], ["스트레스", "#ff922b"], ["기분", "#20c997"]].map(([l, c]) => (
            <div key={l} className="flex items-center gap-1.5 text-[10px] text-gray-400">
              <span className="w-2.5 h-2.5 rounded-sm" style={{ backgroundColor: c }} /> {l}
            </div>
          ))}
        </div>
      </div>

      {/* 신뢰구간 포함 예측 차트 */}
      {daily_history && daily_history.length > 0 && (
        <div className="bg-gray-800 border border-gray-700 rounded-xl p-5">
          <h3 className="text-sm font-semibold text-gray-400 mb-3">예측 신뢰구간 (95% CI)</h3>
          <ErrorBarChart
            data={daily_history.map((d, i) => {
              const dayIdx = i + 1;
              const uncertainty = Math.sqrt(dayIdx / 7);
              return {
                day: d.day,
                weight_kg: d.weight_kg,
                weight_lower: +(d.weight_kg - 0.3 * uncertainty).toFixed(1),
                weight_upper: +(d.weight_kg + 0.3 * uncertainty).toFixed(1),
                sleep_score: d.sleep_score,
                sleep_lower: Math.max(0, Math.round(d.sleep_score - 5 * uncertainty)),
                sleep_upper: Math.min(100, Math.round(d.sleep_score + 5 * uncertainty)),
                stress_level: d.stress_level,
                stress_lower: Math.max(0, Math.round(d.stress_level - 7 * uncertainty)),
                stress_upper: Math.min(100, Math.round(d.stress_level + 7 * uncertainty)),
                mood_score: d.mood_score,
                mood_lower: Math.max(0, Math.round(d.mood_score - 6 * uncertainty)),
                mood_upper: Math.min(100, Math.round(d.mood_score + 6 * uncertainty)),
              };
            })}
            metrics={[
              { key: "weight_kg", label: "체중(kg)", color: "#f59e0b", lowerKey: "weight_lower", upperKey: "weight_upper" },
              { key: "sleep_score", label: "수면", color: "#748ffc", lowerKey: "sleep_lower", upperKey: "sleep_upper" },
              { key: "stress_level", label: "스트레스", color: "#ff6b6b", lowerKey: "stress_lower", upperKey: "stress_upper" },
              { key: "mood_score", label: "기분", color: "#10b981", lowerKey: "mood_lower", upperKey: "mood_upper" },
            ]}
            height={280}
          />
        </div>
      )}
    </div>
  );
}

function ResultCard({ label, value, color, sub }) {
  return (
    <div className="bg-gray-700/40 rounded-xl p-4 text-center">
      <p className="text-[11px] text-gray-500">{label}</p>
      <p className="text-2xl font-bold mt-1" style={{ color }}>{value}</p>
      <p className="text-[10px] text-gray-500 mt-0.5">{sub}</p>
    </div>
  );
}
