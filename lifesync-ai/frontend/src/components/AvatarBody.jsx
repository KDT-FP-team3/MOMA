/**
 * AvatarBody — 항상 걸어다니는 임바디AI 로봇 캐릭터
 *
 * Props:
 *   bmi        15~40   체형 (몸통/팔다리 굵기, 걸음 폭)
 *   mood       0~100   기분 (표정)
 *   energy     0~100   활력 (걸음 속도)
 *   stress     0~100   스트레스 (떨림, 땀)
 *   sleep      0~100   수면 (눈 크기)
 *   health     0~100   건강 (색상 톤)
 *   size       기본 180
 *   animate    기본 true
 */
import { useMemo } from "react";

function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); }

function getBodyStage(bmi) {
  if (bmi <= 18.5) return 0;
  if (bmi <= 23)   return 1;
  if (bmi <= 25)   return 2;
  if (bmi <= 30)   return 3;
  return 4;
}

const SKIN_SHADES = {
  healthy: { skin: "#f5d0a9", cheek: "#f4a4a0", shadow: "#e8b88a" },
  tired:   { skin: "#e8c99b", cheek: "#d4908e", shadow: "#d4a878" },
  sick:    { skin: "#ddc09a", cheek: "#c88080", shadow: "#c8a070" },
};

export default function AvatarBody({
  bmi = 23, mood = 60, energy = 60, stress = 40, sleep = 70, health = 70,
  size = 180, animate = true,
}) {
  const p = useMemo(() => {
    const stage = getBodyStage(bmi);

    // Body proportions — 체형에 따라 달라짐
    const headR = 28;
    const bodyW = 18 + stage * 10;
    const bodyH = 42 + stage * 4;
    const armThick = 7 + stage * 1.5;
    const legThick = 8 + stage * 2;
    const legGap = 10 + stage * 3;

    // 걸음 속도 — 활력이 높을수록 빠르게, 비만일수록 느리게
    const walkSpeed = Math.max(0.6, (energy / 100) * 1.2 - stage * 0.1);
    const walkDuration = 1.2 / walkSpeed; // 초

    // 걸음 폭 — 체형이 클수록 좁은 보폭
    const strideLen = Math.max(8, 18 - stage * 2);

    // Skin tone
    const h = clamp(health, 0, 100);
    const shade = h > 60 ? SKIN_SHADES.healthy : h > 30 ? SKIN_SHADES.tired : SKIN_SHADES.sick;

    // Sleep → eye state
    const eyeState = sleep > 60 ? "open" : sleep > 30 ? "half" : "closed";

    // Stress effects
    const sweating = stress > 60;
    const tremor = stress > 75;

    // Mouth
    const m = clamp(mood, 0, 100);
    const mouthCurve = (m - 50) / 50;

    return {
      stage, headR, bodyW, bodyH, armThick, legThick, legGap,
      shade, eyeState, sweating, tremor, mouthCurve, m,
      walkDuration, strideLen,
    };
  }, [bmi, mood, energy, stress, sleep, health]);

  const cx = 90;
  const headY = 38;
  const neckY = headY + p.headR;
  const shoulderY = neckY + 6;
  const bodyEndY = shoulderY + p.bodyH;
  const armY = shoulderY + 6;
  const armLen = 32 + p.stage;
  const legLen = 38;
  const totalH = bodyEndY + legLen + 20;

  const stageLabels = ["저체중", "정상", "과체중", "비만", "고도비만"];
  const stageColors = ["#60a5fa", "#10b981", "#f59e0b", "#f97316", "#ef4444"];

  const wd = p.walkDuration;
  const sl = p.strideLen;
  const armSwing = sl * 0.8;

  return (
    <div className="inline-flex flex-col items-center gap-2">
      <svg
        viewBox={`0 0 180 ${totalH + 4}`}
        width={size}
        height={size * (totalH + 4) / 180}
        style={{ overflow: "visible" }}
      >
        <defs>
          <radialGradient id="bodyShadow">
            <stop offset="60%" stopColor={p.shade.skin} />
            <stop offset="100%" stopColor={p.shade.shadow} />
          </radialGradient>
          <radialGradient id="blushL" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor={p.shade.cheek} stopOpacity="0.5" />
            <stop offset="100%" stopColor={p.shade.cheek} stopOpacity="0" />
          </radialGradient>
          <radialGradient id="blushR" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor={p.shade.cheek} stopOpacity="0.5" />
            <stop offset="100%" stopColor={p.shade.cheek} stopOpacity="0" />
          </radialGradient>
          <style>{`
            @keyframes walkBounce {
              0%, 100% { transform: translateY(0); }
              25% { transform: translateY(-3px); }
              75% { transform: translateY(-3px); }
            }
            @keyframes leftLegWalk {
              0%   { transform: rotate(${sl}deg); }
              50%  { transform: rotate(-${sl}deg); }
              100% { transform: rotate(${sl}deg); }
            }
            @keyframes rightLegWalk {
              0%   { transform: rotate(-${sl}deg); }
              50%  { transform: rotate(${sl}deg); }
              100% { transform: rotate(-${sl}deg); }
            }
            @keyframes leftArmSwing {
              0%   { transform: rotate(-${armSwing}deg); }
              50%  { transform: rotate(${armSwing}deg); }
              100% { transform: rotate(-${armSwing}deg); }
            }
            @keyframes rightArmSwing {
              0%   { transform: rotate(${armSwing}deg); }
              50%  { transform: rotate(-${armSwing}deg); }
              100% { transform: rotate(${armSwing}deg); }
            }
            @keyframes floaty {
              0%,100% { transform: translateY(0); }
              50% { transform: translateY(-3px); }
            }
          `}</style>
        </defs>

        {/* 전체 바운스 (걸을 때 살짝 위아래) */}
        <g style={animate ? {
          animation: `walkBounce ${wd}s ease-in-out infinite`,
        } : {}}>

          {/* === BODY (둥근 몸통) === */}
          <rect
            x={cx - p.bodyW / 2}
            y={shoulderY}
            width={p.bodyW}
            height={p.bodyH}
            rx={p.bodyW / 2.5}
            fill="url(#bodyShadow)"
          />
          {p.stage >= 2 && (
            <ellipse
              cx={cx}
              cy={shoulderY + p.bodyH * 0.55}
              rx={p.bodyW / 2 - 3}
              ry={p.bodyH / 2.5}
              fill={p.shade.skin}
              opacity={0.5}
            />
          )}

          {/* === NECK === */}
          <rect x={cx - 5} y={neckY - 2} width={10} height={10} rx={4} fill={p.shade.skin} />

          {/* === LEFT ARM (걸을 때 반대로 흔듦) === */}
          <g style={animate ? {
            transformOrigin: `${cx - p.bodyW / 2 + 2}px ${armY}px`,
            animation: `leftArmSwing ${wd}s ease-in-out infinite`,
          } : {}}>
            <line
              x1={cx - p.bodyW / 2 + 2} y1={armY}
              x2={cx - p.bodyW / 2 + 2 - 4} y2={armY + armLen}
              stroke={p.shade.skin} strokeWidth={p.armThick} strokeLinecap="round"
            />
            <circle
              cx={cx - p.bodyW / 2 + 2 - 4}
              cy={armY + armLen}
              r={p.armThick * 0.55}
              fill={p.shade.skin}
            />
          </g>

          {/* === RIGHT ARM === */}
          <g style={animate ? {
            transformOrigin: `${cx + p.bodyW / 2 - 2}px ${armY}px`,
            animation: `rightArmSwing ${wd}s ease-in-out infinite`,
          } : {}}>
            <line
              x1={cx + p.bodyW / 2 - 2} y1={armY}
              x2={cx + p.bodyW / 2 - 2 + 4} y2={armY + armLen}
              stroke={p.shade.skin} strokeWidth={p.armThick} strokeLinecap="round"
            />
            <circle
              cx={cx + p.bodyW / 2 - 2 + 4}
              cy={armY + armLen}
              r={p.armThick * 0.55}
              fill={p.shade.skin}
            />
          </g>

          {/* === LEFT LEG (걷기 애니메이션) === */}
          <g style={animate ? {
            transformOrigin: `${cx - p.legGap / 2}px ${bodyEndY - 2}px`,
            animation: `leftLegWalk ${wd}s ease-in-out infinite`,
          } : {}}>
            <line
              x1={cx - p.legGap / 2} y1={bodyEndY - 2}
              x2={cx - p.legGap / 2} y2={bodyEndY + legLen}
              stroke={p.shade.skin} strokeWidth={p.legThick} strokeLinecap="round"
            />
            <ellipse
              cx={cx - p.legGap / 2}
              cy={bodyEndY + legLen + 2}
              rx={p.legThick * 0.7} ry={4}
              fill={p.shade.shadow}
            />
          </g>

          {/* === RIGHT LEG === */}
          <g style={animate ? {
            transformOrigin: `${cx + p.legGap / 2}px ${bodyEndY - 2}px`,
            animation: `rightLegWalk ${wd}s ease-in-out infinite`,
          } : {}}>
            <line
              x1={cx + p.legGap / 2} y1={bodyEndY - 2}
              x2={cx + p.legGap / 2} y2={bodyEndY + legLen}
              stroke={p.shade.skin} strokeWidth={p.legThick} strokeLinecap="round"
            />
            <ellipse
              cx={cx + p.legGap / 2}
              cy={bodyEndY + legLen + 2}
              rx={p.legThick * 0.7} ry={4}
              fill={p.shade.shadow}
            />
          </g>

          {/* === HEAD === */}
          <circle cx={cx} cy={headY} r={p.headR} fill={p.shade.skin} />

          {/* Hair */}
          <path
            d={`M ${cx - p.headR + 2} ${headY - 4}
                Q ${cx - p.headR} ${headY - p.headR - 4}, ${cx} ${headY - p.headR - 6}
                Q ${cx + p.headR} ${headY - p.headR - 4}, ${cx + p.headR - 2} ${headY - 4}`}
            fill="#3b3029" stroke="none"
          />
          <path
            d={`M ${cx - p.headR + 1} ${headY - 6} Q ${cx - p.headR - 3} ${headY}, ${cx - p.headR + 3} ${headY + 6}`}
            fill="#3b3029" stroke="none"
          />
          <path
            d={`M ${cx + p.headR - 1} ${headY - 6} Q ${cx + p.headR + 3} ${headY}, ${cx + p.headR - 3} ${headY + 6}`}
            fill="#3b3029" stroke="none"
          />

          {/* Cheek blush */}
          <ellipse cx={cx - 14} cy={headY + 8} rx={6} ry={4} fill="url(#blushL)" />
          <ellipse cx={cx + 14} cy={headY + 8} rx={6} ry={4} fill="url(#blushR)" />

          {/* === EYES === */}
          {p.eyeState === "open" ? (
            <>
              <ellipse cx={cx - 9} cy={headY - 2} rx={5} ry={5.5} fill="white" />
              <ellipse cx={cx + 9} cy={headY - 2} rx={5} ry={5.5} fill="white" />
              <circle cx={cx - 9} cy={headY - 1} r={3} fill="#2d1b0e" />
              <circle cx={cx + 9} cy={headY - 1} r={3} fill="#2d1b0e" />
              <circle cx={cx - 10} cy={headY - 3} r={1.2} fill="white" />
              <circle cx={cx + 8} cy={headY - 3} r={1.2} fill="white" />
            </>
          ) : p.eyeState === "half" ? (
            <>
              <ellipse cx={cx - 9} cy={headY - 1} rx={5} ry={3} fill="white" />
              <ellipse cx={cx + 9} cy={headY - 1} rx={5} ry={3} fill="white" />
              <circle cx={cx - 9} cy={headY} r={2.5} fill="#2d1b0e" />
              <circle cx={cx + 9} cy={headY} r={2.5} fill="#2d1b0e" />
              <path d={`M ${cx - 14} ${headY - 3} Q ${cx - 9} ${headY - 4.5}, ${cx - 4} ${headY - 3}`} fill="none" stroke={p.shade.shadow} strokeWidth={1.5} />
              <path d={`M ${cx + 4} ${headY - 3} Q ${cx + 9} ${headY - 4.5}, ${cx + 14} ${headY - 3}`} fill="none" stroke={p.shade.shadow} strokeWidth={1.5} />
            </>
          ) : (
            <>
              <path d={`M ${cx - 13} ${headY - 1} Q ${cx - 9} ${headY + 2}, ${cx - 5} ${headY - 1}`} fill="none" stroke="#2d1b0e" strokeWidth={2} strokeLinecap="round" />
              <path d={`M ${cx + 5} ${headY - 1} Q ${cx + 9} ${headY + 2}, ${cx + 13} ${headY - 1}`} fill="none" stroke="#2d1b0e" strokeWidth={2} strokeLinecap="round" />
            </>
          )}

          {/* Eyebrows (sad) */}
          {p.m < 30 && (
            <>
              <line x1={cx - 13} y1={headY - 10} x2={cx - 5} y2={headY - 8} stroke="#3b3029" strokeWidth={1.8} strokeLinecap="round" />
              <line x1={cx + 5} y1={headY - 8} x2={cx + 13} y2={headY - 10} stroke="#3b3029" strokeWidth={1.8} strokeLinecap="round" />
            </>
          )}

          {/* === MOUTH === */}
          {p.mouthCurve > 0.3 ? (
            <path
              d={`M ${cx - 7} ${headY + 10} Q ${cx} ${headY + 10 + p.mouthCurve * 8}, ${cx + 7} ${headY + 10}`}
              fill="none" stroke="#c2410c" strokeWidth={2} strokeLinecap="round"
            />
          ) : p.mouthCurve > 0 ? (
            <path
              d={`M ${cx - 5} ${headY + 11} Q ${cx} ${headY + 13}, ${cx + 5} ${headY + 11}`}
              fill="none" stroke="#92400e" strokeWidth={1.8} strokeLinecap="round"
            />
          ) : p.mouthCurve > -0.3 ? (
            <line x1={cx - 4} y1={headY + 12} x2={cx + 4} y2={headY + 12}
              stroke="#92400e" strokeWidth={1.8} strokeLinecap="round"
            />
          ) : (
            <path
              d={`M ${cx - 6} ${headY + 14} Q ${cx} ${headY + 14 + p.mouthCurve * 5}, ${cx + 6} ${headY + 14}`}
              fill="none" stroke="#92400e" strokeWidth={2} strokeLinecap="round"
            />
          )}

          {p.m > 85 && (
            <ellipse cx={cx} cy={headY + 13} rx={5} ry={3} fill="#c2410c" opacity={0.3} />
          )}

          {/* === STRESS: 땀방울 === */}
          {p.sweating && (
            <g opacity={0.65}>
              <path
                d={`M ${cx + p.headR + 3} ${headY - 6} Q ${cx + p.headR + 5} ${headY - 1}, ${cx + p.headR + 3} ${headY + 4}`}
                fill="none" stroke="#7dd3fc" strokeWidth={1.8}
              />
              <circle cx={cx + p.headR + 3} cy={headY + 6} r={2.5} fill="#7dd3fc" opacity={0.6} />
            </g>
          )}

          {/* Happy sparkles */}
          {p.m > 80 && (
            <g opacity={0.7} style={{ animation: "floaty 2s ease-in-out infinite" }}>
              <text x={cx - p.headR - 10} y={headY - 14} fontSize={10} className="select-none">*</text>
              <text x={cx + p.headR + 6} y={headY - 16} fontSize={8} className="select-none">*</text>
            </g>
          )}

          {/* Sad cloud */}
          {p.m < 20 && (
            <g opacity={0.4}>
              <ellipse cx={cx} cy={headY - p.headR - 14} rx={16} ry={8} fill="#94a3b8" />
              <ellipse cx={cx - 8} cy={headY - p.headR - 16} rx={8} ry={6} fill="#94a3b8" />
              <ellipse cx={cx + 8} cy={headY - p.headR - 16} rx={8} ry={6} fill="#94a3b8" />
            </g>
          )}

          {/* 걷는 그림자 (발 아래) */}
          <ellipse
            cx={cx}
            cy={bodyEndY + legLen + 8}
            rx={p.legGap + 6}
            ry={3}
            fill="rgba(0,0,0,0.08)"
            style={animate ? {
              animation: `walkBounce ${wd}s ease-in-out infinite`,
              animationDirection: "reverse",
            } : {}}
          />
        </g>
      </svg>

      {/* Stage label */}
      <span
        className="text-xs font-semibold px-3 py-1 rounded-full"
        style={{
          backgroundColor: stageColors[p.stage] + "18",
          color: stageColors[p.stage],
          border: `1px solid ${stageColors[p.stage]}30`,
        }}
      >
        {stageLabels[p.stage]} · BMI {bmi.toFixed(1)}
      </span>
    </div>
  );
}
