/**
 * GaugePanel — 6개 건강 계기판 (SVG 게이지 + WebSocket 실시간)
 *
 * SVG circle로 직접 게이지를 그려 정확한 비율 표시.
 * WebSocket 실시간 + 전역 상태 동기화.
 */
import { useEffect } from "react";
import { useAppState } from "../../context/AppStateContext";

const GAUGE_CONFIG = [
  { key: "reactive_oxygen", label: "활성산소",    unit: "/100", color: "#ff6b6b", gradient: "from-red-500/10 to-rose-500/5",    borderHover: "hover:border-red-500/30",    invert: true },
  { key: "blood_purity",    label: "혈액 청정도", unit: "/100", color: "#51cf66", gradient: "from-emerald-500/10 to-green-500/5", borderHover: "hover:border-emerald-500/30" },
  { key: "hair_loss_risk",  label: "탈모 위험도", unit: "%",    color: "#ffd43b", gradient: "from-yellow-500/10 to-amber-500/5",  borderHover: "hover:border-yellow-500/30", invert: true },
  { key: "sleep_score",     label: "수면 점수",   unit: "/100", color: "#748ffc", gradient: "from-indigo-500/10 to-blue-500/5",   borderHover: "hover:border-indigo-500/30" },
  { key: "stress_level",    label: "스트레스",    unit: "/100", color: "#ff922b", gradient: "from-orange-500/10 to-amber-500/5",  borderHover: "hover:border-orange-500/30", invert: true },
  { key: "weekly_achievement", label: "주간 달성률", unit: "%", color: "#20c997", gradient: "from-teal-500/10 to-cyan-500/5",     borderHover: "hover:border-teal-500/30" },
];

function getStatus(value, invert) {
  const v = invert ? 100 - value : value;
  if (v >= 80) return { text: "우수", cls: "bg-emerald-500/20 text-emerald-400" };
  if (v >= 60) return { text: "양호", cls: "bg-green-500/15 text-green-400" };
  if (v >= 40) return { text: "보통", cls: "bg-yellow-500/15 text-yellow-400" };
  if (v >= 20) return { text: "주의", cls: "bg-orange-500/15 text-orange-400" };
  return { text: "위험", cls: "bg-red-500/15 text-red-400" };
}

const DEFAULT_GAUGES = {
  reactive_oxygen: 62, blood_purity: 78, hair_loss_risk: 23,
  sleep_score: 71, stress_level: 45, weekly_achievement: 67,
};

export default function GaugePanel() {
  const { state, updateState } = useAppState();

  // 전역 state만 사용 (이중 state 제거)
  const gauges = state.gauges || DEFAULT_GAUGES;

  useEffect(() => {
    let socket = null;
    let reconnectTimer = null;
    let unmounted = false;
    let retryCount = 0;
    const MAX_RETRIES = 10;
    const VALID_KEYS = new Set(["reactive_oxygen","blood_purity","hair_loss_risk","sleep_score","stress_level","weekly_achievement"]);

    function connect() {
      if (unmounted || retryCount >= MAX_RETRIES) return;
      // Capacitor 앱에서는 VITE_API_BASE로, 웹에서는 현재 호스트로 연결
      const apiBase = import.meta.env.VITE_API_BASE || "";
      let wsUrl;
      if (apiBase) {
        wsUrl = apiBase.replace("https://", "wss://").replace("http://", "ws://") + "/ws";
      } else {
        const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        wsUrl = `${protocol}//${window.location.host}/ws`;
      }
      socket = new WebSocket(wsUrl);

      socket.onopen = () => {
        retryCount = 0; // 연결 성공 시 카운터 리셋
        socket.send(JSON.stringify({ type: "subscribe", data: { user_id: "default" } }));
      };
      socket.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === "gauge_update" && msg.data && typeof msg.data === "object") {
            const safe = {};
            for (const [k, v] of Object.entries(msg.data)) {
              if (VALID_KEYS.has(k) && typeof v === "number") safe[k] = v;
            }
            if (Object.keys(safe).length > 0) {
              updateState("gauges", (prev) => ({ ...prev, ...safe }));
            }
          }
        } catch { /* malformed JSON */ }
      };
      socket.onerror = () => {};
      socket.onclose = () => {
        if (!unmounted) {
          retryCount++;
          // 점진적 대기: 3s → 6s → 12s → ... 최대 30s
          const delay = Math.min(3000 * Math.pow(2, retryCount - 1), 30000);
          reconnectTimer = setTimeout(connect, delay);
        }
      };
    }

    connect();

    return () => {
      unmounted = true;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      if (socket) socket.close();
    };
  }, [updateState]);

  return (
    <div className="bg-gray-800 rounded-2xl p-5 md:p-6 border border-gray-700">
      <div className="flex items-center justify-between mb-5">
        <h2 className="text-sm font-semibold text-white">상세 건강 지표</h2>
        <span className="text-[10px] text-white">실시간 업데이트</span>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3 md:gap-4">
        {GAUGE_CONFIG.map(({ key, label, unit, color, gradient, borderHover, invert }) => {
          const value = Math.round(gauges[key] || 0);
          const status = getStatus(value, invert);
          // SVG 게이지: 240도 범위 (210 ~ -30)
          const R = 36, C = 2 * Math.PI * R;
          const arcLen = C * 240 / 360;
          const filled = arcLen * value / 100;

          return (
            <div
              key={key}
              className={`flex flex-col items-center bg-gradient-to-b ${gradient} rounded-xl p-3 border border-gray-700/30 ${borderHover} transition-all duration-300 group cursor-default`}
            >
              <div className="relative w-20 h-20 md:w-24 md:h-24 group-hover:scale-105 transition-transform duration-300">
                <svg viewBox="0 0 100 100" className="w-full h-full">
                  <circle cx="50" cy="50" r={R} fill="none" stroke="#e5e7eb" strokeWidth="8"
                    strokeDasharray={`${arcLen} ${C}`}
                    strokeLinecap="round" transform="rotate(150 50 50)" opacity="0.25" />
                  <circle cx="50" cy="50" r={R} fill="none" stroke={color} strokeWidth="8"
                    strokeDasharray={`${filled} ${C}`}
                    strokeLinecap="round" transform="rotate(150 50 50)"
                    style={{ transition: "stroke-dasharray 0.5s ease" }} />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className="text-lg md:text-xl font-bold transition-colors duration-500" style={{ color }}>
                    {value}
                  </span>
                  <span className="text-[9px] text-white">{unit}</span>
                </div>
              </div>
              <span className="text-[11px] text-white mt-1.5 font-medium">{label}</span>
              <span className={`text-[9px] px-2 py-0.5 rounded-full font-medium mt-1 ${status.cls}`}>
                {status.text}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
