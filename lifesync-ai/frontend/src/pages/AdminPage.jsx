/**
 * AdminPage — 관리자 통합 대시보드
 *
 * 하나의 화면에서 확인:
 *   - 서버 상태 (버전, 환경)
 *   - API 키 설정 상태 (7개)
 *   - 플러그인 활성/폴백 상태 (11개 슬롯)
 *   - GPU/CPU 디바이스 정보
 *   - 공유 서비스 상태
 */
import { useState, useEffect, useCallback } from "react";
import Layout from "../components/layout/Layout";
import axios from "axios";

const STATUS_COLORS = {
  ok: "bg-emerald-500",
  warn: "bg-amber-500",
  error: "bg-red-500",
};

function StatusDot({ ok }) {
  return (
    <span
      className={`inline-block w-2.5 h-2.5 rounded-full ${
        ok ? STATUS_COLORS.ok : STATUS_COLORS.error
      }`}
    />
  );
}

function Card({ title, children, icon }) {
  return (
    <div className="bg-gray-800/60 border border-gray-700 rounded-xl p-5">
      <h3 className="text-base font-bold text-white mb-3 flex items-center gap-2">
        <span className="text-lg">{icon}</span>
        {title}
      </h3>
      {children}
    </div>
  );
}

export default function AdminPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastRefresh, setLastRefresh] = useState(null);

  const fetchStatus = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await axios.get("/api/admin/status");
      setData(res.data);
      setLastRefresh(new Date().toLocaleTimeString("ko-KR"));
    } catch (err) {
      setError(err.response?.data?.detail || err.message || "서버 연결 실패");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  if (loading && !data) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-96">
          <div className="text-white text-lg">시스템 상태 조회 중...</div>
        </div>
      </Layout>
    );
  }

  if (error && !data) {
    return (
      <Layout>
        <div className="flex flex-col items-center justify-center h-96 gap-4">
          <div className="text-red-400 text-lg">서버 연결 실패</div>
          <div className="text-white text-sm">{error}</div>
          <button
            onClick={fetchStatus}
            className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg text-sm"
          >
            다시 시도
          </button>
        </div>
      </Layout>
    );
  }

  const { server, api_keys, plugins, device, services } = data || {};

  // 플러그인 통계
  const pluginEntries = Object.entries(plugins || {});
  const activePlugins = pluginEntries.filter(([, v]) => v.status === "plugin").length;
  const fallbackPlugins = pluginEntries.filter(([, v]) => v.status === "fallback").length;

  return (
    <Layout>
      <div className="p-4 lg:p-6 space-y-5">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <h1 className="text-2xl font-bold text-white">관리자 패널</h1>
            <p className="text-white text-sm mt-1">
              시스템 전체 상태를 한 눈에 확인합니다
            </p>
          </div>
          <div className="flex items-center gap-3">
            {lastRefresh && (
              <span className="text-xs text-white">
                마지막 갱신: {lastRefresh}
              </span>
            )}
            <button
              onClick={fetchStatus}
              disabled={loading}
              className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white rounded-lg text-sm font-medium transition-colors"
            >
              {loading ? "조회 중..." : "새로고침"}
            </button>
          </div>
        </div>

        {/* Summary Bar */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="bg-gray-800/60 border border-gray-700 rounded-lg p-3 text-center">
            <div className="text-2xl font-bold text-emerald-400">
              {api_keys?.configured || 0}/{api_keys?.total || 0}
            </div>
            <div className="text-xs text-white mt-1">API 키</div>
          </div>
          <div className="bg-gray-800/60 border border-gray-700 rounded-lg p-3 text-center">
            <div className="text-2xl font-bold text-cyan-400">
              {activePlugins}/{pluginEntries.length}
            </div>
            <div className="text-xs text-white mt-1">플러그인 활성</div>
          </div>
          <div className="bg-gray-800/60 border border-gray-700 rounded-lg p-3 text-center">
            <div className="text-2xl font-bold text-purple-400">
              {device?.device === "cuda" ? "GPU" : "CPU"}
            </div>
            <div className="text-xs text-white mt-1">디바이스</div>
          </div>
          <div className="bg-gray-800/60 border border-gray-700 rounded-lg p-3 text-center">
            <div className="text-2xl font-bold text-amber-400">
              {server?.version || "?"}
            </div>
            <div className="text-xs text-white mt-1">서버 버전</div>
          </div>
        </div>

        {/* Cards Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          {/* Server Info */}
          <Card title="서버 상태" icon="">
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-white">상태</span>
                <span className="text-emerald-400 font-medium">{server?.status}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-white">버전</span>
                <span className="text-white">{server?.version}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-white">환경</span>
                <span className={`font-medium ${server?.env === "production" ? "text-red-400" : "text-cyan-400"}`}>
                  {server?.env}
                </span>
              </div>
            </div>
          </Card>

          {/* API Keys */}
          <Card title="API 키 상태" icon="">
            <div className="space-y-1.5 text-sm">
              {Object.entries(api_keys?.details || {}).map(([key, ok]) => (
                <div key={key} className="flex items-center justify-between">
                  <span className="text-white font-mono text-xs">{key}</span>
                  <span className="flex items-center gap-1.5">
                    <StatusDot ok={ok} />
                    <span className={ok ? "text-emerald-400" : "text-red-400"}>
                      {ok ? "설정됨" : "미설정"}
                    </span>
                  </span>
                </div>
              ))}
            </div>
          </Card>

          {/* Plugins */}
          <Card title={`플러그인 (${activePlugins} 활성 / ${fallbackPlugins} 폴백)`} icon="">
            <div className="space-y-1.5 text-sm">
              {pluginEntries.map(([slot, info]) => (
                <div key={slot} className="flex items-center justify-between">
                  <span className="text-white font-mono text-xs">{slot}</span>
                  <span className="flex items-center gap-1.5">
                    <StatusDot ok={info.status === "plugin"} />
                    <span
                      className={
                        info.status === "plugin"
                          ? "text-emerald-400"
                          : "text-amber-400"
                      }
                    >
                      {info.status === "plugin" ? info.class : `폴백 (${info.class})`}
                    </span>
                  </span>
                </div>
              ))}
            </div>
          </Card>

          {/* Device */}
          <Card title="디바이스 정보" icon="">
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-white">디바이스</span>
                <span className={`font-bold ${device?.device === "cuda" ? "text-emerald-400" : "text-white"}`}>
                  {device?.device?.toUpperCase()}
                </span>
              </div>
              {device?.gpu_name && (
                <div className="flex justify-between">
                  <span className="text-white">GPU</span>
                  <span className="text-white">{device.gpu_name}</span>
                </div>
              )}
              {device?.vram_gb > 0 && (
                <div className="flex justify-between">
                  <span className="text-white">VRAM</span>
                  <span className="text-white">{device.vram_gb} GB</span>
                </div>
              )}
              <div className="flex justify-between">
                <span className="text-white">PyTorch</span>
                <span className="text-white">{device?.torch_version || "미설치"}</span>
              </div>
              {device?.cuda_version && (
                <div className="flex justify-between">
                  <span className="text-white">CUDA</span>
                  <span className="text-white">{device.cuda_version}</span>
                </div>
              )}
            </div>
          </Card>

          {/* Services */}
          <Card title="공유 서비스" icon="">
            <div className="space-y-1.5 text-sm">
              {Object.entries(services || {}).map(([name, ok]) => (
                <div key={name} className="flex items-center justify-between">
                  <span className="text-white">{name}</span>
                  <span className="flex items-center gap-1.5">
                    <StatusDot ok={ok} />
                    <span className={ok ? "text-emerald-400" : "text-red-400"}>
                      {ok ? "활성" : "비활성"}
                    </span>
                  </span>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </Layout>
  );
}
