/**
 * RoadmapTimeline — 12주 로드맵 타임라인
 * @returns {JSX.Element}
 */
import { useState, useEffect } from "react";
import axios from "axios";

const phaseColors = {
  "적응기": "bg-blue-500",
  "발전기": "bg-orange-500",
  "강화기": "bg-purple-500",
  "완성기": "bg-cyan-500",
};

const domainColors = {
  exercise: "text-blue-400",
  food: "text-orange-400",
  health: "text-green-400",
  hobby: "text-purple-400",
};

export default function RoadmapTimeline() {
  const [roadmap, setRoadmap] = useState([]);
  const [expandedWeek, setExpandedWeek] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchRoadmap = async () => {
      try {
        const res = await axios.get("/api/roadmap/default");
        setRoadmap(res.data.roadmap || []);
      } catch {
        // 폴백 데이터
        setRoadmap(generateFallbackRoadmap());
      } finally {
        setLoading(false);
      }
    };
    fetchRoadmap();
  }, []);

  const toggleWeek = (week) => {
    setExpandedWeek(expandedWeek === week ? null : week);
  };

  if (loading) {
    return (
      <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
        <h2 className="text-lg font-semibold text-cyan-400 mb-4">
          12주 로드맵
        </h2>
        <div className="flex justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-400" />
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
      <h2 className="text-lg font-semibold text-cyan-400 mb-4">
        12주 결과 로드맵
      </h2>

      {/* 타임라인 */}
      <div className="relative">
        {/* 중앙 수직선 */}
        <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-gray-700" />

        <div className="space-y-4">
          {roadmap.map((week) => {
            const phaseColor = phaseColors[week.phase] || "bg-gray-500";
            const isExpanded = expandedWeek === week.week;

            return (
              <div key={week.week} className="relative pl-14">
                {/* 타임라인 노드 */}
                <div
                  className={`absolute left-4 w-4 h-4 rounded-full ${phaseColor} border-2 border-gray-800`}
                  style={{ top: "6px" }}
                />

                <div
                  className="bg-gray-700/50 rounded-lg p-4 hover:bg-gray-700 cursor-pointer transition-colors"
                  onClick={() => toggleWeek(week.week)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <span className="font-bold text-lg">{week.week}주차</span>
                      <span
                        className={`text-xs px-2 py-0.5 rounded-full ${phaseColor} text-white`}
                      >
                        {week.phase}
                      </span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-sm text-gray-400">
                        {week.expected_progress}
                      </span>
                      <span className="text-gray-500">
                        {isExpanded ? "▲" : "▼"}
                      </span>
                    </div>
                  </div>

                  {/* 진행률 바 */}
                  <div className="mt-2 w-full bg-gray-600 rounded-full h-1.5">
                    <div
                      className={`${phaseColor} h-1.5 rounded-full transition-all`}
                      style={{
                        width: `${Math.min(100, (week.week / 12) * 100)}%`,
                      }}
                    />
                  </div>

                  {/* 확장 내용 */}
                  {isExpanded && week.goals && (
                    <div className="mt-3 space-y-2">
                      {week.goals.map((goal, idx) => (
                        <div
                          key={idx}
                          className="flex items-center gap-3 text-sm bg-gray-800/50 rounded p-2"
                        >
                          <span
                            className={
                              domainColors[goal.domain] || "text-gray-400"
                            }
                          >
                            {goal.name}
                          </span>
                          <span className="text-gray-500">
                            강도 {(goal.intensity * 100).toFixed(0)}%
                          </span>
                          {goal.description && (
                            <span className="text-gray-500 text-xs">
                              — {goal.description}
                            </span>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function generateFallbackRoadmap() {
  const phases = ["적응기", "적응기", "발전기", "발전기", "강화기", "강화기", "강화기", "강화기", "완성기", "완성기", "완성기", "완성기"];
  return phases.map((phase, i) => ({
    week: i + 1,
    phase,
    expected_progress: `목표 대비 ${Math.min(100, Math.round(((i + 1) / 12) * 100))}% 진행`,
    goals: [
      { name: "체중 관리", domain: "exercise", intensity: Math.min(1, (i + 1) / 8.4), description: "목표 체중 달성" },
      { name: "식단 개선", domain: "food", intensity: Math.min(1, (i + 1) / 8.4), description: "균형 잡힌 식단" },
      { name: "스트레스 관리", domain: "hobby", intensity: Math.min(1, (i + 1) / 8.4), description: "스트레스 해소 루틴" },
    ],
  }));
}
