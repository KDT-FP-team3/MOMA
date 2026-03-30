/**
 * TeamLeaderPage — 전체 관리 대시보드
 *
 * 4개 탭:
 *   1. 아키텍처 진행 현황 (플러그인 + 오케스트레이터 CASCADE 시각화)
 *   2. 팀 활동 & 충돌 감지
 *   3. 백업 & 롤백
 *   4. 보안 대시보드
 */
import { useState, useEffect, useCallback } from "react";
import {
  Shield, GitBranch, AlertTriangle, Lock, RefreshCw,
  CheckCircle, XCircle, AlertCircle, ArrowRight, Tag,
  Activity, Users, Code, ChevronRight, Network,
} from "lucide-react";
import Layout from "../components/layout/Layout";

const API = import.meta.env.VITE_API_BASE || import.meta.env.VITE_API_URL || "";
const TABS = [
  { key: "progress", label: "아키텍처 현황", icon: Network },
  { key: "activity", label: "팀 활동", icon: Users },
  { key: "backup", label: "백업 & 롤백", icon: GitBranch },
  { key: "security", label: "보안", icon: Lock },
];

/* 상태 색상 유틸 */
const statusColor = (s) =>
  s === "active" ? "text-emerald-400" : s === "fallback" ? "text-amber-400" : "text-red-400";
const statusBg = (s) =>
  s === "active" ? "bg-emerald-500/15" : s === "fallback" ? "bg-amber-500/15" : "bg-red-500/15";
const auditIcon = (s) =>
  s === "pass" ? <CheckCircle size={16} className="text-emerald-400" />
    : s === "warn" ? <AlertCircle size={16} className="text-amber-400" />
    : <XCircle size={16} className="text-red-400" />;

/* 기술 스택 → 담당 업무 매핑 */
const TECH_STACK_MAP = [
  { tech: "LangGraph",  usage: "오케스트레이터 DAG 워크플로우", owner: "공통 (core) — orchestrator.py" },
  { tech: "LangChain",  usage: "LLM 체인 + 프롬프트 관리",    owner: "팀원 A·B·C·D — 각 플러그인 LLM 호출" },
  { tech: "PPO RL",     usage: "강화학습 행동 최적화",         owner: "공통 (core) — rl_engine/ppo_agent.py" },
  { tech: "OpenCLIP",   usage: "이미지 512D 임베딩 + 유사도", owner: "팀원 E — plugins/vision_korean/" },
  { tech: "YOLO",       usage: "한식 식재료 실시간 감지",      owner: "팀원 E — plugins/vision_korean/" },
  { tech: "MediaPipe",  usage: "33 랜드마크 자세 분석",        owner: "팀원 E — plugins/vision_korean/" },
  { tech: "RAG",        usage: "벡터 검색 + 리랭킹 추천",     owner: "팀원 A — plugins/food_rag/" },
  { tech: "ChromaDB",   usage: "벡터 DB (레시피·운동·건강)",   owner: "팀원 A·B·C·D — 각 knowledge DB" },
  { tech: "Supabase",   usage: "PostgreSQL 사용자 상태 저장",  owner: "공통 (core) — services/user_state_manager.py" },
  { tech: "GPT-4o",     usage: "멀티모달 LLM 추론 엔진",      owner: "팀원 A·B·C·D — 각 플러그인 추천 생성" },
];

/* CASCADE 연결 — 소스 도메인별 그룹 (중복 없이 정리) */
const CASCADE_GROUPS = [
  { source: "요리 (food)", color: "text-orange-400", effects: [
    { to: "건강", label: "칼로리/영양 → 건강 지표 영향" },
    { to: "운동", label: "칼로리 초과 시 추가 운동 필요" },
  ]},
  { source: "운동 (exercise)", color: "text-blue-400", effects: [
    { to: "건강", label: "수면 개선 + 스트레스 감소" },
    { to: "요리", label: "운동 후 단백질 식사 권장" },
  ]},
  { source: "건강 (health)", color: "text-emerald-400", effects: [
    { to: "운동", label: "건강 위험 시 운동 강도 조절" },
    { to: "요리", label: "건강 위험 시 식단 제한" },
  ]},
  { source: "취미 (hobby)", color: "text-violet-400", effects: [
    { to: "건강", label: "스트레스 해소 효과" },
    { to: "요리", label: "폭식 충동 감소" },
    { to: "운동", label: "운동 동기부여 상승" },
  ]},
];

export default function TeamLeaderPage() {
  const [tab, setTab] = useState("progress");
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState({});

  const fetchAll = useCallback(async () => {
    setLoading(true);
    try {
      const endpoints = {
        progress: "/api/admin/team-progress",
        conflicts: "/api/admin/conflicts",
        backups: "/api/admin/backups",
        security: "/api/admin/security-audit",
        orchestrator: "/api/admin/orchestrator-stats",
      };
      const results = await Promise.allSettled(
        Object.entries(endpoints).map(async ([key, url]) => {
          const controller = new AbortController();
          const timer = setTimeout(() => controller.abort(), 10000);
          try {
            const res = await fetch(`${API}${url}`, { signal: controller.signal });
            if (!res.ok) throw new Error(`${url}: ${res.status}`);
            return [key, await res.json()];
          } finally {
            clearTimeout(timer);
          }
        })
      );
      const newData = {};
      results.forEach((r) => {
        if (r.status === "fulfilled") {
          const [key, val] = r.value;
          newData[key] = val;
        }
      });
      setData(newData);
    } catch (e) {
      console.error("데이터 로드 실패:", e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchAll(); }, []);

  return (
    <Layout>
      <div className="min-h-screen bg-gray-950 text-gray-100 p-4 lg:p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500 to-cyan-500 flex items-center justify-center shadow-lg">
              <Shield size={20} className="text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">전체 관리 대시보드</h1>
              <p className="text-xs text-white">LifeSync AI v0.3.0 — 6 Plugins + Orchestrator</p>
            </div>
          </div>
          <button
            onClick={fetchAll}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gray-800 hover:bg-gray-700 text-sm transition-all disabled:opacity-50"
          >
            <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
            새로고침
          </button>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 mb-6 bg-gray-900 p-1 rounded-xl w-fit">
          {TABS.map((t) => (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                tab === t.key
                  ? "bg-gradient-to-r from-cyan-500/20 to-violet-500/15 text-cyan-400"
                  : "text-white hover:text-white"
              }`}
            >
              <t.icon size={15} />
              {t.label}
            </button>
          ))}
        </div>

        {/* Content */}
        {tab === "progress" && <ProgressTab data={data} />}
        {tab === "activity" && <ActivityTab data={data} />}
        {tab === "backup" && <BackupTab data={data} onRefresh={fetchAll} />}
        {tab === "security" && <SecurityTab data={data} />}
      </div>
    </Layout>
  );
}


/* ============================================================
   Tab 1: 아키텍처 진행 현황 + 오케스트레이터 CASCADE
   ============================================================ */
function ProgressTab({ data }) {
  const plugins = data.progress?.plugins || [];
  const orch = data.orchestrator || {};

  return (
    <div className="space-y-6">
      {/* 오케스트레이터 통계 */}
      <div className="bg-gray-900/70 rounded-2xl border border-gray-800 p-5">
        <h2 className="text-sm font-semibold text-violet-400 mb-4 flex items-center gap-2">
          <Activity size={16} /> 오케스트레이터 통계 (LangGraph StateGraph)
        </h2>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard label="총 호출" value={orch.total_calls ?? 0} />
          <StatCard label="평균 CASCADE" value={orch.avg_cascade_effects ?? 0} suffix="개" />
          <StatCard label="에러율" value={`${orch.error_rate ?? 0}%`} warn={orch.error_rate > 5} />
          <div className="bg-gray-800/50 rounded-xl p-3">
            <p className="text-[10px] text-white mb-2">도메인별 호출</p>
            <div className="space-y-1">
              {Object.entries(orch.calls_by_domain || {}).map(([d, c]) => (
                <div key={d} className="flex justify-between text-xs">
                  <span className="text-white">{d}</span>
                  <span className="text-cyan-400 font-mono">{c}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* 기술 스택 → 담당 업무 매핑 (위로 이동) */}
      <div className="bg-gray-900/70 rounded-2xl border border-gray-800 p-5">
        <h2 className="text-sm font-semibold text-cyan-400 mb-4 flex items-center gap-2">
          <Code size={16} /> 기술 스택별 담당 업무
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
          {TECH_STACK_MAP.map((t, i) => (
            <div key={i} className="flex items-center gap-3 bg-gray-800/40 rounded-lg px-3 py-2.5">
              <span className="text-xs font-mono font-bold text-white bg-gray-700/50 px-2 py-0.5 rounded min-w-[80px] text-center">{t.tech}</span>
              <div className="flex-1 min-w-0">
                <span className="text-xs text-white block">{t.usage}</span>
                <span className="text-[10px] text-cyan-400">{t.owner}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* CASCADE 연결 — 소스 도메인별 그룹화 (아래로 이동) */}
      <div className="bg-gray-900/70 rounded-2xl border border-gray-800 p-5">
        <h2 className="text-sm font-semibold text-cyan-400 mb-4 flex items-center gap-2">
          <Network size={16} /> 크로스 도메인 CASCADE 연결
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {CASCADE_GROUPS.map((g, i) => (
            <div key={i} className="bg-gray-800/40 rounded-xl p-3">
              <h3 className={`text-xs font-semibold ${g.color} mb-2`}>{g.source}</h3>
              <div className="space-y-1.5">
                {g.effects.map((e, j) => (
                  <div key={j} className="flex items-center gap-2 text-xs">
                    <ArrowRight size={10} className="text-white flex-shrink-0" />
                    <span className="text-white font-medium">{e.to}</span>
                    <span className="text-white">{e.label}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 플러그인 카드 그리드 */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {plugins.map((p) => (
          <PluginCard key={p.plugin} plugin={p} />
        ))}
      </div>
    </div>
  );
}

function StatCard({ label, value, suffix = "", warn = false }) {
  return (
    <div className="bg-gray-800/50 rounded-xl p-3">
      <p className="text-[10px] text-white mb-1">{label}</p>
      <p className={`text-lg font-bold font-mono ${warn ? "text-red-400" : "text-white"}`}>
        {value}{suffix}
      </p>
    </div>
  );
}

function PluginCard({ plugin: p }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className={`rounded-2xl border p-4 transition-all ${
      p.status === "active"
        ? "bg-gray-900/70 border-emerald-500/30"
        : "bg-gray-900/70 border-amber-500/30"
    }`}>
      <div className="flex items-start justify-between mb-3">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Code size={14} className="text-white" />
            <span className="font-semibold text-sm text-white">{p.plugin}</span>
          </div>
          <p className="text-[11px] text-white">팀원 {p.member} — {p.role}</p>
        </div>
        <span className={`text-[10px] font-medium px-2 py-0.5 rounded-full ${statusBg(p.status)} ${statusColor(p.status)}`}>
          {p.status === "active" ? "ACTIVE" : "FALLBACK"}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-2 text-xs mb-3">
        <div className="bg-gray-800/50 rounded-lg p-2">
          <span className="text-white">코드</span>
          <span className="float-right text-cyan-400 font-mono">{p.code_lines}줄</span>
        </div>
        <div className="bg-gray-800/50 rounded-lg p-2">
          <span className="text-white">30일 커밋</span>
          <span className="float-right text-cyan-400 font-mono">{p.recent_commits_30d}건</span>
        </div>
      </div>

      {p.last_commit_date && (
        <p className="text-[10px] text-white mb-2">
          마지막 커밋: {p.last_commit_date}
        </p>
      )}

      {/* 최근 커밋 */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="text-[11px] text-white hover:text-white flex items-center gap-1 transition-all"
      >
        <ChevronRight size={12} className={`transition-transform ${expanded ? "rotate-90" : ""}`} />
        최근 커밋 {p.recent_log?.length || 0}건
      </button>
      {expanded && p.recent_log?.length > 0 && (
        <div className="mt-2 space-y-1">
          {p.recent_log.map((c, i) => (
            <div key={i} className="text-[11px] bg-gray-800/30 rounded-lg px-2 py-1.5">
              <span className="text-violet-400 font-mono mr-2">{c.hash}</span>
              <span className="text-white">{c.message}</span>
              <span className="text-white ml-2">{c.relative_date}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}


/* ============================================================
   Tab 2: 팀 활동 & 충돌 감지
   ============================================================ */
function ActivityTab({ data }) {
  const conflicts = data.conflicts?.conflicts || [];
  const plugins = data.progress?.plugins || [];

  // 모든 플러그인의 최근 커밋을 합쳐서 시간순 정렬
  const allCommits = plugins.flatMap((p) =>
    (p.recent_log || []).map((c) => ({ ...c, plugin: p.plugin, member: p.member }))
  );

  return (
    <div className="space-y-6">
      {/* 충돌 경고 */}
      <div className="bg-gray-900/70 rounded-2xl border border-gray-800 p-5">
        <h2 className="text-sm font-semibold text-amber-400 mb-4 flex items-center gap-2">
          <AlertTriangle size={16} /> 충돌 감지 (최근 7일)
        </h2>
        {conflicts.length === 0 ? (
          <div className="flex items-center gap-2 text-sm text-emerald-400">
            <CheckCircle size={16} /> 충돌 없음
          </div>
        ) : (
          <div className="space-y-2">
            {conflicts.map((c, i) => (
              <div
                key={i}
                className={`flex items-center gap-3 rounded-xl px-4 py-2.5 text-xs ${
                  c.risk === "high" ? "bg-red-500/10 border border-red-500/30" : "bg-amber-500/10 border border-amber-500/20"
                }`}
              >
                <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                  c.risk === "high" ? "bg-red-500/20 text-red-400" : "bg-amber-500/20 text-amber-400"
                }`}>
                  {c.risk.toUpperCase()}
                </span>
                <span className="text-white font-mono flex-1 truncate">{c.file}</span>
                <span className="text-white">{c.authors.join(", ")}</span>
              </div>
            ))}
          </div>
        )}
        <p className="text-[10px] text-white mt-3">
          같은 파일을 여러 author가 수정한 경우 감지. core/, main.py 수정은 HIGH 위험.
        </p>
      </div>

      {/* 최근 팀 커밋 타임라인 */}
      <div className="bg-gray-900/70 rounded-2xl border border-gray-800 p-5">
        <h2 className="text-sm font-semibold text-cyan-400 mb-4 flex items-center gap-2">
          <GitBranch size={16} /> 최근 팀 활동
        </h2>
        {allCommits.length === 0 ? (
          <p className="text-sm text-white">커밋 기록 없음</p>
        ) : (
          <div className="space-y-1.5">
            {allCommits.map((c, i) => (
              <div key={i} className="flex items-center gap-3 text-xs bg-gray-800/30 rounded-lg px-3 py-2">
                <span className="text-violet-400 font-mono w-14 flex-shrink-0">{c.hash}</span>
                <span className="text-cyan-400 w-28 flex-shrink-0">{c.plugin}</span>
                <span className="text-white w-14 flex-shrink-0">팀원{c.member}</span>
                <span className="text-white flex-1 truncate">{c.message}</span>
                <span className="text-white text-[10px] flex-shrink-0">{c.relative_date}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}


/* ============================================================
   Tab 3: 백업 & 롤백
   ============================================================ */
function BackupTab({ data, onRefresh }) {
  const tags = data.backups?.tags || [];
  const [creating, setCreating] = useState(false);
  const [tagName, setTagName] = useState("");
  const [message, setMessage] = useState("팀장 백업");

  const createBackup = async () => {
    setCreating(true);
    try {
      const body = {};
      if (tagName) body.tag_name = tagName;
      if (message) body.message = message;

      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), 10000);
      const res = await fetch(`${API}/api/admin/backup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
        signal: controller.signal,
      });
      clearTimeout(timer);
      if (!res.ok) {
        const err = await res.json();
        alert(`백업 실패: ${err.detail || res.status}`);
        return;
      }
      const result = await res.json();
      alert(`백업 생성 완료: ${result.tag}`);
      setTagName("");
      onRefresh();
    } catch (e) {
      alert(`백업 실패: ${e.message}`);
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* 새 백업 생성 */}
      <div className="bg-gray-900/70 rounded-2xl border border-gray-800 p-5">
        <h2 className="text-sm font-semibold text-emerald-400 mb-4 flex items-center gap-2">
          <Tag size={16} /> 새 백업 생성
        </h2>
        <div className="flex flex-wrap gap-3 items-end">
          <div>
            <label className="text-[10px] text-white block mb-1">태그명 (선택)</label>
            <input
              type="text"
              value={tagName}
              onChange={(e) => setTagName(e.target.value)}
              placeholder="auto-generated"
              className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 w-52 focus:border-cyan-500 focus:outline-none"
            />
          </div>
          <div>
            <label className="text-[10px] text-white block mb-1">메시지</label>
            <input
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 w-64 focus:border-cyan-500 focus:outline-none"
            />
          </div>
          <button
            onClick={createBackup}
            disabled={creating}
            className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-sm font-medium text-white transition-all disabled:opacity-50"
          >
            {creating ? "생성 중..." : "백업 생성"}
          </button>
        </div>
      </div>

      {/* 기존 태그 목록 */}
      <div className="bg-gray-900/70 rounded-2xl border border-gray-800 p-5">
        <h2 className="text-sm font-semibold text-cyan-400 mb-4 flex items-center gap-2">
          <GitBranch size={16} /> 백업 태그 목록 ({tags.length}개)
        </h2>
        {tags.length === 0 ? (
          <p className="text-sm text-white">태그 없음</p>
        ) : (
          <div className="space-y-1.5">
            {tags.map((t, i) => (
              <div key={i} className="flex items-center gap-3 bg-gray-800/30 rounded-lg px-4 py-2.5 text-xs">
                <Tag size={12} className="text-cyan-400 flex-shrink-0" />
                <span className="text-white font-mono font-medium">{t.tag}</span>
                <span className="text-white ml-auto">{t.date}</span>
              </div>
            ))}
          </div>
        )}
        <div className="mt-4 bg-gray-800/30 rounded-xl p-3">
          <p className="text-[10px] text-white font-medium mb-1">롤백 명령어 (터미널에서 직접 실행)</p>
          <code className="text-[11px] text-amber-400 font-mono">
            git checkout &lt;tag-name&gt;  # 해당 시점으로 이동
          </code>
        </div>
      </div>
    </div>
  );
}


/* ============================================================
   Tab 4: 보안 대시보드
   ============================================================ */
function SecurityTab({ data }) {
  const audit = data.security || {};
  const checks = audit.checks || [];
  const summary = audit.summary || {};

  // 카테고리별 그룹핑
  const categories = {};
  checks.forEach((c) => {
    if (!categories[c.category]) categories[c.category] = [];
    categories[c.category].push(c);
  });

  return (
    <div className="space-y-6">
      {/* 요약 */}
      <div className="bg-gray-900/70 rounded-2xl border border-gray-800 p-5">
        <h2 className="text-sm font-semibold text-violet-400 mb-4 flex items-center gap-2">
          <Shield size={16} /> 보안 점수
        </h2>
        <div className="flex items-center gap-6">
          <div className={`text-4xl font-bold font-mono ${
            summary.score >= 80 ? "text-emerald-400" : summary.score >= 50 ? "text-amber-400" : "text-red-400"
          }`}>
            {summary.score ?? 0}
            <span className="text-lg text-white">/100</span>
          </div>
          <div className="grid grid-cols-3 gap-4 text-xs">
            <div>
              <span className="text-emerald-400 font-bold text-lg">{summary.pass ?? 0}</span>
              <span className="text-white ml-1">통과</span>
            </div>
            <div>
              <span className="text-amber-400 font-bold text-lg">{summary.warn ?? 0}</span>
              <span className="text-white ml-1">주의</span>
            </div>
            <div>
              <span className="text-red-400 font-bold text-lg">{summary.fail ?? 0}</span>
              <span className="text-white ml-1">실패</span>
            </div>
          </div>
        </div>
        <p className="text-[10px] text-white mt-2">환경: {audit.environment || "unknown"}</p>
      </div>

      {/* 카테고리별 체크리스트 */}
      {Object.entries(categories).map(([cat, items]) => (
        <div key={cat} className="bg-gray-900/70 rounded-2xl border border-gray-800 p-5">
          <h3 className="text-sm font-semibold text-white mb-3">{cat}</h3>
          <div className="space-y-2">
            {items.map((c, i) => (
              <div key={i} className="flex items-center gap-3 text-xs bg-gray-800/30 rounded-lg px-3 py-2.5">
                {auditIcon(c.status)}
                <span className="text-gray-200 font-medium w-40 flex-shrink-0">{c.item}</span>
                <span className="text-white flex-1">{c.detail}</span>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
