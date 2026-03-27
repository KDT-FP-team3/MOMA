/**
 * CharacterCard — 게이미피케이션 캐릭터 카드
 *
 * Props:
 *   profile  — { level, exp, nextLevelExp, title, badges, streak }
 *   stats    — { bmi, mood, energy, stress, sleep, health }
 */
import { useState, useEffect, useRef } from "react";
import { Flame, Star, Trophy, Zap, Heart, Shield } from "lucide-react";
import AvatarBody from "./AvatarBody";

/** 스탯 바 색상: 점수 구간별 */
function statColor(value) {
  if (value >= 80) return "#10b981"; // green
  if (value >= 60) return "#f59e0b"; // amber
  if (value >= 40) return "#f97316"; // orange
  return "#ef4444"; // red
}

/** 스탯 설정 */
const STAT_CONFIG = [
  { key: "bmi", label: "BMI", icon: Heart, format: (v) => v.toFixed(1), max: 40 },
  { key: "mood", label: "기분", icon: Star, format: (v) => Math.round(v), max: 100 },
  { key: "energy", label: "활력", icon: Zap, format: (v) => Math.round(v), max: 100 },
  { key: "stress", label: "스트레스", icon: Shield, format: (v) => Math.round(v), max: 100 },
  { key: "sleep", label: "수면", icon: Star, format: (v) => Math.round(v), max: 100 },
  { key: "health", label: "건강", icon: Trophy, format: (v) => Math.round(v), max: 100 },
];

/** 스파클 파티클 (레벨업 시) */
function Sparkle({ delay, x, y }) {
  return (
    <span
      className="pointer-events-none absolute text-yellow-300"
      style={{
        left: `${x}%`,
        top: `${y}%`,
        fontSize: "14px",
        animation: `sparkle-float 1s ease-out ${delay}s forwards`,
        opacity: 0,
      }}
    >
      ✦
    </span>
  );
}

/**
 * @param {{
 *   profile: { level: number, exp: number, nextLevelExp: number, title: string, badges: string[], streak: number },
 *   stats: { bmi: number, mood: number, energy: number, stress: number, sleep: number, health: number },
 * }} props
 */
export default function CharacterCard({ profile, stats }) {
  const {
    level = 1,
    exp = 0,
    nextLevelExp = 100,
    title = "건강 새싹",
    badges = [],
    streak = 0,
  } = profile ?? {};

  const {
    bmi = 23,
    mood = 60,
    energy = 60,
    stress = 40,
    sleep = 70,
    health = 70,
  } = stats ?? {};

  const [showLevelUp, setShowLevelUp] = useState(false);
  const prevLevel = useRef(level);

  // 레벨 변화 감지 → 애니메이션 트리거
  useEffect(() => {
    if (level > prevLevel.current) {
      setShowLevelUp(true);
      const timer = setTimeout(() => setShowLevelUp(false), 1500);
      prevLevel.current = level;
      return () => clearTimeout(timer);
    }
    prevLevel.current = level;
  }, [level]);

  const expPercent = nextLevelExp > 0 ? Math.min((exp / nextLevelExp) * 100, 100) : 0;

  // BMI는 0-100 스케일이 아니므로 정규화 (15-40 → 0-100, 23이 최적)
  const bmiScore = Math.max(0, 100 - Math.abs(bmi - 23) * 8);

  return (
    <>
      {/* 레벨업 CSS 애니메이션 */}
      <style>{`
        @keyframes level-up-bounce {
          0%   { transform: scale(1); }
          30%  { transform: scale(1.15); }
          50%  { transform: scale(0.95); }
          70%  { transform: scale(1.05); }
          100% { transform: scale(1); }
        }
        @keyframes sparkle-float {
          0%   { opacity: 1; transform: translateY(0) scale(1); }
          100% { opacity: 0; transform: translateY(-40px) scale(0.3); }
        }
        @keyframes glow-pulse {
          0%, 100% { box-shadow: 0 0 8px rgba(56,189,248,0.4); }
          50%      { box-shadow: 0 0 20px rgba(56,189,248,0.8); }
        }
      `}</style>

      <div
        className="relative w-72 rounded-2xl border border-gray-700/60 bg-gray-900 p-5 shadow-xl"
        style={showLevelUp ? { animation: "level-up-bounce 0.6s ease-out" } : undefined}
      >
        {/* ── 레벨업 스파클 ── */}
        {showLevelUp && (
          <div className="pointer-events-none absolute inset-0 overflow-hidden rounded-2xl">
            <Sparkle delay={0} x={20} y={10} />
            <Sparkle delay={0.1} x={75} y={15} />
            <Sparkle delay={0.2} x={50} y={5} />
            <Sparkle delay={0.15} x={30} y={25} />
            <Sparkle delay={0.25} x={80} y={30} />
            <Sparkle delay={0.05} x={10} y={20} />
          </div>
        )}

        {/* ── 아바타 ── */}
        <div className="flex justify-center">
          <AvatarBody
            bmi={bmi}
            mood={mood}
            energy={energy}
            stress={stress}
            sleep={sleep}
            health={health}
            size={120}
          />
        </div>

        {/* ── 레벨 배지 ── */}
        <div className="mt-3 flex justify-center">
          <div
            className="flex h-12 w-12 items-center justify-center rounded-full border-2 border-cyan-400 bg-gray-800 text-lg font-bold text-cyan-300"
            style={{ animation: "glow-pulse 2s ease-in-out infinite" }}
          >
            {level}
          </div>
        </div>

        {/* ── 타이틀 ── */}
        <p className="mt-2 text-center text-sm font-semibold text-gray-300">
          {title}
        </p>

        {/* ── EXP 바 ── */}
        <div className="mt-3">
          <div className="flex items-center justify-between text-xs text-gray-500">
            <span>EXP</span>
            <span>
              {exp} / {nextLevelExp}
            </span>
          </div>
          <div className="mt-1 h-2.5 w-full overflow-hidden rounded-full bg-gray-800">
            <div
              className="h-full rounded-full transition-all duration-500"
              style={{
                width: `${expPercent}%`,
                background: "linear-gradient(90deg, #22d3ee, #3b82f6)",
              }}
            />
          </div>
        </div>

        {/* ── 스트릭 ── */}
        {streak > 0 && (
          <div className="mt-2 flex items-center justify-center gap-1.5 text-sm">
            <Flame className="h-4 w-4 text-orange-400" />
            <span className="font-medium text-orange-300">
              {streak}일 연속
            </span>
          </div>
        )}

        {/* ── 6 스탯 바 ── */}
        <div className="mt-4 space-y-2">
          {STAT_CONFIG.map(({ key, label, icon: Icon, format, max }) => {
            const raw = key === "bmi" ? bmi : (stats?.[key] ?? 0);
            const score = key === "bmi" ? bmiScore : raw;
            const color = key === "stress"
              ? statColor(100 - score) // 스트레스는 낮을수록 좋음
              : statColor(score);

            return (
              <div key={key} className="flex items-center gap-2">
                <Icon className="h-3.5 w-3.5 shrink-0 text-gray-500" />
                <span className="w-14 shrink-0 text-xs text-gray-400">
                  {label}
                </span>
                <div className="h-2 flex-1 overflow-hidden rounded-full bg-gray-800">
                  <div
                    className="h-full rounded-full transition-all duration-500"
                    style={{
                      width: `${Math.min((score / 100) * 100, 100)}%`,
                      backgroundColor: color,
                    }}
                  />
                </div>
                <span className="w-8 text-right text-xs font-medium text-gray-300">
                  {format(raw)}
                </span>
              </div>
            );
          })}
        </div>

        {/* ── 뱃지 행 ── */}
        {badges.length > 0 && (
          <div className="mt-4 flex flex-wrap justify-center gap-2">
            {badges.map((badge, i) => (
              <div
                key={i}
                className="flex h-8 w-8 items-center justify-center rounded-full border border-gray-600 bg-gray-800 text-sm"
                title={badge}
              >
                {badge}
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  );
}
