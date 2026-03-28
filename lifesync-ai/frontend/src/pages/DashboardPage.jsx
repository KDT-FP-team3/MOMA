/**
 * DashboardPage — 메인 대시보드 허브
 *
 * 데이터 흐름:
 *   마운트 → GET /api/dashboard/default → gauges + domainSummary 초기화
 *   채팅 입력 → QuickChat → /api/query → cascade_effects → gauges 업데이트
 *   WebSocket → gauge_update 메시지 → 실시간 반영
 */
import { useEffect, useMemo } from "react";
import Layout from "../components/layout/Layout";
import GaugePanel from "../components/dashboard/GaugePanel";
import QuickChat from "../components/dashboard/QuickChat";
import CascadeAlert from "../components/cascade/CascadeAlert";
import { useAppState } from "../context/AppStateContext";
import { Activity, TrendingUp, Utensils, Dumbbell, Heart, Palette } from "lucide-react";
import axios from "axios";

const DOMAIN_ICONS = {
  food: { icon: Utensils, label: "요리", color: "text-orange-400", bg: "bg-orange-500/10" },
  exercise: { icon: Dumbbell, label: "운동", color: "text-blue-400", bg: "bg-blue-500/10" },
  health: { icon: Heart, label: "건강", color: "text-green-400", bg: "bg-green-500/10" },
  hobby: { icon: Palette, label: "취미", color: "text-purple-400", bg: "bg-purple-500/10" },
};

export default function DashboardPage() {
  const { state, updateState } = useAppState();

  // 마운트 시 대시보드 데이터 로드
  useEffect(() => {
    axios.get(`/api/dashboard/${state.userId || "default"}`)
      .then((res) => {
        if (res.data.gauges) updateState("gauges", res.data.gauges);
        if (res.data.domain_summary) updateState("domainSummary", res.data.domain_summary);
      })
      .catch(() => { /* 오프라인이면 기존 상태 유지 */ });
  }, []);

  // 4개 도메인 요약 카드 데이터
  const domainCards = useMemo(() => {
    const ds = state.domainSummary || {};
    return Object.entries(DOMAIN_ICONS).map(([key, cfg]) => ({
      ...cfg,
      value: ds[key]?.value || "-",
      sub: ds[key]?.sub || "",
    }));
  }, [state.domainSummary]);

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

        {/* 도메인 요약 카드 — API 데이터 연동 */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {domainCards.map(({ icon: Icon, label, value, sub, color, bg }) => (
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
