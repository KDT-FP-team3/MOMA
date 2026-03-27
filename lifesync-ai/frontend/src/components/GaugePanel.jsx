/**
 * GaugePanel — 6개 계기판 컴포넌트
 *
 * 6개 지수: 활성산소, 혈액청정도, 탈모위험도, 수면점수, 스트레스, 주간달성률
 * Recharts RadialBarChart 사용, WebSocket으로 실시간 데이터 수신
 *
 * @returns {JSX.Element}
 */
import { useState, useEffect, useRef } from "react";
import { RadialBarChart, RadialBar, Tooltip } from "recharts";

/** @type {{ name: string, key: string, fill: string }[]} */
const GAUGE_CONFIG = [
  { name: "활성산소", key: "reactive_oxygen", fill: "#ff6b6b" },
  { name: "혈액청정도", key: "blood_purity", fill: "#51cf66" },
  { name: "탈모위험도", key: "hair_loss_risk", fill: "#ffd43b" },
  { name: "수면점수", key: "sleep_score", fill: "#748ffc" },
  { name: "스트레스", key: "stress_level", fill: "#ff922b" },
  { name: "주간달성률", key: "weekly_achievement", fill: "#20c997" },
];

/** @type {Record<string, number>} */
const DEFAULT_VALUES = {
  reactive_oxygen: 0,
  blood_purity: 0,
  hair_loss_risk: 0,
  sleep_score: 0,
  stress_level: 0,
  weekly_achievement: 0,
};

export default function GaugePanel() {
  const [gaugeData, setGaugeData] = useState(DEFAULT_VALUES);
  const wsRef = useRef(null);

  useEffect(() => {
    // WebSocket 연결 및 데이터 수신
    const wsUrl =
      (window.location.protocol === "https:" ? "wss://" : "ws://") +
      window.location.host +
      "/ws";

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        ws.send(
          JSON.stringify({ type: "subscribe", data: { channel: "gauge" } })
        );
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          if (message.type === "gauge_update" && message.data) {
            setGaugeData((prev) => ({ ...prev, ...message.data }));
          }
        } catch {
          // JSON 파싱 실패 무시
        }
      };

      ws.onerror = (error) => {
        console.error("GaugePanel WebSocket error:", error);
      };
    } catch {
      console.warn("WebSocket 연결 실패 — 오프라인 모드");
    }

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  // RadialBarChart용 데이터 변환
  const chartData = GAUGE_CONFIG.map((gauge) => ({
    name: gauge.name,
    value: gaugeData[gauge.key] || 0,
    fill: gauge.fill,
  }));

  return (
    <div className="gauge-panel">
      <h2>Dashboard Gauges</h2>
      <div style={{ display: "flex", flexWrap: "wrap", gap: "16px" }}>
        {chartData.map((item) => (
          <div key={item.name} style={{ textAlign: "center" }}>
            <RadialBarChart
              width={160}
              height={160}
              cx="50%"
              cy="50%"
              innerRadius="60%"
              outerRadius="90%"
              barSize={12}
              data={[item]}
              startAngle={180}
              endAngle={0}
            >
              <RadialBar
                dataKey="value"
                cornerRadius={6}
                background={{ fill: "#eee" }}
              />
              <Tooltip />
            </RadialBarChart>
            <p style={{ margin: 0, fontSize: "14px", fontWeight: "bold" }}>
              {item.name}
            </p>
            <p style={{ margin: 0, fontSize: "12px", color: "#666" }}>
              {item.value}%
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
