/**
 * RoadmapPage — 12주 로드맵 전용 페이지
 */
import { useState, useEffect } from "react";
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Tooltip } from "recharts";
import axios from "axios";
import Layout from "../components/layout/Layout";

const phaseStyles = {
  "적응기": { color: "bg-blue-500", text: "text-blue-400" },
  "발전기": { color: "bg-orange-500", text: "text-orange-400" },
  "강화기": { color: "bg-purple-500", text: "text-purple-400" },
  "완성기": { color: "bg-cyan-500", text: "text-cyan-400" },
};

const domainColors = {
  exercise: "#60a5fa",
  food: "#fb923c",
  health: "#4ade80",
  hobby: "#c084fc",
};

export default function RoadmapPage() {
  const [roadmap, setRoadmap] = useState([]);
  const [expandedWeek, setExpandedWeek] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const res = await axios.get("/api/roadmap/default");
        setRoadmap(res.data.roadmap || []);
      } catch {
        setRoadmap(fallbackRoadmap());
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  // 주간 진행률 차트 데이터
  const chartData = roadmap.map((w) => ({
    week: `${w.week}주`,
    exercise: Math.round((w.goals?.find((g) => g.domain === "exercise")?.intensity || 0) * 100),
    food: Math.round((w.goals?.find((g) => g.domain === "food")?.intensity || 0) * 100),
    hobby: Math.round((w.goals?.find((g) => g.domain === "hobby")?.intensity || 0) * 100),
  }));

  return (
    <Layout>
      <div className="p-4 md:p-6 space-y-6 max-w-5xl mx-auto">
        <div>
          <h1 className="text-xl font-bold">12주 로드맵</h1>
          <p className="text-sm text-white mt-0.5">
            Top-5 조언 기반 자동 생성된 결과 로드맵
          </p>
        </div>

        {/* 도메인별 진행률 차트 */}
        <div className="bg-gray-800 border border-gray-700 rounded-xl p-5">
          <h3 className="text-sm font-semibold text-white mb-4">주간 도메인별 강도</h3>
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData}>
                <XAxis dataKey="week" tick={{ fill: "#6b7280", fontSize: 11 }} />
                <YAxis tick={{ fill: "#6b7280", fontSize: 11 }} domain={[0, 100]} />
                <Tooltip
                  contentStyle={{ backgroundColor: "#1f2937", border: "1px solid #374151", borderRadius: 8 }}
                  labelStyle={{ color: "#9ca3af" }}
                />
                <Bar dataKey="exercise" fill={domainColors.exercise} radius={[2, 2, 0, 0]} name="운동" />
                <Bar dataKey="food" fill={domainColors.food} radius={[2, 2, 0, 0]} name="식단" />
                <Bar dataKey="health" fill={domainColors.health} radius={[2, 2, 0, 0]} name="건강" />
                <Bar dataKey="hobby" fill={domainColors.hobby} radius={[2, 2, 0, 0]} name="취미" />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="flex gap-4 mt-3 justify-center">
            {[["운동", domainColors.exercise], ["식단", domainColors.food], ["취미", domainColors.hobby]].map(([l, c]) => (
              <div key={l} className="flex items-center gap-1.5 text-xs text-white">
                <span className="w-2.5 h-2.5 rounded-sm" style={{ backgroundColor: c }} />
                {l}
              </div>
            ))}
          </div>
        </div>

        {/* 타임라인 */}
        {loading ? (
          <div className="flex justify-center py-10">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-400" />
          </div>
        ) : (
          <div className="relative">
            <div className="absolute left-5 top-0 bottom-0 w-0.5 bg-gray-700" />

            <div className="space-y-3">
              {roadmap.map((week) => {
                const ps = phaseStyles[week.phase] || phaseStyles["적응기"];
                const isOpen = expandedWeek === week.week;
                const progress = Math.min(100, Math.round((week.week / 12) * 100));

                return (
                  <div key={week.week} className="relative pl-12">
                    <div className={`absolute left-3.5 w-3 h-3 rounded-full ${ps.color} border-2 border-gray-900`} style={{ top: 8 }} />

                    <div
                      className="bg-gray-800 border border-gray-700 rounded-xl p-4 hover:border-gray-600 cursor-pointer transition-all"
                      onClick={() => setExpandedWeek(isOpen ? null : week.week)}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="font-bold">{week.week}주차</span>
                          <span className={`text-[10px] px-2 py-0.5 rounded-full text-white ${ps.color}`}>{week.phase}</span>
                        </div>
                        <span className="text-xs text-white">{progress}%</span>
                      </div>

                      <div className="mt-2 w-full bg-gray-700 rounded-full h-1">
                        <div className={`${ps.color} h-1 rounded-full`} style={{ width: `${progress}%` }} />
                      </div>

                      {isOpen && week.goals && (
                        <div className="mt-3 space-y-2">
                          {week.goals.map((goal, i) => (
                            <div key={i} className="flex items-center gap-3 text-sm bg-gray-700/40 rounded-lg p-2.5">
                              <span className="w-2 h-2 rounded-full" style={{ backgroundColor: domainColors[goal.domain] || "#6b7280" }} />
                              <span style={{ color: domainColors[goal.domain] || "#9ca3af" }}>{goal.name}</span>
                              <span className="text-white text-xs">강도 {Math.round(goal.intensity * 100)}%</span>
                              <span className="text-white text-xs ml-auto">{goal.description}</span>
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
        )}
      </div>
    </Layout>
  );
}

function fallbackRoadmap() {
  const phases = ["적응기", "적응기", "발전기", "발전기", "강화기", "강화기", "강화기", "강화기", "완성기", "완성기", "완성기", "완성기"];
  return phases.map((phase, i) => ({
    week: i + 1,
    phase,
    expected_progress: `${Math.min(100, Math.round(((i + 1) / 12) * 100))}%`,
    goals: [
      { name: "체중 관리", domain: "exercise", intensity: Math.min(1, (i + 1) / 8.4), description: "목표 체중 달성" },
      { name: "식단 개선", domain: "food", intensity: Math.min(1, (i + 1) / 8.4), description: "균형 잡힌 식단" },
      { name: "스트레스 관리", domain: "hobby", intensity: Math.min(1, (i + 1) / 8.4), description: "스트레스 해소" },
    ],
  }));
}
