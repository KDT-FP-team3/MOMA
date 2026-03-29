/**
 * CascadeAlert — 크로스 도메인 연쇄 경고 알림
 * @param {{ alerts?: Array }} props
 * @returns {JSX.Element}
 */
import { useState, useEffect } from "react";

// 예시 연쇄 효과 데이터
const EXAMPLE_CASCADES = [
  {
    id: 1,
    source: "food",
    trigger: "야식 라면 (23시)",
    severity: "high",
    effects: [
      { domain: "health", impact: "수면 질 -35%", delta: -35 },
      { domain: "exercise", impact: "다음날 운동 성과 -20%", delta: -20 },
      { domain: "exercise", impact: "체중 목표 +2일 지연", delta: 2 },
    ],
    reward: -5,
    alternative: "삶은 달걀 + 따뜻한 물 (120kcal)",
  },
  {
    id: 2,
    source: "exercise",
    trigger: "미세먼지 76㎍/㎥ 야외 러닝",
    severity: "medium",
    effects: [
      { domain: "health", impact: "호흡기 위험 증가", delta: -15 },
      { domain: "health", impact: "활성산소 증가", delta: -10 },
    ],
    reward: -4,
    alternative: "실내 HIIT 전환 + YouTube 링크",
  },
  {
    id: 3,
    source: "hobby",
    trigger: "기타 연주 30분",
    severity: "positive",
    effects: [
      { domain: "health", impact: "스트레스 -15%", delta: 15 },
      { domain: "food", impact: "폭식 충동 -40%", delta: 40 },
    ],
    reward: 2,
    alternative: null,
  },
];

const severityConfig = {
  high: { color: "border-red-500", bg: "bg-red-900/20", badge: "bg-red-600", label: "위험" },
  medium: { color: "border-yellow-500", bg: "bg-yellow-900/20", badge: "bg-yellow-600", label: "주의" },
  positive: { color: "border-green-500", bg: "bg-green-900/20", badge: "bg-green-600", label: "보너스" },
};

const domainIcons = {
  food: "🍽️",
  exercise: "🏃",
  health: "❤️",
  hobby: "🎨",
};

export default function CascadeAlert({ alerts = [] }) {
  const [displayAlerts, setDisplayAlerts] = useState(EXAMPLE_CASCADES);
  const [dismissed, setDismissed] = useState(new Set());

  useEffect(() => {
    if (alerts.length > 0) {
      setDisplayAlerts(alerts);
    }
  }, [alerts]);

  const dismiss = (id) => {
    setDismissed((prev) => new Set([...prev, id]));
  };

  const visibleAlerts = displayAlerts.filter((a) => !dismissed.has(a.id));

  return (
    <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
      <h2 className="text-lg font-semibold text-cyan-400 mb-4">
        크로스 도메인 연쇄 경고
      </h2>

      {visibleAlerts.length === 0 ? (
        <p className="text-white text-center py-8">현재 연쇄 경고 없음</p>
      ) : (
        <div className="space-y-4">
          {visibleAlerts.map((alert) => {
            const config = severityConfig[alert.severity] || severityConfig.medium;
            return (
              <div
                key={alert.id}
                className={`border-l-4 ${config.color} ${config.bg} rounded-r-lg p-4`}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <span>{domainIcons[alert.source]}</span>
                      <span className="font-medium">{alert.trigger}</span>
                      <span
                        className={`text-xs px-2 py-0.5 rounded-full ${config.badge} text-white`}
                      >
                        {config.label}
                      </span>
                      <span
                        className={`text-sm font-bold ${
                          alert.reward >= 0 ? "text-green-400" : "text-red-400"
                        }`}
                      >
                        보상 {alert.reward > 0 ? "+" : ""}
                        {alert.reward}
                      </span>
                    </div>

                    {/* 연쇄 효과 체인 */}
                    <div className="space-y-1 ml-6">
                      {alert.effects.map((effect, idx) => (
                        <div
                          key={idx}
                          className="flex items-center gap-2 text-sm"
                        >
                          <span className="text-white">→</span>
                          <span>{domainIcons[effect.domain]}</span>
                          <span
                            className={
                              effect.delta > 0 ? "text-green-400" : "text-red-400"
                            }
                          >
                            {effect.impact}
                          </span>
                        </div>
                      ))}
                    </div>

                    {/* 대안 제시 */}
                    {alert.alternative && (
                      <div className="mt-2 ml-6 text-sm text-cyan-400">
                        💡 대안: {alert.alternative}
                      </div>
                    )}
                  </div>

                  <button
                    onClick={() => dismiss(alert.id)}
                    className="text-white hover:text-white text-lg"
                  >
                    ✕
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
