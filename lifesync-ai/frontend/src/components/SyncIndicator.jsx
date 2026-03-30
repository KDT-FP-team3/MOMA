/**
 * SyncIndicator — 데이터 동기화 상태 표시 컴포넌트
 *
 * 상태:
 *   syncing  → 🔵 파란 깜빡임 (서버와 동기화 중)
 *   synced   → 🟢 녹색 점등 (동기화 완료, 최신 상태)
 *   offline  → 🟡 노란 점등 (오프라인, 로컬 데이터 사용)
 *   error    → 🔴 빨간 점등 (동기화 실패)
 *
 * 사용:
 *   <SyncIndicator />
 *   상단 네비게이션 바에 배치하여 항상 표시
 */
import { useState, useEffect, useCallback, useRef } from "react";
import { useAppState } from "../context/AppStateContext";
import axios from "axios";

const API_BASE = import.meta.env.VITE_API_BASE || "";

// 동기화 상태 설정
const SYNC_STATES = {
  syncing: { color: "#3b82f6", label: "동기화 중", blink: true },
  synced:  { color: "#10b981", label: "최신 상태", blink: false },
  offline: { color: "#f59e0b", label: "오프라인",  blink: false },
  error:   { color: "#ef4444", label: "동기화 실패", blink: false },
};

// 동기화 주기 (밀리초)
const SYNC_INTERVAL = 30_000; // 30초마다 자동 동기화

export default function SyncIndicator() {
  const { state, updateState } = useAppState();
  const [syncStatus, setSyncStatus] = useState("offline");
  const [showTooltip, setShowTooltip] = useState(false);
  const [lastSyncTime, setLastSyncTime] = useState(null);
  const syncingRef = useRef(false);

  // 온라인/오프라인 감지
  useEffect(() => {
    const onOnline = () => {
      if (syncStatus === "offline") syncNow();
    };
    const onOffline = () => setSyncStatus("offline");

    window.addEventListener("online", onOnline);
    window.addEventListener("offline", onOffline);

    // 초기 상태
    if (!navigator.onLine) setSyncStatus("offline");

    return () => {
      window.removeEventListener("online", onOnline);
      window.removeEventListener("offline", onOffline);
    };
  }, [syncStatus]);

  // 서버와 동기화
  const syncNow = useCallback(async () => {
    if (syncingRef.current) return;
    if (!navigator.onLine) {
      setSyncStatus("offline");
      return;
    }

    const userId = state.userId || "default";
    if (userId === "default" && !state.authUser) {
      // 로그인 안 한 상태 → 동기화 불필요
      setSyncStatus("synced");
      return;
    }

    syncingRef.current = true;
    setSyncStatus("syncing");

    try {
      // 1. 서버에서 최신 데이터 가져오기
      const res = await axios.get(`${API_BASE}/api/dashboard/${userId}`, {
        timeout: 10000,
      });

      // 2. 로컬 상태 업데이트
      if (res.data.gauges) {
        updateState("gauges", res.data.gauges);
      }
      if (res.data.domain_summary) {
        updateState("domainSummary", res.data.domain_summary);
      }

      // 3. 로컬 변경사항이 있으면 서버에 업로드
      const localState = state.simulatorState;
      if (localState && localState.started) {
        try {
          await axios.put(`${API_BASE}/api/state/${userId}`, {
            simulator_state: localState,
          }, { timeout: 5000 });
        } catch {
          // 업로드 실패해도 다운로드는 성공
        }
      }

      setSyncStatus("synced");
      setLastSyncTime(new Date());
    } catch (err) {
      if (!navigator.onLine) {
        setSyncStatus("offline");
      } else {
        setSyncStatus("error");
      }
    } finally {
      syncingRef.current = false;
    }
  }, [state.userId, state.authUser, state.simulatorState, updateState]);

  // 자동 동기화 (30초 간격)
  useEffect(() => {
    if (!state.authUser) return; // 로그인 안 하면 동기화 안 함

    // 로그인 직후 즉시 1회 동기화
    syncNow();

    const timer = setInterval(syncNow, SYNC_INTERVAL);
    return () => clearInterval(timer);
  }, [state.authUser, syncNow]);

  // 렌더링
  const config = SYNC_STATES[syncStatus] || SYNC_STATES.offline;
  const timeStr = lastSyncTime
    ? `${lastSyncTime.getHours()}:${String(lastSyncTime.getMinutes()).padStart(2, "0")}`
    : "";

  return (
    <div
      className="relative flex items-center gap-1.5 cursor-pointer select-none"
      onClick={() => {
        setShowTooltip(!showTooltip);
        if (syncStatus === "error" || syncStatus === "offline") syncNow();
      }}
      title={config.label}
    >
      {/* 동기화 상태 원형 인디케이터 */}
      <span
        className={`inline-block w-2.5 h-2.5 rounded-full ${config.blink ? "animate-pulse" : ""}`}
        style={{ backgroundColor: config.color, boxShadow: `0 0 6px ${config.color}80` }}
      />

      {/* 툴팁 */}
      {showTooltip && (
        <div className="absolute top-8 right-0 bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-xs whitespace-nowrap z-50 shadow-lg">
          <div className="flex items-center gap-2 mb-1">
            <span
              className={`w-2 h-2 rounded-full ${config.blink ? "animate-pulse" : ""}`}
              style={{ backgroundColor: config.color }}
            />
            <span className="text-white font-medium">{config.label}</span>
          </div>
          {lastSyncTime && (
            <div className="text-gray-400">마지막 동기화: {timeStr}</div>
          )}
          {syncStatus === "error" && (
            <div className="text-red-400 mt-1">탭하여 재시도</div>
          )}
          {syncStatus === "offline" && (
            <div className="text-yellow-400 mt-1">로컬 데이터 사용 중</div>
          )}
        </div>
      )}
    </div>
  );
}
