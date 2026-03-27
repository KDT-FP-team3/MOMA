/**
 * SimulationAnimation — 3D 마법 애니메이션 효과
 *
 * 시뮬레이션 실행 시: 카드 3D 회전 → 마법진 이펙트 → 결과 출현
 * CSS 3D transform + perspective (외부 라이브러리 없음)
 */
import { useState, useEffect } from "react";

const PARTICLES = Array.from({ length: 12 }, (_, i) => ({
  id: i,
  angle: (i / 12) * 360,
  delay: i * 0.06,
  size: 4 + Math.random() * 6,
}));

export default function SimulationAnimation({ active, onComplete, children }) {
  const [phase, setPhase] = useState("idle"); // idle | spinning | magic | reveal

  useEffect(() => {
    if (!active) {
      setPhase("idle");
      return;
    }

    setPhase("spinning");
    const t1 = setTimeout(() => setPhase("magic"), 800);
    const t2 = setTimeout(() => setPhase("reveal"), 2000);
    const t3 = setTimeout(() => {
      setPhase("idle");
      onComplete?.();
    }, 2800);

    return () => { clearTimeout(t1); clearTimeout(t2); clearTimeout(t3); };
  }, [active, onComplete]);

  if (phase === "idle") return <>{children}</>;

  return (
    <div className="relative w-full min-h-[300px] flex items-center justify-center overflow-hidden">
      {/* 배경 마법진 */}
      {(phase === "magic" || phase === "reveal") && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          {/* 외부 원 */}
          <div
            className="absolute w-64 h-64 rounded-full border-2 border-cyan-400/40"
            style={{
              animation: "spin 3s linear infinite",
              boxShadow: "0 0 30px rgba(6,182,212,0.3), inset 0 0 30px rgba(6,182,212,0.1)",
            }}
          />
          {/* 내부 원 */}
          <div
            className="absolute w-40 h-40 rounded-full border border-blue-400/30"
            style={{ animation: "spin 2s linear infinite reverse" }}
          />
          {/* 파티클 */}
          {PARTICLES.map((p) => (
            <div
              key={p.id}
              className="absolute rounded-full bg-cyan-400"
              style={{
                width: p.size,
                height: p.size,
                opacity: 0,
                animation: `particle-fly 1.2s ease-out ${p.delay}s forwards`,
                transform: `rotate(${p.angle}deg) translateY(-80px)`,
              }}
            />
          ))}
          {/* 중앙 글로우 */}
          <div
            className="absolute w-20 h-20 rounded-full"
            style={{
              background: "radial-gradient(circle, rgba(6,182,212,0.6) 0%, transparent 70%)",
              animation: "pulse-glow 1s ease-in-out infinite",
            }}
          />
        </div>
      )}

      {/* 3D 회전 카드 */}
      <div
        className="relative z-10 w-full"
        style={{
          perspective: "800px",
          transformStyle: "preserve-3d",
        }}
      >
        <div
          style={{
            transform:
              phase === "spinning"
                ? "perspective(800px) rotateY(180deg) scale(0.9)"
                : phase === "magic"
                ? "perspective(800px) rotateY(360deg) scale(0.95)"
                : "perspective(800px) rotateY(0deg) scale(1)",
            transition: "transform 0.8s cubic-bezier(0.4, 0, 0.2, 1)",
            opacity: phase === "reveal" ? 1 : phase === "magic" ? 0.7 : 0.5,
          }}
        >
          {children}
        </div>
      </div>

      {/* 텍스트 */}
      {phase === "magic" && (
        <div className="absolute bottom-4 left-0 right-0 text-center z-20">
          <p className="text-cyan-400 text-sm font-semibold animate-pulse">
            건강 데이터를 분석하고 있습니다...
          </p>
        </div>
      )}

      {/* 인라인 CSS 애니메이션 */}
      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
        @keyframes particle-fly {
          0% { opacity: 0; transform: rotate(var(--angle, 0deg)) translateY(0); }
          30% { opacity: 1; }
          100% { opacity: 0; transform: rotate(var(--angle, 0deg)) translateY(-120px); }
        }
        @keyframes pulse-glow {
          0%, 100% { transform: scale(1); opacity: 0.6; }
          50% { transform: scale(1.3); opacity: 1; }
        }
      `}</style>
    </div>
  );
}
