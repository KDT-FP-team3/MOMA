# LifeSync AI — Claude Code 프로젝트 컨텍스트 (v0.3.0)

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
main.py (180줄 — 미들웨어 + 라우터 등록만. 팀장만 수정)
  ├→ routers/ai_router.py    ← 그룹 A 전담 (사진분석, 시뮬레이션, 모델동기화)
  ├→ routers/api_router.py   ← 그룹 B 전담 (쿼리, 인증, 대시보드, WebSocket)
  └→ frontend/src/           ← 그룹 C 전담 (11개 페이지, 컴포넌트)
```

## 데이터 흐름 (v0.3.0 — 5개 연결 완료)
```
[온보딩] → POST /api/onboarding → Supabase → LifeEnv 초기 상태
    ↓
[대시보드] ← GET /api/dashboard/{uid} + WebSocket gauge_update
    ↓
[채팅] → POST /api/query → Orchestrator → Agent → CASCADE → updated_gauges
    ↓
[시뮬레이터] → POST /api/simulation/step → PPO optimal_action 추천
    ↓
[사진] → POST /api/photo/upload → YOLO → POST /api/query → 게이지 업데이트
```

## 폴더 구조
```
lifesync-ai/
├── backend/
│   ├── app/
│   │   ├── main.py                    # 미들웨어(보안헤더/CORS/JWT/RateLimit) + 라우터 등록
│   │   └── routers/
│   │       ├── ai_router.py           # 그룹A: /api/photo, /api/simulation, /api/models, /api/rl
│   │       └── api_router.py          # 그룹B: /api/query, /api/dashboard, /api/auth, /api/onboarding, /ws
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
│       ├── weather_monitor.py         # AirKorea + OpenWeather API
│       └── plan_adjuster.py           # 날씨 → 운동 플랜 자동 조정
├── frontend/src/
│   ├── pages/ (11개)                  # Landing, Login, Onboarding, Dashboard, Analysis,
│   │                                  # Simulator, Schedule, Roadmap, Avatar, Report, Architecture
│   ├── components/                    # GaugePanel, QuickChat, ErrorBarChart, AvatarBody 등
│   ├── context/                       # AppStateContext (전역 상태), ThemeContext
│   └── services/offlineEngine.js      # IndexedDB 모델 캐싱 + smartSimulate
├── data/                              # recipes.csv, exercises.json, health_guidelines.json
├── scripts/                           # start.bat, train_and_upload.py
├── tests/                             # E2E, 에이전트, RL, 음성, API 에러 테스트
├── docs/                              # 보고서 (html, docx, md)
└── frontend/android/                  # Capacitor Android APK 빌드
```

## 팀 분업 (3그룹)
| 그룹 | 라우터 | 담당 모듈 |
|------|--------|-----------|
| A (AI/ML) 2명 | ai_router.py | rl_engine, multimodal, knowledge, risk_engine, scripts |
| B (백엔드) 2명 | api_router.py | agents, voice, services, dashboard, environment |
| C (프론트) 2명 | frontend/src/ | pages, components, context, services, android |

### 충돌 방지 규칙
1. 그룹 A는 ai_router.py만, 그룹 B는 api_router.py만 수정
2. main.py 수정 필요 시 팀장에게 PR 요청
3. 각 그룹은 자기 브랜치에서 작업 → PR로 main 병합

## 보안 (v0.3.0)
- JWT 인증: 프로덕션에서 JWT_SECRET 필수 (미설정 시 서버 시작 거부)
- WebSocket: 프로덕션에서 토큰 없으면 연결 거부
- Rate Limit: IP별 분당 60회
- 보안 헤더: XSS, Clickjacking, HSTS
- 입력 검증: user_id 정규식, 모델명 정규식, 파일 확장자 화이트리스트
- 경로 트래버설 방지: models/ 디렉터리 밖 접근 차단

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

## 금지 사항
1. .env 파일 내용을 코드에 하드코딩 금지
2. requirements.txt, docker-compose.yml 무단 수정 금지
3. orchestrator.py의 run_chain() 시그니처 변경 금지 (팀장 승인 필수)
4. main 브랜치 직접 push 금지
5. 새 라이브러리 추가 시 반드시 버전 고정
