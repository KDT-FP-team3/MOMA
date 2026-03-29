/**
 * ReportPage — 주간 건강 리포트 페이지
 */
import Layout from "../components/layout/Layout";
import AvatarBody from "../components/AvatarBody";
import ErrorBarChart from "../components/ErrorBarChart";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  CartesianGrid,
  Cell,
  LabelList,
} from "recharts";

/* ── 날짜 범위 계산 ── */
function getWeekRange() {
  const now = new Date();
  const day = now.getDay();
  const monday = new Date(now);
  monday.setDate(now.getDate() - ((day + 6) % 7));
  const sunday = new Date(monday);
  sunday.setDate(monday.getDate() + 6);
  const fmt = (d) =>
    `${d.getFullYear()}.${String(d.getMonth() + 1).padStart(2, "0")}.${String(d.getDate()).padStart(2, "0")}`;
  return `${fmt(monday)} ~ ${fmt(sunday)}`;
}

/* ── Mock 주간 데이터 ── */
const DAYS = ["월", "화", "수", "목", "금", "토", "일"];

const weeklyChoices = [
  { day: "월", choice: "샐러드 + 닭가슴살 점심", score: 88 },
  { day: "화", choice: "야식 라면 (23시)", score: 42 },
  { day: "수", choice: "기타 연주 30분 + 스트레칭", score: 92 },
  { day: "목", choice: "에어프라이어 요리 저녁", score: 85 },
  { day: "금", choice: "튀김 치킨 + 맥주", score: 38 },
  { day: "토", choice: "아침 조깅 5km + 건강식", score: 95 },
  { day: "일", choice: "미세먼지 속 야외 러닝", score: 45 },
];

const dailyScores = DAYS.map((day, i) => ({
  day,
  score: weeklyChoices[i].score,
}));

const radarData = [
  { subject: "기분", value: 72 },
  { subject: "에너지", value: 68 },
  { subject: "수면", value: 55 },
  { subject: "스트레스관리", value: 60 },
  { subject: "건강", value: 75 },
  { subject: "체중관리", value: 62 },
];

const topGood = [
  { rank: 1, text: "토요일 아침 조깅 5km + 건강식", effect: "+15 에너지, -체중 0.3kg" },
  { rank: 2, text: "수요일 기타 연주 30분", effect: "스트레스 -15%, 폭식 충동 -40%" },
  { rank: 3, text: "월요일 샐러드 + 닭가슴살 점심", effect: "칼로리 -40%, 영양 균형 +20%" },
];

const topBad = [
  { rank: 1, text: "금요일 튀김 치킨 + 맥주", effect: "콜레스테롤 위험 +12%, 칼로리 +800kcal" },
  { rank: 2, text: "화요일 야식 라면 (23시)", effect: "수면 -35%, 다음날 운동 -20%" },
  { rank: 3, text: "일요일 미세먼지 속 야외 러닝", effect: "활성산소 증가, 혈액 청정도 하락" },
];

/* ── 주 시작 / 주 끝 아바타 상태 ── */
const avatarStart = { bmi: 25.2, mood: 50, energy: 55, stress: 60, sleep: 50, health: 55 };
const avatarEnd = { bmi: 24.8, mood: 65, energy: 68, stress: 45, sleep: 60, health: 70 };

/* ── 연쇄 효과 흐름 ── */
const cascadeSteps = [
  { label: "야식 라면 (23시)", color: "text-red-400", bg: "bg-red-500/20" },
  { label: "수면 -35%", color: "text-orange-400", bg: "bg-orange-500/20" },
  { label: "운동 -20%", color: "text-yellow-400", bg: "bg-yellow-500/20" },
  { label: "체중 목표 +2일 지연", color: "text-red-400", bg: "bg-red-500/20" },
];

/* ── 점수 → 색상 ── */
function scoreColor(score) {
  if (score >= 80) return "#3b82f6"; // 파랑
  if (score >= 65) return "#10b981"; // 초록
  if (score >= 50) return "#f59e0b"; // 노랑
  if (score >= 35) return "#f97316"; // 주황
  return "#ef4444"; // 빨강
}

/* ── 커스텀 레이더 눈금 라벨 (꼭짓점에 숫자 표시) ── */
function CustomRadarTick({ payload, x, y, cx, cy }) {
  const item = radarData.find((d) => d.subject === payload.value);
  const dx = x - cx;
  const dy = y - cy;
  const dist = Math.sqrt(dx * dx + dy * dy);
  const offsetX = dist > 0 ? (dx / dist) * 18 : 0;
  const offsetY = dist > 0 ? (dy / dist) * 18 : 0;
  return (
    <g>
      <text x={x + offsetX} y={y + offsetY} textAnchor="middle" dominantBaseline="central" fill="#9ca3af" fontSize={12}>
        {payload.value}
      </text>
      {item && (
        <text x={x + offsetX} y={y + offsetY + 14} textAnchor="middle" dominantBaseline="central" fill="#06b6d4" fontSize={11} fontWeight={600}>
          {item.value}
        </text>
      )}
    </g>
  );
}

/* ── 커스텀 Tooltip ── */
function CustomBarTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-gray-900 border border-gray-600 rounded-lg px-3 py-2 text-sm">
      <p className="text-white">{label}요일</p>
      <p className="font-bold" style={{ color: scoreColor(payload[0].value) }}>{payload[0].value}점</p>
    </div>
  );
}

/* ── 주간 트렌드 신뢰구간 데이터 (12주, 실제 날짜 사용) ── */
const DAY_NAMES = ["일", "월", "화", "수", "목", "금", "토"];
function generateTrendData() {
  const now = new Date();
  now.setHours(0, 0, 0, 0);
  const startDay = new Date(now);
  // 과거 42일(6주) + 미래 42일(6주) = 총 84일(12주, 오늘 중심)
  startDay.setDate(now.getDate() - 42);
  const data = [];
  for (let i = 0; i < 84; i++) {
    const d = new Date(startDay);
    d.setDate(startDay.getDate() + i);
    const month = d.getMonth() + 1;
    const date = d.getDate();
    const dow = d.getDay(); // 0=일, 6=토
    const dayLabel = `${month}/${date}(${DAY_NAMES[dow]})`;
    const isPast = d <= now;
    const daysFromNow = (d - now) / 86400000;
    const uncertainty = isPast ? 0.3 : 0.3 + Math.abs(daysFromNow) * 0.15;
    const baseWeight = 74.5 - i * 0.05 + Math.sin(i * 0.5) * 0.3;
    const baseSleep = 55 + i * 0.8 + (dow === 0 || dow === 6 ? 5 : 0);
    const baseStress = 60 - i * 0.7 + (dow === 1 ? 5 : 0);
    const baseMood = 50 + i * 0.9 + (dow === 0 || dow === 6 ? 3 : -1);
    data.push({
      day: dayLabel,
      date: d.toISOString().slice(0, 10),
      month,
      dow,
      weight_kg: +baseWeight.toFixed(1),
      weight_lower: +(baseWeight - uncertainty).toFixed(1),
      weight_upper: +(baseWeight + uncertainty).toFixed(1),
      sleep_score: Math.min(100, Math.max(0, Math.round(baseSleep))),
      sleep_lower: Math.max(0, Math.round(baseSleep - 5 * uncertainty)),
      sleep_upper: Math.min(100, Math.round(baseSleep + 5 * uncertainty)),
      stress_level: Math.min(100, Math.max(0, Math.round(baseStress))),
      stress_lower: Math.max(0, Math.round(baseStress - 7 * uncertainty)),
      stress_upper: Math.min(100, Math.round(baseStress + 7 * uncertainty)),
      mood_score: Math.min(100, Math.max(0, Math.round(baseMood))),
      mood_lower: Math.max(0, Math.round(baseMood - 6 * uncertainty)),
      mood_upper: Math.min(100, Math.round(baseMood + 6 * uncertainty)),
    });
  }
  return data;
}
const weeklyTrendData = generateTrendData();

const weeklyTrendMetrics = [
  { key: "weight_kg", label: "체중(kg)", color: "#f59e0b", lowerKey: "weight_lower", upperKey: "weight_upper" },
  { key: "sleep_score", label: "수면", color: "#748ffc", lowerKey: "sleep_lower", upperKey: "sleep_upper" },
  { key: "stress_level", label: "스트레스", color: "#ff6b6b", lowerKey: "stress_lower", upperKey: "stress_upper" },
  { key: "mood_score", label: "기분", color: "#10b981", lowerKey: "mood_lower", upperKey: "mood_upper" },
];

/* ── 메인 컴포넌트 ── */
export default function ReportPage() {
  const weekRange = getWeekRange();

  return (
    <Layout>
      <div className="max-w-6xl mx-auto space-y-8 pb-20 lg:pb-8">
        {/* 헤더 */}
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-bold text-white">
            {"📊"} 주간 건강 리포트
          </h1>
          <p className="text-white text-lg">{weekRange}</p>
        </div>

        {/* Top 3 좋았던 / 나빴던 선택 */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* 좋았던 선택 */}
          <div className="bg-gray-800/50 border border-gray-700 rounded-2xl p-6">
            <h2 className="text-lg font-semibold text-emerald-400 mb-4">
              {"✅"} 이번 주 가장 좋았던 선택 Top 3
            </h2>
            <div className="space-y-3">
              {topGood.map((item) => (
                <div
                  key={item.rank}
                  className="flex items-start gap-3 bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-3"
                >
                  <span className="text-emerald-400 font-bold text-lg min-w-[28px]">
                    {item.rank}
                  </span>
                  <div>
                    <p className="text-white text-sm font-medium">{item.text}</p>
                    <p className="text-emerald-300/70 text-xs mt-1">{item.effect}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* 나빴던 선택 */}
          <div className="bg-gray-800/50 border border-gray-700 rounded-2xl p-6">
            <h2 className="text-lg font-semibold text-red-400 mb-4">
              {"⚠️"} 이번 주 나빴던 선택 Top 3
            </h2>
            <div className="space-y-3">
              {topBad.map((item) => (
                <div
                  key={item.rank}
                  className="flex items-start gap-3 bg-red-500/10 border border-red-500/20 rounded-xl p-3"
                >
                  <span className="text-red-400 font-bold text-lg min-w-[28px]">
                    {item.rank}
                  </span>
                  <div>
                    <p className="text-white text-sm font-medium">{item.text}</p>
                    <p className="text-red-300/70 text-xs mt-1">{item.effect}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* 레이더 차트 + 바 차트 */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* 레이더 차트 — 6개 차원 */}
          <div className="bg-gray-800/50 border border-gray-700 rounded-2xl p-6">
            <h2 className="text-lg font-semibold text-white mb-4">
              {"🎯"} 종합 분석
            </h2>
            <ResponsiveContainer width="100%" height={300}>
              <RadarChart data={radarData} cx="50%" cy="50%" outerRadius="65%">
                <PolarGrid stroke="#374151" />
                <PolarAngleAxis
                  dataKey="subject"
                  tick={<CustomRadarTick />}
                />
                <PolarRadiusAxis
                  angle={30}
                  domain={[0, 100]}
                  tick={{ fill: "#6b7280", fontSize: 10 }}
                />
                <Radar
                  name="이번 주"
                  dataKey="value"
                  stroke="#06b6d4"
                  fill="#06b6d4"
                  fillOpacity={0.25}
                  strokeWidth={2}
                />
              </RadarChart>
            </ResponsiveContainer>
          </div>

          {/* 바 차트 — 일별 종합 점수 */}
          <div className="bg-gray-800/50 border border-gray-700 rounded-2xl p-6">
            <h2 className="text-lg font-semibold text-white mb-4">
              {"📈"} 일별 종합 점수
            </h2>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={dailyScores}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.5} />
                <XAxis dataKey="day" tick={{ fill: "#9ca3af", fontSize: 12 }} />
                <YAxis domain={[0, 100]} tick={{ fill: "#6b7280", fontSize: 10 }} />
                <Tooltip content={<CustomBarTooltip />} />
                <Bar
                  dataKey="score"
                  radius={[6, 6, 0, 0]}
                  barSize={32}
                >
                  {dailyScores.map((entry, idx) => (
                    <Cell key={idx} fill={scoreColor(entry.score)} />
                  ))}
                  <LabelList dataKey="score" position="top" fill="#e5e7eb" fontSize={11} fontWeight={600} />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* 주간 트렌드 신뢰구간 차트 */}
        <div className="bg-gray-800/50 border border-gray-700 rounded-2xl p-6">
          <h2 className="text-lg font-semibold text-white mb-2">
            {"📉"} 건강 트렌드 (신뢰구간)
          </h2>
          <p className="text-sm text-white mb-1">
            미래로 갈수록 불확실성이 커지는 예측 밴드를 보여줍니다.
          </p>
          <div className="flex flex-wrap gap-4 text-xs text-white mb-4">
            <span className="flex items-center gap-1">
              <span className="inline-block w-4 h-0.5 bg-blue-400 opacity-50" style={{borderTop: "2px dashed #3b82f6"}} /> 토요일
            </span>
            <span className="flex items-center gap-1">
              <span className="inline-block w-4 h-0.5 bg-red-400 opacity-50" style={{borderTop: "2px dashed #ef4444"}} /> 일요일
            </span>
            <span className="flex items-center gap-1">
              <span className="inline-block w-3 h-3 rounded-sm" style={{background: "rgba(59,130,246,0.15)"}} /> 홀수 월
            </span>
            <span className="flex items-center gap-1">
              <span className="inline-block w-3 h-3 rounded-sm" style={{background: "rgba(139,92,246,0.15)"}} /> 짝수 월
            </span>
          </div>
          <ErrorBarChart
            data={weeklyTrendData}
            metrics={weeklyTrendMetrics}
            height={380}
          />
        </div>

        {/* Before / After 아바타 비교 */}
        <div className="bg-gray-800/50 border border-gray-700 rounded-2xl p-6">
          <h2 className="text-lg font-semibold text-white mb-6 text-center">
            {"🧍"} Before / After 비교
          </h2>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-8">
            {/* Before */}
            <div className="flex flex-col items-center gap-3">
              <span className="text-sm font-medium text-white bg-gray-700/50 px-3 py-1 rounded-full">
                주 시작
              </span>
              <AvatarBody {...avatarStart} size={180} />
              <div className="text-xs text-white space-y-0.5 text-center">
                <p>기분 {avatarStart.mood} · 에너지 {avatarStart.energy}</p>
                <p>스트레스 {avatarStart.stress} · 수면 {avatarStart.sleep}</p>
              </div>
            </div>

            {/* 화살표 */}
            <div className="text-4xl text-cyan-400 font-light hidden sm:block">
              {"→"}
            </div>
            <div className="text-2xl text-cyan-400 font-light sm:hidden">
              {"↓"}
            </div>

            {/* After */}
            <div className="flex flex-col items-center gap-3">
              <span className="text-sm font-medium text-emerald-400 bg-emerald-500/10 px-3 py-1 rounded-full">
                주 끝
              </span>
              <AvatarBody {...avatarEnd} size={180} />
              <div className="text-xs text-white space-y-0.5 text-center">
                <p>기분 {avatarEnd.mood} · 에너지 {avatarEnd.energy}</p>
                <p>스트레스 {avatarEnd.stress} · 수면 {avatarEnd.sleep}</p>
              </div>
            </div>
          </div>
        </div>

        {/* 크로스 도메인 연쇄 효과 */}
        <div className="bg-gray-800/50 border border-gray-700 rounded-2xl p-6">
          <h2 className="text-lg font-semibold text-white mb-4">
            {"⛓️"} 크로스 도메인 연쇄 효과
          </h2>
          <p className="text-white text-sm mb-4">
            하나의 선택이 다른 영역으로 어떻게 연쇄적으로 영향을 미치는지 보여줍니다.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-2">
            {cascadeSteps.map((step, idx) => (
              <div key={idx} className="flex items-center gap-2">
                <span
                  className={`${step.bg} ${step.color} text-sm font-medium px-4 py-2 rounded-xl border border-gray-600/50 whitespace-nowrap`}
                >
                  {step.label}
                </span>
                {idx < cascadeSteps.length - 1 && (
                  <span className="text-white text-lg font-bold">{"→"}</span>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* 종합 요약 및 조언 */}
        <div className="bg-gray-800/50 border border-gray-700 rounded-2xl p-6">
          <h2 className="text-lg font-semibold text-white mb-4">
            {"💡"} 이번 주 종합 요약
          </h2>
          <div className="space-y-3 text-white text-sm leading-relaxed">
            <p>
              이번 주 종합 점수는 <span className="text-cyan-400 font-semibold">69.3점</span>입니다.
              주 전반에 비해 후반으로 갈수록 개선되는 경향을 보였습니다.
            </p>
            <p>
              <span className="text-emerald-400 font-medium">잘한 점:</span>{" "}
              토요일 아침 조깅과 수요일 취미 활동이 전체 건강 지수 향상에 크게 기여했습니다.
              에어프라이어를 활용한 조리법은 칼로리를 40% 줄이는 효과가 있었습니다.
            </p>
            <p>
              <span className="text-red-400 font-medium">개선 필요:</span>{" "}
              야식 섭취(화요일)와 미세먼지 날 야외 운동(일요일)은 수면과 건강 지표에 악영향을 미쳤습니다.
              야식은 수면 질을 35% 저하시키고 다음날 운동 효율을 20% 감소시킵니다.
            </p>
            <p>
              <span className="text-yellow-400 font-medium">다음 주 추천:</span>{" "}
              야식 대신 저녁 식사를 충분히 하고, 미세먼지가 높은 날은 실내 운동으로 전환하세요.
              기타 연주 등 취미 활동을 주 3회 이상 유지하면 스트레스 관리에 큰 도움이 됩니다.
            </p>
          </div>
        </div>
      </div>
    </Layout>
  );
}
