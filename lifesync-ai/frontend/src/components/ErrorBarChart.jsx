/**
 * ErrorBarChart — 신뢰구간 밴드를 포함한 시계열 차트
 *
 * Recharts Area(밴드) + Line(평균값) 조합으로
 * 과거 데이터와 미래 예측을 시각적으로 구분합니다.
 *
 * Props:
 *   data     — [{day, weight_kg, weight_lower, weight_upper, ...}]
 *   metrics  — [{key, label, color, lowerKey, upperKey}]
 *   height   — 차트 높이 (기본 300)
 */
import { useMemo } from "react";
import {
  ResponsiveContainer,
  ComposedChart,
  Area,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
} from "recharts";

/** @type {Record<string, string>} */
const DEFAULT_COLORS = {
  weight: "#f59e0b",
  sleep: "#748ffc",
  stress: "#ff6b6b",
  mood: "#10b981",
};

/**
 * 오늘 날짜를 YYYY-MM-DD 형식으로 반환합니다.
 * @returns {string}
 */
function getToday() {
  const d = new Date();
  return d.toISOString().slice(0, 10);
}

/**
 * @param {{ payload?: object }} props
 */
function CustomTooltip({ active, payload, label }) {
  if (!active || !payload || payload.length === 0) return null;

  // Area 항목은 제외하고 Line 항목만 표시
  const lines = payload.filter((p) => p.dataKey && !p.dataKey.includes("_range"));

  return (
    <div className="rounded-lg border border-gray-700 bg-gray-900/95 px-3 py-2 text-sm shadow-lg">
      <p className="mb-1 font-semibold text-gray-300">{label}</p>
      {lines.map((entry) => {
        const metricKey = entry.dataKey;
        const row = entry.payload;
        // lowerKey / upperKey 를 찾기 위해 접미사 추론
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
            {range && (
              <span className="text-gray-500">({range})</span>
            )}
          </div>
        );
      })}
    </div>
  );
}

/**
 * @param {{
 *   data: object[],
 *   metrics: { key: string, label: string, color?: string, lowerKey?: string, upperKey?: string }[],
 *   height?: number,
 * }} props
 */
export default function ErrorBarChart({ data = [], metrics = [], height = 300 }) {
  const today = useMemo(getToday, []);

  // 각 데이터 포인트에 Area용 range 배열 필드를 주입
  const enriched = useMemo(() => {
    return data.map((row) => {
      const extra = {};
      for (const m of metrics) {
        const lk = m.lowerKey ?? `${m.key.replace(/_kg$|_score$|_level$|_index$/, "")}_lower`;
        const uk = m.upperKey ?? `${m.key.replace(/_kg$|_score$|_level$|_index$/, "")}_upper`;
        extra[`${m.key}_range`] = [row[lk] ?? row[m.key], row[uk] ?? row[m.key]];
      }
      return { ...row, ...extra };
    });
  }, [data, metrics]);

  // 과거/미래 분할 인덱스
  const splitIdx = useMemo(() => {
    const idx = enriched.findIndex((d) => d.day > today);
    return idx === -1 ? enriched.length : idx;
  }, [enriched, today]);

  // 과거/미래 데이터 (경계점은 양쪽에 포함하여 연결)
  const pastData = useMemo(() => enriched.slice(0, splitIdx), [enriched, splitIdx]);
  const futureData = useMemo(
    () => (splitIdx > 0 ? enriched.slice(splitIdx - 1) : enriched),
    [enriched, splitIdx],
  );

  if (data.length === 0 || metrics.length === 0) {
    return (
      <div
        className="flex items-center justify-center text-gray-500"
        style={{ height }}
      >
        데이터가 없습니다
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <ComposedChart data={enriched} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
        <XAxis
          dataKey="day"
          tick={{ fill: "#94a3b8", fontSize: 12 }}
          tickLine={false}
          axisLine={{ stroke: "#475569" }}
        />
        <YAxis
          tick={{ fill: "#94a3b8", fontSize: 12 }}
          tickLine={false}
          axisLine={{ stroke: "#475569" }}
        />
        <Tooltip content={<CustomTooltip />} />
        <Legend
          verticalAlign="bottom"
          iconType="circle"
          wrapperStyle={{ paddingTop: 12, fontSize: 13 }}
        />

        {metrics.map((m) => {
          const color = m.color ?? DEFAULT_COLORS[m.key] ?? "#94a3b8";

          return [
            /* ── 과거: 좁은 밴드 (실측 신뢰구간) ── */
            <Area
              key={`past-band-${m.key}`}
              data={pastData}
              dataKey={`${m.key}_range`}
              fill={color}
              fillOpacity={0.15}
              stroke="none"
              isAnimationActive={false}
              legendType="none"
              tooltipType="none"
              name={`${m.label} 과거 밴드`}
              connectNulls
            />,

            /* ── 미래: 넓은 밴드 (예측 신뢰구간) ── */
            <Area
              key={`future-band-${m.key}`}
              data={futureData}
              dataKey={`${m.key}_range`}
              fill={color}
              fillOpacity={0.25}
              stroke={color}
              strokeOpacity={0.3}
              strokeDasharray="4 4"
              isAnimationActive={false}
              legendType="none"
              tooltipType="none"
              name={`${m.label} 예측 밴드`}
              connectNulls
            />,

            /* ── 과거 평균선 (실선) ── */
            <Line
              key={`past-line-${m.key}`}
              data={pastData}
              dataKey={m.key}
              stroke={color}
              strokeWidth={2}
              dot={{ r: 4, fill: color, stroke: "#1e293b", strokeWidth: 1.5 }}
              isAnimationActive={false}
              legendType="none"
              name={`${m.label} 과거`}
              connectNulls
            />,

            /* ── 미래 평균선 (점선) ── */
            <Line
              key={`future-line-${m.key}`}
              data={futureData}
              dataKey={m.key}
              stroke={color}
              strokeWidth={2}
              strokeDasharray="6 4"
              dot={{ r: 4, fill: "#1e293b", stroke: color, strokeWidth: 2 }}
              isAnimationActive={false}
              name={m.label}
              connectNulls
            />,
          ];
        })}
      </ComposedChart>
    </ResponsiveContainer>
  );
}
