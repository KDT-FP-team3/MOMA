/**
 * GaugePanel — 6개 계기판 (Tailwind 리팩토링)
 */
import { useState, useEffect, useCallback } from "react";
import { RadialBarChart, RadialBar, ResponsiveContainer } from "recharts";
import { useAppState } from "../../context/AppStateContext";

const GAUGE_CONFIG = [
  { key: "reactive_oxygen", label: "활성산소", unit: "/100", color: "#ff6b6b", statusKey: "caution" },
  { key: "blood_purity", label: "혈액 청정도", unit: "/100", color: "#51cf66", statusKey: "good" },
  { key: "hair_loss_risk", label: "탈모 위험도", unit: "%", color: "#ffd43b", statusKey: "low", invert: true },
  { key: "sleep_score", label: "수면 점수", unit: "/100", color: "#748ffc", statusKey: "normal" },
  { key: "stress_level", label: "스트레스", unit: "/100", color: "#ff922b", statusKey: "normal", invert: true },
  { key: "weekly_achievement", label: "주간 달성률", unit: "%", color: "#20c997", statusKey: "progress" },
];

function getStatus(value, invert) {
  const v = invert ? 100 - value : value;
  if (v >= 80) return { text: "우수", cls: "bg-green-600" };
  if (v >= 60) return { text: "양호", cls: "bg-green-700" };
  if (v >= 40) return { text: "보통", cls: "bg-yellow-600" };
  if (v >= 20) return { text: "주의", cls: "bg-orange-600" };
  return { text: "위험", cls: "bg-red-600" };
}

export default function GaugePanel() {
  const { state, updateState } = useAppState();

  // 전역 상태의 gauges를 로컬에서도 사용 (WebSocket 업데이트 반영)
  const [gauges, setGauges] = useState(state.gauges || {
    reactive_oxygen: 62, blood_purity: 78, hair_loss_risk: 23,
    sleep_score: 71, stress_level: 45, weekly_achievement: 67,
  });

  // 전역 상태 변경 시 로컬에 반영
  useEffect(() => {
    if (state.gauges) setGauges((prev) => ({ ...prev, ...state.gauges }));
  }, [state.gauges]);

  const [ws, setWs] = useState(null);

  const connectWs = useCallback(() => {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host;
    const socket = new WebSocket(`${protocol}//${host}/ws`);

    socket.onopen = () => {
      socket.send(JSON.stringify({ type: "subscribe", data: { user_id: "default" } }));
    };
    socket.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === "gauge_update" && msg.data) {
          // 로컬 + 전역 모두 업데이트
          setGauges((prev) => ({ ...prev, ...msg.data }));
          updateState("gauges", (prev) => ({ ...prev, ...msg.data }));
        }
      } catch { /* ignore */ }
    };
    socket.onclose = () => setTimeout(connectWs, 3000);
    setWs(socket);
  }, []);

  useEffect(() => {
    connectWs();
    return () => ws?.close();
  }, []);

  return (
    <div className="bg-gray-800 rounded-xl p-4 md:p-6 border border-gray-700">
      <h2 className="text-sm font-semibold text-gray-400 mb-4">건강 계기판</h2>
      <div className="grid grid-cols-3 md:grid-cols-6 gap-3 md:gap-4">
        {GAUGE_CONFIG.map(({ key, label, unit, color, invert }) => {
          const value = Math.round(gauges[key] || 0);
          const status = getStatus(value, invert);
          const data = [{ value, fill: color }];

          return (
            <div key={key} className="flex flex-col items-center">
              <div className="relative w-24 h-24 md:w-28 md:h-28">
                <ResponsiveContainer width="100%" height="100%">
                  <RadialBarChart
                    innerRadius="70%"
                    outerRadius="100%"
                    data={data}
                    startAngle={210}
                    endAngle={-30}
                  >
                    <RadialBar
                      dataKey="value"
                      cornerRadius={6}
                      background={{ fill: "#2d3748" }}
                    />
                  </RadialBarChart>
                </ResponsiveContainer>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className="text-xl md:text-2xl font-bold" style={{ color }}>
                    {value}
                  </span>
                  <span className="text-[10px] text-gray-500">{unit}</span>
                </div>
              </div>
              <span className="text-xs text-gray-400 mt-1">{label}</span>
              <span className={`text-[10px] px-1.5 py-0.5 rounded-full text-white mt-1 ${status.cls}`}>
                {status.text}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
