/**
 * ErrorBarChart — 신뢰구간 밴드 + 주말 세로선 + 월별 배경색 + 좌우 스크롤
 *
 * Props:
 *   data     — [{day, date, month, dow, weight_kg, weight_lower, ...}]
 *   metrics  — [{key, label, color, lowerKey, upperKey}]
 *   height   — 차트 높이 (기본 350)
 */
import { useState, useMemo, useRef, useCallback, useEffect } from "react";
import {
  ComposedChart,
  Area,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ReferenceLine,
  ReferenceArea,
} from "recharts";

const DEFAULT_COLORS = {
  weight: "#f59e0b",
  sleep: "#748ffc",
  stress: "#ff6b6b",
  mood: "#10b981",
};

const MONTH_BG_COLORS = [
  "rgba(59,130,246,0.06)",
  "rgba(139,92,246,0.06)",
];

/** 뷰 옵션: days = 화면에 보일 일수, pxPerDay = 포인트당 고정 픽셀 */
const VIEW_OPTIONS = [
  { label: "1주",  days: 7,  pxPerDay: 120 },
  { label: "2주",  days: 14, pxPerDay: 68 },
  { label: "4주",  days: 28, pxPerDay: 38 },
  { label: "8주",  days: 56, pxPerDay: 22, skipInterval: 6 },
  { label: "12주", days: 84, pxPerDay: 16, skipInterval: 6 },
];

function getToday() {
  return new Date().toISOString().slice(0, 10);
}

/** 커스텀 X축 틱 — 날짜 + 요일 2줄 표시 */
function CustomXTick({ x, y, payload, data }) {
  const idx = payload?.index;
  const item = idx != null && data?.[idx] ? data[idx] : null;
  const dow = item?.dow;

  let fill = "#94a3b8";
  if (dow === 6) fill = "#60a5fa";
  if (dow === 0) fill = "#f87171";

  const label = String(payload.value ?? "");
  const match = label.match(/^(\d+\/\d+)\((.)\)$/);
  const datePart = match ? match[1] : label;
  const dayPart = match ? `(${match[2]})` : "";

  return (
    <g transform={`translate(${x},${y})`}>
      <text
        x={0} y={0} dy={14}
        textAnchor="middle" fill={fill}
        fontSize={11}
        fontWeight={dow === 0 || dow === 6 ? 700 : 400}
      >
        {datePart}
      </text>
      <text
        x={0} y={0} dy={27}
        textAnchor="middle" fill={fill}
        fontSize={10}
        fontWeight={dow === 0 || dow === 6 ? 600 : 400}
      >
        {dayPart}
      </text>
    </g>
  );
}

/** 커스텀 툴팁 */
function CustomTooltip({ active, payload, label }) {
  if (!active || !payload || payload.length === 0) return null;
  const seen = new Set();
  const lines = payload.filter((p) => {
    if (!p.dataKey || p.dataKey.includes("_range") || p.dataKey.includes("_past") || p.dataKey.includes("_future")) return false;
    if (String(p.name).includes("예측")) return false;
    if (String(p.name).includes("밴드")) return false;
    if (seen.has(p.name)) return false;
    seen.add(p.name);
    return true;
  });

  return (
    <div className="rounded-lg border border-gray-700 bg-gray-900/95 px-3 py-2 text-sm shadow-lg z-50">
      <p className="mb-1 font-semibold text-gray-300">{label}</p>
      {lines.map((entry) => {
        const metricKey = entry.dataKey;
        const row = entry.payload;
        const base = metricKey.replace(/_kg$|_score$|_level$|_index$/, "");
        const lower = row[`${base}_lower`] ?? row[`${metricKey}_lower`];
        const upper = row[`${base}_upper`] ?? row[`${metricKey}_upper`];
        const value = entry.value;
        const range =
          lower != null && upper != null
            ? `${Number(lower).toFixed(1)} ~ ${Number(upper).toFixed(1)}`
            : null;

        return (
          <div key={metricKey} className="flex items-center gap-2">
            <span
              className="inline-block h-2.5 w-2.5 rounded-full"
              style={{ backgroundColor: entry.color }}
            />
            <span className="text-gray-400">{entry.name}:</span>
            <span className="font-medium text-white">
              {Number(value).toFixed(1)}
            </span>
            {range && <span className="text-gray-500">({range})</span>}
          </div>
        );
      })}
    </div>
  );
}

function getMonthBands(data) {
  if (!data || data.length === 0) return [];
  const bands = [];
  let currentMonth = data[0].month;
  let startIdx = 0;
  for (let i = 1; i <= data.length; i++) {
    const m = i < data.length ? data[i].month : -1;
    if (m !== currentMonth) {
      bands.push({
        x1: data[startIdx].day,
        x2: data[i - 1].day,
        month: currentMonth,
        color: MONTH_BG_COLORS[currentMonth % 2],
      });
      currentMonth = m;
      startIdx = i;
    }
  }
  return bands;
}

function getWeekendLines(data) {
  if (!data) return [];
  return data
    .filter((d) => d.dow === 6 || d.dow === 0)
    .map((d) => ({
      day: d.day,
      dow: d.dow,
      color: d.dow === 6 ? "#3b82f6" : "#ef4444",
    }));
}

export default function ErrorBarChart({
  data = [],
  metrics = [],
  height = 350,
}) {
  const today = useMemo(getToday, []);
  const scrollRef = useRef(null);
  const containerRef = useRef(null);
  const [viewIdx, setViewIdx] = useState(2); // 기본: 4주
  const view = VIEW_OPTIONS[viewIdx];

  /**
   * 데이터 enrichment: 과거/미래를 구분하는 키를 추가
   * - 과거: metric_key 값 유지, future_metric_key = null
   * - 미래: metric_key = null, future_metric_key 값 유지
   * - 경계점(오늘): 양쪽 모두 값 있음 (선이 연결되도록)
   */
  const enriched = useMemo(() => {
    const splitPoint = data.findIndex((d) => d.date > today);
    const splitIdx = splitPoint === -1 ? data.length : splitPoint;

    return data.map((row, i) => {
      const extra = {};
      const isPast = i <= splitIdx;
      const isFuture = i >= splitIdx - 1;

      for (const m of metrics) {
        const lk = m.lowerKey ?? `${m.key.replace(/_kg$|_score$|_level$|_index$/, "")}_lower`;
        const uk = m.upperKey ?? `${m.key.replace(/_kg$|_score$|_level$|_index$/, "")}_upper`;
        const val = row[m.key];
        const lo = row[lk] ?? val;
        const hi = row[uk] ?? val;

        // 과거 값
        extra[`${m.key}_past`] = isPast ? val : null;
        extra[`${m.key}_past_range`] = isPast ? [lo, hi] : [null, null];

        // 미래 값
        extra[`${m.key}_future`] = isFuture ? val : null;
        extra[`${m.key}_future_range`] = isFuture ? [lo, hi] : [null, null];

        // 전체 범위 (툴팁용)
        extra[`${m.key}_range`] = [lo, hi];
      }
      return { ...row, ...extra };
    });
  }, [data, metrics, today]);

  const monthBands = useMemo(() => getMonthBands(enriched), [enriched]);
  const weekendLines = useMemo(() => getWeekendLines(enriched), [enriched]);

  const todayIdx = useMemo(() => {
    const idx = enriched.findIndex((d) => d.date >= today);
    return idx === -1 ? enriched.length - 1 : idx;
  }, [enriched, today]);

  /** 컨테이너 너비 추적 (반응형) */
  const [containerW, setContainerW] = useState(900);
  useEffect(() => {
    if (containerRef.current) setContainerW(containerRef.current.clientWidth);
    const handleResize = () => {
      if (containerRef.current) setContainerW(containerRef.current.clientWidth);
    };
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  /** 고정 pxPerDay 사용 — 항상 데이터 전체 너비를 확보, 스크롤로 탐색 */
  const pxPerDay = view.pxPerDay;
  const chartWidth = Math.max(enriched.length * pxPerDay + 74, containerW);

  const scrollToStart = useCallback(() => {
    if (scrollRef.current) scrollRef.current.scrollTo({ left: 0, behavior: "smooth" });
  }, []);

  const scrollToToday = useCallback(() => {
    if (!scrollRef.current) return;
    const targetX = todayIdx * pxPerDay - scrollRef.current.clientWidth / 3;
    scrollRef.current.scrollTo({ left: Math.max(0, targetX), behavior: "smooth" });
  }, [todayIdx, pxPerDay]);

  useEffect(() => {
    const timer = setTimeout(scrollToStart, 100);
    return () => clearTimeout(timer);
  }, [scrollToStart, viewIdx]);

  const todayLabel = useMemo(() => {
    const item = enriched.find((d) => d.date >= today);
    return item?.day;
  }, [enriched, today]);

  const tickInterval = useMemo(() => {
    // skipInterval이 설정된 뷰(8주, 12주): 일요일만 표시
    if (view.skipInterval) return view.skipInterval;
    // 라벨 최소 너비 55px 확보
    const minLabelWidth = 55;
    if (pxPerDay >= minLabelWidth) return 0;
    return Math.ceil(minLabelWidth / pxPerDay) - 1;
  }, [view, pxPerDay]);

  if (data.length === 0 || metrics.length === 0) {
    return (
      <div className="flex items-center justify-center text-gray-500" style={{ height }}>
        데이터가 없습니다
      </div>
    );
  }

  return (
    <div className="relative" ref={containerRef}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex gap-1">
          {VIEW_OPTIONS.map((opt, i) => (
            <button
              key={opt.label}
              onClick={() => setViewIdx(i)}
              className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                viewIdx === i
                  ? "bg-cyan-600 text-white"
                  : "bg-gray-700 text-gray-400 hover:bg-gray-600 hover:text-gray-200"
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
        <button
          onClick={scrollToToday}
          className="px-3 py-1 text-xs font-semibold bg-cyan-600 hover:bg-cyan-500
                     text-white rounded-md shadow transition-colors"
        >
          📍 현재
        </button>
      </div>

      <div
        ref={scrollRef}
        className="overflow-x-auto overflow-y-hidden"
        style={{ height: height + 70 }}
      >
        <ComposedChart
          data={enriched}
          width={chartWidth}
          height={height + 40}
          margin={{ top: 8, right: 24, bottom: 36, left: 50 }}
        >
          {monthBands.map((band, i) => (
            <ReferenceArea
              key={`month-${i}`}
              x1={band.x1}
              x2={band.x2}
              fill={band.color}
              fillOpacity={1}
              strokeOpacity={0}
            />
          ))}

          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />

          {weekendLines.map((wl, i) => (
            <ReferenceLine
              key={`weekend-${i}`}
              x={wl.day}
              stroke={wl.color}
              strokeOpacity={0.35}
              strokeWidth={1.5}
              strokeDasharray="4 3"
            />
          ))}

          {todayLabel && (
            <ReferenceLine
              x={todayLabel}
              stroke="#ffffff"
              strokeWidth={2}
              strokeOpacity={0.6}
              label={{
                value: "오늘",
                position: "top",
                fill: "#fff",
                fontSize: 11,
                fontWeight: 600,
              }}
            />
          )}

          <XAxis
            dataKey="day"
            tick={<CustomXTick data={enriched} />}
            tickLine={false}
            axisLine={{ stroke: "#475569" }}
            interval={tickInterval}
            height={45}
          />
          <YAxis
            tick={{ fill: "#94a3b8", fontSize: 12 }}
            tickLine={false}
            axisLine={{ stroke: "#475569" }}
            domain={[0, 100]}
          />
          <Tooltip content={<CustomTooltip />} />

          <Legend
            verticalAlign="bottom"
            iconType="circle"
            wrapperStyle={{ paddingTop: 4, fontSize: 12 }}
            payload={metrics.map((m) => ({
              value: m.label,
              type: "circle",
              color: m.color ?? DEFAULT_COLORS[m.key] ?? "#94a3b8",
            }))}
          />

          {metrics.map((m) => {
            const color = m.color ?? DEFAULT_COLORS[m.key] ?? "#94a3b8";

            return [
              /* 과거 밴드 (좁은) */
              <Area
                key={`past-band-${m.key}`}
                dataKey={`${m.key}_past_range`}
                fill={color}
                fillOpacity={0.15}
                stroke="none"
                isAnimationActive={false}
                legendType="none"
                tooltipType="none"
                name={`${m.label} 과거밴드`}
                connectNulls
              />,

              /* 미래 밴드 (넓은, 불확실성) */
              <Area
                key={`future-band-${m.key}`}
                dataKey={`${m.key}_future_range`}
                fill={color}
                fillOpacity={0.25}
                stroke={color}
                strokeOpacity={0.3}
                strokeDasharray="4 4"
                isAnimationActive={false}
                legendType="none"
                tooltipType="none"
                name={`${m.label} 예측밴드`}
                connectNulls
              />,

              /* 과거 선 (실선) */
              <Line
                key={`past-line-${m.key}`}
                dataKey={`${m.key}_past`}
                stroke={color}
                strokeWidth={2}
                dot={{ r: 3, fill: color, stroke: "#1e293b", strokeWidth: 1 }}
                isAnimationActive={false}
                legendType="none"
                name={m.label}
                connectNulls
              />,

              /* 미래 선 (점선) */
              <Line
                key={`future-line-${m.key}`}
                dataKey={`${m.key}_future`}
                stroke={color}
                strokeWidth={2}
                strokeDasharray="6 4"
                dot={{ r: 3, fill: "#1e293b", stroke: color, strokeWidth: 1.5 }}
                isAnimationActive={false}
                legendType="none"
                name={`${m.label} 예측`}
                connectNulls
              />,
            ];
          })}
        </ComposedChart>
      </div>
    </div>
  );
}
