/**
 * CascadeAlert — 크로스 도메인 연쇄 경고 (실시간)
 */
import { useState, useEffect } from "react";
import { AlertTriangle, CheckCircle, X, ChevronDown, ChevronUp } from "lucide-react";

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
    trigger: "미세먼지 76ug/m3 야외 러닝",
    severity: "medium",
    effects: [
      { domain: "health", impact: "호흡기 위험 증가", delta: -15 },
      { domain: "health", impact: "활성산소 증가", delta: -10 },
    ],
    reward: -4,
    alternative: "실내 HIIT 전환",
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

const severityStyles = {
  high: { border: "border-l-red-500", icon: AlertTriangle, iconColor: "text-red-400", badge: "bg-red-600", label: "위험" },
  medium: { border: "border-l-yellow-500", icon: AlertTriangle, iconColor: "text-yellow-400", badge: "bg-yellow-600", label: "주의" },
  positive: { border: "border-l-green-500", icon: CheckCircle, iconColor: "text-green-400", badge: "bg-green-600", label: "보너스" },
};

const domainLabels = { food: "[요리]", exercise: "[운동]", health: "[건강]", hobby: "[취미]" };

export default function CascadeAlert({ alerts: propAlerts }) {
  const [alerts, setAlerts] = useState(EXAMPLE_CASCADES);
  const [dismissed, setDismissed] = useState(new Set());
  const [expanded, setExpanded] = useState(new Set([1]));

  useEffect(() => {
    if (propAlerts?.length > 0) setAlerts(propAlerts);
  }, [propAlerts]);

  const toggle = (id) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const visible = alerts.filter((a) => !dismissed.has(a.id));

  return (
    <div className="bg-gray-800 rounded-xl border border-gray-700 flex flex-col h-[420px]">
      <div className="px-4 py-3 border-b border-gray-700 flex items-center justify-between">
        <h3 className="font-semibold text-sm text-cyan-400">연쇄 경고</h3>
        {visible.length > 0 && (
          <span className="text-[10px] bg-red-600 text-white px-1.5 py-0.5 rounded-full">
            {visible.length}
          </span>
        )}
      </div>

      <div className="flex-1 overflow-y-auto px-3 py-3 space-y-2">
        {visible.length === 0 ? (
          <p className="text-center text-white text-sm py-10">연쇄 경고 없음</p>
        ) : (
          visible.map((alert) => {
            const style = severityStyles[alert.severity] || severityStyles.medium;
            const Icon = style.icon;
            const isOpen = expanded.has(alert.id);

            return (
              <div
                key={alert.id}
                className={`border-l-2 ${style.border} bg-gray-700/30 rounded-r-lg overflow-hidden`}
              >
                {/* Header */}
                <div
                  className="flex items-center gap-2 px-3 py-2.5 cursor-pointer hover:bg-gray-700/50 transition-colors"
                  onClick={() => toggle(alert.id)}
                >
                  <Icon size={14} className={style.iconColor} />
                  <span className="text-sm flex-1">
                    {domainLabels[alert.source]} {alert.trigger}
                  </span>
                  <span className={`text-[10px] px-1.5 py-0.5 rounded-full text-white ${style.badge}`}>
                    {alert.reward > 0 ? "+" : ""}{alert.reward}
                  </span>
                  {isOpen ? <ChevronUp size={14} className="text-white" /> : <ChevronDown size={14} className="text-white" />}
                  <button
                    onClick={(e) => { e.stopPropagation(); setDismissed((p) => new Set([...p, alert.id])); }}
                    className="text-white hover:text-white"
                  >
                    <X size={12} />
                  </button>
                </div>

                {/* Details */}
                {isOpen && (
                  <div className="px-3 pb-3 space-y-1.5">
                    {alert.effects.map((eff, i) => (
                      <div key={i} className="flex items-center gap-2 text-xs ml-5">
                        <span className="text-white">→</span>
                        <span>{domainLabels[eff.domain]}</span>
                        <span className={eff.delta > 0 ? "text-green-400" : "text-red-400"}>
                          {eff.impact}
                        </span>
                      </div>
                    ))}
                    {alert.alternative && (
                      <div className="ml-5 mt-1 text-xs text-cyan-400/80">
                         {alert.alternative}
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
