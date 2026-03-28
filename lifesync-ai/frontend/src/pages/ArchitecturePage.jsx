/**
 * ArchitecturePage — Interactive system architecture map (n8n-style node graph)
 * - Hover: show popup, leave: hide
 * - Click: pin popup permanently, auto-redistribute nodes to avoid overlap
 * - "전체보기" button: show all popups, auto-redistribute all
 */
import { useState, useCallback, useRef, useMemo, useEffect } from "react";
import Layout from "../components/layout/Layout";

/* ------------------------------------------------------------------ */
/*  DATA                                                               */
/* ------------------------------------------------------------------ */

const STATUS_META = {
  active: { label: "활성", color: "#10b981", bg: "rgba(16,185,129,0.10)", text: "text-emerald-400" },
  partial: { label: "부분구현", color: "#f59e0b", bg: "rgba(245,158,11,0.10)", text: "text-amber-400" },
  pending: { label: "대기", color: "#6b7280", bg: "rgba(107,114,128,0.10)", text: "text-gray-400" },
};

const NODES = [
  { id: "frontend",      emoji: "\u269B\uFE0F",  label: "Frontend (React)",            status: "active",  col: 0, row: 0, desc: "React 18 대시보드 + 시뮬레이터", path: "frontend/src/", features: ["11개 페이지", "WebSocket 실시간", "코드 스플리팅"], role: "사용자 인터페이스", pros: "React.lazy 빠른 로딩, Tailwind 일관된 디자인", cons: "SSR 미지원, 대형 페이지 존재", reason: "건강 데이터를 시각화하고 의사결정하는 핵심 접점" },
  { id: "whisper",        emoji: "\uD83C\uDF99\uFE0F", label: "Whisper STT",             status: "pending", col: 0, row: 1, desc: "음성→텍스트 변환", path: "backend/voice/stt_processor.py", features: ["한국어 지원", "실시간 처리"], role: "음성 인식", pros: "높은 한국어 정확도", cons: "스텁 상태 (미구현)", reason: "요리/운동 중 손을 못 쓸 때 음성 입력 필수" },
  { id: "gtts",           emoji: "\uD83D\uDD0A",  label: "gTTS Response",               status: "pending", col: 0, row: 2, desc: "텍스트→음성 응답", path: "backend/voice/tts_responder.py", features: ["한국어 TTS", "MP3 생성"], role: "음성 출력", pros: "무료, 한국어 지원", cons: "스텁 상태, 기계적 음질", reason: "시각 장애 접근성, 운동 중 화면 못 볼 때" },

  { id: "fastapi",        emoji: "\uD83D\uDE80",  label: "FastAPI Backend",             status: "active",  col: 1, row: 0, desc: "REST API + WebSocket 서버 (Router 분리)", path: "backend/app/main.py", features: ["main.py 180줄 (미들웨어만)", "ai_router.py (그룹A)", "api_router.py (그룹B)", "30+ 엔드포인트"], role: "중앙 API 서버", pros: "Router 분리로 팀 간 충돌 제거, 비동기, Swagger", cons: "라우터 간 서비스 중복 초기화", reason: "프론트와 AI/ML을 연결하는 유일한 통로. Router 패턴으로 3그룹 동시 개발 가능" },
  { id: "websocket",      emoji: "\uD83D\uDD0C",  label: "WebSocket",                   status: "active",  col: 1, row: 1, desc: "실시간 양방향 통신", path: "backend/app/routers/api_router.py", features: ["게이지 실시간 업데이트", "JWT 토큰 인증", "echo/voice/query/feedback/subscribe"], role: "실시간 통신", pros: "HTTP 폴링 대비 지연 90% 감소", cons: "서버 재시작 시 연결 끊김", reason: "대시보드 게이지가 실시간 변해야 행동 효과 즉시 확인" },
  { id: "docker",         emoji: "\uD83D\uDC33",  label: "Docker",                      status: "active",  col: 1, row: 2, desc: "컨테이너 오케스트레이션", path: "docker-compose.yml", features: ["백엔드+ChromaDB+프론트", "한 명령 실행"], role: "환경 일관성", pros: "'내 PC에서는 되는데' 문제 해결", cons: "Docker Desktop 설치 필요", reason: "6명 팀원 동일 개발환경 보장, Railway 배포 필수" },
  { id: "railway",        emoji: "\uD83D\uDE82",  label: "Railway Deploy",              status: "active",  col: 1, row: 3, desc: "클라우드 배포 ($5/월)", path: "railway.toml", features: ["GitHub 자동 배포", "볼륨 마운트", "Health check"], role: "백엔드 배포", pros: "$5/월 24시간 운영, 설정 간편", cons: "GPU 미지원, 콜드 스타트", reason: "로컬 설치 없이 서비스를 사용할 수 있는 공유 URL" },

  { id: "orchestrator",   emoji: "\uD83D\uDD04",  label: "Orchestrator (LangGraph)",    status: "active",  col: 2, row: 0, desc: "조건 분기 + 대화 메모리 엔진", path: "backend/agents/orchestrator.py", features: ["조건 분기", "멀티도메인", "대화 메모리 50턴", "평가 노드"], role: "요청 라우팅 + 연쇄 효과", pros: "LangGraph로 복잡한 워크플로우 선언적 관리", cons: "직렬 실행 (병렬 미지원)", reason: "'라면 먹었다'→건강 위험+추가 운동 권장+수면 영향 예측" },
  { id: "simulator",      emoji: "\u23F0",        label: "Schedule Simulator",          status: "active",  col: 2, row: 1, desc: "24시간 스케줄 N일 시뮬레이션", path: "backend/rl_engine/schedule_simulator.py", features: ["15개 활동 유형", "시간대 패널티", "종합 분석"], role: "장기 건강 예측", pros: "오프라인 JS 버전도 동작", cons: "결정론적 (확률 변동 없음)", reason: "'이 스케줄로 한 달 살면?'을 미리 확인" },
  { id: "risk",           emoji: "\u26A0\uFE0F",  label: "Risk Engine",                 status: "active",  col: 2, row: 2, desc: "음식 위험도 + 야식 패널티", path: "backend/risk_engine/", features: ["베이지안 위험도", "야식 -5 패널티", "타임라인"], role: "위험 경고", pros: "시간대 기반 동적 위험도 계산", cons: "규칙 기반으로 새 패턴 적응 못 함", reason: "튀김의 콜레스테롤, 야식의 수면 영향 등 구체적 경고" },

  { id: "food",           emoji: "\uD83C\uDF73",  label: "Food Agent (LangChain)",      status: "active",  col: 3, row: 0, desc: "RAG 기반 레시피 추천", path: "backend/agents/food_agent.py", features: ["쿼리 확장+리랭킹", "위험도 평가", "영양 분석"], role: "개인화 식단 추천", pros: "10만건 레시피에서 RAG 검색 + LLM 설명", cons: "LLM API 비용, 응답 2-5초", reason: "BMI/목표에 따라 개인화된 식단 추천" },
  { id: "exercise",       emoji: "\uD83C\uDFCB\uFE0F", label: "Exercise Agent (LangChain)", status: "active", col: 3, row: 1, desc: "운동 추천 + 부상 위험 평가", path: "backend/agents/exercise_agent.py", features: ["미세먼지 연동", "부상 위험도", "실내 대체 운동"], role: "안전한 운동 추천", pros: "환경+개인 상태 고려한 추천", cons: "날씨 API 미연동", reason: "부상 이력, 미세먼지 등 고려한 안전한 운동" },
  { id: "health",         emoji: "\uD83C\uDFE5",  label: "Health Agent (LangChain)",     status: "active",  col: 3, row: 2, desc: "건강검진 분석 + 플랜", path: "backend/agents/health_agent.py", features: ["메트릭 분석", "위험도 분류", "맞춤 플랜"], role: "건강 해석 + 플랜", pros: "검진 숫자를 알기 쉬운 자연어로 해석", cons: "의료 면허 없는 AI 한계", reason: "검진 결과의 의미를 모르는 사용자에게 가이드" },
  { id: "hobby",          emoji: "\uD83C\uDFB8",  label: "Hobby Agent (LangChain)",      status: "active",  col: 3, row: 3, desc: "스트레스 해소 취미 추천", path: "backend/agents/hobby_agent.py", features: ["스트레스 기반", "크로스 도메인 시너지", "감소율 모델링"], role: "정신건강 관리", pros: "기타 30분→스트레스 -15% 등 연쇄 효과", cons: "취미 카탈로그 제한적", reason: "건강 관리 = 식단+운동+정신건강 → 지속 가능" },
  { id: "ppo",            emoji: "\uD83C\uDFAF",  label: "PPO Reinforcement Learning",  status: "active",  col: 3, row: 4, desc: "PPO 강화학습 정책", path: "backend/rl_engine/ppo_agent.py", features: ["40차원 상태", "10개 행동", "84스텝 에피소드"], role: "최적 행동 학습", pros: "피드백으로 지속 개선, 다축 보상 균형", cons: "CPU 학습 느림, 초기 데이터 부족", reason: "규칙 기반은 개인차 미반영 → RL로 개인별 최적 전략" },
  { id: "retrain",        emoji: "\uD83D\uDD01",  label: "Retrain Scheduler",           status: "active",  col: 3, row: 5, desc: "피드백 기반 자동 재학습", path: "backend/rl_engine/retrain_scheduler.py", features: ["6시간 주기", "보상 하락 감지", "사용자별 가중치"], role: "자동 모델 개선", pros: "수동 개입 없이 자동 개선", cons: "서버 리소스 소모", reason: "'이 추천은 별로' 피드백 → 다음에 더 나은 추천" },
  { id: "optuna",         emoji: "\uD83D\uDD2C",  label: "Optuna AutoTuner",            status: "active",  col: 3, row: 6, desc: "하이퍼파라미터 자동 최적화", path: "backend/rl_engine/auto_tuner.py", features: ["100 trial", "lr/gamma/batch 탐색", "베이지안 최적화"], role: "RL 성능 최적화", pros: "수동 튜닝 대비 체계적 탐색", cons: "연산 시간 (GPU 권장)", reason: "RL 성능은 하이퍼파라미터에 극도로 민감" },

  { id: "gpt4o",          emoji: "\uD83E\uDD16",  label: "GPT-4o-mini",                 status: "active",  col: 4, row: 0, desc: "OpenAI LLM 추론 엔진", path: ".env (OPENAI_API_KEY)", features: ["자연어 생성", "분석", "추천", "개인화 조언"], role: "자연어 이해/생성", pros: "한국어 우수, 맥락 이해, 창의적 추천", cons: "API 비용, 할루시네이션 가능", reason: "'왜 이 레시피인지' 자연어 설명 생성" },
  { id: "chromadb",       emoji: "\uD83D\uDCDA",  label: "ChromaDB (RAG)",              status: "active",  col: 4, row: 1, desc: "벡터 DB + 쿼리 확장 + 리랭킹", path: "backend/knowledge/", features: ["4개 컬렉션", "다중 쿼리", "컨텍스트 부스트"], role: "지식 검색 엔진", pros: "무료, persistent, 한국어 multilingual", cons: "대규모(100만건+) 성능 저하", reason: "LLM만으로는 최신 레시피 모름 → RAG로 지식 주입" },
  { id: "supabase",       emoji: "\uD83D\uDC18",  label: "Supabase PostgreSQL",         status: "active",  col: 4, row: 2, desc: "사용자 상태 영속 저장", path: "backend/services/user_state_manager.py", features: ["40차원 State 벡터", "UPSERT", "인메모리 폴백"], role: "상태 저장소", pros: "무료 500MB, REST API 자동 제공", cons: "연결 수 제한, timeout 발생", reason: "앱 종료 후 다시 와도 이전 건강 상태 유지" },
  { id: "s3",             emoji: "\u2601\uFE0F",  label: "AWS S3 Model Storage",        status: "active",  col: 4, row: 3, desc: "모델 가중치 + 버전 관리", path: "backend/services/model_registry.py", features: ["SHA256 체크섬", "버전 관리", "클라이언트 동기화"], role: "모델 중앙 저장소", pros: "내구성 99.999999999%, 글로벌 접근", cons: "AWS 계정 필요", reason: "GPU 학습 모델을 서버/클라이언트가 공유" },
  { id: "yolo",           emoji: "\uD83D\uDCF7",  label: "YOLO Food Recognition",       status: "partial", col: 4, row: 4, desc: "YOLOv8 식재료 인식", path: "backend/multimodal/food_recognizer.py", features: ["객체 감지", "CPU ~100ms", "80+ 카테고리"], role: "식재료 자동 인식", pros: "실시간 추론, 높은 정확도", cons: "한국 음식 특화 안 됨", reason: "식단 사진으로 자동 칼로리/영양소 추정" },
  { id: "openclip",       emoji: "\uD83D\uDDBC\uFE0F", label: "OpenCLIP Embedding",     status: "partial", col: 4, row: 5, desc: "512차원 이미지/텍스트 임베딩", path: "backend/multimodal/photo_analyzer.py", features: ["얼굴/체형 분석", "LLM 개인화 조언", "Top-K"], role: "이미지 AI 분석", pros: "이미지+텍스트 크로스 모달 검색", cons: "ViT-B-32 정확도 한계 (GPU시 ViT-L-14)", reason: "사진 한 장으로 건강 상태 추정 + 맞춤 조언" },
  { id: "mediapipe",      emoji: "\uD83E\uDD38",  label: "MediaPipe Pose",              status: "partial", col: 4, row: 6, desc: "자세 분석 33 랜드마크", path: "backend/multimodal/pose_analyzer.py", features: ["어깨/척추 정렬", "자세 점수", "운동 폼 교정"], role: "자세 교정 AI", pros: "무료, CPU 실시간, 높은 정확도", cons: "정적 이미지만 (실시간 비디오 미구현)", reason: "잘못된 운동 자세 → 부상 → AI 교정으로 안전" },

  // Layer 5: 배포 + 오프라인
  { id: "offline",        emoji: "\uD83D\uDCF1",  label: "Offline Engine (JS)",          status: "active",  col: 0, row: 3, desc: "오프라인 추론 + 모델 동기화", path: "frontend/src/services/offlineEngine.js", features: ["IndexedDB 캐싱", "smartSimulate", "5초 지연 동기화"], role: "오프라인 폴백", pros: "네트워크 없이 핵심 기능 사용", cons: "LLM 추천은 오프라인 불가", reason: "지하철/비행기 등 오프라인이 빈번 → 앱 멈추면 안 됨" },
  { id: "capacitor",      emoji: "\uD83D\uDCF2",  label: "Capacitor (Android APK)",     status: "active",  col: 0, row: 4, desc: "Android APK 빌드", path: "frontend/capacitor.config.json", features: ["카메라", "파일시스템", "오프라인 모드"], role: "모바일 앱 변환", pros: "웹+앱 하나의 코드베이스, 네이티브 API", cons: "iOS 별도 추가 필요", reason: "핸드폰 직접 설치 요구사항 충족" },
  { id: "vercel",         emoji: "\u25B2",        label: "Vercel (Frontend Deploy)",    status: "active",  col: 1, row: 4, desc: "프론트엔드 CDN 배포", path: "frontend/vercel.json", features: ["자동 배포", "SPA Rewrite", "글로벌 CDN"], role: "프론트 배포", pros: "완전 무료, 전 세계 빠른 로딩", cons: "서버 사이드 로직 불가", reason: "프론트엔드는 CDN이 훨씬 빠르고 저렴" },
  { id: "jwt",            emoji: "\uD83D\uDD10",  label: "JWT Auth + Rate Limit",       status: "active",  col: 1, row: 5, desc: "인증 + API 보안 미들웨어", path: "backend/app/main.py", features: ["Bearer 토큰", "분당 60회 제한", "Kakao OAuth"], role: "보안 게이트", pros: "사용자별 데이터 격리, DDoS 방어", cons: "refresh token 미구현", reason: "건강 데이터는 민감 → 인증 없는 접근 차단 필수" },
  { id: "gpu_train",      emoji: "\uD83D\uDDA5\uFE0F", label: "GPU Training Pipeline",  status: "active",  col: 2, row: 3, desc: "로컬 GPU 학습 → S3 업로드", path: "scripts/train_and_upload.py", features: ["PPO 학습", "Optuna 최적화", "서버 업로드"], role: "모델 학습 파이프라인", pros: "클라우드 GPU 비용 절감", cons: "로컬 GPU 필요, 수동 실행", reason: "RL 학습은 연산 집약적 → 로컬 GPU 활용" },
];

// Connection categories with distinct colors
const CONN_CATEGORIES = {
  api:     { color: "#3b82f6", labelFill: "#93c5fd", bg: "#1e3a5f", border: "#3b82f6", legend: "API 통신" },       // blue
  agent:   { color: "#8b5cf6", labelFill: "#c4b5fd", bg: "#3b1f6e", border: "#8b5cf6", legend: "에이전트 라우팅" }, // purple
  llm:     { color: "#f59e0b", labelFill: "#fcd34d", bg: "#5c3d0a", border: "#f59e0b", legend: "LLM 추론" },       // amber
  rag:     { color: "#10b981", labelFill: "#6ee7b7", bg: "#0d3b2e", border: "#10b981", legend: "RAG 검색" },       // emerald
  data:    { color: "#06b6d4", labelFill: "#67e8f9", bg: "#0c3644", border: "#06b6d4", legend: "데이터 저장" },     // cyan
  vision:  { color: "#f43f5e", labelFill: "#fda4af", bg: "#5c1525", border: "#f43f5e", legend: "비전/멀티모달" },   // rose
  voice:   { color: "#a78bfa", labelFill: "#ddd6fe", bg: "#3b2d6e", border: "#a78bfa", legend: "음성 처리" },       // violet
  rl:      { color: "#ec4899", labelFill: "#f9a8d4", bg: "#5c1540", border: "#ec4899", legend: "강화학습" },        // pink
};

const CONNECTIONS = [
  { from: "frontend",  to: "fastapi",      label: "HTTP REST API",      cat: "api" },
  { from: "frontend",  to: "websocket",    label: "실시간 상태 동기화",   cat: "api" },
  { from: "fastapi",   to: "orchestrator", label: "사용자 요청 라우팅",   cat: "agent" },
  { from: "orchestrator", to: "food",      label: "음식 도메인 요청",     cat: "agent" },
  { from: "orchestrator", to: "exercise",  label: "운동 도메인 요청",     cat: "agent" },
  { from: "orchestrator", to: "health",    label: "건강 도메인 요청",     cat: "agent" },
  { from: "orchestrator", to: "hobby",     label: "취미 도메인 요청",     cat: "agent" },
  { from: "food",      to: "gpt4o",        label: "LLM 추론 요청",       cat: "llm" },
  { from: "exercise",  to: "gpt4o",        label: "LLM 추론 요청",       cat: "llm" },
  { from: "health",    to: "gpt4o",        label: "LLM 추론 요청",       cat: "llm" },
  { from: "hobby",     to: "gpt4o",        label: "LLM 추론 요청",       cat: "llm" },
  { from: "food",      to: "chromadb",     label: "레시피 RAG 검색",     cat: "rag" },
  { from: "exercise",  to: "chromadb",     label: "운동 RAG 검색",       cat: "rag" },
  { from: "health",    to: "chromadb",     label: "건강 RAG 검색",       cat: "rag" },
  { from: "hobby",     to: "chromadb",     label: "취미 RAG 검색",       cat: "rag" },
  { from: "fastapi",   to: "supabase",     label: "사용자 상태 CRUD",    cat: "data" },
  { from: "fastapi",   to: "simulator",    label: "시뮬레이션 요청",      cat: "rl" },
  { from: "fastapi",   to: "risk",         label: "위험도 평가 요청",     cat: "data" },
  { from: "fastapi",   to: "yolo",         label: "이미지 식재료 인식",   cat: "vision" },
  { from: "fastapi",   to: "openclip",     label: "이미지 임베딩",        cat: "vision" },
  { from: "fastapi",   to: "mediapipe",    label: "자세 분석 요청",       cat: "vision" },
  { from: "simulator", to: "ppo",          label: "정책 추론 요청",       cat: "rl" },
  { from: "frontend",  to: "whisper",      label: "음성 데이터 전송",     cat: "voice" },
  { from: "whisper",   to: "fastapi",      label: "변환된 텍스트",        cat: "voice" },
  { from: "fastapi",   to: "gtts",         label: "TTS 생성 요청",       cat: "voice" },
  { from: "gtts",      to: "frontend",     label: "음성 응답 재생",       cat: "voice" },
  // RL 피드백 루프
  { from: "fastapi",   to: "retrain",      label: "피드백 → 재학습 트리거", cat: "rl" },
  { from: "retrain",   to: "optuna",       label: "하이퍼파라미터 최적화",  cat: "rl" },
  { from: "retrain",   to: "ppo",          label: "PPO 재학습 실행",       cat: "rl" },
  // 모델 동기화
  { from: "ppo",        to: "s3",          label: "모델 업로드",           cat: "data" },
  { from: "s3",         to: "frontend",    label: "모델 다운로드 (동기화)",  cat: "data" },
  { from: "gpu_train",  to: "s3",          label: "학습 모델 업로드",       cat: "rl" },
  { from: "gpu_train",  to: "ppo",         label: "PPO 학습 실행",         cat: "rl" },
  // 오프라인 + 배포
  { from: "frontend",  to: "offline",      label: "오프라인 추론 폴백",     cat: "api" },
  { from: "offline",   to: "capacitor",    label: "APK 내장 추론",         cat: "api" },
  { from: "frontend",  to: "vercel",       label: "CDN 배포",             cat: "api" },
  // 보안
  { from: "fastapi",   to: "jwt",          label: "인증 + Rate Limit",    cat: "api" },
  // 멀티모달 LLM 연결
  { from: "openclip",  to: "gpt4o",        label: "LLM 개인화 조언 생성",  cat: "llm" },
  // ── v0.3.0 데이터 흐름 연결 (5개 연결) ──
  { from: "frontend",  to: "orchestrator", label: "채팅 → 게이지 자동 업데이트", cat: "agent" },
  { from: "orchestrator", to: "supabase",  label: "연쇄효과 → 상태 영속 저장",  cat: "data" },
  { from: "frontend",  to: "supabase",     label: "온보딩 → 초기 상태 저장",    cat: "data" },
  { from: "ppo",       to: "simulator",    label: "PPO 최적 행동 추천",        cat: "rl" },
];

/* ------------------------------------------------------------------ */
/*  LAYOUT                                                             */
/* ------------------------------------------------------------------ */

const NODE_W = 210;
const NODE_H = 56;
const POPUP_W = 260;
const POPUP_H = 280;

// Tree layout: hand-tuned positions for maximum clarity
// Structure: Frontend (root) → Backend → branches fan out
const TREE_POS = {
  // Layer 0: Entry point (left)
  frontend:     { x: 40,   y: 280 },
  whisper:      { x: 40,   y: 500 },
  gtts:         { x: 40,   y: 620 },

  // Layer 1: Server core (center-left)
  fastapi:      { x: 340,  y: 280 },
  websocket:    { x: 340,  y: 140 },
  docker:       { x: 340,  y: 500 },
  railway:      { x: 340,  y: 620 },

  // Layer 2: Processing (center) — fanned out vertically
  orchestrator: { x: 680,  y: 100 },
  simulator:    { x: 680,  y: 300 },
  risk:         { x: 680,  y: 500 },

  // Layer 3: Domain agents — wide fan
  food:         { x: 1040, y: 40 },
  exercise:     { x: 1040, y: 200 },
  health:       { x: 1040, y: 360 },
  hobby:        { x: 1040, y: 520 },
  ppo:          { x: 1040, y: 680 },

  // Layer 4: AI/Data backends — spread right
  gpt4o:        { x: 1400, y: 40 },
  chromadb:     { x: 1400, y: 200 },
  supabase:     { x: 1400, y: 360 },
  s3:           { x: 1400, y: 520 },
  yolo:         { x: 1400, y: 680 },
  openclip:     { x: 1400, y: 840 },
  mediapipe:    { x: 1400, y: 1000 },

  // RL 확장
  retrain:      { x: 1040, y: 840 },
  optuna:       { x: 1040, y: 960 },

  // 배포 + 오프라인
  offline:      { x: 40,   y: 740 },
  capacitor:    { x: 40,   y: 880 },
  vercel:       { x: 340,  y: 740 },
  jwt:          { x: 340,  y: 880 },
  gpu_train:    { x: 680,  y: 680 },
};

const EXPANDED_POPUP_OFFSET = POPUP_H + 16;

function nodePos(node, expandedMode = false, pinnedSet = new Set()) {
  const base = TREE_POS[node.id] || { x: 100, y: 100 };
  let extraY = 0;
  if (expandedMode) {
    // In expanded mode, shift everything down to make room for popups
    // Count how many nodes above this one (by y) in the layout
    const aboveCount = Object.entries(TREE_POS).filter(([id, pos]) => pos.y < base.y).length;
    extraY = aboveCount * (EXPANDED_POPUP_OFFSET * 0.35);
  } else if (pinnedSet.size > 0) {
    const sorted = Object.entries(TREE_POS).sort((a, b) => a[1].y - b[1].y);
    for (const [id, pos] of sorted) {
      if (pos.y < base.y && pinnedSet.has(id)) {
        extraY += POPUP_H * 0.4;
      }
    }
  }
  return { x: base.x, y: base.y + extraY };
}

/* ------------------------------------------------------------------ */
/*  SVG helpers                                                        */
/* ------------------------------------------------------------------ */

function anchorRight(node, expanded, pinned) {
  const p = nodePos(node, expanded, pinned);
  return { x: p.x + NODE_W, y: p.y + NODE_H / 2 };
}
function anchorLeft(node, expanded, pinned) {
  const p = nodePos(node, expanded, pinned);
  return { x: p.x, y: p.y + NODE_H / 2 };
}

function curvePath(from, to, expanded, pinned) {
  const a = anchorRight(from, expanded, pinned);
  const b = anchorLeft(to, expanded, pinned);
  if (b.x <= a.x) {
    // Backward connection — loop around
    const loopOut = 60;
    const midY = Math.min(a.y, b.y) - 50;
    return `M ${a.x} ${a.y} C ${a.x + loopOut} ${a.y}, ${a.x + loopOut} ${midY}, ${(a.x + b.x) / 2} ${midY} S ${b.x - loopOut} ${b.y}, ${b.x} ${b.y}`;
  }
  // Forward connection — gentle S-curve with more horizontal space
  const dx = Math.min((b.x - a.x) * 0.4, 160);
  return `M ${a.x} ${a.y} C ${a.x + dx} ${a.y}, ${b.x - dx} ${b.y}, ${b.x} ${b.y}`;
}

/* ------------------------------------------------------------------ */
/*  COMPONENTS                                                         */
/* ------------------------------------------------------------------ */

function NodeRect({ node, isHighlighted, onClick, onMouseEnter, onMouseLeave, expanded, pinned }) {
  const { x, y } = nodePos(node, expanded, pinned);
  const s = STATUS_META[node.status];

  return (
    <g
      className="cursor-pointer"
      onClick={() => onClick(node.id)}
      onMouseEnter={() => onMouseEnter(node.id)}
      onMouseLeave={onMouseLeave}
    >
      <rect x={x - 2} y={y - 2} width={NODE_W + 4} height={NODE_H + 4} rx={14}
        fill="none" stroke={s.color} strokeWidth={isHighlighted ? 3 : 0} opacity={isHighlighted ? 0.6 : 0}
      />
      <rect x={x} y={y} width={NODE_W} height={NODE_H} rx={12}
        fill={isHighlighted ? s.bg : "#1f2937"} stroke={s.color} strokeWidth={1.5}
        className="transition-all duration-200"
      />
      <circle cx={x + 14} cy={y + NODE_H / 2} r={5} fill={s.color} />
      <text x={x + 28} y={y + NODE_H / 2} fontSize={16} dominantBaseline="central" className="select-none pointer-events-none">
        {node.emoji}
      </text>
      <text x={x + 48} y={y + NODE_H / 2} fontSize={12.5} fill="#e5e7eb" dominantBaseline="central" fontWeight={600} className="select-none pointer-events-none">
        {node.label.length > 24 ? node.label.slice(0, 23) + "\u2026" : node.label}
      </text>
    </g>
  );
}

function InlinePopup({ node, expanded, pinned }) {
  const { x, y } = nodePos(node, expanded, pinned);
  const s = STATUS_META[node.status];
  const popupX = x;
  const popupY = y + NODE_H + 6;

  const connected = [
    ...CONNECTIONS.filter((c) => c.from === node.id).map((c) => {
      const n = NODES.find((nd) => nd.id === c.to);
      return n ? `→ ${n.label}` : null;
    }),
    ...CONNECTIONS.filter((c) => c.to === node.id).map((c) => {
      const n = NODES.find((nd) => nd.id === c.from);
      return n ? `← ${n.label}` : null;
    }),
  ].filter(Boolean);

  return (
    <foreignObject x={popupX} y={popupY} width={POPUP_W} height={POPUP_H} className="pointer-events-none overflow-visible">
      <div className="bg-gray-800/95 border border-gray-600 rounded-lg shadow-xl p-2.5 backdrop-blur-sm"
        style={{ borderLeftColor: s.color, borderLeftWidth: 3, width: POPUP_W, maxHeight: POPUP_H, overflow: "hidden", fontSize: 10, lineHeight: 1.4 }}
      >
        <div className="flex items-center gap-1.5 mb-1">
          <span className={`font-bold ${s.text}`} style={{ fontSize: 11 }}>{s.label}</span>
          {node.role && <span className="text-cyan-400 font-medium" style={{ fontSize: 9 }}>{node.role}</span>}
        </div>
        <p className="text-gray-300 mb-1">{node.desc}</p>
        <div className="text-blue-400 font-mono truncate mb-1" style={{ fontSize: 9 }}>{node.path}</div>
        <div className="flex flex-wrap gap-0.5 mb-1">
          {node.features.map((f, i) => (
            <span key={i} className="px-1 py-0.5 rounded bg-gray-700/60 text-gray-400" style={{ fontSize: 9 }}>{f}</span>
          ))}
        </div>
        {node.pros && (
          <div className="text-emerald-400 mb-0.5" style={{ fontSize: 9 }}>
            <span className="text-emerald-500 font-bold">+</span> {node.pros}
          </div>
        )}
        {node.cons && (
          <div className="text-red-400 mb-0.5" style={{ fontSize: 9 }}>
            <span className="text-red-500 font-bold">-</span> {node.cons}
          </div>
        )}
        {node.reason && (
          <div className="text-yellow-300 mb-0.5" style={{ fontSize: 9 }}>
            <span className="text-yellow-400 font-bold">!</span> {node.reason}
          </div>
        )}
        {connected.length > 0 && (
          <div className="text-gray-500 truncate" style={{ fontSize: 9 }}>
            {connected.slice(0, 4).join(", ")}{connected.length > 4 ? ` +${connected.length - 4}` : ""}
          </div>
        )}
      </div>
    </foreignObject>
  );
}

function ConnectionLine({ conn, connIndex, nodes, hoveredConn, onEnter, onLeave, expanded, pinned, showAllLabels }) {
  const fromNode = nodes.find((n) => n.id === conn.from);
  const toNode = nodes.find((n) => n.id === conn.to);
  if (!fromNode || !toNode) return null;

  const cat = CONN_CATEGORIES[conn.cat] || CONN_CATEGORIES.api;
  const d = curvePath(fromNode, toNode, expanded, pinned);
  const key = `${conn.from}-${conn.to}`;
  const isHovered = hoveredConn === key;
  const showLabel = showAllLabels || isHovered;

  // Label position: offset along the curve to avoid overlap
  const a = anchorRight(fromNode, expanded, pinned);
  const b = anchorLeft(toNode, expanded, pinned);
  // Use t parameter (0.3-0.7) spread across connections to same target
  const t = 0.35 + (connIndex % 5) * 0.07;
  const labelX = a.x + (b.x - a.x) * t;
  const labelY = a.y + (b.y - a.y) * t - 14; // offset above the line

  const labelW = conn.label.length * 8.5 + 16;

  return (
    <g onMouseEnter={() => onEnter(key)} onMouseLeave={onLeave}>
      <path d={d} fill="none" stroke="transparent" strokeWidth={14} className="cursor-pointer" />
      <path d={d} fill="none" stroke={showLabel ? cat.color : "#374151"} strokeWidth={showLabel ? 2 : 1.2}
        markerEnd={`url(#arrow-${conn.cat})`} className="transition-all duration-200"
        opacity={showLabel ? 1 : 0.5}
      />
      {showLabel && (
        <g>
          <rect
            x={labelX - labelW / 2}
            y={labelY - 10}
            width={labelW}
            height={20}
            rx={4}
            fill={cat.bg}
            stroke={cat.border}
            strokeWidth={0.7}
            opacity={0.95}
          />
          <text
            x={labelX}
            y={labelY}
            textAnchor="middle"
            dominantBaseline="central"
            fill={cat.labelFill}
            fontSize={10}
            fontWeight={500}
            className="pointer-events-none select-none"
          >
            {conn.label}
          </text>
        </g>
      )}
    </g>
  );
}

/* ------------------------------------------------------------------ */
/*  PAGE                                                               */
/* ------------------------------------------------------------------ */

export default function ArchitecturePage() {
  const [pinnedIds, setPinnedIds] = useState(new Set());
  const [hoveredNodeId, setHoveredNodeId] = useState(null);
  const [hoveredConn, setHoveredConn] = useState(null);
  const [connTooltip, setConnTooltip] = useState(null);
  const [showAll, setShowAll] = useState(false);
  const wrapperRef = useRef(null);
  const svgRef = useRef(null);

  const pinnedSet = showAll ? new Set(NODES.map((n) => n.id)) : pinnedIds;

  const stats = useMemo(() => {
    const counts = { active: 0, partial: 0, pending: 0 };
    NODES.forEach((n) => counts[n.status]++);
    return counts;
  }, []);

  const handleNodeClick = useCallback((id) => {
    if (showAll) return; // In show-all mode, clicks don't toggle
    setPinnedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }, [showAll]);

  const toggleShowAll = useCallback(() => {
    setShowAll((prev) => {
      if (!prev) setPinnedIds(new Set()); // clear individual pins when entering show-all
      return !prev;
    });
  }, []);

  // Calculate SVG dimensions based on current expanded state
  const expanded = showAll;

  // Calculate SVG dimensions dynamically
  let maxX = 0, maxY = 0;
  NODES.forEach((n) => {
    const p = nodePos(n, expanded, pinnedSet);
    const rightX = p.x + NODE_W + 40;
    let bottomY = p.y + NODE_H;
    if (expanded || pinnedSet.has(n.id)) {
      bottomY += POPUP_H + 16;
    }
    if (rightX > maxX) maxX = rightX;
    if (bottomY > maxY) maxY = bottomY;
  });
  const svgWidth = maxX + 40;
  const svgHeight = maxY + 60;

  // Visible popup nodes: hovered (not pinned) or pinned
  const hoverPopupNode = hoveredNodeId && !pinnedSet.has(hoveredNodeId) ? NODES.find((n) => n.id === hoveredNodeId) : null;

  return (
    <Layout>
      <div className="p-4 lg:p-6 space-y-4 relative">
        {/* Title + stats */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <h1 className="text-2xl font-bold text-white">Architecture Map</h1>

          <div className="flex items-center gap-4 text-sm">
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
              <span className="text-gray-300">활성: {stats.active}</span>
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
              <span className="text-gray-300">부분구현: {stats.partial}</span>
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-gray-500" />
              <span className="text-gray-300">대기: {stats.pending}</span>
            </span>
            <span className="text-gray-500">|</span>
            <span className="text-gray-300">전체: {NODES.length}</span>
          </div>
        </div>

        {/* Connection color legend */}
        <div className="flex flex-wrap items-center gap-3 text-xs">
          <span className="text-gray-500 font-medium">연결선:</span>
          {Object.entries(CONN_CATEGORIES).map(([key, cat]) => (
            <span key={key} className="flex items-center gap-1">
              <span className="w-5 h-0.5 rounded" style={{ backgroundColor: cat.color }} />
              <span className="text-gray-400">{cat.legend}</span>
            </span>
          ))}
        </div>

        {/* Controls */}
        <div className="flex items-center gap-4 text-xs text-gray-400">
          <span>호버: 상세 미리보기 · 클릭: 고정 · 다시 클릭: 해제</span>
          <button
            onClick={toggleShowAll}
            className={`ml-auto px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              showAll
                ? "bg-cyan-600 hover:bg-cyan-500 text-white"
                : "bg-gray-700 hover:bg-gray-600 text-gray-300"
            }`}
          >
            {showAll ? "접기" : "전체보기"}
          </button>
          {pinnedIds.size > 0 && !showAll && (
            <button
              onClick={() => setPinnedIds(new Set())}
              className="px-3 py-2 rounded-lg text-sm bg-gray-700 hover:bg-gray-600 text-gray-300"
            >
              모두 해제 ({pinnedIds.size})
            </button>
          )}
        </div>

        {/* SVG canvas */}
        <div
          ref={wrapperRef}
          className="w-full overflow-x-auto rounded-xl border border-gray-700 bg-gray-950/60 relative"
          onMouseMove={(e) => {
            if (hoveredConn) {
              const rect = wrapperRef.current?.getBoundingClientRect();
              if (rect) {
                setConnTooltip({
                  label: CONNECTIONS.find((c) => `${c.from}-${c.to}` === hoveredConn)?.label || "",
                  x: e.clientX - rect.left + 12,
                  y: e.clientY - rect.top - 28,
                });
              }
            }
          }}
        >
          <svg
            ref={svgRef}
            viewBox={`0 0 ${svgWidth} ${svgHeight}`}
            width={svgWidth}
            height={svgHeight}
            className="min-w-[1100px]"
            style={{ transition: "height 0.3s ease, width 0.3s ease" }}
          >
            <defs>
              <marker id="arrowhead" markerWidth={8} markerHeight={6} refX={8} refY={3} orient="auto">
                <polygon points="0 0, 8 3, 0 6" fill="#6b7280" />
              </marker>
              {Object.entries(CONN_CATEGORIES).map(([key, cat]) => (
                <marker key={key} id={`arrow-${key}`} markerWidth={8} markerHeight={6} refX={8} refY={3} orient="auto">
                  <polygon points="0 0, 8 3, 0 6" fill={cat.color} />
                </marker>
              ))}
            </defs>

            {/* layer labels */}
            {[
              { x: 145, label: "User Interface" },
              { x: 445, label: "Server / Infra" },
              { x: 785, label: "Orchestration" },
              { x: 1145, label: "Domain Agents" },
              { x: 1505, label: "AI / Data" },
            ].map(({ x, label }) => (
              <text key={label} x={x} y={20}
                textAnchor="middle" fill="#4b5563" fontSize={12} fontWeight={600}
              >
                {label}
              </text>
            ))}

            {/* connections */}
            {CONNECTIONS.map((conn, idx) => (
              <ConnectionLine
                key={`${conn.from}-${conn.to}`}
                conn={conn}
                connIndex={idx}
                nodes={NODES}
                hoveredConn={hoveredConn}
                onEnter={setHoveredConn}
                onLeave={() => { setHoveredConn(null); setConnTooltip(null); }}
                expanded={expanded}
                pinned={pinnedSet}
                showAllLabels={showAll}
              />
            ))}

            {/* nodes */}
            {NODES.map((node) => (
              <NodeRect
                key={node.id}
                node={node}
                isHighlighted={pinnedSet.has(node.id) || hoveredNodeId === node.id}
                onClick={handleNodeClick}
                onMouseEnter={setHoveredNodeId}
                onMouseLeave={() => setHoveredNodeId(null)}
                expanded={expanded}
                pinned={pinnedSet}
              />
            ))}

            {/* Pinned popups (inline in SVG, below each node) */}
            {NODES.filter((n) => pinnedSet.has(n.id)).map((node) => (
              <InlinePopup key={`popup-${node.id}`} node={node} expanded={expanded} pinned={pinnedSet} />
            ))}

            {/* Hover popup (only for non-pinned, as SVG foreignObject) */}
            {hoverPopupNode && (
              <InlinePopup node={hoverPopupNode} expanded={expanded} pinned={pinnedSet} />
            )}
          </svg>

          {/* Connection tooltip (HTML, follows cursor) */}
          {connTooltip && connTooltip.label && (
            <div
              className="absolute pointer-events-none z-40 px-3 py-1.5 rounded-md bg-slate-900 border border-blue-500/60 text-blue-300 text-xs font-medium whitespace-nowrap shadow-lg"
              style={{ left: connTooltip.x, top: connTooltip.y }}
            >
              {connTooltip.label}
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
}
