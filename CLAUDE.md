# LifeSync AI — Claude Code 프로젝트 컨텍스트 (v0.4.0)

## 프로젝트 개요
- 프로젝트명: LifeSync AI
- 설명: 4개 도메인(요리/운동/건강/취미)을 하나의 유기체로 통합 관리하는 AI 에이전트
- 팀: 6명 | 기간: 4주 | 루트 폴더: MOMA/lifesync-ai/

## 기술 스택
| 영역 | 기술 |
|------|------|
| Backend | Python 3.11, FastAPI, WebSocket, LangGraph, LangChain |
| AI/ML | GPT-4o-mini, OpenCLIP, MediaPipe, YOLOv8, PPO(Stable-Baselines3), Optuna |
| DB | ChromaDB (Vector/RAG), Supabase PostgreSQL (State) |
| Frontend | React 18, Recharts, Tailwind CSS, Capacitor (Android APK) |
| Infra | Railway ($5/월), Vercel (무료 CDN), AWS S3, Docker Compose |

## 아키텍처: Router 분리 패턴
```
main.py (290줄 — 미들웨어 + 플러그인 등록 + 라우터 등록만. 관리자만 수정)
  ├→ routers/ai_router.py    ← 그룹 A 전담 (사진분석, 시뮬레이션, 모델동기화)
  ├→ routers/api_router.py   ← 그룹 B 전담 (쿼리, 인증, 대시보드, WebSocket)
  ├→ routers/admin_router.py ← 전체 관리 (팀 진행, 충돌 감지, 백업, 보안 감사)
  └→ frontend/src/           ← 그룹 C 전담 (14개 페이지, 컴포넌트)
```

## 데이터 흐름 (v0.4.0 — 7개 연결)
```
[온보딩] → POST /api/onboarding → Supabase → LifeEnv 초기 상태
    ↓
[대시보드] ← GET /api/dashboard/{uid} + WebSocket gauge_update (Samsung Health 스타일)
    ↓
[채팅/솔루션] → POST /api/query → Orchestrator → Agent → CASCADE → updated_gauges
    ↓
[시뮬레이터] → POST /api/simulation/step → PPO optimal_action 추천
    ↓
[사진] → POST /api/photo/upload → YOLO → POST /api/query → 게이지 업데이트
    ↓
[전체 관리] → GET /api/admin/* → git 통계, 충돌 감지, 백업, 보안 감사
    ↓
[피드백] → POST /api/feedback → reward → RetainScheduler → PPO 재학습
```

## 폴더 구조
```
lifesync-ai/
├── backend/
│   ├── app/
│   │   ├── main.py                    # 미들웨어(보안헤더/CORS/JWT/RateLimit) + 라우터 등록
│   │   └── routers/
│   │       ├── ai_router.py           # 그룹A: /api/photo, /api/simulation, /api/models, /api/rl
│   │       ├── api_router.py          # 그룹B: /api/query, /api/dashboard, /api/auth, /api/onboarding, /ws
│   │       └── admin_router.py        # 전체관리: /api/admin/team-progress, conflicts, backup, security-audit
│   ├── agents/
│   │   ├── orchestrator.py            # LangGraph StateGraph (8노드 DAG, CASCADE_RULES)
│   │   ├── food_agent.py              # GPT-4o-mini + ChromaDB RAG (레시피 추천)
│   │   ├── exercise_agent.py          # 운동 추천 (미세먼지/부상 고려)
│   │   ├── health_agent.py            # 건강검진 분석 (temp=0.3, 보수적)
│   │   └── hobby_agent.py             # 스트레스 기반 취미 추천
│   ├── rl_engine/
│   │   ├── env/life_env.py            # Gymnasium Env (40D 상태, 10 행동, 84스텝)
│   │   ├── ppo_agent.py               # PPO (Stable-Baselines3)
│   │   ├── reward_cross_domain.py     # 다축 보상 함수 + 야식/위험 패널티
│   │   ├── auto_tuner.py              # Optuna 100 trial Bayesian 탐색
│   │   ├── retrain_scheduler.py       # 6h 주기 자동 재학습
│   │   ├── schedule_simulator.py      # 24시간 스케줄 N일 시뮬레이션
│   │   └── uncertainty_estimator.py   # 예측 불확실성 추정
│   ├── multimodal/
│   │   ├── clip_embedder.py           # OpenCLIP ViT-B-32 512D 임베딩
│   │   ├── photo_analyzer.py          # CLIP + MediaPipe → LLM 개인화 조언
│   │   ├── food_recognizer.py         # YOLOv8 식재료 감지 (CPU ~100ms)
│   │   └── pose_analyzer.py           # MediaPipe 33 랜드마크 자세 분석
│   ├── knowledge/
│   │   ├── chroma_client.py           # ChromaDB 공통 클라이언트
│   │   ├── recipe_db.py               # 10만건 레시피 (쿼리 확장 + 리랭킹)
│   │   ├── exercise_db.py             # 운동 + 부상 데이터
│   │   ├── health_guidelines.py       # 건강검진 가이드라인
│   │   └── hobby_catalog.py           # 취미 카탈로그
│   ├── risk_engine/
│   │   ├── food_risk_scorer.py        # 베이지안 음식 위험도
│   │   ├── night_meal_penalty.py      # 야식 패널티 (23시: -5)
│   │   ├── timeline_generator.py      # 이벤트 타임라인
│   │   └── health_models.py           # 6개 건강 모델
│   ├── voice/
│   │   ├── stt_processor.py           # Whisper STT
│   │   ├── intent_classifier.py       # LLM + 키워드 도메인 분류
│   │   └── tts_responder.py           # gTTS 응답
│   ├── services/
│   │   ├── user_state_manager.py      # Supabase 40D State 벡터 관리
│   │   ├── feedback_collector.py      # 피드백 → Reward 변환
│   │   ├── kakao_auth.py              # 카카오 OAuth + JWT 발급/검증
│   │   ├── model_registry.py          # S3 모델 버전 관리 (SHA256)
│   │   ├── gamification.py            # 레벨, EXP, 칭호 시스템
│   │   ├── quest_system.py            # 일일 퀘스트 (3개 건강 미션)
│   │   └── input_validator.py         # 입력 검증 (파일/텍스트)
│   ├── dashboard/gauge_calculator.py  # 6개 게이지 점수 계산
│   └── environment/
│       ├── weather_monitor.py         # 기상청 단기예보 + 에어코리아 대기오염 API
│       └── plan_adjuster.py           # 날씨 → 운동 플랜 자동 조정
├── frontend/src/
│   ├── pages/ (13개)                  # Landing, Login, Onboarding, Dashboard(Samsung Health),
│   │                                  # Analysis, Simulator(+로드맵 탭), Schedule, Avatar, Report,
│   │                                  # Architecture, Admin, TeamLeader (전체 관리)
│   ├── components/                    # GaugePanel, QuickChat, CascadeAlert, AvatarBody(걷기) 등
│   ├── context/                       # AppStateContext (전역 상태), ThemeContext (라이트/다크)
│   └── services/offlineEngine.js      # IndexedDB 모델 캐싱 + smartSimulate
├── data/                              # recipes.csv, exercises.json, health_guidelines.json
├── scripts/                           # start.bat, train_and_upload.py
├── tests/                             # E2E, 에이전트, RL, 음성, API 에러 테스트
├── docs/                              # 보고서 (html, docx, md)
└── frontend/android/                  # Capacitor Android APK 빌드
```

## 아키텍처: 코어 + 플러그인
```
코어 (폴백으로 기본 동작 보장)
  ├→ core/interfaces.py      ← Protocol 정의 (플러그인 계약)
  ├→ core/fallbacks.py       ← 규칙 기반 기본 구현 (LLM 없이 동작)
  ├→ core/plugin_registry.py ← 플러그인 등록/조회 싱글톤
  └→ plugins/                ← 팀원별 독립 폴더
       ├→ food_rag/          ← 팀원 A (RAG 고도화)
       ├→ exercise_weather/  ← 팀원 B (운동+날씨)
       ├→ health_checkup/    ← 팀원 C (건강검진)
       ├→ hobby_stress/      ← 팀원 D (취미+스트레스)
       ├→ vision_korean/     ← 팀원 E (한식 YOLO)
       └→ voice_stt/         ← 팀원 F (음성 STT/TTS)
```

### 플러그인 규칙
1. 팀원은 **자기 plugins/ 폴더만** 수정 (다른 폴더 수정 금지)
2. plugin.py의 register() 함수에서 레지스트리에 등록
3. 구현 안 하면 → 폴백(BasicAgent)이 자동 동작 → 프로젝트에 영향 없음
4. 구현 완료하면 → 코어에 자동 연결 → 시너지 효과
5. GET /api/plugins/status 로 활성/폴백 상태 조회 가능

## 팀 분업 (6명)
| 팀원 | 플러그인 폴더 | 담당 | 코어 폴백 |
|------|-------------|------|----------|
| A | plugins/food_rag/ | RAG 레시피 추천 + LangChain | BasicFoodAgent |
| B | plugins/exercise_weather/ | 운동+날씨+부상 | BasicExerciseAgent |
| C | plugins/health_checkup/ | 건강검진 분석 | BasicHealthAgent |
| D | plugins/hobby_stress/ | 취미+스트레스 시너지 | BasicHobbyAgent |
| E | plugins/vision_korean/ | YOLO 한식 + CLIP | BasicImageAnalyzer |
| F | plugins/voice_stt/ | Whisper STT + gTTS | BasicVoiceProcessor |

### 충돌 방지 규칙
1. 팀원은 **plugins/자기폴더/** 만 수정 → git 충돌 원천 차단
2. main.py, core/ 수정 필요 시 관리자에게 PR 요청
3. 각 팀원은 자기 브랜치에서 작업 → PR로 main 병합
4. CODEOWNERS: 파일별 자동 리뷰어 배정

## 보안 (v0.4.0)
- JWT 인증: 프로덕션에서 JWT_SECRET 필수 (미설정 시 서버 시작 거부)
- WebSocket: 프로덕션에서 토큰 없으면 연결 거부
- Rate Limit: IP별 분당 60회
- 보안 헤더: XSS, Clickjacking, HSTS
- 입력 검증: user_id 정규식, 모델명 정규식, 파일 확장자 화이트리스트
- 경로 트래버설 방지: models/ 디렉터리 밖 접근 차단
- PUBLIC_PATHS: 관리 API(backup 등)는 인증 필요 (v0.4.0 강화)
- WebSocket 데이터 검증: VALID_KEYS 화이트리스트로 게이지 값 검증 (v0.4.0)

## 보상 함수
```
R(s,a,t) = w1*taste + w2*health + w3*fitness + w4*mood + w5*habit
           - penalty_night - penalty_risk - penalty_skip + bonus
```

## 환경변수 (.env)
```
OPENAI_API_KEY=              # OpenAI API 키
DATABASE_URL=                # postgresql://...supabase.co/postgres
CHROMA_PATH=/data/chroma
JWT_SECRET=                  # python -c "import secrets; print(secrets.token_urlsafe(64))"
KAKAO_CLIENT_ID=             # 카카오 REST API 키
KAKAO_CLIENT_SECRET=         # 카카오 Client Secret
KAKAO_REDIRECT_URI=http://localhost:5173/auth/kakao/callback
ENV=development              # development | production
CORS_ORIGINS=http://localhost:5173,http://localhost:8000
```

## 코드 컨벤션
- Python: Black, 타입 힌트, docstring Google 스타일
- JS/JSX: Prettier, 함수형 컴포넌트, props 타입 명시
- 커밋: feat: / fix: / docs: / test: / refactor:
- 환경변수: 절대 하드코딩 금지

## 전역 제한사항 (모든 팀원 필수)

### 절대 금지
1. `.env` 파일 내용을 코드에 하드코딩 금지
2. `main.py`, `core/` 디렉토리 직접 수정 금지 (관리자 PR 필수)
3. `orchestrator.py`의 `run_chain()` 시그니처 변경 금지
4. `main` 브랜치 직접 push 금지 (PR로만 병합)
5. 다른 팀원의 `plugins/` 폴더 수정 금지
6. `requirements.txt`, `docker-compose.yml` 무단 수정 금지

### 필수 준수
1. 자기 `plugins/자기폴더/` 안에서만 코드 작성
2. `core/interfaces.py`의 Protocol 메서드 시그니처를 정확히 구현
3. `plugin.py`의 `register(registry)` 함수로만 코어에 연결
4. 새 라이브러리 추가 시 반드시 **버전 고정** + 관리자 승인
5. 모든 함수에 **타입 힌트 + docstring** 필수
6. 테스트 코드를 `plugins/자기폴더/tests/`에 작성

### 인터페이스 계약 (변경 불가)
```python
# DomainAgent — food/exercise/hobby 에이전트
def recommend(self, user_state: dict[str, Any]) -> dict[str, Any]:
    # 반환 필수 키: recommendations(list), explanation(str)

# HealthAgent — 건강 에이전트 (오케스트레이터가 analyze_checkup() 호출)
def analyze_checkup(self, user_state: dict[str, Any]) -> dict[str, Any]:
    # 반환 필수 키: recommendations(list), explanation(str)
def recommend(self, user_state: dict[str, Any]) -> dict[str, Any]:
    # analyze_checkup()으로 위임

# KnowledgeBase — RAG 지식베이스
def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:

# RLAgent — 강화학습 에이전트
def predict(self, state: Any) -> tuple[int, float]:  # (action, confidence)
def train(self, total_timesteps: int = 10000) -> dict[str, Any]:

# ImageAnalyzer — 이미지 분석
def analyze(self, image_bytes: bytes) -> dict[str, Any]:

# VoiceProcessor — 음성 처리
def speech_to_text(self, audio_bytes: bytes) -> str:
def text_to_speech(self, text: str) -> bytes:
```

## 팀원별 CLAUDE.md 위치
각 플러그인 폴더에 독립 CLAUDE.md가 있습니다:
```
plugins/food_rag/CLAUDE.md        ← 팀원 A 전용 컨텍스트
plugins/exercise_weather/CLAUDE.md ← 팀원 B 전용 컨텍스트
plugins/health_checkup/CLAUDE.md   ← 팀원 C 전용 컨텍스트
plugins/hobby_stress/CLAUDE.md     ← 팀원 D 전용 컨텍스트
plugins/vision_korean/CLAUDE.md    ← 팀원 E 전용 컨텍스트
plugins/voice_stt/CLAUDE.md        ← 팀원 F 전용 컨텍스트
```
Claude Code / Cursor가 해당 폴더에서 작업 시 자동으로 읽습니다.

## v0.4.0 주요 변경 사항

### 신규 기능
- 전체 관리 대시보드 (TeamLeaderPage): 4탭 (아키텍처/팀활동/백업/보안)
- Samsung Health 스타일 대시보드: 모니터링 허브 + 솔루션/인사이트/코칭 3탭
- 라이트 모드 전역 전환: Samsung Blue (#1a73e8), 다크/라이트 토글
- 걸어다니는 아바타 캐릭터: CSS 걷기 애니메이션, BMI별 보폭/속도
- admin_router.py: 7개 관리 API (team-progress, conflicts, backup, security-audit 등)

### 버그 수정 19건 + 품질 개선 5건
- WebSocket 재연결 타이머/의존성/데이터 검증 수정 (B1,B2,N5,F1)
- BasicHealthAgent analyze_checkup() 메서드 추가 (B5)
- PUBLIC_PATHS 보안 강화 (N1)
- GaugePanel 이중 state 제거 → 전역만 사용 (C2)
- 폴백 에이전트에 is_fallback: true 표시 + 로그 추가 (C3)
- 플러그인 등록 시 인터페이스 검증 추가 (C4)
- 게이지 RadialBarChart domain=[0,100] 스케일 수정

### 문서
- docs/architecture-report-v7.docx: 24개 섹션, 262 paragraphs
- docs/report.html: v0.4.0 변경 이력 + 다이어그램 업데이트
- ArchitecturePage: admin_router, TeamLeader, Dashboard v2 노드 추가

## 에이전트 점검 현황 (자동 업데이트)
- 마지막 점검: 2026-03-30 03:29 UTC
- 전체 건강도: 82/100
- 코드 품질: 80/100 (pass:5 fail:1 warn:0)
- 플러그인: active 6개 / fallback 5개
- CASCADE 규칙: 9개 활성
- API 서비스: 3개 정상 / 환경변수 3개 설정
- 보안 점수: 100/100 (이슈 1건)

### 보안 주의사항
- ENV=development - 인증 우회 활성 (개발 전용)
