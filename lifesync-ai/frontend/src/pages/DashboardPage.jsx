/**
 * DashboardPage — 메인 대시보드 허브
 */
import Layout from "../components/layout/Layout";
import GaugePanel from "../components/dashboard/GaugePanel";
import QuickChat from "../components/dashboard/QuickChat";
import CascadeAlert from "../components/cascade/CascadeAlert";
import { Activity, TrendingUp, Utensils, Dumbbell, Heart, Palette } from "lucide-react";

const DOMAIN_SUMMARY = [
  { icon: Utensils, label: "요리", value: "1,850 kcal", sub: "오늘 섭취", color: "text-orange-400", bg: "bg-orange-500/10" },
  { icon: Dumbbell, label: "운동", value: "45분", sub: "오늘 활동", color: "text-blue-400", bg: "bg-blue-500/10" },
  { icon: Heart, label: "건강", value: "양호", sub: "종합 상태", color: "text-green-400", bg: "bg-green-500/10" },
  { icon: Palette, label: "취미", value: "30분", sub: "기타 연주", color: "text-purple-400", bg: "bg-purple-500/10" },
];

export default function DashboardPage() {
  return (
    <Layout>
      <div className="p-4 md:p-6 space-y-6 max-w-7xl mx-auto">
        {/* 헤더 */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold">대시보드</h1>
            <p className="text-sm text-gray-500 mt-0.5">실시간 건강 모니터링</p>
          </div>
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <Activity size={14} className="text-green-400" />
            <span>실시간 연결</span>
          </div>
        </div>

        {/* 도메인 요약 카드 */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {DOMAIN_SUMMARY.map(({ icon: Icon, label, value, sub, color, bg }) => (
            <div
              key={label}
              className="bg-gray-800 border border-gray-700 rounded-xl p-4 hover:border-gray-600 transition-colors"
            >
              <div className="flex items-center gap-2 mb-2">
                <div className={`w-8 h-8 rounded-lg ${bg} flex items-center justify-center`}>
                  <Icon size={16} className={color} />
                </div>
                <span className="text-xs text-gray-400">{label}</span>
              </div>
              <p className="text-lg font-bold">{value}</p>
              <p className="text-[11px] text-gray-500">{sub}</p>
            </div>
          ))}
        </div>

        {/* 계기판 */}
        <GaugePanel />

        {/* 2열: 채팅 + 연쇄 경고 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <QuickChat />
          <CascadeAlert />
        </div>

        {/* 주간 트렌드 (간략) */}
        <div className="bg-gray-800 rounded-xl border border-gray-700 p-4 md:p-6">
          <div className="flex items-center gap-2 mb-3">
            <TrendingUp size={16} className="text-cyan-400" />
            <h3 className="text-sm font-semibold text-gray-400">이번 주 요약</h3>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
            <div>
              <p className="text-2xl font-bold text-orange-400">12,950</p>
              <p className="text-xs text-gray-500">주간 칼로리 섭취 (kcal)</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-blue-400">4.5</p>
              <p className="text-xs text-gray-500">주간 운동 시간 (h)</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-green-400">7.2</p>
              <p className="text-xs text-gray-500">평균 수면 (h)</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-purple-400">2.5</p>
              <p className="text-xs text-gray-500">취미 활동 (h)</p>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}
